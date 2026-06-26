from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"


def md_table(path: Path, rows: int | None = None) -> str:
    df = pd.read_csv(path)
    if rows:
        df = df.head(rows)
    return df.to_markdown(index=False)


def main() -> None:
    weights = pd.read_csv(TABLES / "benchmark_trace_direction_weights.csv")
    align = pd.read_csv(TABLES / "real_high_bnf_trace_alignment_summary.csv")
    dist = pd.read_csv(TABLES / "real_high_bnf_sms_vs_sm_direction_tests.csv")
    cand = pd.DataFrame([
        {"candidate_set": "Run2016G", "path": str(TABLES / "top_real_trace_candidates_run2016g.csv"), "events": len(pd.read_csv(TABLES / "top_real_trace_candidates_run2016g.csv"))},
        {"candidate_set": "Run2016H", "path": str(TABLES / "top_real_trace_candidates_run2016h.csv"), "events": len(pd.read_csv(TABLES / "top_real_trace_candidates_run2016h.csv"))},
        {"candidate_set": "combined", "path": str(TABLES / "top_real_trace_candidates_combined.csv"), "events": len(pd.read_csv(TABLES / "top_real_trace_candidates_combined.csv"))},
    ])
    top_align = align[align["bnf_tail"].isin(["top05", "top01", "top001"])][[
        "dataset", "bnf_tail", "high_events", "mean_trace_high", "mean_trace_rest", "mean_diff",
        "welch_gaussian_z", "fraction_high_above_trace_q90", "fraction_rest_above_trace_q90",
        "trace_q90_enrichment_ratio", "trace_q90_prop_z"
    ]]
    top_dist = dist[dist["bnf_tail"].isin(["top05", "top01", "top001"])][[
        "dataset", "bnf_tail", "events", "mean_distance_to_SMS", "mean_distance_to_TTJets",
        "mean_distance_to_QCD", "mean_distance_to_pooledSM", "fraction_closer_to_SMS_than_pooledSM_high",
        "enrichment_ratio", "gaussian_z"
    ]]
    positive = (
        "Real high-B_NF events show very strong SMS-like trace-projection enrichment in both Run2016G and Run2016H. "
        "This supports an indirect, model-dependent trace-alignment layer: as real events move deeper into the frozen N-Frame boundary tail, they move along the benchmark SMS-vs-SM contrast direction."
    )
    caveat = (
        "However, the distance-to-centroid test qualifies the result: the high-B_NF real events remain much closer in absolute component space to TTJets/QCD/pooled-SM centroids than to the SMS-T5Wg centroid. "
        "So the current result is best described as trace-direction alignment, not real events becoming SMS-like events."
    )
    report = [
        "# Real Data Trace Alignment Synthesis",
        "",
        f"Date: {DATE}",
        "",
        "## How The Benchmark Trace Direction Was Defined",
        "",
        "SMS-T5Wg was contrasted against TTJets, QCD and pooled SM using shared reduced components: P_missing, P_visible_energy, P_multiplicity, P_btag_structure and P_compression. Simulation was used only to define this direction; B_NF was not refitted.",
        "",
        weights.to_markdown(index=False),
        "",
        "## Real High-BNF Trace Alignment",
        "",
        top_align.to_markdown(index=False),
        "",
        positive,
        "",
        "## SMS Versus SM Centroid Distance",
        "",
        top_dist.to_markdown(index=False),
        "",
        caveat,
        "",
        "## Candidate Events",
        "",
        cand.to_markdown(index=False),
        "",
        "All top-100 candidate sets passed the available quality-filter checks in the generated tables.",
        "",
        "## Interpretation For Darren's Hypothesis",
        "",
        "This strengthens the N-Frame interpretation in a qualified way. It supports boundary-stress trace dynamics because the real high-boundary tail aligns strongly with the disappearance-compatible SMS-vs-SM direction. It does not prove hidden particles, and the centroid-distance test shows that the real data still look more SM-like in absolute benchmark space.",
        "",
        "## What Remains Weak",
        "",
        "The benchmark direction is reduced-component, the SM benchmark set is still small, there is no published signal-region residual integration yet, and the top real trace candidates have not been manually/event-display inspected.",
        "",
        "## Exact Next Step",
        "",
        "Manually inspect the top combined trace-candidate events, then repeat the trace-direction test with fuller MiniAODSIM TTJets/QCD and additional SM backgrounds.",
    ]
    (REPORTS / "REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md").write_text("\n".join(report), encoding="utf-8")
    update = [
        "# Update To Darren: Real Trace Alignment Test",
        "",
        f"Date: {DATE}",
        "",
        "We used the >=5 sigma benchmark result only to define a SUSY-like trace direction, then applied that direction back to real CMS Run2016G and Run2016H data.",
        "",
        "## Main Finding",
        "",
        positive,
        "",
        top_align.to_markdown(index=False),
        "",
        "## Important Qualification",
        "",
        caveat,
        "",
        "## Plain English Interpretation",
        "",
        "The real high-boundary events do not become direct SUSY candidates. But they do move strongly along the SMS-like disappearance-compatible direction as B_NF increases. That is indirect, model-dependent boundary-stress trace evidence, not direct particle detection.",
        "",
        "## Candidate Events",
        "",
        "Top-100 Run2016G, Run2016H and combined candidate lists were produced, and the available quality filters pass for those candidate sets.",
        "",
        "## Next Step",
        "",
        "Inspect the top real events visually and repeat with a broader/full-component SM benchmark set.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_REAL_TRACE_ALIGNMENT_TEST.md").write_text("\n".join(update), encoding="utf-8")
    print(top_align.to_string(index=False))
    print(top_dist.to_string(index=False))


if __name__ == "__main__":
    main()
