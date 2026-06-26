from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from susy_signal_common import DATE, REPORTS, ROOT, TABLES


REAL = ROOT / "data" / "processed" / "trace_direction" / "combined_real_with_full_component_signal_qcd_trace_direction.csv"


def test_subset(label: str, df: pd.DataFrame) -> dict:
    base = "B_NF_trace_base"
    trace = "Trace_full_component_signal_vs_qcd"
    if len(df) < 100:
        return {"stress_test": label, "events_remaining": len(df), "status": "too_few_events"}
    high = df[df[base] >= df[base].quantile(.95)]
    rest = df[df[base] < df[base].quantile(.95)]
    res = stats.ttest_ind(high[trace], rest[trace], equal_var=False, alternative="greater")
    return {
        "stress_test": label,
        "events_remaining": len(df),
        "high_tail_events": len(high),
        "mean_trace_high": high[trace].mean(),
        "mean_trace_rest": rest[trace].mean(),
        "mean_diff": high[trace].mean() - rest[trace].mean(),
        "welch_p": res.pvalue,
        "welch_z": float(stats.norm.isf(res.pvalue)) if res.pvalue > 0 else np.inf,
        "top_source_file_fraction_high_tail": high["source_file"].value_counts(normalize=True).iloc[0] if "source_file" in high and len(high) else np.nan,
        "top_run_fraction_high_tail": high["run"].value_counts(normalize=True).iloc[0] if "run" in high and len(high) else np.nan,
        "status": "tested",
    }


def main() -> None:
    df = pd.read_csv(REAL, low_memory=False)
    tests = {"all_real": df}
    if "source_file" in df:
        top_source = df["source_file"].value_counts().idxmax()
        tests["exclude_top_source_file"] = df[df["source_file"] != top_source]
    if "run" in df:
        top_run = df["run"].value_counts().idxmax()
        tests["exclude_top_run"] = df[df["run"] != top_run]
    if "lumi" in df:
        top_lumi = df["lumi"].value_counts().idxmax()
        tests["exclude_top_lumi"] = df[df["lumi"] != top_lumi]
    if "standard_quality_clean" in df:
        tests["standard_quality_only"] = df[df["standard_quality_clean"].astype(bool)]
    for col in ["N_primary_vertices", "packed_candidate_count", "secondary_vertex_count"]:
        if col in df:
            lo, hi = df[col].quantile([.01, .99])
            tests[f"exclude_extreme_{col}"] = df[(df[col] >= lo) & (df[col] <= hi)]
    if "primary_dataset" in df:
        for dataset in ["JetHT", "MET", "SingleMuon"]:
            tests[f"{dataset}_only"] = df[df["primary_dataset"].eq(dataset)]
    rows = [test_subset(label, subset) for label, subset in tests.items()]
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "strict_artifact_systematics_after_signal_parity.csv", index=False)
    report = [
        "# Strict Artefact/Systematics After Signal Parity Report",
        "",
        f"Date: {DATE}",
        "",
        "This stress test reruns the high-B_NF versus trace-alignment comparison after excluding obvious provenance and reconstruction artefact candidates.",
        "",
        out.to_markdown(index=False),
    ]
    (REPORTS / "STRICT_ARTIFACT_SYSTEMATICS_AFTER_SIGNAL_PARITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
