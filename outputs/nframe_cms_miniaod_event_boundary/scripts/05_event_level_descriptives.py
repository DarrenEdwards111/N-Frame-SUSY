import argparse
from pathlib import Path

import pandas as pd

from common import PROCESSED_DIR, TABLES_DIR, read_features, ensure_dirs


SUMMARY_COLS = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_jets_50",
    "leading_jet_pt",
    "N_leptons",
    "N_btags_medium",
    "MET_fraction",
    "S_event_proxy",
    "B_event_jetonly_z",
    "B_event_z",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize event-level N-Frame variables.")
    parser.add_argument("--input", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    args = parser.parse_args()

    ensure_dirs()
    df = read_features(Path(args.input))
    cols = [col for col in SUMMARY_COLS if col in df.columns]
    summary = df[cols].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
    summary.to_csv(TABLES_DIR / "event_level_summary.csv")
    df["B_quartile"] = pd.qcut(df["B_event_z"].rank(method="first"), q=4, labels=["Q1", "Q2", "Q3", "Q4"])
    quartile = df.groupby("B_quartile", observed=False).agg(
        N_events=("B_event_z", "size"),
        mean_MET=("MET_pt", "mean"),
        mean_HT=("HT", "mean"),
        mean_Njets=("N_jets_30", "mean"),
        mean_Njets50=("N_jets_50", "mean"),
        mean_Nleptons=("N_leptons", "mean"),
        mean_MET_fraction=("MET_fraction", "mean"),
        mean_B_event_jetonly_z=("B_event_jetonly_z", "mean"),
        mean_B_event_z=("B_event_z", "mean"),
    )
    missing = pd.DataFrame(
        [
            {"column": col, "missing_fraction": float(df[col].isna().mean()), "nonmissing": int(df[col].notna().sum())}
            for col in df.columns
        ]
    )
    quartile.to_csv(TABLES_DIR / "b_quartile_summary.csv")
    missing.to_csv(TABLES_DIR / "event_feature_missingness.csv", index=False)
    print(f"Wrote summaries to {TABLES_DIR}")


if __name__ == "__main__":
    main()
