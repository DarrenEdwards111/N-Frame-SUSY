from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
REAL_FITTED = ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
PARAMS = ["B_P_displacement_proxy", "B_P_reconstruction", "B_P_multiplicity", "B_P_btag_structure", "B_P_visible_energy", "B_P_missing", "B_P_compression"]


def ci(frac, n):
    if n == 0:
        return np.nan, np.nan
    se = (frac * (1 - frac) / n) ** 0.5
    return max(0, frac - 1.96 * se), min(1, frac + 1.96 * se)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    real = pd.read_csv(REAL_FITTED)
    thresholds = []
    for q, label in [(0.90, "q90"), (0.95, "q95"), (0.99, "q99"), (0.999, "q999")]:
        thresholds.append({"threshold_source": "Run2016G_standard_quality_real_data", "threshold": label, "quantile": q, "value": real["B_NF_fitted_z"].quantile(q)})
    th = pd.DataFrame(thresholds)
    th.to_csv(TABLES / "bnf_thresholds_real_and_sm.csv", index=False)
    rows = []
    for sample, group in df.groupby("sample_id"):
        for _, t in th.iterrows():
            frac = (group["B_NF_fitted_frozen_raw"] > t.value).mean()
            lo, hi = ci(frac, len(group))
            rows.append({"sample_id": sample, "classification": group.classification.iloc[0], "process_label": group.process_label.iloc[0], "threshold": t.threshold, "threshold_value": t.value, "events": len(group), "tail_fraction": frac, "ci_low": lo, "ci_high": hi, "mean_BNF": group.B_NF_fitted_frozen_raw.mean(), "median_BNF": group.B_NF_fitted_frozen_raw.median()})
    enrich = pd.DataFrame(rows)
    enrich.to_csv(TABLES / "susy_vs_sm_high_bnf_tail_enrichment.csv", index=False)
    driver_rows = []
    q95 = th.loc[th.threshold.eq("q95"), "value"].iloc[0]
    for sample, group in df.groupby("sample_id"):
        tail = group[group.B_NF_fitted_frozen_raw > q95]
        rest = group[group.B_NF_fitted_frozen_raw <= q95]
        for p in PARAMS:
            driver_rows.append({"sample_id": sample, "parameter_family": p.replace("B_", ""), "q95_tail_mean": tail[p].mean(), "rest_mean": rest[p].mean(), "top_minus_rest": tail[p].mean() - rest[p].mean(), "tail_events": len(tail)})
    drivers = pd.DataFrame(driver_rows)
    drivers.to_csv(TABLES / "susy_vs_sm_bnf_parameter_drivers.csv", index=False)
    report = ["# SUSY Versus SM High B_NF Tail Test", "", "Date: 2026-06-09", "", "The fitted B_NF equation is frozen from real data. Available local samples include SUSY-like benchmarks but no local SM simulated background samples, so SUSY-vs-SM specificity is not yet testable.", "", "## Real-Data Thresholds", "", th.to_markdown(index=False), "", "## Benchmark Tail Fractions", "", enrich.to_markdown(index=False), "", "## Parameter Drivers", "", drivers.to_markdown(index=False), "", "## Interpretation", "", "This is benchmark-level evidence only. It is not discovery evidence and not evidence that SUSY was found. A true SUSY > SM test requires ttbar/QCD/W/Z background simulations processed with the same frozen equation."]
    (REPORTS / "BNF_THRESHOLD_DEFINITION_REPORT.md").write_text("\n".join(["# B_NF Threshold Definition Report", "", "Date: 2026-06-09", "", th.to_markdown(index=False)]), encoding="utf-8")
    (REPORTS / "SUSY_VS_SM_HIGH_BNF_TAIL_TEST.md").write_text("\n".join(report), encoding="utf-8")
    print(enrich.to_string(index=False))


if __name__ == "__main__":
    main()
