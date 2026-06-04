import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES_DIR, PROCESSED_DIR, read_features, ensure_dirs


def save_hist(df, col, filename, bins=60, logy=True):
    if col not in df:
        return
    plt.figure(figsize=(7, 5))
    plt.hist(df[col].dropna(), bins=bins)
    if logy:
        plt.yscale("log")
    plt.xlabel(col)
    plt.ylabel("Events")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / filename, dpi=170)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Make event-level N-Frame plots.")
    parser.add_argument("--input", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    parser.add_argument("--max-scatter", type=int, default=50000)
    args = parser.parse_args()

    ensure_dirs()
    df = read_features(Path(args.input))
    for col, name in [
        ("MET_pt", "met_distribution.png"),
        ("HT", "ht_distribution.png"),
        ("N_jets_30", "njets_distribution.png"),
        ("B_event_jetonly_z", "b_event_jetonly_z_distribution.png"),
        ("B_event_z", "b_event_z_distribution.png"),
    ]:
        save_hist(df, col, name)

    sample = df.sample(min(len(df), args.max_scatter), random_state=7)
    if sample["MET_pt"].notna().any():
        plt.figure(figsize=(7, 5))
        sc = plt.scatter(sample["MET_pt"], sample["HT"], c=sample["B_event_z"], s=5, alpha=0.55, cmap="viridis")
        plt.xlabel("MET_pt")
        plt.ylabel("HT")
        plt.colorbar(sc, label="B_event_z")
        plt.grid(alpha=0.25)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "met_vs_ht_colored_by_b_event_z.png", dpi=170)
        plt.close()

    plt.figure(figsize=(7, 5))
    sc = plt.scatter(sample["N_jets_30"], sample["HT"], c=sample["B_event_jetonly_z"], s=5, alpha=0.55, cmap="viridis")
    plt.xlabel("N_jets_30")
    plt.ylabel("HT")
    plt.colorbar(sc, label="B_event_jetonly_z")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "njets_vs_ht_colored_by_b_event_jetonly_z.png", dpi=170)
    plt.close()

    df["B_quartile"] = pd.qcut(df["B_event_z"].rank(method="first"), q=4, labels=["Q1", "Q2", "Q3", "Q4"])
    q = df.groupby("B_quartile", observed=False).agg(
        MET_pt=("MET_pt", "mean"),
        N_jets_30=("N_jets_30", "mean"),
        MET_fraction=("MET_fraction", "mean"),
    )
    for col, filename in [
        ("MET_pt", "b_quartile_vs_mean_met.png"),
        ("N_jets_30", "b_quartile_vs_mean_njets.png"),
        ("MET_fraction", "b_quartile_vs_mean_met_fraction.png"),
    ]:
        if col not in q or q[col].isna().all():
            continue
        plt.figure(figsize=(6, 4))
        plt.plot(q.index.astype(str), q[col], marker="o")
        plt.xlabel("B quartile")
        plt.ylabel(f"Mean {col}")
        plt.grid(alpha=0.25)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / filename, dpi=170)
        plt.close()

    cols = [
        c
        for c in ["MET_pt", "HT", "N_jets_30", "N_jets_50", "leading_jet_pt", "N_leptons", "N_btags_medium", "MET_fraction", "S_event_proxy", "B_event_jetonly_z", "B_event_z"]
        if c in df and df[c].notna().any()
    ]
    corr = df[cols].corr(numeric_only=True)
    plt.figure(figsize=(8, 7))
    im = plt.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    plt.xticks(range(len(cols)), cols, rotation=45, ha="right")
    plt.yticks(range(len(cols)), cols)
    plt.colorbar(im, label="Correlation")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "event_variable_correlation_heatmap.png", dpi=170)
    plt.close()
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
