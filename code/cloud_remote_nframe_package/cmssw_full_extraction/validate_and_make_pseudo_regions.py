import sys
from pathlib import Path

import pandas as pd


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "event_features_nframe_scored.csv")
    out_dir = src.resolve().parent
    df = pd.read_csv(src)
    cols = ["MET_pt", "HT", "N_jets_30", "N_leptons", "N_btags_medium", "MET_fraction", "S_event_proxy", "B_event_z"]
    with open(out_dir / "event_feature_validation.txt", "w", encoding="utf-8") as out:
        out.write(f"N events: {len(df)}\n")
        out.write(df[cols].describe().to_string())
        out.write("\n")
        out.write(f"MET nonzero fraction: {(df['MET_pt'] > 0).mean()}\n")
        out.write(f"lepton nonzero fraction: {(df['N_leptons'] > 0).mean()}\n")
        out.write(f"btag nonzero fraction: {(df['N_btags_medium'] > 0).mean()}\n")
        out.write(f"high MET fraction: {(df['high_MET'] == 1).mean()}\n")
        out.write(f"high multiplicity fraction: {(df['high_multiplicity'] == 1).mean()}\n")

    regions = {
        "SR1_low_boundary": df[(df.MET_pt < 150) & (df.N_jets_30 < 4)],
        "SR2_medium_MET": df[(df.MET_pt >= 150) & (df.MET_pt < 250)],
        "SR3_high_MET": df[df.MET_pt >= 250],
        "SR4_high_MET_high_jets": df[(df.MET_pt >= 250) & (df.N_jets_30 >= 6)],
        "SR5_high_boundary": df[df.B_event_z >= 1],
        "SR6_extreme_boundary": df[df.B_event_z >= 2],
        "SR7_high_MET_fraction": df[df.MET_fraction >= 0.4],
        "SR8_high_multiplicity": df[df.N_jets_30 >= 8],
    }
    rows = []
    for name, sub in regions.items():
        rows.append(
            {
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
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "pseudo_signal_regions_from_cmssw.csv", index=False)
    print(out)


if __name__ == "__main__":
    main()
