# Boundary Stress To SUSY Relevance With SM Backgrounds

Date: 2026-06-09

## Frozen Equation

The real-data-fitted B_NF equation was frozen. It was not refitted on SUSY or SM simulation.

## SUSY Benchmarks And SM Backgrounds

| sample_id                        | process_label              | classification   | threshold   |   threshold_value |   events |   mean_BNF |   median_BNF |   tail_fraction |   ci_low |   ci_high |
|:---------------------------------|:---------------------------|:-----------------|:------------|------------------:|---------:|-----------:|-------------:|----------------:|---------:|----------:|
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | q95         |             1.968 |     5000 |  1.6124    |    1.57143   |         0.1978  | 0.186095 | 0.208905  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | q95         |             1.968 |    50000 |  0.875909  |    0.830251  |         0.04908 | 0.047199 | 0.050781  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | q95         |             1.968 |    50000 |  0.630491  |    0.55262   |         0.02446 | 0.02324  | 0.0257905 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | q95         |             1.968 |     2394 |  0.0390909 |    0.0403913 |         0       | 0        | 0         |

## q95 Ratios

| threshold   | signal_sample                | sm_background_sample             |   signal_tail_fraction |   sm_tail_fraction |   tail_ratio_signal_over_sm |   signal_minus_sm |
|:------------|:-----------------------------|:---------------------------------|-----------------------:|-------------------:|----------------------------:|------------------:|
| q95         | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                 0.1978 |            0.02446 |                     8.08667 |           0.17334 |
| q95         | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                 0.1978 |            0.04908 |                     4.03015 |           0.14872 |
| q95         | susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot |                 0      |            0.02446 |                     0       |          -0.02446 |
| q95         | susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          |                 0      |            0.04908 |                     0       |          -0.04908 |

## Simple Separability

| signal_sample                | sm_background_sample             | feature                |   auc_signal_vs_sm |
|:-----------------------------|:---------------------------------|:-----------------------|-------------------:|
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_NF_fitted_frozen_raw |          0.909178  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_P_missing            |          0.993871  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_P_visible_energy     |          0.987048  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_P_multiplicity       |          0.976099  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_P_btag_structure     |          0.35922   |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_P_reconstruction     |        nan         |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | B_P_displacement_proxy |        nan         |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_NF_fitted_frozen_raw |          0.839075  |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_P_missing            |          0.985792  |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_P_visible_energy     |          0.99839   |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_P_multiplicity       |          0.950298  |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_P_btag_structure     |          0.21345   |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_P_reconstruction     |        nan         |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | B_P_displacement_proxy |        nan         |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_NF_fitted_frozen_raw |          0.166663  |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_P_missing            |          0.345729  |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_P_visible_energy     |          0.0062604 |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_P_multiplicity       |          0.116171  |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_P_btag_structure     |          0.754447  |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_P_reconstruction     |        nan         |
| susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot | B_P_displacement_proxy |        nan         |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_NF_fitted_frozen_raw |          0.0954497 |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_P_missing            |          0.261814  |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_P_visible_energy     |          0.117356  |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_P_multiplicity       |          0.0849008 |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_P_btag_structure     |          0.594252  |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_P_reconstruction     |        nan         |
| susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          | B_P_displacement_proxy |        nan         |

## Interpretation

SMS-T5Wg remains higher than the tested SM backgrounds in q95 high-boundary occupancy. This strengthens the SUSY-relevance interpretation at benchmark level, while still not making a discovery claim. HToAA4B remains low in this pilot. The NanoAODSIM route is partial because packed_candidate_count is unavailable; MiniAODSIM would be needed for the fullest reconstruction component.

## Remaining Missing Work

Add more SUSY topologies, more SM backgrounds, full MiniAOD variables where practical, published SUSY signal-region overlap, and manual/event-display inspection.