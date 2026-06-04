import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES_DIR, PROCESSED_DIR, TABLES_DIR, ensure_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Make N-Frame boundary-access diagnostic plots.")
    parser.add_argument("--input", default=PROCESSED_DIR / "signal_regions_scored.csv")
    args = parser.parse_args()

    ensure_dirs()
    df = pd.read_csv(args.input)
    ranked_b = df["B_access_z"].rank(method="first")
    df["B_quartile"] = pd.qcut(ranked_b, q=4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    median_b = df["B_access_z"].median()
    df["B_group"] = df["B_access_z"].ge(median_b).map({False: "Low B", True: "High B"})

    plt.figure(figsize=(7, 5))
    x = df["B_access_z"].to_numpy()
    y = df["Z"].to_numpy()
    plt.scatter(x, y, s=22, alpha=0.65)
    slope, intercept = np.polyfit(x, y, 1)
    xs = np.linspace(np.nanmin(x), np.nanmax(x), 100)
    plt.plot(xs, intercept + slope * xs, color="#C44E52", linewidth=2)
    plt.xlabel("B_access_z")
    plt.ylabel("Z")
    plt.grid(alpha=0.25)
    plt.title("Boundary-access score vs Z")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "b_access_vs_z.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 5))
    y = df["Delta_N"].to_numpy()
    plt.scatter(x, y, s=22, alpha=0.65, color="#4C78A8")
    slope, intercept = np.polyfit(x, y, 1)
    plt.plot(xs, intercept + slope * xs, color="#C44E52", linewidth=2)
    plt.xlabel("B_access_z")
    plt.ylabel("Delta_N")
    plt.grid(alpha=0.25)
    plt.title("Boundary-access score vs observed-minus-expected")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "b_access_vs_delta_n.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 5))
    quartiles = ["Q1 low", "Q2", "Q3", "Q4 high"]
    grouped = [df.loc[df["B_quartile"].astype(str) == q, "Z"].to_numpy() for q in quartiles]
    plt.boxplot(grouped, labels=quartiles, patch_artist=True)
    means = [np.nanmean(g) for g in grouped]
    plt.plot(range(1, len(means) + 1), means, marker="o", color="#C44E52", linewidth=2)
    plt.ylabel("Z")
    plt.grid(axis="y", alpha=0.25)
    plt.title("Z by boundary-access quartile")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "mean_z_by_b_access_quartile.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 5))
    low = df.loc[df["B_group"] == "Low B", "Z"].to_numpy()
    high = df.loc[df["B_group"] == "High B", "Z"].to_numpy()
    bins = np.histogram_bin_edges(df["Z"].to_numpy(), bins=24)
    plt.hist(low, bins=bins, density=True, histtype="step", linewidth=2, label="Low B")
    plt.hist(high, bins=bins, density=True, histtype="step", linewidth=2, label="High B")
    plt.xlabel("Z")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.title("Z distribution for low-B and high-B regions")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "z_hist_low_high_b.png", dpi=180)
    plt.close()

    forest = (
        df.groupby(["analysis", "B_group"], as_index=False)
        .agg(mean_Z=("Z", "mean"), n=("Z", "size"))
        .pivot(index="analysis", columns="B_group", values="mean_Z")
        .reset_index()
    )
    forest.to_csv(TABLES_DIR / "mean_z_low_high_by_analysis.csv", index=False)

    with open(TABLES_DIR / "plot_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "figures": [
                    "b_access_vs_z.png",
                    "b_access_vs_delta_n.png",
                    "mean_z_by_b_access_quartile.png",
                    "z_hist_low_high_b.png",
                ],
                "tables": ["mean_z_low_high_by_analysis.csv"],
            },
            handle,
            indent=2,
        )
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
