# Expanded Background Mimicry Report

Date: 2026-06-09

## q95 Driver Summary

| sample_id                            | process_label                             | classification   |   q95_tail_events |   P_missing |   P_visible_energy |   P_multiplicity |   P_btag_structure |   P_displacement_proxy |   P_reconstruction |   P_compression |
|:-------------------------------------|:------------------------------------------|:-----------------|------------------:|------------:|-------------------:|-----------------:|-------------------:|-----------------------:|-------------------:|----------------:|
| qcd_ht1000to1500_nanoaodsim_pilot    | QCD HT1000to1500                          | SM_background    |              2591 |   0.09612   |           3.42121  |          1.62777 |           0.704216 |                4.1183  |           1.38135  |       -3.18287  |
| qcd_ht500to700_nanoaodsim_pilot      | QCD HT500to700                            | SM_background    |               446 |  -0.233741  |           1.13801  |          1.15503 |           1.04565  |                4.32794 |           1.53428  |       -2.73861  |
| qcd_ht700to1000_nanoaodsim_pilot     | QCD HT700to1000                           | SM_background    |              1223 |  -0.0812332 |           2.03912  |          1.29545 |           0.851955 |                4.33178 |           1.51232  |       -2.94797  |
| sms_t2tt_compressed_nanoaodsim_pilot | SMS-T2tt compressed stop mStop300 mLSP290 | signal           |               685 |  12.239     |           2.5849   |          1.03422 |           0.358764 |                3.00128 |           0.979874 |       -0.721418 |
| sms_t5wg_mg1500_mlsp1_signal         | SMS-T5Wg mGluino1500 mLSP1                | signal           |               989 |  16.0434    |           6.20937  |          3.93228 |           0.989996 |              nan       |         nan        |       -1.20319  |
| ttjets_nanoaodsim_pilot              | TTJets inclusive                          | SM_background    |              2454 |   0.466838  |           1.1271   |          1.99553 |           2.29026  |                3.8842  |           1.3124   |       -2.3267   |
| wjets_lnu_nanoaodsim_pilot           | WJetsToLNu                                | SM_background    |                 1 |   0.217557  |          -0.785559 |         -1.1304  |          -0.403068 |                5.74325 |           2.11872  |        3.22721  |

## SMS Driver Distances

| comparison                                       | other_classification   |   euclidean_distance |   cosine_similarity | components_compared                                                      |
|:-------------------------------------------------|:-----------------------|---------------------:|--------------------:|:-------------------------------------------------------------------------|
| SMS-T5Wg vs qcd_ht1000to1500_nanoaodsim_pilot    | SM_background          |             16.4742  |            0.380684 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs qcd_ht500to700_nanoaodsim_pilot      | SM_background          |             17.3418  |            0.204879 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs qcd_ht700to1000_nanoaodsim_pilot     | SM_background          |             16.9532  |            0.30119  | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs sms_t2tt_compressed_nanoaodsim_pilot | signal                 |              6.05307 |            0.977019 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs ttjets_nanoaodsim_pilot              | SM_background          |             16.588   |            0.385145 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs wjets_lnu_nanoaodsim_pilot           | SM_background          |             18.6168  |           -0.161361 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |