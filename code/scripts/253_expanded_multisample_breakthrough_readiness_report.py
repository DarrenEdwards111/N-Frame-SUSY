from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_expanded_multisample_breakthrough_readiness"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

REAL_LEDGER = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation" / "tables" / "15_run2016g_fresh_grouped_remote_ledger.csv"
THREE_STATS = ROOT / "outputs_opq_remote_three_sample_statistical_robustness" / "tables" / "01_opq_three_sample_statistics.csv"
THREE_COMBINED = ROOT / "outputs_opq_remote_three_sample_statistical_robustness" / "tables" / "03_opq_three_sample_combined_statistics.csv"
LIKE_KEY = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood_three_sample" / "tables" / "05_key_10pct_likelihood_readout.csv"
LIKE_COMBINED = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood_three_sample" / "tables" / "06_combined_10pct_likelihood_readout.csv"
SM_COVERAGE = ROOT / "outputs_remote_opq_sm_background_build" / "tables" / "05_remote_sm_coverage_summary.csv"
SM_TIERS = ROOT / "outputs_remote_opq_sm_background_build" / "tables" / "08_remote_sm_normalisation_tiers.csv"
TTASSOC_SEARCH = ROOT / "outputs_remote_opq_sm_background_build" / "tables" / "12_top_associated_search_records.csv"
TTASSOC_STRESS = ROOT / "outputs_remote_opq_ttassoc_shape_contamination_stress" / "tables" / "02_ttassoc_shape_stress_combined.csv"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    run2016g = pd.read_csv(REAL_LEDGER)
    three_stats = pd.read_csv(THREE_STATS)
    three_combined = pd.read_csv(THREE_COMBINED)
    like_key = pd.read_csv(LIKE_KEY)
    like_combined = pd.read_csv(LIKE_COMBINED)
    coverage = pd.read_csv(SM_COVERAGE)
    tiers = pd.read_csv(SM_TIERS)
    ttassoc_search = pd.read_csv(TTASSOC_SEARCH)
    ttassoc_stress = pd.read_csv(TTASSOC_STRESS)

    tier_summary = (
        tiers.groupby(["process_family", "normalisation_tier"], as_index=False)
        .agg(records=("record_id", "count"), feature_rows=("feature_rows", "sum"))
        .sort_values(["process_family", "normalisation_tier"])
    )
    stress_key = ttassoc_stress[ttassoc_stress["ttassoc_shape_fraction"].isin([0.0, 0.1, 0.2, 0.5])].copy()
    stress_key = stress_key[["ttassoc_shape_fraction", "region", "fisher_Z", "min_sample_Z", "controls_close_if_control_region"]]

    run2016g.to_csv(TABLES / "01_run2016g_added_real_data_ledger.csv", index=False)
    three_stats.to_csv(TABLES / "02_three_sample_opq_statistics.csv", index=False)
    like_combined.to_csv(TABLES / "03_three_sample_likelihood_combined.csv", index=False)
    tier_summary.to_csv(TABLES / "04_sm_normalisation_tier_summary_after_ttassoc.csv", index=False)
    stress_key.to_csv(TABLES / "05_ttassoc_stress_key_readout.csv", index=False)

    met = like_combined[like_combined["region"].eq("MET_trace")].iloc[0]
    controls = like_combined[like_combined["region"].eq("JetHT_SingleMuon_controls")].iloc[0]
    shape = three_combined.iloc[0]
    run2016g_rows = int(run2016g["events_written"].sum()) if "events_written" in run2016g else 0
    report = f"""# Expanded Multisample Breakthrough-Readiness Report

## Purpose

This report records the next-step work completed after the previous
make-or-break OPQ likelihood. The target was to move closer to Darren's
boundary-trace claim by adding more real CMS validation data, strengthening the
Standard Model background coverage, and keeping the N-Frame score frozen.

The tested score remained:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

No OPQ retuning was performed in this run.

## 1. New Independent Real-Data Validation Added

Fresh Run2016G CMS MiniAOD streams were processed remotely through XRootD. No
raw ROOT files were retained locally.

{run2016g.to_markdown(index=False)}

Total fresh Run2016G compact events added: **{run2016g_rows:,}**.

This gives the formal three-sample validation set:

- `Run2015D_remote_mht_aware_holdout`
- `Run2016H_remote_mht_aware`
- `Run2016G_remote_mht_aware_fresh`

This is now more than two real-data validation samples, but still only two
calendar years: 2015 and 2016.

## 2. Frozen OPQ Three-Sample Statistical Robustness

The trace region is MET 0jet. Controls are JetHT and SingleMuon under the same
microband construction.

{three_stats.to_markdown(index=False, floatfmt='.6g')}

Combined result:

{three_combined.to_markdown(index=False, floatfmt='.6g')}

Readout:

- Combined three-sample OPQ shape Z: **{shape.fisher_shape_Z:.3f}**
- Weakest individual sample shape Z: **{shape.min_sample_shape_Z:.3f}**
- Samples with shape Z >= 5: **{int(shape.samples_shape_Z_ge_5)} / {int(shape.sample_count)}**
- Samples with positive bootstrap shoulder interval: **{int(shape.samples_positive_bootstrap_ci)} / {int(shape.sample_count)}**

Interpretation: the added Run2016G sample preserves the same sign of the
boundary-trace effect, but it is weaker than Run2015D and Run2016H. That
strengthens repeatability while also qualifying the claim.

## 3. Three-Sample Approximate SM Sideband Likelihood

The approximate process-aware SM sideband likelihood was rerun with all three
real validation samples.

Key 10 percent shape-uncertainty readout:

{like_key.to_markdown(index=False, floatfmt='.6g')}

Combined 10 percent readout:

{like_combined.to_markdown(index=False, floatfmt='.6g')}

Main result:

- Combined MET trace Fisher Z: **{met.fisher_Z:.3f}**
- Weakest individual MET likelihood Z: **{met.min_sample_Z:.3f}**
- Combined JetHT/SingleMuon control Z: **{controls.fisher_Z:.3f}**
- Controls close under the same likelihood: **{bool(controls.controls_close_if_control_region)}**

Interpretation: under the current approximate SM template, the MET trace remains
high while JetHT/SingleMuon controls close. This is the strongest current
multisample evidence for an N-Frame boundary-trace pattern.

## 4. Standard Model Background Coverage After This Run

Compact MC feature coverage after adding ZNuNu HT-binned records, TTJets, and
TTZ/TTW top-associated records:

{coverage.to_markdown(index=False, floatfmt='.6g')}

Normalisation tiers:

{tier_summary.to_markdown(index=False, floatfmt='.6g')}

Exact record-level sum-of-generator-weights were searched for in the CERN
record JSON and were not found. Therefore the likelihood remains an approximate
stable-generator-weight stress likelihood, not an official CMS
luminosity-weighted discovery likelihood.

## 5. Rare TTZ/TTW Top-Associated Check

The CERN API exposed usable TTZ/TTW MiniAODSIM records:

{ttassoc_search.to_markdown(index=False)}

These records were extracted and scored. They were not promoted to the strict
yield template because their generator weights are highly variable and the TTZ
records do not expose usable cross-section fields in the local metadata table.

To avoid ignoring them, a separate shape-contamination stress test blended their
OPQ shape into the SM sideband template at fixed fractions:

{stress_key.to_markdown(index=False, floatfmt='.6g')}

Interpretation: the MET trace remains above 6 sigma combined even with a large
20 percent TTZ/TTW shape blend, while controls still close. At an extreme 50
percent blend the MET result drops to about 3.4 sigma. This means rare
top-associated shape uncertainty does not explain the result at plausible
fractions, but official TTZ/TTW normalisation is still not closed.

## 6. Breakthrough Status

Current status: **strong exploratory multisample boundary-trace evidence, not
yet publication-grade discovery evidence**.

What became stronger in this run:

- The result now includes a third real CMS validation sample.
- The frozen OPQ score still produces a combined MET trace excess.
- JetHT/SingleMuon controls close in the approximate likelihood.
- ZNuNu, TTJets, and TTZ/TTW coverage have all been explicitly checked.
- The TTZ/TTW shape-contamination stress test does not remove the MET trace at
  plausible fractions.

What still prevents a final breakthrough/discovery claim:

- Exact full-record MC sum-of-generator-weights are still missing.
- TTZ/TTW are not yet luminosity-normalised.
- The likelihood is not an official CMS HistFactory model with full detector,
  trigger, object, process-mixture, and finite-MC nuisance treatment.
- The validation now has three samples, but only two years. A stronger claim
  needs either a third year or a detector/configuration-equivalent cross-era
  test.
- Run2016G is positive but weaker than Run2015D/Run2016H, so the effect is
  repeatable but not uniform.

## 7. Exact Next Action

The next decisive action is to remove the last two publication-grade blockers
without changing the OPQ score:

1. Compute or obtain exact full-record sum-of-generator-weights for the MC
   records already used.
2. Add official/defensible TTZ and TTW cross sections and normalisation, or
   document why their contribution is bounded below the stress-test level.
3. Rerun the same frozen three-sample likelihood.
4. Add a genuinely new validation year or equivalent cross-era CMS sample. If
   Run2017/Run2018 MiniAOD remains unavailable through Open Data, the practical
   next choice is a third-year proxy such as CMS 2012/AOD-derived variables or
   a larger pre-declared set of unused 2016 eras as a weaker replication layer.

If the MET trace remains high, controls close, and the result survives exact MC
normalisation plus another independent era, then the project moves from strong
exploratory evidence toward a publishable breakthrough-level N-Frame
boundary-trace claim.
"""
    (REPORTS / "01_EXPANDED_MULTISAMPLE_BREAKTHROUGH_READINESS.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_EXPANDED_MULTISAMPLE_BREAKTHROUGH_READINESS.md")
    print(like_combined.to_string(index=False))


if __name__ == "__main__":
    main()
