import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT / "data" / "processed" / "signal_regions_metadata_enriched.csv"
DEFAULT_OUTPUT = PROJECT / "data" / "processed" / "signal_regions_metadata_complete_model_inputs.csv"
DEFAULT_MISSINGNESS = PROJECT / "results" / "tables" / "complete_model_metadata_missingness.csv"


FEATURES = [
    "MET_enriched",
    "HT_or_meff_enriched",
    "N_jets_enriched",
    "N_leptons_enriched",
    "N_btags_enriched",
]


def fill_numeric(df, col):
    flag_col = col.replace("_enriched", "") + "_imputed"
    df[flag_col] = df[col].isna().astype(int)

    # Prefer within-analysis medians so analysis families keep their scale.
    analysis_median = df.groupby("analysis")[col].transform("median")
    global_median = df[col].median()
    if not np.isfinite(global_median):
        global_median = 0.0
    df[col + "_complete"] = df[col].fillna(analysis_median).fillna(global_median).fillna(0.0)
    return flag_col, col + "_complete"


def main():
    parser = argparse.ArgumentParser(
        description="Create a 0%-missing model-input metadata table with explicit imputation flags."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--missingness-output", default=str(DEFAULT_MISSINGNESS))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    flag_cols = []
    complete_cols = []
    for col in FEATURES:
        flag, complete = fill_numeric(df, col)
        flag_cols.append(flag)
        complete_cols.append(complete)

    df["category_imputed"] = df["category_enriched"].isna().astype(int)
    df["category_enriched_complete"] = df["category_enriched"].fillna("uncategorized")
    flag_cols.append("category_imputed")
    complete_cols.append("category_enriched_complete")
    df["metadata_imputation_count"] = df[flag_cols].sum(axis=1)
    df["metadata_verified_fraction"] = 1.0 - (df["metadata_imputation_count"] / len(flag_cols))

    missingness = []
    for col in complete_cols:
        missingness.append(
            {
                "column": col,
                "missing_count": int(df[col].isna().sum()),
                "missing_fraction": float(df[col].isna().mean()),
            }
        )
    missingness = pd.DataFrame(missingness)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.missingness_output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    missingness.to_csv(args.missingness_output, index=False)
    print(f"Wrote complete model-input table: {args.output}")
    print(missingness.to_string(index=False))
    print("Important: *_complete columns are model inputs, not fully verified extracted SR metadata.")


if __name__ == "__main__":
    main()
