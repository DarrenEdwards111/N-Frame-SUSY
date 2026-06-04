import argparse

import numpy as np
import pandas as pd

from common import PROCESSED_DIR, ensure_dirs


FEATURES = ["MET", "HT_or_meff", "N_jets", "N_leptons", "N_btags"]
BONUS_TERMS = {
    "compressed": ["compressed", "soft", "isr"],
    "disappearing_track": ["disappearing", "tracklet"],
    "long_lived": ["long_lived", "long-lived", "llp"],
    "displaced": ["displaced", "vertex", "dv"],
    "high_MET": ["high_met", "high-missing", "met_high"],
    "high_multiplicity": ["high_multiplicity", "many_jets", "nj10", "nj12", "entropy"],
}


def zscore(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    mean = vals.mean(skipna=True)
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - mean) / std).fillna(0.0)


def category_bonus(category: str) -> int:
    text = str(category).lower()
    return sum(1 for terms in BONUS_TERMS.values() if any(term in text for term in terms))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute deviations and N-Frame boundary-access scores.")
    parser.add_argument("--input", default=PROCESSED_DIR / "signal_regions.csv")
    parser.add_argument("--output", default=PROCESSED_DIR / "signal_regions_scored.csv")
    args = parser.parse_args()

    ensure_dirs()
    df = pd.read_csv(args.input)
    df["Delta_N"] = df["N_obs"] - df["N_exp"]
    df["Z"] = df["Delta_N"] / df["sigma_exp"]

    for feature in FEATURES:
        df[f"z_{feature}"] = zscore(df[feature])

    df["category_bonus"] = df["category"].map(category_bonus)
    df["B_access"] = df[[f"z_{f}" for f in FEATURES]].sum(axis=1) + df["category_bonus"]
    df["B_access_z"] = zscore(df["B_access"])
    df.to_csv(args.output, index=False)
    print(f"Wrote scored table with {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
