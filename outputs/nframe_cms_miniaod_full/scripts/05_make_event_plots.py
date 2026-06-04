from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "event_features_nframe_scored.csv"
FIG = ROOT / "results" / "figures"


def hist(df, col, name):
    plt.figure(figsize=(7, 5))
    plt.hist(df[col].dropna(), bins=60)
    plt.yscale("log")
    plt.xlabel(col)
    plt.ylabel("Events")
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=170)
    plt.close()


def main():
    df = pd.read_csv(SRC)
    for col, name in [
        ("MET_pt", "met_pt_hist.png"),
        ("HT", "ht_hist.png"),
        ("N_jets_30", "njets30_hist.png"),
        ("N_leptons", "nleptons_hist.png"),
        ("N_btags_medium", "nbtags_medium_hist.png"),
        ("B_event_z", "b_event_z_hist.png"),
    ]:
        hist(df, col, name)

    sample = df.sample(min(len(df), 50000), random_state=7)
    plt.figure(figsize=(7, 5))
    sc = plt.scatter(sample.MET_pt, sample.HT, c=sample.B_event_z, s=5, alpha=0.5)
    plt.xlabel("MET_pt")
    plt.ylabel("HT")
    plt.colorbar(sc, label="B_event_z")
    plt.tight_layout()
    plt.savefig(FIG / "met_vs_ht_colored_by_b_event_z.png", dpi=170)
    plt.close()

    pseudo = ROOT / "results" / "tables" / "pseudo_signal_regions_from_cmssw.csv"
    if pseudo.exists():
        ps = pd.read_csv(pseudo)
        plt.figure(figsize=(10, 5))
        plt.bar(ps.pseudo_region, ps.mean_B_event_z)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Mean B_event_z")
        plt.tight_layout()
        plt.savefig(FIG / "b_event_z_by_pseudo_signal_region.png", dpi=170)
        plt.close()

    cols = ["MET_pt", "HT", "N_jets_30", "N_leptons", "N_btags_medium", "MET_fraction", "S_event_proxy", "B_event_z", "R_missing", "R_multiplicity", "R_reconstruction"]
    corr = df[cols].corr(numeric_only=True)
    plt.figure(figsize=(9, 8))
    im = plt.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    plt.xticks(range(len(cols)), cols, rotation=45, ha="right")
    plt.yticks(range(len(cols)), cols)
    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig(FIG / "event_variable_correlation_heatmap.png", dpi=170)
    plt.close()
    print(f"Wrote plots to {FIG}")


if __name__ == "__main__":
    main()
