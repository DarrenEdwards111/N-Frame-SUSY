from __future__ import annotations

from pathlib import Path

import pandas as pd

from fuller_component_common import DATE, OUT, REPORTS, TABLES


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def yn(value: bool) -> str:
    return "yes" if bool(value) else "no"


def main() -> None:
    manifest = read(TABLES / "fuller_component_download_manifest.csv")
    smoke = read(TABLES / "fuller_component_smoke_extraction_summary.csv")
    full = read(TABLES / "fuller_component_full_extraction_summary.csv")
    score = read(TABLES / "fuller_component_bnf_summary.csv")
    compare = read(TABLES / "fuller_vs_reduced_component_tail_comparison.csv")
    sigma = read(TABLES / "fuller_component_sigma_tests.csv")
    incremental = read(TABLES / "fuller_component_bnf_vs_met_ht_incremental_tests.csv")
    trace = read(TABLES / "fuller_component_real_trace_alignment_summary.csv")
    availability = read(TABLES / "fuller_component_feature_availability.csv")

    total_downloaded = int(manifest["actual_size_bytes"].sum()) if not manifest.empty else 0
    total_events = int(full["events_written"].sum()) if not full.empty else 0
    p_disp = availability["has_secondary_vertex_count"].all() if not availability.empty else False
    p_reco = availability["has_packed_candidate_count"].all() if not availability.empty else False
    qcd1000 = score[score["sample_id"].astype(str).str.contains("qcd_ht1000", na=False)] if not score.empty else pd.DataFrame()
    strongest = score.sort_values("mean_BNF", ascending=False).head(1) if not score.empty else pd.DataFrame()
    sms_q95 = sigma[
        sigma["signal_sample"].astype(str).str.contains("t5wg", case=False, na=False)
        & sigma["threshold"].eq("q95")
    ] if not sigma.empty else pd.DataFrame()
    inc_med = incremental.groupby("score", as_index=False)["auc"].median().sort_values("auc", ascending=False) if not incremental.empty else pd.DataFrame()

    interpretation = (
        "qualified/partial. The fuller-component SM MiniAODSIM extraction worked and confirms that P_displacement_proxy "
        "and P_reconstruction can be populated from MiniAOD, but the accessible fuller sample set contains no signal file. "
        "High-HT QCD becomes a stronger boundary mimic than SMS-T5Wg in q95/q99 tail tests, so the earlier SUSY-like result "
        "is less specific than it looked from the reduced benchmark layer."
    )

    synthesis = [
        "# Fuller Component MiniAODSIM Benchmark Synthesis",
        "",
        f"Date: {DATE}",
        "",
        "## What was done",
        "",
        "We searched CERN Open Data metadata for MiniAODSIM benchmark files, planned a download under the 25 GB cap, downloaded accessible files, ran CMSSW extraction, applied the frozen Run2016G fitted N-Frame equation, and compared the fuller-component results with the earlier reduced benchmark layer.",
        "",
        "No B_NF refit was performed. No discovery claim is made. This is not a SUSY classifier.",
        "",
        "## Data outcome",
        "",
        f"- Selected files in plan: {len(manifest)}",
        f"- Downloaded or already present files: {int(manifest['download_status'].isin(['already_present', 'downloaded', 'downloaded_xrdcp']).sum()) if not manifest.empty else 0}",
        f"- Total downloaded bytes: {total_downloaded}",
        f"- Successful full CMSSW extractions: {int(full['status'].eq('success').sum()) if not full.empty else 0}",
        f"- Total extracted fuller-component events: {total_events}",
        f"- P_displacement_proxy available through secondary vertices: {yn(p_disp)}",
        f"- P_reconstruction available through packed candidates: {yn(p_reco)}",
        "",
        "## Sample summary",
        "",
        score.to_markdown(index=False) if not score.empty else "No scored fuller-component samples were available.",
        "",
        "## Key statistical result",
        "",
        sms_q95.to_markdown(index=False) if not sms_q95.empty else "SMS-T5Wg could not be tested against fuller-component backgrounds.",
        "",
        "## Incremental score check",
        "",
        inc_med.to_markdown(index=False) if not inc_med.empty else "No incremental score table was available.",
        "",
        "## Trace direction",
        "",
        trace.to_markdown(index=False) if not trace.empty else "No fuller-component real-data trace application was available.",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "## Exact next action",
        "",
        "Find an accessible MiniAODSIM signal file, preferably SMS-T5Wg or another high-MET simplified model, and rerun phases 101-108 with at least one signal and the existing high-HT QCD fuller-component backgrounds.",
    ]
    (REPORTS / "FULLER_COMPONENT_BENCHMARK_SYNTHESIS.md").write_text("\n".join(synthesis), encoding="utf-8")

    darren = [
        "# Update to Darren: Fuller Component MiniAODSIM Benchmark",
        "",
        f"Date: {DATE}",
        "",
        "## Stage 1: What we added",
        "",
        "We moved from reduced NanoAOD-style benchmark checks to MiniAODSIM files where packed candidates and secondary vertices are available. This lets us test the fitted N-Frame equation with fuller versions of P_reconstruction and P_displacement_proxy.",
        "",
        "## Stage 2: What worked",
        "",
        f"CMSSW extraction succeeded for QCD HT1000to1500, QCD HT700to1000, and WJetsToLNu, giving {total_events} fuller-component simulated background events. All successful samples had secondary-vertex and packed-candidate information.",
        "",
        "## Stage 3: Main finding",
        "",
        "The high-HT QCD MiniAODSIM sample is a strong boundary mimic. Its q95 and q99 boundary-tail fractions are higher than the earlier SMS-T5Wg benchmark, so the previous signal-like tail result is not specific to SUSY-like samples.",
        "",
        "## Stage 4: What failed",
        "",
        "The planned SingleTop and compressed T2tt files were listed in the metadata but were missing at the advertised CERN EOS paths. Because no MiniAODSIM signal file survived download, we could not build a true fuller-component signal-vs-background trace direction.",
        "",
        "## Stage 5: Interpretation",
        "",
        "This qualifies the N-Frame interpretation rather than strengthens it unambiguously. It supports the idea that the fitted boundary finds unusual high-energy/high-complexity event structure, but it also shows that Standard Model high-HT QCD can occupy the same boundary region.",
        "",
        "## Next task",
        "",
        "Locate an accessible MiniAODSIM signal sample and repeat the fuller-component benchmark against the existing high-HT QCD fuller backgrounds.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_FULLER_COMPONENT_BENCHMARK.md").write_text("\n".join(darren), encoding="utf-8")
    print((REPORTS / "FULLER_COMPONENT_BENCHMARK_SYNTHESIS.md").resolve())
    print((REPORTS / "UPDATE_TO_DARREN_FULLER_COMPONENT_BENCHMARK.md").resolve())


if __name__ == "__main__":
    main()
