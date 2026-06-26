# Benchmark Coverage And Gaps Audit

Date: 2026-06-09

## Existing Reports

| report                                                   | exists   |   size_bytes |
|:---------------------------------------------------------|:---------|-------------:|
| FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md | True     |        44583 |
| SUSY_VS_SM_SPECIFICITY_TEST_REPORT.md                    | True     |        12463 |
| SM_BACKGROUND_MIMICRY_ANALYSIS_REPORT.md                 | True     |         7618 |
| REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md                   | True     |        10252 |
| REAL_TRACE_CANDIDATE_SANITY_CHECK_SYNTHESIS.md           | True     |         6751 |

## Current Benchmark Coverage

| sample_id                        | process_label              | classification   | data_tier   |   events | component_mode    | available_components                                                                                           | missing_components                    |   mean_BNF |   q95_tail_fraction |
|:---------------------------------|:---------------------------|:-----------------|:------------|---------:|:------------------|:---------------------------------------------------------------------------------------------------------------|:--------------------------------------|-----------:|--------------------:|
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | NANOAODSIM  |    50000 | full-component    | P_displacement_proxy;P_reconstruction;P_multiplicity;P_btag_structure;P_visible_energy;P_missing;P_compression |                                       |  0.630491  |             0.02446 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | nan         |     5000 | reduced-component | P_multiplicity;P_btag_structure;P_visible_energy;P_missing;P_compression                                       | P_displacement_proxy;P_reconstruction |  1.6124    |             0.1978  |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | nan         |     2394 | reduced-component | P_multiplicity;P_btag_structure;P_visible_energy;P_missing;P_compression                                       | P_displacement_proxy;P_reconstruction |  0.0390909 |             0       |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | NANOAODSIM  |    50000 | full-component    | P_displacement_proxy;P_reconstruction;P_multiplicity;P_btag_structure;P_visible_energy;P_missing;P_compression |                                       |  0.875909  |             0.04908 |

## Main Weaknesses

| gap                                      | impact                                                                                                   |
|:-----------------------------------------|:---------------------------------------------------------------------------------------------------------|
| SM backgrounds limited to TTJets and QCD | Specificity may not hold against W/Z/DY/single-top/diboson.                                              |
| Reduced-component feature alignment      | NanoAODSIM lacks packed candidates; SUSY benchmark features lack displacement/reconstruction components. |
| Limited SUSY topology coverage           | Only SMS-T5Wg and HToAA4B have been scored before expansion.                                             |
| No published signal-region overlap       | Cannot yet connect candidate events to published CMS SUSY regions.                                       |