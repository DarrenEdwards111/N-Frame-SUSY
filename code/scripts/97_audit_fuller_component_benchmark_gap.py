from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
EVENTS = ROOT / "data" / "processed" / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv"
REPORT_INPUTS = [
    "EXPANDED_BENCHMARK_AND_TRACE_ROBUSTNESS_SYNTHESIS.md",
    "UPDATE_TO_DARREN_EXPANDED_BENCHMARK_ROBUSTNESS.md",
    "EXPANDED_BENCHMARK_FIVE_SIGMA_TEST_REPORT.md",
    "EXPANDED_REAL_TRACE_ALIGNMENT_REPORT.md",
    "FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md",
    "REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md",
]
COMPONENTS = ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression", "P_displacement_proxy", "P_reconstruction"]


def comp_state(group: pd.DataFrame, comp: str) -> str:
    col = f"B_{comp}"
    if col not in group:
        return "missing"
    if group[col].notna().any():
        if comp == "P_reconstruction" and "packed_candidate_count" in group and not group["packed_candidate_count"].notna().any():
            return "reduced"
        return "available"
    return "missing"


def main() -> None:
    df = pd.read_csv(EVENTS, low_memory=False)
    rows = []
    q95 = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv").query("threshold == 'q95'")["value"].iloc[0]
    for (sample, proc, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        row = {
            "sample_id": sample, "process_label": proc, "classification": cls,
            "data_tier": g["data_tier"].dropna().iloc[0] if "data_tier" in g and g["data_tier"].notna().any() else "MiniAOD-derived/reduced",
            "events": len(g), "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
            "q95_tail_fraction": (g["B_NF_fitted_frozen_raw"] > q95).mean(),
        }
        for comp in COMPONENTS:
            row[comp] = comp_state(g, comp)
        row["component_mode"] = "full-component" if all(row[c] == "available" for c in COMPONENTS) else "reduced-component"
        row["needs_miniaodsim_replacement"] = row["component_mode"] == "reduced-component" or sample in ["ttjets_nanoaodsim_pilot", "qcd_ht1000to1500_nanoaodsim_pilot", "qcd_ht700to1000_nanoaodsim_pilot"]
        rows.append(row)
    audit = pd.DataFrame(rows).sort_values(["classification", "q95_tail_fraction"], ascending=[True, False])
    audit.to_csv(TABLES / "fuller_component_benchmark_gap_audit.csv", index=False)
    report_status = pd.DataFrame([{"report": r, "exists": (REPORTS / r).exists(), "size_bytes": (REPORTS / r).stat().st_size if (REPORTS / r).exists() else 0} for r in REPORT_INPUTS])
    explanation = (
        "MiniAODSIM matters because the real-data B_NF model was strongest in reconstruction/displacement-related axes. "
        "NanoAODSIM lacks packed_candidate_count, so P_reconstruction is reduced and benchmark comparison is not fully aligned with the real MiniAOD validation."
    )
    report = ["# Fuller Component Benchmark Gap Audit", "", f"Date: {DATE}", "", "## Existing Reports", "", report_status.to_markdown(index=False), "", "## Benchmark Component State", "", audit.to_markdown(index=False), "", "## Why This Matters", "", explanation]
    (REPORTS / "FULLER_COMPONENT_BENCHMARK_GAP_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
