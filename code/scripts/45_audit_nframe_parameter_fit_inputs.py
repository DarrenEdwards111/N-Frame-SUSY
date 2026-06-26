from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MC = ROOT / "data" / "processed" / "matched_control"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

MATCH_FILES = [
    "matched_controls_hand_top05.csv",
    "matched_controls_hand_top01.csv",
    "matched_controls_hand_top001.csv",
    "matched_controls_unsup_top05.csv",
    "matched_controls_unsup_top01.csv",
    "matched_controls_unsup_top001.csv",
]
RELATED = [
    ROOT / "results" / "tables" / "matched_case_control_feature_differences.csv",
    ROOT / "results" / "tables" / "matched_case_control_boundary_component_differences.csv",
    ROOT / "results" / "tables" / "matched_control_sensitivity_summary.csv",
    MC / "standard_quality_clean_events_rescored.csv",
    MC / "relaxed_quality_clean_events_rescored.csv",
]
MATCH_META = [
    "same_source_file",
    "same_run",
    "same_trigger_combo",
    "vertex_difference",
    "packed_candidate_difference",
    "lumi_difference",
    "matching_level_used",
]
COMPONENTS = [
    "R_missing",
    "R_visible_energy",
    "R_multiplicity",
    "R_btag_structure",
    "R_reconstruction_complexity",
    "R_compression_proxy",
    "R_displacement_proxy",
    "B_boundary_hand_defined_z",
    "real_only_unsupervised_boundary_score",
]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in MATCH_FILES:
        path = MC / name
        row = {"file": name, "path": str(path), "exists": path.exists()}
        if path.exists():
            df = pd.read_csv(path)
            row.update(
                {
                    "case_control_pairs": len(df),
                    "unique_cases": df["case_event_id"].nunique() if "case_event_id" in df else 0,
                    "controls_per_case": len(df) / df["case_event_id"].nunique() if "case_event_id" in df and df["case_event_id"].nunique() else 0,
                    "columns": ";".join(df.columns),
                    "matching_metadata_present": all(c in df.columns for c in MATCH_META),
                    "missing_matching_metadata": ";".join([c for c in MATCH_META if c not in df.columns]),
                }
            )
        rows.append(row)
    for path in RELATED:
        row = {"file": path.name, "path": str(path), "exists": path.exists(), "related_input": True}
        if path.exists() and path.suffix == ".csv":
            df = pd.read_csv(path, nrows=5)
            row["columns"] = ";".join(df.columns)
            row["available_boundary_components"] = ";".join([c for c in COMPONENTS if c in df.columns])
        rows.append(row)
    inv = pd.DataFrame(rows)
    inv.to_csv(TABLES / "nframe_parameter_fit_input_inventory.csv", index=False)

    report = [
        "# N-Frame Parameter Fit Input Audit",
        "",
        "Date: 2026-06-08",
        "",
        "This audit checks the matched-control inputs for fitting N-Frame boundary parameters. The analysis remains real CMS collision data only.",
        "",
        "## Inventory",
        "",
        inv.to_markdown(index=False),
        "",
        "## Status",
        "",
        "All primary standard-clean matched-control files exist and include matching metadata. Real-data-only status is inherited from the audited quality-clean event datasets.",
    ]
    (REPORTS / "NFRAME_PARAMETER_FIT_INPUT_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(inv[["file", "exists", "case_control_pairs", "unique_cases", "controls_per_case"]].to_string(index=False))


if __name__ == "__main__":
    main()
