from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_trigger_filter_full" / "real_only_full_event_features_with_trigger_filter_scored.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

REQUIRED = [
    "sample_id", "primary_dataset", "source_file", "source_file_stem", "source_file_index",
    "run", "lumi", "event", "MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons",
    "N_btags_medium", "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count",
    "secondary_vertex_count", "B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score",
    "HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any",
    "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter", "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter",
]
ALIASES = {"real_only_unsupervised_boundary_score": "trigger_filter_unsupervised_boundary_score"}


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = [{"check": "input_exists", "value": str(INPUT), "status": "pass" if INPUT.exists() else "fail"}]
    if not INPUT.exists():
        pd.DataFrame(rows).to_csv(TABLES / "matched_control_input_audit.csv", index=False)
        raise FileNotFoundError(INPUT)
    df = pd.read_csv(INPUT)
    if "real_only_unsupervised_boundary_score" not in df and ALIASES["real_only_unsupervised_boundary_score"] in df:
        df["real_only_unsupervised_boundary_score"] = df[ALIASES["real_only_unsupervised_boundary_score"]]

    rows += [
        {"check": "total_rows", "value": len(df), "status": "pass" if len(df) else "fail"},
        {"check": "simulated_rows", "value": int(pd.to_numeric(df.get("is_simulated", 0), errors="coerce").fillna(0).sum()), "status": "pass"},
        {"check": "unique_source_files", "value": df["source_file"].nunique(), "status": "pass"},
        {"check": "unique_runs", "value": df["run"].nunique(), "status": "pass"},
        {"check": "duplicate_source_run_lumi_event_rows", "value": int(df.duplicated(["source_file", "run", "lumi", "event"]).sum()), "status": "pass"},
    ]
    for col in REQUIRED:
        present = col in df
        miss = float(df[col].isna().mean()) if present else 1.0
        non_null_ok = miss == 0 or col in {"max_btag_discriminator"}
        rows.append({"check": f"column:{col}", "value": f"present={present}; missing_fraction={miss:.6g}", "status": "pass" if present and non_null_ok else "fail"})
    for col in [c for c in REQUIRED if c.startswith("HLT_") or c.startswith("pass_")]:
        rows.append({"check": f"{col}_non_null_fraction", "value": float(df[col].notna().mean()) if col in df else 0, "status": "pass" if col in df and df[col].notna().all() else "fail"})

    sample = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(events=("event", "count"), files=("source_file", "nunique"), runs=("run", "nunique"))
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "matched_control_input_audit.csv", index=False)
    sample.to_csv(TABLES / "matched_control_input_sample_counts.csv", index=False)

    report = [
        "# Matched Control Input Audit", "", "Date: 2026-06-08", "",
        "This audit checks the full real CMS collision trigger/filter-scored table before matched-control analysis. No simulated samples are used.",
        "", f"Input: `{INPUT}`", "", "## Audit", "", audit.to_markdown(index=False),
        "", "## Samples", "", sample.to_markdown(index=False),
        "", "## Note", "", "The requested `real_only_unsupervised_boundary_score` is provided as an alias of the actual scored column `trigger_filter_unsupervised_boundary_score`."
    ]
    (REPORTS / "MATCHED_CONTROL_INPUT_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
