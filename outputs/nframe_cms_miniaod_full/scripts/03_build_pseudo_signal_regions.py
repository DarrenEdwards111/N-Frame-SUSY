from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "event_features_nframe_scored.csv"


def summarize(df, name, sub):
    return {
        "pseudo_region": name,
        "N_events": len(sub),
        "mean_MET": sub.MET_pt.mean() if len(sub) else None,
        "mean_HT": sub.HT.mean() if len(sub) else None,
        "mean_Njets30": sub.N_jets_30.mean() if len(sub) else None,
        "mean_Nleptons": sub.N_leptons.mean() if len(sub) else None,
        "mean_Nbtags_medium": sub.N_btags_medium.mean() if len(sub) else None,
        "mean_MET_fraction": sub.MET_fraction.mean() if len(sub) else None,
        "mean_S_event_proxy": sub.S_event_proxy.mean() if len(sub) else None,
        "mean_B_event_z": sub.B_event_z.mean() if len(sub) else None,
        "mean_R_missing": sub.R_missing.mean() if len(sub) else None,
        "mean_R_multiplicity": sub.R_multiplicity.mean() if len(sub) else None,
        "mean_R_reconstruction": sub.R_reconstruction.mean() if len(sub) else None,
    }


def main():
    df = pd.read_csv(SRC)
    regions = {
        "SR1_low_boundary": df[(df.MET_pt < 150) & (df.N_jets_30 < 4)],
        "SR2_medium_MET": df[(df.MET_pt >= 150) & (df.MET_pt < 250)],
        "SR3_high_MET": df[df.MET_pt >= 250],
        "SR4_high_MET_high_jets": df[(df.MET_pt >= 250) & (df.N_jets_30 >= 6)],
        "SR5_high_boundary": df[df.B_event_z >= 1],
        "SR6_extreme_boundary": df[df.B_event_z >= 2],
        "SR7_high_MET_fraction": df[df.MET_fraction >= 0.4],
        "SR8_high_multiplicity": df[df.N_jets_30 >= 8],
        "SR9_high_reconstruction": df[df.R_reconstruction >= 1],
        "SR10_high_missing": df[df.R_missing >= 1],
    }
    out = pd.DataFrame([summarize(df, name, sub) for name, sub in regions.items()])
    out.to_csv(ROOT / "data" / "processed" / "pseudo_signal_regions_from_cmssw.csv", index=False)
    out.to_csv(ROOT / "results" / "tables" / "pseudo_signal_regions_from_cmssw.csv", index=False)
    print(out)


if __name__ == "__main__":
    main()
