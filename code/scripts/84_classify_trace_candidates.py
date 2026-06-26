from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
INFILE = TRACE / "top_trace_candidates_with_diagnostic_flags.csv"


def classify(r) -> tuple[str, str, str, str, str]:
    tags = []
    caveats = []
    if r.fails_any_available_quality_filter:
        return (
            "likely_detector_or_data_quality_concern",
            "quality-filter-failure",
            "high",
            "This event fails at least one available data-quality filter.",
            "Do not use as trace evidence unless an expert explains the failure.",
        )
    if r.high_btag_top_like and r.SM_centroid_like and r.closer_to_TTJets_than_SMS:
        return (
            "likely_SM_top_heavy_flavour_like",
            "b-tags;multiplicity;TTJets-close",
            "high",
            "The event has b-tag/top-like structure and is closer to the TTJets/SM benchmark than to SMS.",
            "Treat as ordinary top/heavy-flavour-like unless a physicist finds an anomaly.",
        )
    if r.QCD_like_high_HT_low_MET and r.SM_centroid_like and r.closer_to_QCD_than_SMS:
        return (
            "likely_QCD_multijet_like",
            "high-HT;low-MET;QCD-close",
            "high",
            "The event is dominated by visible multijet activity and is closer to QCD/SM than to SMS.",
            "Treat as ordinary multijet-like unless further checks disagree.",
        )
    if r.high_BNF_and_high_trace and (r.SM_centroid_like or r.source_file_overconcentration_flag or r.run_overconcentration_flag or r.lumi_overconcentration_flag):
        tags = ["high-BNF", "high-trace"]
        if r.SM_centroid_like:
            tags.append("SM-centroid-close")
        if r.source_file_overconcentration_flag or r.run_overconcentration_flag or r.lumi_overconcentration_flag:
            tags.append("provenance-concentration-warning")
        return (
            "trace_direction_aligned_but_SM_like",
            ";".join(tags),
            "medium",
            "The event is strongly aligned with the SMS-like trace direction, but it has either SM-centroid closeness or provenance concentration warnings.",
            "Useful for boundary-stress follow-up, but do not call it a direct trace-compatible candidate yet.",
        )
    if r.high_BNF_and_high_trace and r.SMS_trace_like_high_MET_HT_mult and (not r.SM_centroid_like) and r.passes_available_quality_filters:
        return (
            "trace_compatible_follow_up_candidate",
            "high-BNF;high-trace;high-MET/HT/multiplicity;quality-pass",
            "medium",
            "The event passes available quality checks and has high missing-information, visible-recoil and multiplicity stress without a simple SM-centroid match.",
            "Prioritise for expert follow-up.",
        )
    return (
        "unclear_follow_up_needed",
        "mixed-or-incomplete-evidence",
        "low",
        "The automated rules give mixed evidence or do not have enough information to make a clearer classification.",
        "Keep only as a lower-priority follow-up item.",
    )


def main() -> None:
    df = pd.read_csv(INFILE)
    rows = []
    for row in df.itertuples(index=False):
        category, tags, confidence, reason, action = classify(row)
        rows.append({
            "primary_category": category,
            "secondary_tags": tags,
            "confidence_level": confidence,
            "plain_english_reason": reason,
            "caveats": "Automated rule-based classification; not a physics-object-level event display.",
            "recommended_next_action": action,
        })
    out = pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    out.to_csv(TABLES / "classified_top_trace_candidates.csv", index=False)
    for name, group in out.groupby("candidate_set"):
        group.to_csv(TABLES / f"classified_top_trace_candidates_{name}.csv", index=False)
    counts = out.groupby(["candidate_set", "primary_category"], as_index=False).agg(events=("event", "count"))
    total = out.groupby("candidate_set", as_index=False).agg(total=("event", "count"))
    counts = counts.merge(total, on="candidate_set")
    counts["fraction"] = counts["events"] / counts["total"]
    counts.to_csv(TABLES / "trace_candidate_category_counts.csv", index=False)
    report = ["# Trace Candidate Classification Report", "", f"Date: {DATE}", "", "Classification is deliberately conservative. Trace-aligned but SM-like is preferred over overcalling trace-compatible follow-up.", "", counts.to_markdown(index=False)]
    (REPORTS / "TRACE_CANDIDATE_CLASSIFICATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(counts.to_string(index=False))


if __name__ == "__main__":
    main()
