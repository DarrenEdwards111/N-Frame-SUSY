from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
INFILE = TABLES / "classified_top_trace_candidates_combined.csv"


def closest(row) -> str:
    vals = {
        "SMS": row.distance_to_SMS,
        "TTJets": row.distance_to_TTJets,
        "QCD": row.distance_to_QCD,
        "pooled SM": row.distance_to_pooledSM,
    }
    return min(vals, key=vals.get)


def main() -> None:
    df = pd.read_csv(INFILE).head(25).copy()
    rows = []
    lines = ["# Top 25 Trace Candidate Cards", "", f"Date: {DATE}", ""]
    for idx, row in df.reset_index(drop=True).iterrows():
        rank = idx + 1
        closest_name = closest(row)
        why_flagged = f"High boundary score ({row.B_NF_trace_base:.2f}) and high SMS-like trace score ({row.Trace_sms_vs_pooledSM:.2f})."
        why_ordinary = f"Closest benchmark by simple component distance is {closest_name}; distance to SMS is {row.distance_to_SMS:.2f}, distance to pooled SM is {row.distance_to_pooledSM:.2f}."
        why_trace = f"MET {row.MET_pt:.1f}, HT {row.HT:.1f}, jets {row.N_jets_30}, b-tags {row.N_btags_medium}, leptons {row.N_leptons}, secondary vertices {row.secondary_vertex_count}."
        inspect = "Check MET direction, jet balance, b-tags, secondary vertices, lepton content, trigger/filter status and source-file/run concentration."
        rows.append({
            "rank": rank, "run": row.run, "lumi": row.lumi, "event": row.event,
            "dataset": row.primary_dataset, "source_file": row.source_file,
            "B_NF": row.B_NF_trace_base, "trace_score": row.Trace_sms_vs_pooledSM,
            "MET_pt": row.MET_pt, "HT": row.HT, "N_jets_30": row.N_jets_30,
            "N_btags_medium": row.N_btags_medium, "N_leptons": row.N_leptons,
            "secondary_vertex_count": row.secondary_vertex_count,
            "quality_status": "passes available filters" if row.passes_available_quality_filters else "quality concern",
            "closest_benchmark_direction": closest_name, "classification_category": row.primary_category,
            "why_flagged": why_flagged, "why_it_may_be_ordinary": why_ordinary,
            "why_it_may_be_trace_compatible": why_trace, "what_to_inspect_next": inspect,
        })
        lines += [
            f"## Candidate {rank}",
            "",
            f"- Event: run {row.run}, lumi {row.lumi}, event {row.event}",
            f"- Dataset/source: {row.primary_dataset}, `{row.source_file}`",
            f"- Scores: B_NF {row.B_NF_trace_base:.2f}; SMS-like trace {row.Trace_sms_vs_pooledSM:.2f}",
            f"- Event shape: MET {row.MET_pt:.1f}, HT {row.HT:.1f}, jets {row.N_jets_30}, b-tags {row.N_btags_medium}, leptons {row.N_leptons}, secondary vertices {row.secondary_vertex_count}",
            f"- Quality status: {'passes available filters' if row.passes_available_quality_filters else 'quality concern'}",
            f"- Closest benchmark: {closest_name}",
            f"- Classification: {row.primary_category}",
            f"- Why flagged: {why_flagged}",
            f"- Why it may be ordinary: {why_ordinary}",
            f"- Why it may be trace-compatible: {why_trace}",
            f"- What to inspect next: {inspect}",
            "",
        ]
    cards = pd.DataFrame(rows)
    cards.to_csv(TABLES / "top25_trace_candidate_cards.csv", index=False)
    (REPORTS / "TOP25_TRACE_CANDIDATE_CARDS.md").write_text("\n".join(lines), encoding="utf-8")
    print(cards[["rank", "classification_category", "closest_benchmark_direction", "quality_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
