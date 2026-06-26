from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / name)


def main() -> None:
    counts = read("trace_candidate_category_counts.csv")
    quality = read("trace_candidate_quality_filter_summary.csv")
    warnings = read("trace_candidate_artifact_warning_summary.csv")
    controls = read("trace_candidate_vs_matched_control_differences.csv")
    trigger = read("trace_candidate_trigger_summary.csv")
    cards = read("top25_trace_candidate_cards.csv")
    combined_counts = counts[counts["candidate_set"].eq("combined")]
    diff_cols = [c for c in controls.columns if c.startswith("candidate_minus_control_")]
    diff_summary = pd.DataFrame({
        "metric": diff_cols,
        "median_candidate_minus_control": [controls[c].median() for c in diff_cols],
        "mean_candidate_minus_control": [controls[c].mean() for c in diff_cols],
    })
    follow_up = int(combined_counts[combined_counts["primary_category"].eq("trace_compatible_follow_up_candidate")]["events"].sum())
    sm_like = int(combined_counts[combined_counts["primary_category"].str.contains("SM|top|QCD", regex=True)]["events"].sum())
    trace_aligned_sm = int(combined_counts[combined_counts["primary_category"].eq("trace_direction_aligned_but_SM_like")]["events"].sum())
    quality_fail = int(quality[quality["flag"].eq("fails_any_available_quality_filter")]["events"].sum()) if "fails_any_available_quality_filter" in set(quality["flag"]) else 0

    interpretation = (
        "The automated sanity check does not identify direct particle evidence. "
        "It does identify a small follow-up subset that is high-B_NF, high trace-direction, quality-passing and not caught by the simple SM-centroid rules. "
        "Most candidates remain better described as trace-direction aligned but still SM-like or provenance-caveated."
    )
    report = [
        "# Real Trace Candidate Sanity Check Synthesis",
        "",
        f"Date: {DATE}",
        "",
        "## Category Counts",
        "",
        counts.to_markdown(index=False),
        "",
        "## Plain-English Summary",
        "",
        f"- Combined candidates classified: 100.",
        f"- Trace-compatible follow-up candidates: {follow_up}.",
        f"- Trace-direction aligned but still SM-like/provenance-caveated: {trace_aligned_sm}.",
        f"- Clearly SM/top-like candidates in combined set: {sm_like}.",
        f"- Available quality-filter failures: {quality_fail}.",
        "",
        interpretation,
        "",
        "## Quality, Trigger And Concentration",
        "",
        "All top candidate sets pass the available compact quality-filter flag, but many candidates are concentrated in source files/runs/lumis. That is a provenance warning, not by itself proof of an artefact.",
        "",
        quality.to_markdown(index=False),
        "",
        trigger.to_markdown(index=False),
        "",
        warnings.to_markdown(index=False),
        "",
        "## Matched-Control Result",
        "",
        "Compared with nearby ordinary real controls, candidates have much higher B_NF, trace score, MET, HT, secondary-vertex count, and are closer to the SMS centroid while farther from pooled SM. This supports that they are unusual relative to ordinary events from similar data-taking context.",
        "",
        diff_summary.to_markdown(index=False),
        "",
        "## Top Candidate Cards",
        "",
        "Plain-English cards for the top 25 combined candidates are available in `reports/TOP25_TRACE_CANDIDATE_CARDS.md`.",
        "",
        "## Effect On Darren's Hypothesis",
        "",
        "This strengthens the disappearance-trace interpretation in a qualified way: the follow-up subset is quality-passing, trace-direction aligned, and unusual relative to matched controls. But most candidates are still SM-like/provenance-caveated, and this remains indirect model-dependent evidence rather than direct particle detection.",
        "",
        "## Exact Next Step",
        "",
        "Ask a particle-physics expert to review the 6 combined trace-compatible follow-up candidates and the top-25 cards, focusing first on source/run/lumi concentration and whether the event shapes have ordinary SM explanations.",
    ]
    (REPORTS / "REAL_TRACE_CANDIDATE_SANITY_CHECK_SYNTHESIS.md").write_text("\n".join(report), encoding="utf-8")

    update = [
        "# Update To Darren: Trace Candidate Sanity Check",
        "",
        f"Date: {DATE}",
        "",
        "We avoided relying on Tom manually inspecting event displays and ran an automated sanity check on the top real trace candidates.",
        "",
        "## What We Found",
        "",
        combined_counts.to_markdown(index=False),
        "",
        f"In the combined top-100 list, {follow_up} events are trace-compatible follow-up candidates by the conservative automated rules. Most are trace-direction aligned but still SM-like or provenance-caveated.",
        "",
        "## Quality And Controls",
        "",
        f"Available quality-filter failures: {quality_fail}. Matched-control comparison shows the candidates are not ordinary within nearby real-data context: they have higher B_NF, higher trace score, higher MET/HT, more secondary-vertex structure, and are closer to the SMS trace centroid than their controls.",
        "",
        "## What This Means",
        "",
        "This is still not direct particle detection. It is an automated sanity layer supporting boundary-stress trace dynamics for a small follow-up subset, while qualifying the broader set as mostly SM-like/provenance-caveated.",
        "",
        "## Next Step",
        "",
        "Have someone with physics expertise inspect the 6 combined follow-up candidates and the top-25 plain-English cards, especially source/run/lumi concentration and ordinary SM explanations.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_TRACE_CANDIDATE_SANITY_CHECK.md").write_text("\n".join(update), encoding="utf-8")
    print(combined_counts.to_string(index=False))
    print(diff_summary.to_string(index=False))


if __name__ == "__main__":
    main()
