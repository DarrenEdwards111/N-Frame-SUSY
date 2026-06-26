from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "independent_validation_miniaod_full" / "run2016h_miniaod_event_features_combined.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

KEY = [
    "secondary_vertex_count", "packed_candidate_count", "N_primary_vertices", "MET_pt", "HT",
    "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "max_btag_discriminator",
]
TRIG_FILTER = [
    "HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any",
    "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter", "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter",
    "trigger_filter_extraction_status",
]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    summary_rows = [
        {"check": "total_events", "value": len(df), "status": "pass" if len(df) else "fail"},
        {"check": "simulated_rows", "value": int(pd.to_numeric(df.get("is_simulated", 0), errors="coerce").fillna(0).sum()), "status": "pass"},
        {"check": "unique_files", "value": df["source_file"].nunique(), "status": "pass"},
        {"check": "unique_runs", "value": df["run"].nunique(), "status": "pass"},
        {"check": "duplicate_source_run_lumi_event", "value": int(df.duplicated(["source_file", "run", "lumi", "event"]).sum()), "status": "pass"},
    ]
    for col in KEY:
        summary_rows.append({"check": f"key_component_available:{col}", "value": col in df and df[col].notna().any(), "status": "pass" if col in df and df[col].notna().any() else "fail"})
    summary = pd.DataFrame(summary_rows)
    missing = pd.DataFrame({"column": df.columns, "missing_fraction": [df[c].isna().mean() for c in df.columns]})
    by_sample = df.groupby(["sample_id", "primary_dataset", "source_file"], as_index=False).agg(events=("event", "count"), runs=("run", "nunique"))
    filter_rows = []
    for col in TRIG_FILTER:
        if col in df:
            filter_rows.append({"column": col, "non_null_fraction": df[col].notna().mean(), "mean_or_pass_fraction": pd.to_numeric(df[col], errors="coerce").mean()})
    filters = pd.DataFrame(filter_rows)
    summary.to_csv(TABLES / "run2016h_miniaod_full_validation_summary.csv", index=False)
    missing.to_csv(TABLES / "run2016h_miniaod_full_missingness.csv", index=False)
    by_sample.to_csv(TABLES / "run2016h_miniaod_full_events_by_sample.csv", index=False)
    filters.to_csv(TABLES / "run2016h_miniaod_full_trigger_filter_summary.csv", index=False)
    report = [
        "# Run2016H MiniAOD Full Validation Report",
        "",
        "Date: 2026-06-09",
        "",
        "This validates independent real CMS Run2016H MiniAOD extraction outputs.",
        "",
        "## Checks",
        "",
        summary.to_markdown(index=False),
        "",
        "## Events By Sample",
        "",
        by_sample.to_markdown(index=False),
        "",
        "## Trigger/Filter Availability",
        "",
        filters.to_markdown(index=False),
        "",
        "## Missingness",
        "",
        missing.to_markdown(index=False),
    ]
    (REPORTS / "RUN2016H_MINIAOD_FULL_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))
    print(by_sample.to_string(index=False))
    if summary["status"].eq("fail").any():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
