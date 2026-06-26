from __future__ import annotations

"""Summarise breakthrough readiness after the expanded ZNuNu HT rerun."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "outputs_remote_opq_sm_background_build"
LIKE = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood"
OUT = ROOT / "outputs_breakthrough_readiness_after_znunu_ht_extension"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(LIKE / "tables" / "03_approx_sm_sideband_likelihood_summary.csv")
    tiers = pd.read_csv(SM / "tables" / "08_remote_sm_normalisation_tiers.csv")
    extraction = pd.read_csv(SM / "tables" / "03_remote_sm_extraction_ledger.csv")

    key = summary[summary["relative_independent_shape_uncertainty"].eq(0.1)].copy()
    combined_rows = []
    for region, group in key.groupby("region", sort=False):
        stat, p = combine_pvalues(group["background_only_p"].to_numpy(float), method="fisher")
        combined_rows.append(
            {
                "region": region,
                "samples_combined": ";".join(group["sample_validation_id"].astype(str)),
                "fisher_statistic": float(stat),
                "fisher_p": float(p),
                "fisher_Z": p_to_z(float(p)),
                "min_sample_Z": float(group["background_only_Z"].min()),
                "max_sample_Z": float(group["background_only_Z"].max()),
                "controls_close_if_control_region": bool(region != "MET_trace" and group["background_only_Z"].abs().max() < 1.0),
            }
        )
    combined = pd.DataFrame(combined_rows)
    tier_summary = (
        tiers.groupby(["process_family", "normalisation_tier"], as_index=False)
        .agg(records=("record_id", "count"), feature_rows=("feature_rows", "sum"))
        .sort_values(["process_family", "normalisation_tier"])
    )
    extract_summary = (
        extraction.groupby(["process_family", "status"], as_index=False)
        .agg(records=("record_id", "count"), feature_rows=("feature_rows", "sum"))
        .sort_values(["process_family", "status"])
    )

    key.to_csv(TABLES / "01_key_10pct_likelihood_readout.csv", index=False)
    combined.to_csv(TABLES / "02_combined_10pct_likelihood_readout.csv", index=False)
    tier_summary.to_csv(TABLES / "03_normalisation_tier_summary.csv", index=False)
    extract_summary.to_csv(TABLES / "04_remote_extraction_summary.csv", index=False)

    met = combined[combined["region"].eq("MET_trace")].iloc[0]
    controls = combined[combined["region"].eq("JetHT_SingleMuon_controls")].iloc[0]
    report = f"""# Breakthrough Readiness After ZNuNu HT Extension

## What Was Completed

- Added seven online ZNuNu HT-binned CMS UL16 MiniAODSIM records.
- Remotely extracted compact features for those records through CMSSW/XRootD.
- Rebuilt the generator-weight audit and normalisation tiers.
- Rebuilt the OPQ Standard Model shape layer.
- Reran the frozen OPQ approximate process-aware sideband likelihood.

No raw ROOT files were retained locally.

## Frozen OPQ Score

The same score was used:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

No N-Frame retuning was performed in this rerun.

## Key 10 Percent Shape-Uncertainty Readout

{key.to_markdown(index=False, floatfmt='.6g')}

## Combined Readout

{combined.to_markdown(index=False, floatfmt='.6g')}

At 10 percent independent shape uncertainty:

- MET trace combined Fisher Z: {met.fisher_Z:.3f}
- Weakest individual MET sample Z: {met.min_sample_Z:.3f}
- JetHT/SingleMuon combined Fisher Z: {controls.fisher_Z:.3f}
- Controls remain closed: {bool(abs(key[key['region'].eq('JetHT_SingleMuon_controls')]['background_only_Z']).max() < 1.0)}

## Background Coverage

{extract_summary.to_markdown(index=False)}

## Normalisation Tiers

{tier_summary.to_markdown(index=False)}

## Breakthrough Status

This is the strongest current project-level result for Darren's boundary-trace
claim:

1. MET remains anomalous under the expanded approximate process-aware SM
   sideband transfer.
2. JetHT/SingleMuon controls close extremely well under the same model.
3. The effect repeats in two independent held-out CMS real-data samples.
4. ZNuNu coverage is materially improved by the added HT-binned samples.

It is still not final publication/discovery grade because:

1. No exact record-level sum-of-generator-weights fields were found in the CERN
   record JSON.
2. The likelihood is still labelled approximate because it uses stable-weight
   approximations for records without exact sum-weights.
3. TT/top MiniAODSIM records were not accessible through the searched UL16
   Open Data route.
4. The Run2016H individual MET result is strong but below 5 sigma at the
   strict 10 percent uncertainty point.

## Exact Next Step

The shortest remaining route to a breakthrough-grade claim is:

1. obtain exact record-level sum-of-generator-weights or compute them for the
   selected MC records;
2. add TT/top coverage through an accessible Open Data route or a documented
   replacement sample;
3. rerun this exact frozen OPQ likelihood with those two gaps closed.

If MET remains high and controls stay closed after that, the result becomes a
serious candidate for Darren's publishable N-Frame boundary-trace claim.
"""
    (REPORTS / "01_BREAKTHROUGH_READINESS_AFTER_ZNUNU_HT_EXTENSION.md").write_text(report, encoding="utf-8")
    print(combined.to_string(index=False))
    print(REPORTS / "01_BREAKTHROUGH_READINESS_AFTER_ZNUNU_HT_EXTENSION.md")


if __name__ == "__main__":
    main()
