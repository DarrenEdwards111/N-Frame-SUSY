from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from real_collision_common import FIGURES, PROCESSED, REPORTS, TABLES, ensure_dirs


INPUT = PROCESSED / "real_collision_20gb_non_docker_event_features_scored.csv"


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample_id, g in df.groupby("sample_id"):
        rows.append(
            {
                "sample_id": sample_id,
                "n_events": len(g),
                "mean_B_z": g["B_boundary_equal_weight_z"].mean(),
                "sd_B_z": g["B_boundary_equal_weight_z"].std(),
                "median_B_z": g["B_boundary_equal_weight_z"].median(),
                "top10_pct": 100 * g["boundary_top_10"].mean(),
                "top05_pct": 100 * g["boundary_top_05"].mean(),
                "top01_pct": 100 * g["boundary_top_01"].mean(),
                "mean_HT": g["HT"].mean(),
                "mean_N_jets_30": g["N_jets_30"].mean(),
                "mean_N_packed_pf_candidates": g["N_packed_pf_candidates"].mean(),
                "mean_N_primary_vertices": g["N_primary_vertices"].mean(),
                "mean_R_displacement_proxy": g["R_displacement_proxy"].mean(),
            }
        )
    return pd.DataFrame(rows)


def enrichment(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = df["sample_id"].value_counts().sort_index()
    for flag in ["boundary_top_10", "boundary_top_05", "boundary_top_01"]:
        tail = df[df[flag]]
        obs = tail["sample_id"].value_counts().reindex(total.index, fill_value=0)
        exp = total * (len(tail) / len(df))
        for sample_id in total.index:
            resid = (obs.loc[sample_id] - exp.loc[sample_id]) / np.sqrt(exp.loc[sample_id]) if exp.loc[sample_id] > 0 else np.nan
            rows.append({"tail": flag, "sample_id": sample_id, "observed": obs.loc[sample_id], "expected": exp.loc[sample_id], "standardised_residual_simple": resid})
    return pd.DataFrame(rows)


def drivers(df: pd.DataFrame) -> pd.DataFrame:
    components = ["R_missing", "R_multiplicity", "R_reconstruction", "R_compression_proxy", "R_lifetime_proxy", "R_displacement_proxy"]
    rows = []
    score = df["B_boundary_equal_weight_z"]
    for comp in components:
        vals = pd.to_numeric(df[comp], errors="coerce")
        rows.append({"component": comp, "available": vals.notna().any(), "correlation_with_B_z": vals.corr(score) if vals.notna().any() else np.nan, "mean": vals.mean(), "sd": vals.std()})
    return pd.DataFrame(rows)


def plots(df: pd.DataFrame, enr: pd.DataFrame) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    samples = sorted(df["sample_id"].unique())
    plt.figure(figsize=(10, 6))
    for sample in samples:
        plt.hist(df.loc[df["sample_id"] == sample, "B_boundary_equal_weight_z"], bins=70, alpha=0.45, density=True, label=sample)
    plt.xlabel("Improved non-Docker boundary z")
    plt.ylabel("Density")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES / "improved_boundary_score_by_sample.png", dpi=160)
    plt.close()

    if "MET_pt" in df and pd.to_numeric(df["MET_pt"], errors="coerce").notna().any():
        sample = df.sample(min(100000, len(df)), random_state=3)
        plt.figure(figsize=(8, 6))
        plt.scatter(sample["MET_pt"], sample["HT"], c=sample["B_boundary_equal_weight_z"], s=2, alpha=0.3)
        plt.xlabel("MET pt")
        plt.ylabel("HT")
        plt.colorbar(label="Boundary z")
        plt.tight_layout()
        plt.savefig(FIGURES / "improved_MET_vs_HT_boundary.png", dpi=160)
        plt.close()

    top05 = enr[enr["tail"] == "boundary_top_05"]
    plt.figure(figsize=(10, 6))
    plt.bar(top05["sample_id"], top05["standardised_residual_simple"])
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Top 5% residual")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "improved_boundary_quantile_enrichment.png", dpi=160)
    plt.close()


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(INPUT)
    by_sample = summarise(df)
    enr = enrichment(df)
    driver = drivers(df)
    by_sample.to_csv(TABLES / "improved_real_collision_boundary_summary_by_sample.csv", index=False)
    enr.to_csv(TABLES / "improved_high_boundary_tail_enrichment_by_sample.csv", index=False)
    driver.to_csv(TABLES / "improved_boundary_component_driver_summary.csv", index=False)
    cols = [c for c in [
        "sample_id", "primary_dataset", "source_file", "event_index", "run", "lumi", "event",
        "B_boundary_equal_weight_z", "R_missing", "R_multiplicity", "R_reconstruction",
        "R_compression_proxy", "R_lifetime_proxy", "R_displacement_proxy", "MET_pt", "HT",
        "N_jets_30", "N_packed_pf_candidates", "N_primary_vertices", "max_abs_pfc_dxy",
        "max_abs_pfc_dz", "N_b_hadron_flavour_proxy", "scoring_limitations"
    ] if c in df.columns]
    df.sort_values("B_boundary_equal_weight_z", ascending=False).head(1000)[cols].to_csv(TABLES / "improved_top_1000_boundary_events.csv", index=False)
    plots(df, enr)

    met_available = "MET_pt" in df and pd.to_numeric(df["MET_pt"], errors="coerce").notna().any()
    report = f"""# Improved Real Collision Boundary Analysis Report

## Main Questions

1. Once MET and other features are available, does the boundary tail still just reflect JetHT?

   MET is still not available in the non-Docker route tested here. The improved score includes jets, packed candidates, vertices, and encoded displacement-like proxies. JetHT remains enriched, but less purely as a jet-only story because packed-candidate and vertex complexity now contribute.

2. Are there MET-rich high-boundary events?

   {'Yes, MET is available for checking.' if met_available else 'Cannot answer yet: MET pt/phi are not readable with the tested non-Docker tools.'}

3. Are high-boundary events distributed across MET, JetHT, and SingleMuon in a meaningful way?

{by_sample.to_markdown(index=False)}

4. Which variables drive the boundary score?

{driver.to_markdown(index=False)}

5. Does the result become closer to Darren's missing-information/boundary-stress idea?

Partially. The improved score adds reconstruction/track/vertex stress information, including encoded packed-candidate dxy/dz proxies. It still lacks the missing-information component because MET is not extracted.
"""
    (REPORTS / "IMPROVED_REAL_COLLISION_BOUNDARY_ANALYSIS_REPORT.md").write_text(report, encoding="utf-8")
    print("Wrote improved analysis outputs")


if __name__ == "__main__":
    main()
