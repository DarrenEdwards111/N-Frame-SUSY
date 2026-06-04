import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, FIGURES, ensure_dirs, MODEL_FEATURES, BOOL_FIELDS


def main():
    parser = argparse.ArgumentParser(description="Make verified metadata diagnostic plots.")
    parser.add_argument("--verified-only", default=PROCESSED / "signal_regions_verified_only_scored.csv")
    parser.add_argument("--verified-imputed", default=PROCESSED / "signal_regions_verified_plus_imputed_scored.csv")
    args = parser.parse_args()
    ensure_dirs()
    vo = pd.read_csv(args.verified_only)
    vi = pd.read_csv(args.verified_imputed)

    fields = MODEL_FEATURES + BOOL_FIELDS
    coverage = []
    for field in fields:
        col = f"{field}_verified"
        if col in vo:
            coverage.append({"field": field, "verified_coverage": vo[col].mean()})
    cov = pd.DataFrame(coverage)
    cov.to_csv(TABLES / "verified_coverage_by_field.csv", index=False)
    plt.figure(figsize=(9, 5))
    plt.bar(cov["field"], cov["verified_coverage"])
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 1)
    plt.ylabel("Verified coverage")
    plt.tight_layout()
    plt.savefig(FIGURES / "verified_coverage_by_field.png", dpi=180)
    plt.close()

    for df, score, name in [
        (vo, "B_access_verified_z", "verified_only"),
        (vi, "B_access_verified_imputed_z", "verified_plus_imputed"),
    ]:
        plot_df = df[[score, "Z"]].dropna()
        if len(plot_df):
            plt.figure(figsize=(6, 5))
            plt.scatter(plot_df[score], plot_df["Z"], s=10, alpha=0.45)
            plt.xlabel(score)
            plt.ylabel("Z")
            plt.grid(alpha=0.25)
            plt.tight_layout()
            plt.savefig(FIGURES / f"{name}_b_access_vs_z.png", dpi=180)
            plt.close()

    if "experiment" in vi:
        exp = vi.groupby("experiment")[[f"{f}_verified" for f in fields if f"{f}_verified" in vi]].mean().T
        exp.plot(kind="bar", figsize=(10, 5))
        plt.ylabel("Verified coverage")
        plt.tight_layout()
        plt.savefig(FIGURES / "verified_coverage_by_experiment.png", dpi=180)
        plt.close()
    print(f"Wrote verified plots to {FIGURES}")


if __name__ == "__main__":
    main()
