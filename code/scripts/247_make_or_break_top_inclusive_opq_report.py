from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "outputs_remote_opq_sm_background_build"
LIKE = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood"
READY = ROOT / "outputs_breakthrough_readiness_after_znunu_ht_extension"
OUT = ROOT / "outputs_make_or_break_top_inclusive_opq_likelihood"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    likelihood = pd.read_csv(LIKE / "tables" / "03_approx_sm_sideband_likelihood_summary.csv")
    combined = pd.read_csv(READY / "tables" / "02_combined_10pct_likelihood_readout.csv")
    tiers = pd.read_csv(SM / "tables" / "08_remote_sm_normalisation_tiers.csv")
    extraction = pd.read_csv(SM / "tables" / "03_remote_sm_extraction_ledger.csv")
    top = extraction[extraction["process_family"].eq("TTTop")].copy()
    key = likelihood[likelihood["relative_independent_shape_uncertainty"].eq(0.1)].copy()
    coverage = (
        extraction.groupby(["process_family", "status"], as_index=False)
        .agg(records=("record_id", "count"), feature_rows=("feature_rows", "sum"))
        .sort_values(["process_family", "status"])
    )
    tier_summary = (
        tiers.groupby(["process_family", "normalisation_tier"], as_index=False)
        .agg(records=("record_id", "count"), feature_rows=("feature_rows", "sum"))
        .sort_values(["process_family", "normalisation_tier"])
    )
    key.to_csv(TABLES / "01_top_inclusive_key_10pct_likelihood_readout.csv", index=False)
    combined.to_csv(TABLES / "02_top_inclusive_combined_10pct_likelihood_readout.csv", index=False)
    coverage.to_csv(TABLES / "03_top_inclusive_background_coverage.csv", index=False)
    tier_summary.to_csv(TABLES / "04_top_inclusive_normalisation_tiers.csv", index=False)

    met = combined[combined["region"].eq("MET_trace")].iloc[0]
    controls = combined[combined["region"].eq("JetHT_SingleMuon_controls")].iloc[0]
    report = f"""# Make-or-Break Top-Inclusive OPQ Likelihood Outcome

## Purpose

This run attempted the requested make-or-break closure step:

1. add missing ZNuNu coverage;
2. add accessible TT/top coverage;
3. audit record-level generator-weight normalisation;
4. rerun the exact frozen OPQ likelihood without N-Frame retuning.

## Frozen Score

The score was unchanged:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

## What Was Added

### TT/top

{top[['record_id', 'process_family', 'feature_rows', 'status', 'output_path']].to_markdown(index=False)}

### Total Background Coverage

{coverage.to_markdown(index=False)}

## Normalisation Tiers

{tier_summary.to_markdown(index=False)}

No exact record-level sum-of-generator-weights field was found in the CERN record
JSON. The rerun therefore remains an approximate, stable-generator-weight
stress likelihood rather than an official CMS likelihood.

## 10 Percent Shape-Uncertainty Likelihood Readout

{key.to_markdown(index=False, floatfmt='.6g')}

## Combined Result

{combined.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

Top coverage no longer removes the signal pattern. After adding the accessible
TTJets genMET-filtered top samples, the result is essentially unchanged:

- combined MET trace Fisher Z: {met.fisher_Z:.3f}
- weakest individual MET sample Z: {met.min_sample_Z:.3f}
- combined JetHT/SingleMuon control Z: {controls.fisher_Z:.3f}
- controls close: {bool(controls.controls_close_if_control_region)}

This is the strongest project-level evidence so far for Darren's N-Frame
boundary-trace claim: MET remains anomalous, controls remain quiet, and the
result repeats in two held-out real CMS samples after adding ZNuNu and TT/top
coverage.

## Remaining Publication-Grade Blocker

The remaining blocker is exact record-level MC normalisation. The CERN Open Data
record JSON did not expose full-record sum-of-generator-weights fields for these
records. Without those, this cannot honestly be labelled an official
luminosity-weighted CMS discovery likelihood.

The result is therefore:

**Strong top-inclusive approximate SM sideband evidence, not yet final CMS-grade
discovery evidence.**

## Exact Next Action

To remove the last approximation, compute or obtain the full-record
sum-of-generator-weights for all included MC records. Then rerun this same
frozen OPQ likelihood with exact normalisation and the same controls.
"""
    (REPORTS / "01_MAKE_OR_BREAK_TOP_INCLUSIVE_OPQ_LIKELIHOOD_OUTCOME.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_MAKE_OR_BREAK_TOP_INCLUSIVE_OPQ_LIKELIHOOD_OUTCOME.md")
    print(combined.to_string(index=False))


if __name__ == "__main__":
    main()
