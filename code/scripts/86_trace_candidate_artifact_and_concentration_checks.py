from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
INFILE = TABLES / "classified_top_trace_candidates.csv"


def summarise(df: pd.DataFrame, cols: list[str], name: str) -> pd.DataFrame:
    rows = []
    for col in cols:
        if col in df:
            g = df.groupby(["candidate_set", col], dropna=False).size().reset_index(name="events").sort_values(["candidate_set", "events"], ascending=[True, False])
            g["field"] = col
            g = g.rename(columns={col: "value"})
            rows.append(g)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["candidate_set", "value", "events", "field"])


def main() -> None:
    df = pd.read_csv(INFILE)
    source = summarise(df, ["source_file", "run", "lumi", "primary_dataset"], "source")
    source.to_csv(TABLES / "trace_candidate_source_run_lumi_concentration.csv", index=False)
    quality_cols = [c for c in df.columns if c.startswith("fails_") or c in ["passes_available_quality_filters", "missing_quality_filter_info"]]
    quality = pd.DataFrame([{"flag": c, "events": int(df[c].sum()) if df[c].dtype == bool else int((df[c] == True).sum()), "fraction": float((df[c] == True).mean())} for c in quality_cols])
    quality.to_csv(TABLES / "trace_candidate_quality_filter_summary.csv", index=False)
    trig_cols = [c for c in df.columns if c.startswith("trigger_category_")]
    trigger = pd.DataFrame([{"trigger_category": c, "events": int(df[c].sum()), "fraction": float(df[c].mean())} for c in trig_cols])
    trigger.to_csv(TABLES / "trace_candidate_trigger_summary.csv", index=False)
    warn_cols = [
        "source_file_overconcentration_flag", "run_overconcentration_flag", "lumi_overconcentration_flag",
        "extreme_MET", "extreme_HT", "extreme_jet_multiplicity", "high_reconstruction_complexity",
        "high_secondary_vertex_proxy", "high_btag_structure", "SM_centroid_like"
    ]
    warnings = pd.DataFrame([{"warning": c, "events": int(df[c].sum()), "fraction": float(df[c].mean())} for c in warn_cols if c in df])
    warnings.to_csv(TABLES / "trace_candidate_artifact_warning_summary.csv", index=False)
    report = ["# Trace Candidate Artifact And Concentration Report", "", f"Date: {DATE}", "", "## Source/Run/Lumi/Dataset Concentration", "", source.head(80).to_markdown(index=False), "", "## Quality Summary", "", quality.to_markdown(index=False), "", "## Trigger/Dataset Summary", "", trigger.to_markdown(index=False), "", "## Artifact Warning Summary", "", warnings.to_markdown(index=False)]
    (REPORTS / "TRACE_CANDIDATE_ARTIFACT_AND_CONCENTRATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(warnings.to_string(index=False))


if __name__ == "__main__":
    main()
