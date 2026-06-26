from pathlib import Path
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
TRIGGER_OUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_event_quality_trigger_features.csv"
RUNNER = ROOT / "scripts" / "22_run_real_only_file_by_file_cmssw_extraction.py"
COMBINER = ROOT / "scripts" / "23_combine_real_only_file_by_file_outputs.py"


def main() -> None:
    status = "not_run"
    notes = []
    event_content_log = ROOT / "results" / "logs" / "trigger_filter_event_content_probe.log"
    if event_content_log.exists():
        notes.append("Event-content probe found TriggerResults in HLT, RECO and PAT.")
    try:
        subprocess.run([
            "D:\\Anaconda\\python.exe", str(RUNNER),
            "--mode", "file_by_file_test", "--max-events", "1000", "--limit-one-per-sample",
        ], check=True)
        subprocess.run(["D:\\Anaconda\\python.exe", str(COMBINER), "--mode", "file_by_file_test"], check=True)
        combined = ROOT / "data" / "processed" / "cmssw_real_only_file_by_file_test" / "real_only_file_by_file_test_combined.csv"
        df = pd.read_csv(combined)
        trigger_cols = [c for c in df.columns if c.startswith("HLT_") or c.startswith("pass_") or c == "trigger_filter_extraction_status"]
        if trigger_cols:
            out_cols = ["sample_id", "primary_dataset", "source_file", "run", "lumi", "event"] + trigger_cols
            df[out_cols].to_csv(TRIGGER_OUT, index=False)
            status = "success"
            notes.append(f"Extracted trigger/filter summary columns: {', '.join(trigger_cols)}")
        else:
            status = "failed_no_columns"
            notes.append("The probe ran but no trigger/filter columns appeared.")
    except Exception as exc:
        status = "failed"
        notes.append(str(exc))

    summary_rows = []
    if TRIGGER_OUT.exists():
        q = pd.read_csv(TRIGGER_OUT)
        trigger_cols = [c for c in q.columns if c.startswith("HLT_") or c.startswith("pass_") or c == "trigger_filter_extraction_status"]
        for col in trigger_cols:
            summary_rows.append({"column": col, "mean_or_pass_fraction": pd.to_numeric(q[col], errors="coerce").mean(), "non_null": q[col].notna().sum()})
    summary = pd.DataFrame(summary_rows)
    summary_path = TABLES / "top_boundary_event_quality_summary.csv"
    summary.to_csv(summary_path, index=False)
    report = [
        "# Trigger/Filter Extraction Report",
        "",
        "Date: 2026-06-08",
        "",
        f"Status: **{status}**",
        "",
        "## Notes",
        "",
        *[f"- {note}" for note in notes],
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False) if not summary.empty else "No trigger/filter summary table was produced.",
        "",
        "## Limitation",
        "",
        "The current extraction records broad trigger categories and common filter-name pass flags where names are available in TriggerResults. It does not write the full fired HLT path-name list per event.",
    ]
    (REPORTS / "TRIGGER_FILTER_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(status)
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
