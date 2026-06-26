from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"


def main():
    manifest = pd.read_csv(TABLES / "expanded_benchmark_download_manifest.csv")
    summary = pd.read_csv(TABLES / "expanded_benchmark_bnf_summary.csv")
    corr = pd.read_csv(TABLES / "expanded_benchmark_corrected_sigma_tests.csv")
    inc = pd.read_csv(TABLES / "expanded_bnf_vs_met_ht_incremental_tests.csv")
    weights = pd.read_csv(TABLES / "expanded_trace_direction_weights.csv")
    align = pd.read_csv(TABLES / "expanded_real_trace_alignment_summary.csv")
    mimic = pd.read_csv(TABLES / "expanded_driver_profile_distances.csv")
    sms_q95 = corr[(corr["signal_sample"].eq("sms_t5wg_mg1500_mlsp1_signal")) & (corr["threshold"].eq("q95"))].sort_values("bonferroni_z")
    added = manifest[["sample_id", "process_label", "classification", "data_tier", "actual_size_bytes"]]
    survives = bool((sms_q95["remains_5sigma_after_bonferroni"] == True).all())
    bnf_median = inc[inc["model_or_score"].eq("B_NF_fitted")]["auc"].median()
    simple_median = inc[inc["model_or_score"].eq("P_missing_plus_visible_plus_multiplicity")]["auc"].median()
    verdict = "strengthens" if survives else "qualifies"
    report = [
        "# Expanded Benchmark And Trace Robustness Synthesis",
        "",
        f"Date: {DATE}",
        "",
        "## New Samples Added",
        "",
        added.to_markdown(index=False),
        "",
        f"Total new download size: {manifest['actual_size_bytes'].sum() / 1024**3:.3f} GiB.",
        "",
        "## Expanded BNF Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## SMS-T5Wg q95 Corrected Tests",
        "",
        sms_q95.to_markdown(index=False),
        "",
        "## Incremental Test",
        "",
        f"Median B_NF AUC across expanded comparisons: {bnf_median:.3f}. Median missing+visible+multiplicity AUC: {simple_median:.3f}. If the latter is higher, the separation remains largely MET/HT/multiplicity driven.",
        "",
        "## Expanded Trace Direction",
        "",
        weights.to_markdown(index=False),
        "",
        "## Real Data Expanded Trace Alignment",
        "",
        align.to_markdown(index=False),
        "",
        "## Mimicry Distances",
        "",
        mimic.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        f"The expanded automated layer {verdict} Darren's disappearance-trace interpretation in a qualified way. SMS-T5Wg remains benchmark-enriched if the q95 rows above remain above 5 sigma after correction. The result is still indirect, model-dependent benchmark enrichment and real-data trace-direction alignment, not direct particle detection.",
        "",
        "## Remaining Weaknesses",
        "",
        "The expansion used small NanoAODSIM files, so component availability is still reduced. W/Z/DY/single-top/diboson coverage is still incomplete, and published signal-region overlap remains missing.",
    ]
    (REPORTS / "EXPANDED_BENCHMARK_AND_TRACE_ROBUSTNESS_SYNTHESIS.md").write_text("\n".join(report), encoding="utf-8")
    update = [
        "# Update To Darren: Expanded Benchmark Robustness",
        "",
        f"Date: {DATE}",
        "",
        "We did not stop at manual inspection. We broadened the automated benchmark layer with additional WJets, QCD HT bins and a compressed stop-like SUSY benchmark, all treated as benchmark/specificity simulation only.",
        "",
        "## Added Samples",
        "",
        added.to_markdown(index=False),
        "",
        "## Does The 5 Sigma SMS-T5Wg Result Survive?",
        "",
        sms_q95.to_markdown(index=False),
        "",
        "## Does The Trace Direction Still Appear In Real Data?",
        "",
        align[align["bnf_tail"].eq("top01")].to_markdown(index=False),
        "",
        "## Plain English",
        "",
        "This remains indirect, model-dependent evidence. It is not direct particle detection and not a discovery claim. The main weakness is that the added samples are small NanoAODSIM reduced-component benchmarks.",
        "",
        "## Next Step",
        "",
        "Add fuller MiniAODSIM or larger NanoAODSIM W/Z/DY/single-top/diboson backgrounds, then repeat the same frozen-score test.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_EXPANDED_BENCHMARK_ROBUSTNESS.md").write_text("\n".join(update), encoding="utf-8")
    print(added.to_string(index=False))
    print(sms_q95[["background_sample", "p_signal", "p_background", "bonferroni_z", "remains_5sigma_after_bonferroni"]].to_string(index=False))


if __name__ == "__main__":
    main()
