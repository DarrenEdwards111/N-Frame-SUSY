import argparse
from pathlib import Path

import pandas as pd

from common import PROCESSED_DIR, TABLES_DIR, read_features, ensure_dirs


def summarize(df, name, mask):
    sub = df.loc[mask]
    return {
        "pseudo_signal_region": name,
        "N_events": len(sub),
        "mean_MET": sub["MET_pt"].mean(),
        "mean_HT": sub["HT"].mean(),
        "mean_Njets": sub["N_jets_30"].mean(),
        "mean_Njets50": sub["N_jets_50"].mean() if "N_jets_50" in sub else float("nan"),
        "mean_B_event_jetonly_z": sub["B_event_jetonly_z"].mean() if "B_event_jetonly_z" in sub else float("nan"),
        "mean_B_event_z": sub["B_event_z"].mean(),
        "mean_MET_fraction": sub["MET_fraction"].mean(),
        "mean_S_event_proxy": sub["S_event_proxy"].mean(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pseudo signal-region summaries from event scores.")
    parser.add_argument("--input", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    parser.add_argument("--output", default=str(PROCESSED_DIR / "pseudo_signal_regions.csv"))
    args = parser.parse_args()

    ensure_dirs()
    df = read_features(Path(args.input))
    regions = []
    if df["MET_pt"].notna().any():
        regions.extend(
            [
                ("SR1_low_boundary", (df["MET_pt"] < 150) & (df["N_jets_30"] < 4)),
                ("SR2_medium_MET", (df["MET_pt"] >= 150) & (df["MET_pt"] < 250)),
                ("SR3_high_MET", df["MET_pt"] >= 250),
                ("SR4_high_MET_high_jets", (df["MET_pt"] >= 250) & (df["N_jets_30"] >= 6)),
                ("SR7_high_MET_fraction", df["MET_fraction"] >= 0.4),
            ]
        )
    regions.extend(
        [
            ("JSR1_low_jet_boundary", (df["HT"] < 300) & (df["N_jets_30"] < 4)),
            ("JSR2_medium_HT", (df["HT"] >= 300) & (df["HT"] < 700)),
            ("JSR3_high_HT", df["HT"] >= 700),
            ("JSR4_high_HT_high_jets", (df["HT"] >= 700) & (df["N_jets_30"] >= 6)),
            ("JSR5_high_jet_boundary", df["B_event_jetonly_z"] >= 1),
            ("JSR6_extreme_jet_boundary", df["B_event_jetonly_z"] >= 2),
            ("JSR7_high_multiplicity", df["N_jets_30"] >= 8),
            ("JSR8_many_hard_jets", df["N_jets_50"] >= 6),
        ]
    )
    out = pd.DataFrame([summarize(df, name, mask) for name, mask in regions])
    out.to_csv(args.output, index=False)
    out.to_csv(TABLES_DIR / "pseudo_signal_region_summary.csv", index=False)
    print(out)


if __name__ == "__main__":
    main()
