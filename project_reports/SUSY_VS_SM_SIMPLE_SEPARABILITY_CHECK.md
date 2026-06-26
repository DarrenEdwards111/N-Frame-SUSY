# SUSY Versus SM Simple Separability Check

Date: 2026-06-09

## AUC Checks

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

## Caution

This is a descriptive benchmark separability check using the frozen B_NF score and components. It is not a discovery classifier and no equation was refitted on simulation.