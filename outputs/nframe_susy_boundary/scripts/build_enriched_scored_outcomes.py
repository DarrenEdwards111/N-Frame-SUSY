import argparse
from pathlib import Path

import pandas as pd

from compute_boundary_score import zscore, category_bonus, FEATURES


PROJECT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Build scored outcomes using enriched signal-region metadata.")
    parser.add_argument("--input", default=str(PROJECT / "data" / "processed" / "signal_regions_metadata_enriched.csv"))
    parser.add_argument("--output", default=str(PROJECT / "data" / "processed" / "signal_regions_metadata_enriched_scored_outcomes.csv"))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    remap = {
        "MET_enriched": "MET",
        "HT_or_meff_enriched": "HT_or_meff",
        "N_jets_enriched": "N_jets",
        "N_leptons_enriched": "N_leptons",
        "N_btags_enriched": "N_btags",
        "category_enriched": "category",
    }
    for src, dst in remap.items():
        if src in df:
            df[dst] = df[src]

    df["Delta_N"] = df["N_obs"] - df["N_exp"]
    df["Z"] = df["Delta_N"] / df["sigma_exp"]
    for feature in FEATURES:
        df[f"z_{feature}"] = zscore(df[feature])
    df["category_bonus"] = df["category"].map(category_bonus)
    df["B_access"] = df[[f"z_{f}" for f in FEATURES]].sum(axis=1) + df["category_bonus"]
    df["B_access_z"] = zscore(df["B_access"])
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(df)} rows)")


if __name__ == "__main__":
    main()
