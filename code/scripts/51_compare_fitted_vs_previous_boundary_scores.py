from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SCORES = {
    "fitted": "B_NF_fitted_z",
    "hand": "B_boundary_hand_defined_z",
    "unsupervised": "real_only_unsupervised_boundary_score",
}


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    if "real_only_unsupervised_boundary_score" not in df and "trigger_filter_unsupervised_boundary_score" in df:
        df["real_only_unsupervised_boundary_score"] = df["trigger_filter_unsupervised_boundary_score"]
    corr = df[list(SCORES.values())].corr().rename(index={v: k for k, v in SCORES.items()}, columns={v: k for k, v in SCORES.items()})
    corr.to_csv(TABLES / "fitted_vs_previous_score_correlations.csv")
    overlap_rows, comp_rows = [], []
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        masks = {name: df[col] >= df[col].quantile(q) for name, col in SCORES.items()}
        for a, ma in masks.items():
            for b, mb in masks.items():
                overlap_rows.append({"tail": label, "score_a": a, "score_b": b, "jaccard_overlap": float((ma & mb).sum() / (ma | mb).sum()), "a_in_b_fraction": float((ma & mb).sum() / ma.sum())})
            tail = df[ma]
            base = df.primary_dataset.value_counts(normalize=True)
            for ds, frac in tail.primary_dataset.value_counts(normalize=True).items():
                comp_rows.append({"tail": label, "score": a, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base[ds], "enrichment_ratio": frac / base[ds], "events": int((tail.primary_dataset == ds).sum())})
    overlap = pd.DataFrame(overlap_rows)
    comp = pd.DataFrame(comp_rows)
    concentration = []
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        for name, col in SCORES.items():
            tail = df[df[col] >= df[col].quantile(q)].copy()
            tail["lumi_bin"] = (tail["lumi"] // 25) * 25
            concentration.append({"tail": label, "score": name, "top_file_fraction": tail.source_file.value_counts(normalize=True).iloc[0], "top_run_fraction": tail.run.value_counts(normalize=True).iloc[0], "top_lumi_bin_fraction": tail.lumi_bin.value_counts(normalize=True).iloc[0]})
    conc = pd.DataFrame(concentration)
    overlap.to_csv(TABLES / "fitted_vs_previous_top_tail_overlap.csv", index=False)
    comp.to_csv(TABLES / "fitted_vs_previous_tail_composition.csv", index=False)
    conc.to_csv(TABLES / "fitted_vs_previous_concentration.csv", index=False)
    report = [
        "# Fitted Versus Previous Boundary Score Comparison",
        "",
        "Date: 2026-06-08",
        "",
        "The fitted score is compared with the previous hand-defined and unsupervised boundary scores on standard quality-clean real CMS events.",
        "",
        "## Correlations",
        "",
        corr.to_markdown(),
        "",
        "## Top-Tail Overlap",
        "",
        overlap.to_markdown(index=False),
        "",
        "## Tail Composition",
        "",
        comp.to_markdown(index=False),
        "",
        "## Concentration",
        "",
        conc.to_markdown(index=False),
    ]
    (REPORTS / "FITTED_VS_PREVIOUS_BOUNDARY_SCORE_COMPARISON.md").write_text("\n".join(report), encoding="utf-8")
    print(corr.to_string())
    print(conc.to_string(index=False))


if __name__ == "__main__":
    main()
