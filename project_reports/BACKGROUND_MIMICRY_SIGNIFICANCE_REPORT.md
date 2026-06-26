# Background Mimicry Significance Report

Date: 2026-06-09

## Component Tests

| threshold   | background_sample                | parameter_family   |   sms_high_tail_mean |   background_high_tail_mean |   sms_minus_background |   welch_t_one_sided_greater |   p_one_sided_sms_greater |   z_equivalent |
|:------------|:---------------------------------|:-------------------|---------------------:|----------------------------:|-----------------------:|----------------------------:|--------------------------:|---------------:|
| q95         | qcd_ht700to1000_nanoaodsim_pilot | P_missing          |            16.0434   |                  -0.0812332 |              16.1246   |                    93.4969  |              0            |      inf       |
| q95         | qcd_ht700to1000_nanoaodsim_pilot | P_visible_energy   |             6.20937  |                   2.03912   |               4.17025  |                    63.0268  |              0            |      inf       |
| q95         | qcd_ht700to1000_nanoaodsim_pilot | P_multiplicity     |             3.93228  |                   1.29545   |               2.63683  |                    58.2657  |              0            |      inf       |
| q95         | qcd_ht700to1000_nanoaodsim_pilot | P_btag_structure   |             0.989996 |                   0.851955  |               0.138042 |                     2.19272 |              0.0142357    |        2.19073 |
| q95         | qcd_ht700to1000_nanoaodsim_pilot | P_compression      |            -1.20319  |                  -2.94797   |               1.74478  |                    75.7528  |              0            |      inf       |
| q95         | ttjets_nanoaodsim_pilot          | P_missing          |            16.0434   |                   0.466838  |              15.5765   |                    89.5827  |              0            |      inf       |
| q95         | ttjets_nanoaodsim_pilot          | P_visible_energy   |             6.20937  |                   1.1271    |               5.08227  |                    74.8149  |              0            |      inf       |
| q95         | ttjets_nanoaodsim_pilot          | P_multiplicity     |             3.93228  |                   1.99553   |               1.93675  |                    45.1128  |              1.42251e-278 |       35.6447  |
| q95         | ttjets_nanoaodsim_pilot          | P_btag_structure   |             0.989996 |                   2.29026   |              -1.30026  |                   -22.2101  |              1            |     -inf       |
| q95         | ttjets_nanoaodsim_pilot          | P_compression      |            -1.20319  |                  -2.3267    |               1.12351  |                    51.7895  |              0            |      inf       |
| q99         | qcd_ht700to1000_nanoaodsim_pilot | P_missing          |            24.2688   |                   0.104949  |              24.1639   |                    19.5263  |              3.29449e-17  |        8.35418 |
| q99         | qcd_ht700to1000_nanoaodsim_pilot | P_visible_energy   |             8.21294  |                   2.19852   |               6.01442  |                    18.7277  |              1.18822e-17  |        8.47374 |
| q99         | qcd_ht700to1000_nanoaodsim_pilot | P_multiplicity     |             5.35364  |                   1.57419   |               3.77945  |                    10.8364  |              1.82813e-12  |        6.94987 |
| q99         | qcd_ht700to1000_nanoaodsim_pilot | P_btag_structure   |             2.04682  |                   1.50827   |               0.538551 |                     1.15422 |              0.128445     |        1.13377 |
| q99         | qcd_ht700to1000_nanoaodsim_pilot | P_compression      |            -1.0767   |                  -2.95415   |               1.87745  |                    17.6525  |              1.96755e-30  |       11.4053  |
| q99         | ttjets_nanoaodsim_pilot          | P_missing          |            24.2688   |                   0.763423  |              23.5054   |                    18.9591  |              5.62972e-17  |        8.29069 |
| q99         | ttjets_nanoaodsim_pilot          | P_visible_energy   |             8.21294  |                   1.97816   |               6.23478  |                    18.0229  |              2.56237e-20  |        9.16136 |
| q99         | ttjets_nanoaodsim_pilot          | P_multiplicity     |             5.35364  |                   2.54773   |               2.80591  |                     8.22399 |              2.24596e-09  |        5.86498 |
| q99         | ttjets_nanoaodsim_pilot          | P_btag_structure   |             2.04682  |                   2.63922   |              -0.592404 |                    -1.32499 |              0.901941     |       -1.29269 |
| q99         | ttjets_nanoaodsim_pilot          | P_compression      |            -1.0767   |                  -2.55856   |               1.48185  |                    17.0987  |              2.80073e-33  |       11.9623  |

## Profile Distances

|   euclidean_distance |   cosine_similarity |   correlation | components_compared                                                                | threshold   | signal_sample                | background_sample                |   signal_tail_events |   background_tail_events |
|---------------------:|--------------------:|--------------:|:-----------------------------------------------------------------------------------|:------------|:-----------------------------|:---------------------------------|---------------------:|-------------------------:|
|              16.9532 |            0.30119  |      0.286364 | B_P_btag_structure;B_P_compression;B_P_missing;B_P_multiplicity;B_P_visible_energy | q95         | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                  989 |                     1223 |
|              16.588  |            0.385145 |      0.181327 | B_P_btag_structure;B_P_compression;B_P_missing;B_P_multiplicity;B_P_visible_energy | q95         | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                  989 |                     2454 |
|              25.2619 |            0.313822 |      0.201081 | B_P_btag_structure;B_P_compression;B_P_missing;B_P_multiplicity;B_P_visible_energy | q99         | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                   26 |                       61 |
|              24.5315 |            0.434967 |      0.174416 | B_P_btag_structure;B_P_compression;B_P_missing;B_P_multiplicity;B_P_visible_energy | q99         | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                   26 |                      153 |