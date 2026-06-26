from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_discovery_grade_push_20260622"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

THREE_LIKE = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood_three_sample" / "tables" / "06_combined_10pct_likelihood_readout.csv"
THREE_SHAPE = ROOT / "outputs_opq_remote_three_sample_statistical_robustness" / "tables" / "03_opq_three_sample_combined_statistics.csv"
RUN2012_STATS = ROOT / "outputs_run2012c_aod_reduced_opq_analysis" / "tables" / "04_run2012c_aod_reduced_opq_statistics.csv"
RUN2012_LEDGER = ROOT / "outputs_run2012c_aod_reduced_validation" / "tables" / "01_run2012c_aod_reduced_extraction_ledger.csv"
SUMW_PLAN = ROOT / "outputs_remote_opq_sm_background_build" / "tables" / "15_exact_genfilter_sumweight_file_plan_summary.csv"
SUMW_ONE = ROOT / "cloud_remote_nframe_package" / "cmssw_full_extraction" / "exact_genfilter_sumweight_output_one.csv"
TTASSOC_STRESS = ROOT / "outputs_remote_opq_ttassoc_shape_contamination_stress" / "tables" / "02_ttassoc_shape_stress_combined.csv"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    three_like = pd.read_csv(THREE_LIKE)
    three_shape = pd.read_csv(THREE_SHAPE)
    run2012 = pd.read_csv(RUN2012_STATS)
    run2012_ledger = pd.read_csv(RUN2012_LEDGER)
    sumw_plan = pd.read_csv(SUMW_PLAN)
    sumw_one = pd.read_csv(SUMW_ONE)
    ttstress = pd.read_csv(TTASSOC_STRESS)

    three_like.to_csv(TABLES / "01_three_sample_likelihood_baseline.csv", index=False)
    run2012.to_csv(TABLES / "02_run2012c_reduced_aod_cross_era_result.csv", index=False)
    sumw_plan.to_csv(TABLES / "03_exact_sumweight_plan.csv", index=False)
    sumw_one.to_csv(TABLES / "04_exact_sumweight_working_probe.csv", index=False)

    met = three_like[three_like["region"].eq("MET_trace")].iloc[0]
    controls = three_like[three_like["region"].eq("JetHT_SingleMuon_controls")].iloc[0]
    shape = three_shape.iloc[0]
    old = run2012.iloc[0]
    run2012_events = int(run2012_ledger["events_written"].sum())
    stress20 = ttstress[(ttstress["ttassoc_shape_fraction"].eq(0.20)) & (ttstress["region"].eq("MET_trace"))].iloc[0]
    stress50 = ttstress[(ttstress["ttassoc_shape_fraction"].eq(0.50)) & (ttstress["region"].eq("MET_trace"))].iloc[0]

    report = f"""# Discovery-Grade Evidence Push: Outcome

## Purpose

This run attempted to move the N-Frame/CMS boundary-trace result toward final
discovery-grade evidence by attacking the two hard blockers:

1. exact MC normalisation through full-record sum-of-generator-weights;
2. validation beyond the existing 2015/2016 MiniAOD-like samples.

The OPQ score was not retuned:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

## Current Strongest Result Still Standing

Three-sample approximate SM sideband likelihood:

{three_like.to_markdown(index=False, floatfmt='.6g')}

Frozen OPQ three-sample shape combination:

{three_shape.to_markdown(index=False, floatfmt='.6g')}

Readout:

- MET trace combined likelihood Z: **{met.fisher_Z:.3f}**
- JetHT/SingleMuon control combined Z: **{controls.fisher_Z:.3f}**
- Controls close: **{bool(controls.controls_close_if_control_region)}**
- Three-sample OPQ shape Z: **{shape.fisher_shape_Z:.3f}**
- Weakest individual sample shape Z: **{shape.min_sample_shape_Z:.3f}**

This remains the strongest positive evidence in the project.

## Exact Sumweight Progress

CMSSW/ROOT branch inspection found the required products in MC
`LuminosityBlocks`:

- `GenFilterInfo_genFilterEfficiencyProducer__GEN`
- `GenLumiInfoHeader_generator__GEN`
- `GenLumiInfoProduct_generator__GEN`
- `GenRunInfoProduct_generator__GEN`

A ROOT/CMSSW macro was added and successfully read exact per-file
`GenFilterInfo` sums directly from the remote file:

{sumw_one.to_markdown(index=False, floatfmt='.6g')}

Exact full-online plan:

{sumw_plan.to_markdown(index=False)}

Interpretation:

- Exact per-file sumweights are technically solved.
- Full-record exact sumweights are possible for records with complete online
  file coverage, especially W3Jets and TTW.
- Full execution over hundreds of remote files is slow and needs chunked
  production running.
- TTZ remains a blocker: the TTZ records expose only one online file each and
  the local CERN metadata does not expose usable cross-section fields.

## Extra-Era Validation Attempt: Run2012C AOD

Run2012C AOD records were found and processed remotely through the working
CMSSW 10 image:

- MET record 6038
- JetHT record 6036
- SingleMu record 6047
- HTMHTParked record 6034

Total reduced-AOD events extracted: **{run2012_events:,}**

Run2012C result:

{run2012.to_markdown(index=False, floatfmt='.6g')}

Interpretation:

The Run2012C reduced-AOD result is positive in direction but weak:

- shape Z: **{old.shape_Z:.3f}**
- shoulder Z: **{old.shoulder_Z:.3f}**
- MET shoulder above control: **{bool(old.shoulder_above_control)}**

This does **not** give discovery-grade cross-era replication. It suggests the
current OPQ trace is sensitive to feature definitions, detector era, or the
reduced AOD mapping. That is important because it prevents us from overstating
the 2015/2016 result.

## Rare Top-Associated Stress Still Relevant

TTZ/TTW shape-contamination stress already showed:

- MET Z at 20 percent TTZ/TTW shape blend: **{stress20.fisher_Z:.3f}**
- MET Z at 50 percent TTZ/TTW shape blend: **{stress50.fisher_Z:.3f}**

This means plausible rare-top shape contamination does not obviously remove
the signal. However, official TTZ normalisation is still not closed.

## Discovery-Grade Status

Current status:

**Not final discovery-grade evidence.**

What improved:

- A real older-era CMS Run2012C AOD validation path now exists.
- 60,000 Run2012C real collision events were extracted and tested.
- Exact `GenFilterInfo` sumweight extraction from remote MC files is proven.
- The current best 2015/2016 MET trace result remains strong with controls
  closed.

What blocks a final claim:

1. Run2012C reduced-AOD does not strongly replicate the trace.
2. Full-record exact sumweights are not yet production-complete for all MC
   backgrounds.
3. TTZ full normalisation remains unresolved because only partial files and
   incomplete cross-section metadata are available through the current route.
4. The official CMS-grade likelihood with full nuisance modelling is still not
   complete.

## Exact Next Action

The next best action is not OPQ retuning. It is:

1. run the exact `GenFilterInfo` sumweight macro in chunks over all full-online
   W3Jets and TTW files;
2. build a corrected exact/metadata-hybrid SM normalisation table;
3. rerun the frozen three-sample likelihood;
4. improve the Run2012 AOD feature mapping by adding AOD b-tag associations and
   V0/secondary-vertex-like counts, then rerun the same Run2012C test.

Only if the exact-normalised likelihood remains high **and** an improved
cross-era sample replicates strongly should this be called close to
discovery-grade N-Frame boundary-trace evidence.
"""
    (REPORTS / "01_DISCOVERY_GRADE_PUSH_OUTCOME.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_DISCOVERY_GRADE_PUSH_OUTCOME.md")
    print(three_like.to_string(index=False))
    print(run2012.to_string(index=False))


if __name__ == "__main__":
    main()
