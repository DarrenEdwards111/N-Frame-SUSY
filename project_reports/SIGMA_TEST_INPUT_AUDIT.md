# Sigma Test Input Audit

Date: 2026-06-09

## Event-Level Files

- SUSY benchmark events: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\susy_relevance_benchmark_features\susy_sm_benchmark_events_with_BNF.csv` exists=True
- SM background events: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\sm_background_pilot_features\sm_background_events_with_BNF.csv` exists=True
- Real-data threshold table: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\bnf_thresholds_real_and_sm.csv` exists=True

## Input Inventory

| sample_id                        | process_label              | classification   |   event_level_rows | score_columns                                           | component_columns_available                                                                                                  | component_mode                                                                                                         |
|:---------------------------------|:---------------------------|:-----------------|-------------------:|:--------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    |              50000 | B_NF_fitted_frozen_raw;B_NF_fitted_frozen_z_real_scaled | B_P_displacement_proxy;B_P_reconstruction;B_P_multiplicity;B_P_btag_structure;B_P_visible_energy;B_P_missing;B_P_compression | reduced component score; P_reconstruction lacks packed_candidate_count                                                 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           |               5000 | B_NF_fitted_frozen_raw;B_NF_fitted_frozen_z_real_scaled | B_P_multiplicity;B_P_btag_structure;B_P_visible_energy;B_P_missing;B_P_compression                                           | reduced component score; missing P_displacement_proxy; P_reconstruction; P_reconstruction lacks packed_candidate_count |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           |               2394 | B_NF_fitted_frozen_raw;B_NF_fitted_frozen_z_real_scaled | B_P_multiplicity;B_P_btag_structure;B_P_visible_energy;B_P_missing;B_P_compression                                           | reduced component score; missing P_displacement_proxy; P_reconstruction; P_reconstruction lacks packed_candidate_count |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    |              50000 | B_NF_fitted_frozen_raw;B_NF_fitted_frozen_z_real_scaled | B_P_displacement_proxy;B_P_reconstruction;B_P_multiplicity;B_P_btag_structure;B_P_visible_energy;B_P_missing;B_P_compression | reduced component score; P_reconstruction lacks packed_candidate_count                                                 |

## Thresholds

| threshold_source                    | threshold   |   real_quantile |   value |
|:------------------------------------|:------------|----------------:|--------:|
| Run2016G_standard_quality_real_data | q90         |           0.9   | 1.42074 |
| Run2016G_standard_quality_real_data | q95         |           0.95  | 1.968   |
| Run2016G_standard_quality_real_data | q99         |           0.99  | 3.0529  |
| Run2016G_standard_quality_real_data | q999        |           0.999 | 4.46877 |

## Missing Data Issues

The tests use the frozen real-data-fitted B_NF score. They are reduced-component benchmark tests when a sample lacks one or more fitted components; missing components are not silently set to zero.