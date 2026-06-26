from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
TRACE = ROOT / "data" / "processed" / "trace_direction"
DATE = "2026-06-09"

CANDIDATES = {
    "run2016g": TABLES / "top_real_trace_candidates_run2016g.csv",
    "run2016h": TABLES / "top_real_trace_candidates_run2016h.csv",
    "combined": TABLES / "top_real_trace_candidates_combined.csv",
}
FULL = {
    "run2016g": TRACE / "run2016g_real_with_trace_distances.csv",
    "run2016h": TRACE / "run2016h_real_with_trace_distances.csv",
    "combined": TRACE / "combined_real_with_trace_distances.csv",
}
REQUIRED = [
    "real_dataset", "primary_dataset", "sample_id", "source_file", "run", "lumi", "event",
    "B_NF_trace_base", "Trace_sms_vs_pooledSM", "Trace_SMS_reduced", "P_missing",
    "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression",
    "P_displacement_proxy", "P_reconstruction", "MET_pt", "MET_phi", "HT", "N_jets_30",
    "N_jets_50", "leading_jet_pt", "subleading_jet_pt", "N_leptons", "N_muons",
    "N_electrons", "N_btags_medium", "N_btags_tight", "max_btag_discriminator",
    "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count",
    "passes_available_quality_filters", "distance_to_SMS", "distance_to_TTJets",
    "distance_to_QCD", "distance_to_pooledSM",
]


def audit_file(label: str, role: str, path: Path) -> dict:
    row = {"label": label, "role": role, "path": str(path), "exists": path.exists()}
    if not path.exists():
        return row
    sample = pd.read_csv(path, nrows=20)
    row["rows"] = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1
    row["columns"] = ";".join(sample.columns)
    row["bnf_columns"] = ";".join([c for c in sample.columns if "B_NF" in c])
    row["trace_columns"] = ";".join([c for c in sample.columns if "Trace" in c or "trace" in c])
    row["parameter_columns"] = ";".join([c for c in sample.columns if c.startswith("P_")])
    row["quality_columns"] = ";".join([c for c in sample.columns if c.startswith("pass_") or "quality" in c])
    row["trigger_columns"] = ";".join([c for c in sample.columns if c.startswith("HLT_")])
    row["missing_required_columns"] = ";".join([c for c in REQUIRED if c not in sample.columns])
    row["component_mode"] = "full real-data trace table" if role == "full_real" and {"P_displacement_proxy", "P_reconstruction"}.issubset(sample.columns) else "reduced/summary candidate table"
    return row


def main() -> None:
    rows = []
    for label, path in CANDIDATES.items():
        rows.append(audit_file(label, "candidate_top100", path))
    for label, path in FULL.items():
        rows.append(audit_file(label, "full_real", path))
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "trace_candidate_input_audit.csv", index=False)
    report = [
        "# Trace Candidate Input Audit",
        "",
        f"Date: {DATE}",
        "",
        out.to_markdown(index=False),
        "",
        "The top-candidate tables are compact summary tables. Full trace-distance tables contain the component columns needed for thresholds and matched controls. Trigger-path details are limited in the compact candidate tables; unavailable fields are reported as missing rather than inferred.",
    ]
    (REPORTS / "TRACE_CANDIDATE_INPUT_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(out[["label", "role", "exists", "rows", "missing_required_columns"]].to_string(index=False))


if __name__ == "__main__":
    main()
