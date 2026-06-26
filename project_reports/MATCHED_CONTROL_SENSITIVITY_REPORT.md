# Matched Control Sensitivity Report

Date: 2026-06-08

Sensitivity checks compare quality subsets, tail thresholds, score types, and exclusions of the strongest suspect run/source file.

## Matching Quality

| quality_subset         | boundary_score_type            | tail_definition   |   matched_pairs |   matched_cases |   avg_controls_per_case |   same_file_fraction |   same_run_fraction |   same_trigger_fraction |   mean_vertex_difference |   mean_packed_candidate_difference |
|:-----------------------|:-------------------------------|:------------------|----------------:|----------------:|------------------------:|---------------------:|--------------------:|------------------------:|-------------------------:|-----------------------------------:|
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             |           32580 |            6516 |                       5 |             0.999908 |            0.956599 |                0.993769 |                 0.126489 |                            32.6547 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             |           32580 |            6516 |                       5 |             0.999754 |            0.963904 |                0.986556 |                 0.295795 |                            49.3877 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            |            3025 |             605 |                       5 |             1        |            0.95438  |                0.991736 |                 0.13686  |                            41.8592 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             |           30245 |            6049 |                       5 |             0.999901 |            0.958175 |                0.993156 |                 0.130402 |                            33.584  |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             |          151215 |           30243 |                       5 |             0.999934 |            0.959105 |                0.993777 |                 0.130159 |                            31.5609 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            |            3025 |             605 |                       5 |             1        |            0.967603 |                0.984132 |                 0.227438 |                            46.5101 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             |           30245 |            6049 |                       5 |             0.999735 |            0.962076 |                0.98251  |                 0.275384 |                            47.3393 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             |          151215 |           30243 |                       5 |             0.999749 |            0.960183 |                0.989049 |                 0.2494   |                            42.3976 |

## Key Feature Sensitivity

