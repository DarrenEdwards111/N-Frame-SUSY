from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "event_features_nframe_scored.csv"
COLS = ["MET_pt", "HT", "N_jets_30", "N_leptons", "N_btags_medium", "MET_fraction", "S_event_proxy", "B_event_z", "R_missing", "R_multiplicity", "R_reconstruction"]


def main():
    df = pd.read_csv(SRC)
    df[COLS].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T.to_csv(ROOT / "results" / "tables" / "event_level_summary.csv")
    df["B_quartile"] = pd.qcut(df["B_event_z"].rank(method="first"), q=4, labels=["Q1", "Q2", "Q3", "Q4"])
    q = df.groupby("B_quartile", observed=False).agg(
        N_events=("B_event_z", "size"),
        mean_MET=("MET_pt", "mean"),
        mean_HT=("HT", "mean"),
        mean_Njets30=("N_jets_30", "mean"),
        mean_Nleptons=("N_leptons", "mean"),
        mean_Nbtags=("N_btags_medium", "mean"),
        mean_MET_fraction=("MET_fraction", "mean"),
        mean_S_event_proxy=("S_event_proxy", "mean"),
        mean_R_missing=("R_missing", "mean"),
        mean_R_multiplicity=("R_multiplicity", "mean"),
        mean_R_reconstruction=("R_reconstruction", "mean"),
    )
    q.to_csv(ROOT / "results" / "tables" / "b_event_quartile_summary.csv")
    print(f"Wrote descriptives for {len(df)} events")


if __name__ == "__main__":
    main()
