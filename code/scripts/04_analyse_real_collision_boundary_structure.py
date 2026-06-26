from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from real_collision_common import FIGURES, PROCESSED, REPORTS, TABLES, ensure_dirs


INPUT = PROCESSED / "real_collision_20gb_event_features_scored.csv"


def iqr(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return float("nan")
    return float(values.quantile(0.75) - values.quantile(0.25))


def safe_mean(df: pd.DataFrame, col: str) -> float:
    return float(pd.to_numeric(df[col], errors="coerce").mean()) if col in df else float("nan")


def sample_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rows = []
    for key, group in df.groupby(group_col):
        score = group["B_boundary_equal_weight_z"]
        rows.append(
            {
                group_col: key,
                "n_events": len(group),
                "mean_B_boundary_equal_weight_z": score.mean(),
                "sd_B_boundary_equal_weight_z": score.std(),
                "median_B_boundary_equal_weight_z": score.median(),
                "iqr_B_boundary_equal_weight_z": iqr(score),
                "pct_global_top_10": 100 * group["boundary_top_10"].mean(),
                "pct_global_top_05": 100 * group["boundary_top_05"].mean(),
                "pct_global_top_01": 100 * group["boundary_top_01"].mean(),
                "mean_MET_pt": safe_mean(group, "MET_pt"),
                "mean_HT": safe_mean(group, "HT"),
                "mean_N_jets_30": safe_mean(group, "N_jets_30"),
                "mean_N_btags_medium": safe_mean(group, "N_btags_medium"),
                "mean_N_muons": safe_mean(group, "N_muons"),
                "mean_N_electrons": safe_mean(group, "N_electrons"),
            }
        )
    return pd.DataFrame(rows)


def high_tail_enrichment(df: pd.DataFrame) -> pd.DataFrame:
    try:
        from scipy.stats import chi2_contingency
    except Exception:
        chi2_contingency = None

    rows = []
    total_counts = df["sample_id"].value_counts().sort_index()
    total_n = len(df)
    for flag in ["boundary_top_10", "boundary_top_05", "boundary_top_01"]:
        tail = df[df[flag] == True]
        observed = tail["sample_id"].value_counts().reindex(total_counts.index, fill_value=0)
        expected = total_counts * (len(tail) / total_n)
        if chi2_contingency is not None and len(tail) > 0:
            contingency = np.vstack([observed.values, (total_counts - observed).values])
            chi2, pvalue, _, _ = chi2_contingency(contingency)
        else:
            chi2, pvalue = np.nan, np.nan
        for sample_id in total_counts.index:
            exp = expected.loc[sample_id]
            resid = (observed.loc[sample_id] - exp) / math.sqrt(exp) if exp > 0 else np.nan
            rows.append(
                {
                    "tail": flag,
                    "sample_id": sample_id,
                    "observed": int(observed.loc[sample_id]),
                    "expected": float(exp),
                    "standardised_residual_simple": float(resid),
                    "chi_square": float(chi2) if np.isfinite(chi2) else np.nan,
                    "p_value": float(pvalue) if np.isfinite(pvalue) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def pairwise_tests(df: pd.DataFrame) -> pd.DataFrame:
    try:
        from scipy.stats import ks_2samp, mannwhitneyu, ttest_ind
    except Exception:
        ks_2samp = mannwhitneyu = ttest_ind = None
    samples = sorted(df["sample_id"].unique())
    rows = []
    for i, left in enumerate(samples):
        for right in samples[i + 1 :]:
            a = pd.to_numeric(df.loc[df["sample_id"] == left, "B_boundary_equal_weight_z"], errors="coerce").dropna()
            b = pd.to_numeric(df.loc[df["sample_id"] == right, "B_boundary_equal_weight_z"], errors="coerce").dropna()
            pooled = math.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / max(1, len(a) + len(b) - 2))
            cohen_d = (a.mean() - b.mean()) / pooled if pooled else np.nan
            row = {
                "comparison": f"{left} vs {right}",
                "left_sample": left,
                "right_sample": right,
                "n_left": len(a),
                "n_right": len(b),
                "mean_left": a.mean(),
                "mean_right": b.mean(),
                "mean_difference_left_minus_right": a.mean() - b.mean(),
                "cohen_d": cohen_d,
                "welch_t": np.nan,
                "welch_p": np.nan,
                "mann_whitney_u": np.nan,
                "mann_whitney_p": np.nan,
                "ks_statistic": np.nan,
                "ks_p": np.nan,
            }
            if ttest_ind is not None:
                t = ttest_ind(a, b, equal_var=False, nan_policy="omit")
                mw = mannwhitneyu(a, b, alternative="two-sided")
                ks = ks_2samp(a, b)
                row.update(
                    {
                        "welch_t": t.statistic,
                        "welch_p": t.pvalue,
                        "mann_whitney_u": mw.statistic,
                        "mann_whitney_p": mw.pvalue,
                        "ks_statistic": ks.statistic,
                        "ks_p": ks.pvalue,
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def component_driver_summary(df: pd.DataFrame) -> pd.DataFrame:
    components = [
        "R_missing",
        "R_multiplicity",
        "R_reconstruction",
        "R_compression_proxy",
        "R_lifetime_proxy",
        "R_displacement_proxy",
    ]
    rows = []
    score = pd.to_numeric(df["B_boundary_equal_weight_z"], errors="coerce")
    quantile_label = pd.cut(
        score,
        bins=[-np.inf, score.quantile(0.5), score.quantile(0.75), score.quantile(0.9), score.quantile(0.95), score.quantile(0.99), np.inf],
        labels=["bottom_50", "top_50_to_25", "top_25_to_10", "top_10_to_05", "top_05_to_01", "top_01"],
        include_lowest=True,
    )
    df = df.assign(boundary_quantile_band=quantile_label)
    for component in components:
        if component not in df:
            continue
        values = pd.to_numeric(df[component], errors="coerce")
        corr = values.corr(score) if values.notna().any() else np.nan
        for band, group in df.groupby("boundary_quantile_band", observed=False):
            rows.append(
                {
                    "component": component,
                    "available": values.notna().any(),
                    "correlation_with_B_z": corr,
                    "boundary_quantile_band": str(band),
                    "mean_component": pd.to_numeric(group[component], errors="coerce").mean(),
                    "n_events": len(group),
                }
            )
    return pd.DataFrame(rows)


def make_plots(df: pd.DataFrame, enrichment: pd.DataFrame, driver: pd.DataFrame) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    samples = sorted(df["sample_id"].unique())
    plt.figure(figsize=(10, 6))
    for sample in samples:
        values = df.loc[df["sample_id"] == sample, "B_boundary_equal_weight_z"].dropna()
        plt.hist(values, bins=80, alpha=0.45, density=True, label=sample)
    plt.xlabel("B_boundary_equal_weight_z")
    plt.ylabel("Density")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES / "real_collision_boundary_score_histogram_by_sample.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 6))
    data = [df.loc[df["sample_id"] == sample, "B_boundary_equal_weight_z"].dropna() for sample in samples]
    plt.boxplot(data, labels=samples, showfliers=False)
    plt.ylabel("B_boundary_equal_weight_z")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "real_collision_boundary_score_boxplot_by_sample.png", dpi=160)
    plt.close()

    if "HT" in df:
        plt.figure(figsize=(8, 6))
        plot_df = df.sample(min(100000, len(df)), random_state=1)
        plt.scatter(plot_df["HT"], plot_df["B_boundary_equal_weight_z"], s=2, alpha=0.25)
        plt.xlabel("HT from jets > 30")
        plt.ylabel("B_boundary_equal_weight_z")
        plt.tight_layout()
        plt.savefig(FIGURES / "real_collision_B_score_vs_HT.png", dpi=160)
        plt.close()

    if "MET_pt" in df and pd.to_numeric(df["MET_pt"], errors="coerce").notna().any():
        plt.figure(figsize=(8, 6))
        plot_df = df.sample(min(100000, len(df)), random_state=2)
        plt.scatter(plot_df["MET_pt"], plot_df["B_boundary_equal_weight_z"], s=2, alpha=0.25)
        plt.xlabel("MET pt")
        plt.ylabel("B_boundary_equal_weight_z")
        plt.tight_layout()
        plt.savefig(FIGURES / "real_collision_B_score_vs_MET.png", dpi=160)
        plt.close()

    top05 = enrichment[enrichment["tail"] == "boundary_top_05"].copy()
    if not top05.empty:
        plt.figure(figsize=(10, 6))
        plt.bar(top05["sample_id"], top05["standardised_residual_simple"])
        plt.axhline(0, color="black", linewidth=0.8)
        plt.ylabel("Top 5% residual")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(FIGURES / "real_collision_top05_enrichment_bar.png", dpi=160)
        plt.close()

    heat = driver.pivot_table(index="component", columns="boundary_quantile_band", values="mean_component", aggfunc="mean")
    if not heat.empty:
        plt.figure(figsize=(10, 5))
        plt.imshow(heat.fillna(0), aspect="auto", cmap="viridis")
        plt.colorbar(label="Mean component")
        plt.yticks(range(len(heat.index)), heat.index)
        plt.xticks(range(len(heat.columns)), heat.columns, rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(FIGURES / "real_collision_component_heatmap_by_quantile.png", dpi=160)
        plt.close()


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(INPUT)
    by_sample = sample_summary(df, "sample_id")
    by_file = sample_summary(df, "source_file")
    enrichment = high_tail_enrichment(df)
    pairwise = pairwise_tests(df)
    driver = component_driver_summary(df)

    by_sample.to_csv(TABLES / "real_collision_boundary_summary_by_sample.csv", index=False)
    by_file.to_csv(TABLES / "real_collision_boundary_summary_by_file.csv", index=False)
    enrichment.to_csv(TABLES / "high_boundary_tail_enrichment_by_sample.csv", index=False)
    pairwise.to_csv(TABLES / "real_collision_pairwise_boundary_tests.csv", index=False)
    driver.to_csv(TABLES / "boundary_component_driver_summary.csv", index=False)

    cols = [
        "sample_id",
        "source_file",
        "run",
        "lumi",
        "event",
        "B_boundary_equal_weight",
        "B_boundary_equal_weight_z",
        "R_missing",
        "R_multiplicity",
        "R_reconstruction",
        "R_compression_proxy",
        "R_lifetime_proxy",
        "R_displacement_proxy",
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_jets_50",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "scoring_limitations",
    ]
    top_cols = [col for col in cols if col in df.columns]
    df.sort_values("B_boundary_equal_weight_z", ascending=False).head(1000)[top_cols].to_csv(
        TABLES / "top_1000_boundary_events.csv", index=False
    )

    make_plots(df, enrichment, driver)

    top05_text = enrichment[enrichment["tail"] == "boundary_top_05"].sort_values("standardised_residual_simple", ascending=False)
    report = f"""# Real Collision Boundary Structure Analysis

## Scope

This is a real-data-only analysis using `{INPUT}`. No simulated signal outcome is used.

## Main Result

The current boundary score is a visible-jet boundary score only. It describes high visible activity and reconstruction complexity in real CMS collision events, not a full missing-energy or SUSY-like boundary score.

## Summary By Sample

{by_sample.to_markdown(index=False)}

## High-Boundary Tail Enrichment

Top 5% enrichment, sorted by residual:

{top05_text.to_markdown(index=False)}

## Interpretation

High-boundary events in this fallback analysis are driven by jet multiplicity and HT-like visible activity. MET, lepton, b-tag discriminator, trigger, lifetime, and displacement components are unavailable until CMSSW extraction works.

## Outputs

- `results/tables/real_collision_boundary_summary_by_sample.csv`
- `results/tables/real_collision_boundary_summary_by_file.csv`
- `results/tables/high_boundary_tail_enrichment_by_sample.csv`
- `results/tables/real_collision_pairwise_boundary_tests.csv`
- `results/tables/boundary_component_driver_summary.csv`
- `results/tables/top_1000_boundary_events.csv`
- `results/figures/*.png`
"""
    (REPORTS / "REAL_COLLISION_BOUNDARY_ANALYSIS_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote real-data boundary analysis tables and plots")


if __name__ == "__main__":
    main()
