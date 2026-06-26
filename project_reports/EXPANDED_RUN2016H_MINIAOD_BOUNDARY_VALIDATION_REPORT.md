# Expanded Run2016H MiniAOD Boundary Validation Report

Date: 2026-06-09

This validates the existing fitted N-Frame equation on expanded independent real Run2016H MiniAOD data. The equation was not refitted.

## Summary

| primary_dataset   |   events |   files |   runs |   mean_score |   median_score |
|:------------------|---------:|--------:|-------:|-------------:|---------------:|
| JetHT             |    64120 |       3 |      3 |    0.410358  |       0.326667 |
| MET               |    40283 |       3 |      3 |   -0.0133351 |      -0.175733 |
| SingleMuon        |    52572 |       2 |      2 |   -0.49028   |      -0.687864 |

## Top Tail Composition

| tail_label   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-------------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| top05        | JetHT             |       0.752962  |            0.408473 |           1.84336  |     5910 |
| top05        | MET               |       0.173908  |            0.25662  |           0.677684 |     1365 |
| top05        | SingleMuon        |       0.0731303 |            0.334907 |           0.21836  |      574 |
| top01        | JetHT             |       0.764968  |            0.408473 |           1.87275  |     1201 |
| top01        | MET               |       0.16879   |            0.25662  |           0.657741 |      265 |
| top01        | SingleMuon        |       0.066242  |            0.334907 |           0.197792 |      104 |
| top001       | JetHT             |       0.713376  |            0.408473 |           1.74645  |      112 |
| top001       | MET               |       0.216561  |            0.25662  |           0.843894 |       34 |
| top001       | SingleMuon        |       0.0700637 |            0.334907 |           0.209204 |       11 |

## Parameter Drivers

| tail_label   | parameter_family     |   top_mean |    rest_mean |   top_minus_rest |
|:-------------|:---------------------|-----------:|-------------:|-----------------:|
| top001       | P_displacement_proxy |   5.18836  | -0.00519438  |         5.19355  |
| top001       | P_multiplicity       |   2.10133  | -0.00210377  |         2.10344  |
| top001       | P_visible_energy     |   1.9323   | -0.00193454  |         1.93424  |
| top001       | P_reconstruction     |   1.84768  | -0.00184983  |         1.84953  |
| top001       | P_btag_structure     |   1.63027  | -0.00163217  |         1.63191  |
| top001       | P_missing            |   1.24195  | -0.00124339  |         1.24319  |
| top001       | P_compression        |  -0.601987 |  0.000602686 |        -0.60259  |
| top01        | P_displacement_proxy |   3.72123  | -0.0375942   |         3.75882  |
| top01        | P_multiplicity       |   1.64858  | -0.016655    |         1.66524  |
| top01        | P_visible_energy     |   1.49835  | -0.0151373   |         1.51348  |
| top01        | P_reconstruction     |   1.24961  | -0.0126244   |         1.26224  |
| top01        | P_btag_structure     |   1.22614  | -0.0123872   |         1.23852  |
| top01        | P_missing            |   0.486298 | -0.00491289  |         0.491211 |
| top01        | P_compression        |  -0.624122 |  0.00630528  |        -0.630427 |
| top05        | P_displacement_proxy |   2.63327  | -0.138598    |         2.77186  |
| top05        | P_multiplicity       |   1.33652  | -0.0703457   |         1.40687  |
| top05        | P_visible_energy     |   1.20605  | -0.0634785   |         1.26953  |
| top05        | P_btag_structure     |   0.882245 | -0.0464355   |         0.92868  |
| top05        | P_reconstruction     |   0.843594 | -0.0444012   |         0.887995 |
| top05        | P_missing            |   0.294124 | -0.0154807   |         0.309604 |
| top05        | P_compression        |  -0.621767 |  0.0327257   |        -0.654493 |

## File/Run/Lumi Concentration

