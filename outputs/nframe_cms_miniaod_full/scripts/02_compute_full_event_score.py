import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def zscore(series):
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "processed" / "event_features.csv"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "processed" / "event_features_nframe_scored.csv"
    df = pd.read_csv(src)
    if "MET_fraction" not in df:
        df["MET_fraction"] = df["MET_pt"] / (df["HT"].fillna(0) + df["MET_pt"].fillna(0) + 1.0)
    if "N_objects" not in df:
        df["N_objects"] = df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0) + df["N_btags_medium"].fillna(0)
    if "S_event_proxy" not in df:
        df["S_event_proxy"] = np.log1p(df["N_objects"])
    if "high_MET" not in df:
        df["high_MET"] = (df["MET_pt"] >= 250).astype(int)
    if "high_multiplicity" not in df:
        df["high_multiplicity"] = (df["N_jets_30"] >= 6).astype(int)

    df["z_MET"] = zscore(df["MET_pt"])
    df["z_HT"] = zscore(df["HT"])
    df["z_Njets"] = zscore(df["N_jets_30"])
    df["z_Nleptons"] = zscore(df["N_leptons"])
    df["z_Nbtags"] = zscore(df["N_btags_medium"])
    df["z_MET_fraction"] = zscore(df["MET_fraction"])
    df["z_S_event"] = zscore(df["S_event_proxy"])
    df["z_N_objects"] = zscore(df["N_objects"])
    df["B_event"] = (
        df["z_MET"]
        + df["z_HT"]
        + df["z_Njets"]
        + df["z_Nleptons"]
        + df["z_Nbtags"]
        + df["z_MET_fraction"]
        + df["z_S_event"]
    )
    df["B_event_z"] = zscore(df["B_event"])
    df["R_missing"] = df["z_MET"] + df["z_MET_fraction"] + df["high_MET"]
    df["R_multiplicity"] = df["z_Njets"] + df["z_Nleptons"] + df["z_Nbtags"] + df["high_multiplicity"]
    df["R_reconstruction"] = df["z_MET_fraction"] + df["z_S_event"] + df["z_N_objects"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False)
    print(f"Wrote {dst} ({len(df)} rows)")


if __name__ == "__main__":
    main()
