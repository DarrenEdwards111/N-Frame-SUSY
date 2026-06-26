# SM Background Mimicry Analysis Report

Date: 2026-06-09

## Parameter Summary

| sample_id                        | process_label              | classification   | parameter_family     |   mean_parameter |   median_parameter |   p95_parameter |
|:---------------------------------|:---------------------------|:-----------------|:---------------------|-----------------:|-------------------:|----------------:|
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_displacement_proxy |        1.02268   |          1.11323   |        3.42824  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_reconstruction     |        0.096392  |          0.0672918 |        1.19793  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_multiplicity       |        0.682819  |          0.617293  |        1.95773  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_btag_structure     |       -0.0629075 |         -0.25498   |        1.27313  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_visible_energy     |        1.98106   |          1.98992   |        2.97618  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_missing            |       -0.238316  |         -0.346444  |        0.78446  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_compression        |       -3.02389   |         -2.96663   |       -2.11153  |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_displacement_proxy |      nan         |        nan         |      nan        |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_reconstruction     |      nan         |        nan         |      nan        |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_multiplicity       |        3.06615   |          2.95854   |        5.05784  |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_btag_structure     |        0.353516  |         -0.403068  |        2.80349  |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_visible_energy     |        5.28199   |          5.04302   |        8.42895  |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_missing            |        9.82685   |          9.18189   |       19.8563   |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_compression        |       -1.56647   |         -1.48191   |       -0.712012 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_displacement_proxy |      nan         |        nan         |      nan        |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_reconstruction     |      nan         |        nan         |      nan        |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_multiplicity       |       -0.339148  |         -0.460182  |        0.75476  |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_btag_structure     |        1.84995   |          1.87937   |        4.16181  |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_visible_energy     |       -0.344395  |         -0.402422  |        0.331026 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_missing            |       -0.51539   |         -0.575097  |        0.136087 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_compression        |       -1.45505   |         -1.53088   |        0.347266 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_displacement_proxy |        1.38157   |          1.11323   |        3.42824  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_reconstruction     |        0.243012  |          0.212931  |        1.27075  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_multiplicity       |        0.981584  |          0.908086  |        2.36499  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_btag_structure     |        1.28624   |          1.27336   |        2.79508  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_visible_energy     |        0.242506  |          0.107774  |        1.27058  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_missing            |        0.125378  |         -0.126506  |        1.97671  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_compression        |       -1.90616   |         -1.89286   |       -0.64709  |

## SMS-T5Wg Versus SM Driver Contrast

| parameter_family     | signal_sample                | sm_background_sample             |   signal_mean |    sm_mean |   signal_minus_sm |
|:---------------------|:-----------------------------|:---------------------------------|--------------:|-----------:|------------------:|
| P_displacement_proxy | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |    nan        |  1.02268   |        nan        |
| P_reconstruction     | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |    nan        |  0.096392  |        nan        |
| P_multiplicity       | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |      3.06615  |  0.682819  |          2.38333  |
| P_btag_structure     | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |      0.353516 | -0.0629075 |          0.416423 |
| P_visible_energy     | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |      5.28199  |  1.98106   |          3.30093  |
| P_missing            | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |      9.82685  | -0.238316  |         10.0652   |
| P_compression        | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |     -1.56647  | -3.02389   |          1.45741  |
| P_displacement_proxy | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |    nan        |  1.38157   |        nan        |
| P_reconstruction     | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |    nan        |  0.243012  |        nan        |
| P_multiplicity       | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |      3.06615  |  0.981584  |          2.08457  |
| P_btag_structure     | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |      0.353516 |  1.28624   |         -0.932727 |
| P_visible_energy     | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |      5.28199  |  0.242506  |          5.03948  |
| P_missing            | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |      9.82685  |  0.125378  |          9.70147  |
| P_compression        | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |     -1.56647  | -1.90616   |          0.339689 |

## Interpretation

SMS-T5Wg remains higher than the tested SM backgrounds in q95 high-boundary occupancy. This strengthens the SUSY-relevance interpretation at benchmark level, while still not making a discovery claim.