| tail_label   |   top_file_fraction |   top_run_fraction |   top_lumi_bin_fraction |   events |
|:-------------|--------------------:|-------------------:|------------------------:|---------:|
| top05        |            0.322844 |           0.632947 |                0.305899 |     7849 |
| top01        |            0.318471 |           0.625478 |                0.301911 |     1570 |
| top001       |            0.299363 |           0.585987 |                0.273885 |      157 |

## Trigger/Filter Summary

| tail_label   | variable                                |   top_mean |   rest_mean |   top_minus_rest |
|:-------------|:----------------------------------------|-----------:|------------:|-----------------:|
| top05        | HLT_MET_paths_any                       |   0.243216 |   0.311596  |     -0.0683799   |
| top05        | HLT_HT_paths_any                        |   0.941266 |   0.484637  |      0.456629    |
| top05        | HLT_Mu_paths_any                        |   0.318639 |   0.540295  |     -0.221655    |
| top05        | HLT_Ele_paths_any                       |   0.120907 |   0.037532  |      0.0833751   |
| top05        | pass_HBHENoiseFilter                    |   0.998471 |   0.916004  |      0.0824672   |
| top05        | pass_HBHENoiseIsoFilter                 |   0.997962 |   0.991859  |      0.00610229  |
| top05        | pass_goodVertices                       |   0.999745 |   0.999142  |      0.000603525 |
| top05        | pass_EcalDeadCellTriggerPrimitiveFilter |   0.998471 |   0.999437  |     -0.000965575 |
| top05        | pass_BadPFMuonFilter                    |   0.99949  |   0.999866  |     -0.000375504 |
| top05        | pass_globalSuperTightHalo2016Filter     |   0.998216 |   0.987943  |      0.0102733   |
| top01        | HLT_MET_paths_any                       |   0.263694 |   0.308626  |     -0.0449316   |
| top01        | HLT_HT_paths_any                        |   0.953503 |   0.502963  |      0.45054     |
| top01        | HLT_Mu_paths_any                        |   0.33949  |   0.531128  |     -0.191638    |
| top01        | HLT_Ele_paths_any                       |   0.155414 |   0.0405521 |      0.114862    |
| top01        | pass_HBHENoiseFilter                    |   0.996178 |   0.919359  |      0.0768192   |
| top01        | pass_HBHENoiseIsoFilter                 |   0.996178 |   0.992124  |      0.00405454  |
| top01        | pass_goodVertices                       |   0.998726 |   0.999176  |     -0.000450231 |
| top01        | pass_EcalDeadCellTriggerPrimitiveFilter |   0.998726 |   0.999395  |     -0.000669014 |
| top01        | pass_BadPFMuonFilter                    |   1        |   0.999846  |      0.000154435 |
| top01        | pass_globalSuperTightHalo2016Filter     |   0.997452 |   0.988366  |      0.00908635  |
| top001       | HLT_MET_paths_any                       |   0.318471 |   0.308166  |      0.0103052   |
| top001       | HLT_HT_paths_any                        |   0.955414 |   0.507021  |      0.448393    |
| top001       | HLT_Mu_paths_any                        |   0.43949  |   0.529301  |     -0.089811    |
| top001       | HLT_Ele_paths_any                       |   0.242038 |   0.0415003 |      0.200538    |
| top001       | pass_HBHENoiseFilter                    |   0.987261 |   0.92006   |      0.0672009   |
| top001       | pass_HBHENoiseIsoFilter                 |   0.961783 |   0.992195  |     -0.0304113   |
| top001       | pass_goodVertices                       |   0.987261 |   0.999184  |     -0.0119226   |
| top001       | pass_EcalDeadCellTriggerPrimitiveFilter |   1        |   0.999388  |      0.000612175 |
| top001       | pass_BadPFMuonFilter                    |   1        |   0.999847  |      0.000153044 |
| top001       | pass_globalSuperTightHalo2016Filter     |   0.987261 |   0.988458  |     -0.00119681  |

Classification: **Partial validation**.