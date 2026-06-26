import sys

import numpy as np
import pandas as pd


def zscore(series):
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 compute_full_event_score.py event_features.csv event_features_nframe_scored.csv")
    src, dst = sys.argv[1], sys.argv[2]
    df = pd.read_csv(src)
    if "N_jets_all" not in df and "N_jets" in df:
        df["N_jets_all"] = df["N_jets"]
    df["MET_fraction"] = df["MET_pt"] / (df["HT"].fillna(0) + df["MET_pt"].fillna(0) + 1.0)
    df["N_objects"] = df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0)
    df["S_event_proxy"] = np.log1p(
        df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0) + df["N_btags_medium"].fillna(0)
    )
    df["high_MET"] = (df["MET_pt"] >= 250).astype(int)
    df["high_multiplicity"] = (df["N_jets_30"] >= 6).astype(int)
    components = [
        zscore(df["MET_pt"]),
        zscore(df["HT"]),
        zscore(df["N_jets_30"]),
        zscore(df["N_jets_50"]),
        zscore(df["N_leptons"]),
        zscore(df["N_btags_medium"]),
        zscore(df["MET_fraction"]),
        zscore(df["S_event_proxy"]),
        df["high_MET"],
        df["high_multiplicity"],
    ]
    df["B_event"] = sum(components)
    df["B_event_z"] = zscore(df["B_event"])
    df.to_csv(dst, index=False)
    print("wrote", dst, "rows", len(df))


if __name__ == "__main__":
    main()
