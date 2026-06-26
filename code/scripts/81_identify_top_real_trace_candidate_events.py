from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
FILES = {
    "run2016g": OUT / "run2016g_real_with_trace_distances.csv",
    "run2016h": OUT / "run2016h_real_with_trace_distances.csv",
    "combined": OUT / "combined_real_with_trace_distances.csv",
}


def quality_flag(df: pd.DataFrame) -> pd.Series:
    filters = [c for c in df.columns if c.startswith("pass_")]
    if not filters:
        return pd.Series(True, index=df.index)
    return df[filters].fillna(True).astype(bool).all(axis=1)


def candidates(name: str, path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["passes_available_quality_filters"] = quality_flag(df)
    df["candidate_score"] = (
        df["B_NF_trace_base"].rank(pct=True)
        + df["Trace_sms_vs_pooledSM"].rank(pct=True)
        + df["trace_composite_score"].rank(pct=True)
        - df["distance_to_SMS"].rank(pct=True)
        + df["distance_to_pooledSM"].rank(pct=True)
    )
    top = df.sort_values("candidate_score", ascending=False).head(100).copy()
    top["reason_flags"] = "high_BNF;high_SMS_trace;near_SMS_centroid;farther_from_pooledSM"
    cols = [c for c in [
        "real_dataset", "primary_dataset", "sample_id", "source_file", "run", "lumi", "event",
        "B_NF_trace_base", "B_NF_trace_raw", "Trace_sms_vs_pooledSM", "Trace_sms_vs_TTJets",
        "Trace_sms_vs_QCD", "Trace_SMS_reduced", "real_displacement_reconstruction_axis",
        "trace_composite_score", "distance_to_SMS", "distance_to_TTJets", "distance_to_QCD",
        "distance_to_pooledSM", "MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons",
        "N_btags_medium", "N_btags_tight", "secondary_vertex_count", "packed_candidate_count",
        "passes_available_quality_filters", "reason_flags"
    ] if c in top]
    out = top[cols]
    out.to_csv(TABLES / f"top_real_trace_candidates_{name}.csv", index=False)
    return out


def main() -> None:
    summaries = []
    for name, path in FILES.items():
        out = candidates(name, path)
        summaries.append({"candidate_set": name, "events": len(out), "quality_pass_fraction": out["passes_available_quality_filters"].mean() if "passes_available_quality_filters" in out else None})
    summary = pd.DataFrame(summaries)
    report = ["# Top Real Trace Candidate Events Report", "", f"Date: {DATE}", "", summary.to_markdown(index=False), "", "Candidate CSVs contain run/lumi/event/source-file identifiers and trace-distance/component columns for manual inspection."]
    (REPORTS / "TOP_REAL_TRACE_CANDIDATE_EVENTS_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    plan = [
        "# Real Trace Candidate Event Display Plan", "", f"Date: {DATE}", "",
        "Inspect the top combined candidates first, then check whether Run2016G and Run2016H candidates show the same visual topology.",
        "",
        "For each event, inspect MET direction, jet multiplicity, b-tags, secondary vertices, lepton content, trigger/filter status, and whether the topology looks detector-artefact-like, SM-like, or trace-compatible.",
        "",
        "Required identifiers are included in the candidate CSVs: run, lumi, event and source_file. Full visualisation will likely require the corresponding CMS Open Data event-display route or MiniAOD access for the listed source files.",
    ]
    (REPORTS / "REAL_TRACE_CANDIDATE_EVENT_DISPLAY_PLAN.md").write_text("\n".join(plan), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
