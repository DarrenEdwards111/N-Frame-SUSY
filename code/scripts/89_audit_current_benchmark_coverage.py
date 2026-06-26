from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"

REPORT_INPUTS = [
    "FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md",
    "SUSY_VS_SM_SPECIFICITY_TEST_REPORT.md",
    "SM_BACKGROUND_MIMICRY_ANALYSIS_REPORT.md",
    "REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md",
    "REAL_TRACE_CANDIDATE_SANITY_CHECK_SYNTHESIS.md",
]
EVENT_FILES = [
    ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv",
    ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv",
]


def component_mode(group: pd.DataFrame) -> tuple[str, str, str]:
    comps = ["B_P_displacement_proxy", "B_P_reconstruction", "B_P_multiplicity", "B_P_btag_structure", "B_P_visible_energy", "B_P_missing", "B_P_compression"]
    available = [c.replace("B_", "") for c in comps if c in group and group[c].notna().any()]
    missing = [c.replace("B_", "") for c in comps if c not in group or not group[c].notna().any()]
    mode = "full-component" if not missing else "reduced-component"
    return mode, ";".join(available), ";".join(missing)


def main() -> None:
    frames = []
    for path in EVENT_FILES:
        if path.exists():
            frames.append(pd.read_csv(path))
    all_events = pd.concat(frames, ignore_index=True, sort=False)
    rows = []
    for (sample, process, cls), group in all_events.groupby(["sample_id", "process_label", "classification"]):
        mode, avail, miss = component_mode(group)
        rows.append({
            "sample_id": sample,
            "process_label": process,
            "classification": cls,
            "data_tier": group.get("data_tier", pd.Series(["MiniAOD-derived/reduced"])).iloc[0] if "data_tier" in group else "MiniAOD-derived/reduced",
            "events": len(group),
            "component_mode": mode,
            "available_components": avail,
            "missing_components": miss,
            "mean_BNF": group["B_NF_fitted_frozen_raw"].mean(),
            "q95_tail_fraction": (group["B_NF_fitted_frozen_raw"] > pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv").query("threshold == 'q95'")["value"].iloc[0]).mean(),
        })
    coverage = pd.DataFrame(rows)
    gaps = pd.DataFrame([
        {"gap": "SM backgrounds limited to TTJets and QCD", "impact": "Specificity may not hold against W/Z/DY/single-top/diboson."},
        {"gap": "Reduced-component feature alignment", "impact": "NanoAODSIM lacks packed candidates; SUSY benchmark features lack displacement/reconstruction components."},
        {"gap": "Limited SUSY topology coverage", "impact": "Only SMS-T5Wg and HToAA4B have been scored before expansion."},
        {"gap": "No published signal-region overlap", "impact": "Cannot yet connect candidate events to published CMS SUSY regions."},
    ])
    coverage.to_csv(TABLES / "benchmark_coverage_and_gaps.csv", index=False)
    reports = pd.DataFrame([{"report": r, "exists": (REPORTS / r).exists(), "size_bytes": (REPORTS / r).stat().st_size if (REPORTS / r).exists() else 0} for r in REPORT_INPUTS])
    report = ["# Benchmark Coverage And Gaps Audit", "", f"Date: {DATE}", "", "## Existing Reports", "", reports.to_markdown(index=False), "", "## Current Benchmark Coverage", "", coverage.to_markdown(index=False), "", "## Main Weaknesses", "", gaps.to_markdown(index=False)]
    (REPORTS / "BENCHMARK_COVERAGE_AND_GAPS_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