| quality_subset         | boundary_score_type            | tail_definition   | feature                     |   paired_mean_difference |   standardised_paired_mean_difference |   cases |
|:-----------------------|:-------------------------------|:------------------|:----------------------------|-------------------------:|--------------------------------------:|--------:|
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | HT                          |             338.92       |                            0.732761   |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | MET_pt                      |              40.8732     |                            0.503759   |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | N_btags_medium              |               1.22676    |                            1.22097    |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | N_jets_30                   |               2.14659    |                            1.16007    |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | R_btag_structure            |               1.51683    |                            1.31879    |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | R_compression_proxy         |              -0.020023   |                           -0.0257199  |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | R_displacement_proxy        |               2.67342    |                            1.87495    |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | R_missing                   |               0.548914   |                            0.765198   |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | R_reconstruction_complexity |               1.42333    |                            2.38058    |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | R_visible_energy            |               0.480366   |                            0.799369   |    6516 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01             | secondary_vertex_count      |               4.62514    |                            1.87495    |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | HT                          |             176.782      |                            0.375077   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | MET_pt                      |               6.52514    |                            0.0545105  |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | N_btags_medium              |               0.638735   |                            0.574008   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | N_jets_30                   |               0.912953   |                            0.385005   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | R_btag_structure            |               0.645177   |                            0.509409   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | R_compression_proxy         |              -0.00831276 |                           -0.0051535  |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | R_displacement_proxy        |               1.64462    |                            0.812629   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | R_missing                   |              -0.433622   |                           -0.311763   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | R_reconstruction_complexity |               0.738401   |                            0.833755   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | R_visible_energy            |              -0.378727   |                           -0.300784   |    6516 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01             | secondary_vertex_count      |               2.84527    |                            0.812629   |    6516 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | HT                          |             548.766      |                            0.862443   |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | MET_pt                      |              55.1939     |                            0.535252   |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | N_btags_medium              |               1.55372    |                            1.31311    |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | N_jets_30                   |               2.8162     |                            1.39225    |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | R_btag_structure            |               1.93012    |                            1.43913    |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | R_compression_proxy         |              -0.0585695  |                           -0.0720763  |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | R_displacement_proxy        |               3.88868    |                            2.18029    |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | R_missing                   |               0.559785   |                            0.733302   |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | R_reconstruction_complexity |               2.01802    |                            2.96381    |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | R_visible_energy            |               0.516796   |                            0.858924   |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001            | secondary_vertex_count      |               6.7276     |                            2.18029    |     605 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | HT                          |             332.116      |                            0.719552   |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | MET_pt                      |              40.8468     |                            0.499399   |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | N_btags_medium              |               1.20946    |                            1.1937     |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | N_jets_30                   |               2.05174    |                            1.1222     |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | R_btag_structure            |               1.49217    |                            1.28846    |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | R_compression_proxy         |               0.026335   |                            0.0343393  |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | R_displacement_proxy        |               2.638      |                            1.82984    |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | R_missing                   |               0.525737   |                            0.737895   |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | R_reconstruction_complexity |               1.40366    |                            2.38631    |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | R_visible_energy            |               0.413175   |                            0.748647   |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01             | secondary_vertex_count      |               4.56386    |                            1.82984    |    6049 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | HT                          |             223.427      |                            0.628032   |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | MET_pt                      |              31.5428     |                            0.470109   |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | N_btags_medium              |               0.904996   |                            1.00537    |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | N_jets_30                   |               1.61311    |                            0.974475   |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | R_btag_structure            |               1.12343    |                            1.09074    |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | R_compression_proxy         |               0.0511913  |                            0.0668893  |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | R_displacement_proxy        |               1.89857    |                            1.50433    |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | R_missing                   |               0.490651   |                            0.701684   |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | R_reconstruction_complexity |               1.02115    |                            1.8931     |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | R_visible_energy            |               0.365328   |                            0.685956   |   30243 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05             | secondary_vertex_count      |               3.28461    |                            1.50433    |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | HT                          |             277.965      |                            0.398554   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | MET_pt                      |              -0.378399   |                           -0.00572814 |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | N_btags_medium              |               0.483967   |                            0.413819   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | N_jets_30                   |               1.12694    |                            0.366204   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | R_btag_structure            |               0.508147   |                            0.380454   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | R_compression_proxy         |               0.576829   |                            0.320671   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | R_displacement_proxy        |               2.42921    |                            0.852765   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | R_missing                   |              -0.369542   |                           -0.305687   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | R_reconstruction_complexity |               0.856606   |                            0.719644   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | R_visible_energy            |              -0.897179   |                           -0.557563   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001            | secondary_vertex_count      |               4.20264    |                            0.852765   |     605 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | HT                          |             181.47       |                            0.378151   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | MET_pt                      |               0.987209   |                            0.0128314  |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | N_btags_medium              |               0.557084   |                            0.503535   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | N_jets_30                   |               0.845065   |                            0.355141   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | R_btag_structure            |               0.54591    |                            0.427564   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | R_compression_proxy         |               0.0029936  |                            0.00178578 |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | R_displacement_proxy        |               1.5397     |                            0.754684   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | R_missing                   |              -0.482245   |                           -0.365224   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | R_reconstruction_complexity |               0.695253   |                            0.772812   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | R_visible_energy            |              -0.433261   |                           -0.345862   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01             | secondary_vertex_count      |               2.66375    |                            0.754684   |    6049 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | HT                          |             134.185      |                            0.365671   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | MET_pt                      |               1.61711    |                            0.0248598  |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | N_btags_medium              |               0.50409    |                            0.52618    |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | N_jets_30                   |               0.800873   |                            0.391151   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | R_btag_structure            |               0.475245   |                            0.408831   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | R_compression_proxy         |              -0.32959    |                           -0.241578   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | R_displacement_proxy        |               1.15623    |                            0.717109   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | R_missing                   |              -0.456115   |                           -0.363585   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | R_reconstruction_complexity |               0.579254   |                            0.8098     |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | R_visible_energy            |              -0.0969753  |                           -0.109098   |   30243 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05             | secondary_vertex_count      |               2.00034    |                            0.717109   |   30243 |

## Exclusion Sensitivity

