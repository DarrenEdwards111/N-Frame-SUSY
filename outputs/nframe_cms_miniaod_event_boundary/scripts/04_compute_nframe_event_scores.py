import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from common import PROCESSED_DIR, read_features, write_features, ensure_dirs


def zscore(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute event-level N-Frame boundary-access scores.")
    parser.add_argument("--input", default=str(PROCESSED_DIR / "event_features.parquet"))
    parser.add_argument("--output", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    args = parser.parse_args()

    ensure_dirs()
    df = read_features(Path(args.input))
    met_available = "MET_pt" in df and df["MET_pt"].notna().any()
    leptons_available = "N_leptons" in df and df["N_leptons"].notna().any()
    df["MET_fraction"] = df["MET_pt"] / (df["HT"].fillna(0) + df["MET_pt"].fillna(0) + 1)
    df["N_objects"] = df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0)
    df["Visible_HT"] = df["HT"]
    nb = df["N_btags_medium"] if "N_btags_medium" in df else pd.Series(np.nan, index=df.index)
    df["Nb_missing"] = nb.isna().astype(int)
    df["S_event_proxy"] = np.log1p(df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0) + nb.fillna(0))
    df["high_MET"] = (df["MET_pt"] >= 250).astype(int) if met_available else 0
    df["high_multiplicity"] = (df["N_jets_30"] >= 6).astype(int)
    df["R_reconstruction"] = (
        zscore(df["MET_fraction"])
        + zscore(df["N_objects"])
        + (zscore(nb) if nb.notna().any() else 0)
        + df["high_MET"]
        + df["high_multiplicity"]
    )

    df["B_event_jetonly"] = zscore(df["HT"]) + zscore(df["N_jets_30"]) + zscore(df["N_jets_50"]) + zscore(df["S_event_proxy"])
    df["B_event_jetonly_z"] = zscore(df["B_event_jetonly"])

    components = [zscore(df["HT"]), zscore(df["N_jets_30"]), zscore(df["S_event_proxy"])]
    if met_available:
        components.extend([zscore(df["MET_pt"]), zscore(df["MET_fraction"])])
    if leptons_available:
        components.append(zscore(df["N_leptons"]))
    if nb.notna().any():
        components.append(zscore(nb))
    df["B_event"] = sum(components)
    df["B_event_z"] = zscore(df["B_event"])
    if met_available and leptons_available and nb.notna().any():
        df["B_event_status"] = "full_uproot_features"
    else:
        df["B_event_status"] = "partial_jet_level_real_miniaod"
    write_features(df, Path(args.output))
    if Path(args.output).suffix.lower() == ".parquet":
        df.head(1000).to_csv(PROCESSED_DIR / "event_features_nframe_scored_head.csv", index=False)
    print(f"Wrote scored event features: {args.output}")


if __name__ == "__main__":
    main()
