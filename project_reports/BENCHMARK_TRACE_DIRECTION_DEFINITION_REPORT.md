# Benchmark Trace Direction Definition Report

Date: 2026-06-09

Simulation is used only to define benchmark contrast directions. The frozen real-data-fitted B_NF equation is not refitted.

## Component Means

| sample_id                        | process_label              | classification   |   events |   P_missing |   P_visible_energy |   P_multiplicity |   P_btag_structure |   P_compression |
|:---------------------------------|:---------------------------|:-----------------|---------:|------------:|-------------------:|-----------------:|-------------------:|----------------:|
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    |    50000 |   -0.238316 |           1.98106  |         0.682819 |         -0.0629075 |        -3.02389 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           |     5000 |    9.82685  |           5.28199  |         3.06615  |          0.353516  |        -1.56647 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           |     2394 |   -0.51539  |          -0.344395 |        -0.339148 |          1.84995   |        -1.45505 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    |    50000 |    0.125378 |           0.242506 |         0.981584 |          1.28624   |        -1.90616 |
| pooled_sm_benchmark              | Pooled TTJets + QCD        | SM_background    |   100000 |   -0.056469 |           1.11178  |         0.832202 |          0.611668  |        -2.46502 |

## Direction Weights

| direction                               | component        |   raw_contrast |   unit_weight |   signal_mean |   background_mean |
|:----------------------------------------|:-----------------|---------------:|--------------:|--------------:|------------------:|
| sms_vs_pooledSM                         | P_missing        |       9.88332  |     0.898724  |      9.82685  |        -0.056469  |
| sms_vs_pooledSM                         | P_visible_energy |       4.1702   |     0.379211  |      5.28199  |         1.11178   |
| sms_vs_pooledSM                         | P_multiplicity   |       2.23395  |     0.203141  |      3.06615  |         0.832202  |
| sms_vs_pooledSM                         | P_btag_structure |      -0.258152 |    -0.0234746 |      0.353516 |         0.611668  |
| sms_vs_pooledSM                         | P_compression    |       0.898551 |     0.0817084 |     -1.56647  |        -2.46502   |
| sms_vs_TTJets_nanoaodsim_pilot          | P_missing        |       9.70147  |     0.868262  |      9.82685  |         0.125378  |
| sms_vs_TTJets_nanoaodsim_pilot          | P_visible_energy |       5.03948  |     0.451023  |      5.28199  |         0.242506  |
| sms_vs_TTJets_nanoaodsim_pilot          | P_multiplicity   |       2.08457  |     0.186565  |      3.06615  |         0.981584  |
| sms_vs_TTJets_nanoaodsim_pilot          | P_btag_structure |      -0.932727 |    -0.0834772 |      0.353516 |         1.28624   |
| sms_vs_TTJets_nanoaodsim_pilot          | P_compression    |       0.339689 |     0.0304015 |     -1.56647  |        -1.90616   |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_missing        |      10.0652   |     0.918126  |      9.82685  |        -0.238316  |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_visible_energy |       3.30093  |     0.301105  |      5.28199  |         1.98106   |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_multiplicity   |       2.38333  |     0.217403  |      3.06615  |         0.682819  |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_btag_structure |       0.416423 |     0.0379854 |      0.353516 |        -0.0629075 |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_compression    |       1.45741  |     0.132943  |     -1.56647  |        -3.02389   |

P_displacement_proxy and P_reconstruction are kept as a separate real-data boundary axis because they are unavailable or reduced in the SMS benchmark features.