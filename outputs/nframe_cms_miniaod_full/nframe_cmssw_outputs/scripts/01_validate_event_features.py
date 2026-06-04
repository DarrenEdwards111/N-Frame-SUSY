import sys
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED = ["MET_pt", "HT", "N_jets_30", "N_leptons", "N_btags_medium", "MET_fraction", "S_event_proxy"]
COUNTS = ["N_jets_all", "N_jets_30", "N_jets_50", "N_muons", "N_electrons", "N_leptons", "N_btags_medium"]


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/processed/event_features.csv")
    df = pd.read_csv(path)
    print(f"file: {path}")
    print(f"rows: {len(df)}")
    for col in REQUIRED:
        print(f"{col}_exists: {col in df}")
    if len(df):
        print(f"MET_nonzero_fraction: {(df['MET_pt'] > 0).mean() if 'MET_pt' in df else np.nan}")
        print(f"lepton_nonzero_fraction: {(df['N_leptons'] > 0).mean() if 'N_leptons' in df else np.nan}")
        print(f"btag_nonzero_fraction: {(df['N_btags_medium'] > 0).mean() if 'N_btags_medium' in df else np.nan}")
        for col in COUNTS:
            if col in df:
                print(f"{col}_negative_count: {int((df[col] < 0).sum())}")
        if "MET_fraction" in df:
            print(f"MET_fraction_outside_0_1_count: {int(((df.MET_fraction < -0.001) | (df.MET_fraction > 1.001)).sum())}")
        if "S_event_proxy" in df:
            print(f"S_event_proxy_nonfinite_count: {int((~np.isfinite(df.S_event_proxy)).sum())}")
    if all(col in df for col in REQUIRED):
        print(df[REQUIRED].describe().to_string())


if __name__ == "__main__":
    main()
