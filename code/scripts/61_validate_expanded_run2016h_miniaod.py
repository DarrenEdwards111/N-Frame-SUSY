from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_event_features_combined.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

KEY = ["secondary_vertex_count", "packed_candidate_count", "MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "max_btag_discriminator"]
FILTERS = ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter", "pass_goodVertices", "pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter"]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    rows = [
        {"check": "total_events", "value": len(df), "status": "pass" if len(df) else "fail"},
        {"check": "simulated_rows", "value": int(pd.to_numeric(df.get("is_simulated", 0), errors="coerce").fillna(0).sum()), "status": "pass"},
        {"check": "source_files", "value": df.source_file.nunique(), "status": "pass"},
        {"check": "runs", "value": df.run.nunique(), "status": "pass"},
    ]
    for col in KEY:
        rows.append({"check": f"available:{col}", "value": col in df and df[col].notna().any(), "status": "pass" if col in df and df[col].notna().any() else "fail"})
    summary = pd.DataFrame(rows)
    missing = pd.DataFrame({"column": df.columns, "missing_fraction": [df[c].isna().mean() for c in df.columns]})
    by_sample = df.groupby(["primary_dataset"], as_index=False).agg(events=("event", "count"), files=("source_file", "nunique"), runs=("run", "nunique"), lumis=("lumi", "nunique"))
    by_file = df.groupby(["primary_dataset", "source_file"], as_index=False).agg(events=("event", "count"), runs=("run", "nunique"))
    filt = pd.DataFrame([{"variable": c, "non_null_fraction": df[c].notna().mean(), "mean_or_pass_fraction": pd.to_numeric(df[c], errors="coerce").mean()} for c in FILTERS if c in df])
    summary.to_csv(TABLES / "expanded_run2016h_validation_summary.csv", index=False)
    missing.to_csv(TABLES / "expanded_run2016h_missingness.csv", index=False)
    by_file.to_csv(TABLES / "expanded_run2016h_events_by_file.csv", index=False)
    report = ["# Expanded Run2016H MiniAOD Validation Report", "", "Date: 2026-06-09", "", "## Checks", "", summary.to_markdown(index=False), "", "## Events By Dataset", "", by_sample.to_markdown(index=False), "", "## Events By File", "", by_file.to_markdown(index=False), "", "## Trigger/Filter Availability", "", filt.to_markdown(index=False), "", "## Missingness", "", missing.to_markdown(index=False)]
    (REPORTS / "EXPANDED_RUN2016H_MINIAOD_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))
    print(by_sample.to_string(index=False))
    if summary.status.eq("fail").any():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
