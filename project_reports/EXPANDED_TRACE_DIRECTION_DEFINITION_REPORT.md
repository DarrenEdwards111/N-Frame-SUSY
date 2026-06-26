# Expanded Trace Direction Definition Report

Date: 2026-06-09

The expanded trace direction uses SMS-T5Wg versus the expanded pooled SM background set. B_NF is frozen and not refitted.

## Component Means

| sample_id                            | process_label                             | classification   |   events |   P_missing |   P_visible_energy |   P_multiplicity |   P_btag_structure |   P_compression |
|:-------------------------------------|:------------------------------------------|:-----------------|---------:|------------:|-------------------:|-----------------:|-------------------:|----------------:|
| qcd_ht1000to1500_nanoaodsim_pilot    | QCD HT1000to1500                          | SM_background    |    33536 |  -0.0565054 |           3.43455  |       1.01553    |        0.000785741 |       -3.26877  |
| qcd_ht500to700_nanoaodsim_pilot      | QCD HT500to700                            | SM_background    |    50000 |  -0.351285  |           1.08476  |       0.560188   |       -0.0744423   |       -2.7944   |
| qcd_ht700to1000_nanoaodsim_pilot     | QCD HT700to1000                           | SM_background    |    50000 |  -0.238316  |           1.98106  |       0.682819   |       -0.0629075   |       -3.02389  |
| sms_t2tt_compressed_nanoaodsim_pilot | SMS-T2tt compressed stop mStop300 mLSP290 | signal           |    50000 |   4.86883   |           0.599504 |       0.00280818 |       -0.172005    |       -0.460847 |
| sms_t5wg_mg1500_mlsp1_signal         | SMS-T5Wg mGluino1500 mLSP1                | signal           |     5000 |   9.82685   |           5.28199  |       3.06615    |        0.353516    |       -1.56647  |
| susy_htoaa4b_m12_signal              | SUSY HToAA4B mA12                         | signal           |     2394 |  -0.51539   |          -0.344395 |      -0.339148   |        1.84995     |       -1.45505  |
| ttjets_nanoaodsim_pilot              | TTJets inclusive                          | SM_background    |    50000 |   0.125378  |           0.242506 |       0.981584   |        1.28624     |       -1.90616  |
| wjets_lnu_nanoaodsim_pilot           | WJetsToLNu                                | SM_background    |    50000 |  -0.323983  |          -0.682166 |      -0.782708   |       -0.330423    |        1.06597  |
| expanded_pooled_sm                   | Expanded pooled SM                        | SM_background    |   233536 |  -0.176869  |           1.05546  |       0.454538   |        0.175347    |       -1.89498  |

## New Versus Previous Direction

| direction                      | component        |   raw_contrast |   unit_weight |   signal_mean |   background_mean |   previous_unit_weight |
|:-------------------------------|:-----------------|---------------:|--------------:|--------------:|------------------:|-----------------------:|
| sms_t5wg_vs_expanded_pooled_sm | P_missing        |      10.0037   |     0.895125  |      9.82685  |         -0.176869 |              0.898724  |
| sms_t5wg_vs_expanded_pooled_sm | P_visible_energy |       4.22652  |     0.378186  |      5.28199  |          1.05546  |              0.379211  |
| sms_t5wg_vs_expanded_pooled_sm | P_multiplicity   |       2.61162  |     0.233685  |      3.06615  |          0.454538 |              0.203141  |
| sms_t5wg_vs_expanded_pooled_sm | P_btag_structure |       0.178169 |     0.0159424 |      0.353516 |          0.175347 |             -0.0234746 |
| sms_t5wg_vs_expanded_pooled_sm | P_compression    |       0.328507 |     0.0293945 |     -1.56647  |         -1.89498  |              0.0817084 |