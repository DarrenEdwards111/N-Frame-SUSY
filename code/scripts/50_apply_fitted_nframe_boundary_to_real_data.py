from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MC = ROOT / "data" / "processed" / "matched_control"
OUT = ROOT / "data" / "processed" / "nframe_parameter_fit"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

FAMILIES = {
    "P_reconstruction": ["R_reconstruction_complexity", "packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_displacement_proxy": ["R_displacement_proxy", "secondary_vertex_count", "displacement_proxy_raw"],
    "P_multiplicity": ["R_multiplicity", "N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["R_btag_structure", "N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["R_visible_energy", "HT"],
    "P_missing": ["R_missing", "MET_pt"],
    "P_compression": ["R_compression_proxy", "compression_proxy_raw"],
}


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MC / "standard_quality_clean_events.csv")
    if "real_only_unsupervised_boundary_score" not in df and "trigger_filter_unsupervised_boundary_score" in df:
        df["real_only_unsupervised_boundary_score"] = df["trigger_filter_unsupervised_boundary_score"]
    weights = pd.read_csv(TABLES / "nframe_fitted_boundary_equation_weights.csv")
    score = pd.Series(0.0, index=df.index)
    for fam, feats in FAMILIES.items():
        cols = [c for c in feats if c in df]
        family_value = pd.concat([z(df[c]) for c in cols], axis=1).mean(axis=1) if cols else pd.Series(0.0, index=df.index)
        df[f"fitted_{fam}"] = family_value
        w = float(weights.loc[weights.family == fam, "weight"].iloc[0])
        score = score + w * family_value.fillna(0)
    df["B_NF_fitted_raw"] = score
    df["B_NF_fitted_z"] = z(score)
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        df[f"B_NF_fitted_{label}"] = df["B_NF_fitted_z"] >= df["B_NF_fitted_z"].quantile(q)
    out = OUT / "real_data_with_fitted_nframe_boundary_score.csv"
    df.to_csv(out, index=False)

    sample = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(events=("event", "count"), mean_fitted_z=("B_NF_fitted_z", "mean"), top05=("B_NF_fitted_top05", "mean"), top01=("B_NF_fitted_top01", "mean"), top001=("B_NF_fitted_top001", "mean"))
    tail_rows = []
    for label in ["top05", "top01", "top001"]:
        tail = df[df[f"B_NF_fitted_{label}"]]
        base = df.primary_dataset.value_counts(normalize=True)
        for ds, frac in tail.primary_dataset.value_counts(normalize=True).items():
            tail_rows.append({"tail": label, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base[ds], "enrichment_ratio": frac / base[ds], "events": int((tail.primary_dataset == ds).sum())})
    tails = pd.DataFrame(tail_rows)
    fr = df[df.B_NF_fitted_top001].groupby(["source_file", "run"], as_index=False).agg(events=("event", "count"), mean_fitted_z=("B_NF_fitted_z", "mean")).sort_values("events", ascending=False)
    top = df.sort_values("B_NF_fitted_z", ascending=False).head(1000)
    sample.to_csv(TABLES / "fitted_nframe_score_summary_by_sample.csv", index=False)
    tails.to_csv(TABLES / "fitted_nframe_top_tail_by_sample.csv", index=False)
    fr.to_csv(TABLES / "fitted_nframe_top_tail_by_file_run.csv", index=False)
    top.to_csv(TABLES / "fitted_nframe_top_1000_events.csv", index=False)
    driver_cols = [f"fitted_{f}" for f in FAMILIES]
    driver = top[driver_cols].mean().reset_index()
    driver.columns = ["parameter_family", "mean_top1000_value"]
    report = [
        "# Fitted N-Frame Boundary Application Report",
        "",
        "Date: 2026-06-08",
        "",
        "The fitted N-Frame boundary equation was applied to standard quality-clean real CMS collision events.",
        "",
        "## Sample Summary",
        "",
        sample.to_markdown(index=False),
        "",
        "## Top Tail Composition",
        "",
        tails.to_markdown(index=False),
        "",
        "## Top 0.1% File/Run Concentration",
        "",
        fr.head(20).to_markdown(index=False),
        "",
        "## Top-1000 Parameter Drivers",
        "",
        driver.to_markdown(index=False),
    ]
    (REPORTS / "FITTED_NFRAME_BOUNDARY_APPLICATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(sample.to_string(index=False))
    print(tails.to_string(index=False))


if __name__ == "__main__":
    main()