| subset                 | exclusion                                              | score                        | tail   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-----------------------|:-------------------------------------------------------|:-----------------------------|:-------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top05  | MET               |       0.563238  |           0.2873    |           1.96045  |    17034 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top05  | JetHT             |       0.342228  |           0.150256  |           2.27763  |    10350 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top05  | SingleMuon        |       0.0945343 |           0.562444  |           0.168078 |     2859 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top01  | MET               |       0.559431  |           0.2873    |           1.94721  |     3384 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top01  | JetHT             |       0.366507  |           0.150256  |           2.43921  |     2217 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top01  | SingleMuon        |       0.0740618 |           0.562444  |           0.131679 |      448 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top001 | MET               |       0.540496  |           0.2873    |           1.8813   |      327 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top001 | JetHT             |       0.396694  |           0.150256  |           2.64012  |      240 |
| standard_quality_clean | none                                                   | mc_B_boundary_hand_defined_z | top001 | SingleMuon        |       0.0628099 |           0.562444  |           0.111673 |       38 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top05  | MET               |       0.697047  |           0.304001  |           2.29291  |    19923 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top05  | JetHT             |       0.182982  |           0.100859  |           1.81424  |     5230 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top05  | SingleMuon        |       0.119971  |           0.59514   |           0.201584 |     3429 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top01  | MET               |       0.728004  |           0.304001  |           2.39474  |     4162 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top01  | JetHT             |       0.171069  |           0.100859  |           1.69612  |      978 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top01  | SingleMuon        |       0.100927  |           0.59514   |           0.169585 |      577 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top001 | MET               |       0.769231  |           0.304001  |           2.53036  |      440 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top001 | JetHT             |       0.134615  |           0.100859  |           1.33469  |       77 |
| standard_quality_clean | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top001 | SingleMuon        |       0.0961538 |           0.59514   |           0.161565 |       55 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top05  | MET               |       0.627194  |           0.29558   |           2.12191  |    18437 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top05  | JetHT             |       0.267043  |           0.125766  |           2.12333  |     7850 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top05  | SingleMuon        |       0.105763  |           0.578654  |           0.182774 |     3109 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top01  | MET               |       0.635034  |           0.29558   |           2.14844  |     3734 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top01  | JetHT             |       0.278571  |           0.125766  |           2.21499  |     1638 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top01  | SingleMuon        |       0.0863946 |           0.578654  |           0.149303 |      508 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top001 | MET               |       0.653061  |           0.29558   |           2.20943  |      384 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top001 | JetHT             |       0.265306  |           0.125766  |           2.10952  |      156 |
| standard_quality_clean | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top001 | SingleMuon        |       0.0816327 |           0.578654  |           0.141073 |       48 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top05  | MET               |       0.562922  |           0.336067  |           1.67503  |    18340 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top05  | JetHT             |       0.341037  |           0.141711  |           2.40656  |    11111 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top05  | SingleMuon        |       0.0960405 |           0.522222  |           0.183907 |     3129 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top01  | MET               |       0.555709  |           0.336067  |           1.65357  |     3621 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top01  | JetHT             |       0.368324  |           0.141711  |           2.59911  |     2400 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top01  | SingleMuon        |       0.0759669 |           0.522222  |           0.145469 |      495 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top001 | MET               |       0.539877  |           0.336067  |           1.60646  |      352 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top001 | JetHT             |       0.391104  |           0.141711  |           2.75987  |      255 |
| relaxed_quality_clean  | none                                                   | mc_B_boundary_hand_defined_z | top001 | SingleMuon        |       0.0690184 |           0.522222  |           0.132163 |       45 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top05  | MET               |       0.692739  |           0.354611  |           1.95352  |    21389 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top05  | JetHT             |       0.185613  |           0.0943499 |           1.96729  |     5731 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top05  | SingleMuon        |       0.121648  |           0.551039  |           0.220761 |     3756 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top01  | MET               |       0.72296   |           0.354611  |           2.03874  |     4465 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top01  | JetHT             |       0.17649   |           0.0943499 |           1.87059  |     1090 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top01  | SingleMuon        |       0.100551  |           0.551039  |           0.182474 |      621 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top001 | MET               |       0.76699   |           0.354611  |           2.1629   |      474 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top001 | JetHT             |       0.135922  |           0.0943499 |           1.44062  |       84 |
| relaxed_quality_clean  | exclude_run_280007                                     | mc_B_boundary_hand_defined_z | top001 | SingleMuon        |       0.0970874 |           0.551039  |           0.17619  |       60 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top05  | MET               |       0.625974  |           0.345292  |           1.81288  |    19849 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top05  | JetHT             |       0.265414  |           0.118152  |           2.24638  |     8416 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top05  | SingleMuon        |       0.108613  |           0.536557  |           0.202425 |     3444 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top01  | MET               |       0.634342  |           0.345292  |           1.83712  |     4023 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top01  | JetHT             |       0.277673  |           0.118152  |           2.35014  |     1761 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top01  | SingleMuon        |       0.0879849 |           0.536557  |           0.163981 |      558 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top001 | MET               |       0.653543  |           0.345292  |           1.89273  |      415 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top001 | JetHT             |       0.266142  |           0.118152  |           2.25255  |      169 |
| relaxed_quality_clean  | exclude_file_35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | mc_B_boundary_hand_defined_z | top001 | SingleMuon        |       0.080315  |           0.536557  |           0.149686 |       51 |