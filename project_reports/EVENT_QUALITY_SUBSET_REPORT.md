# Event Quality Subset Report

Date: 2026-06-08

This report defines real-data-only quality subsets for matched-control analysis.

## Subset Boundary Summary

| subset                 | score                                 |   events |         mean |     median |      p95 |     p99 |    p999 |
|:-----------------------|:--------------------------------------|---------:|-------------:|-----------:|---------:|--------:|--------:|
| all_events             | B_boundary_hand_defined_z             |   665902 | -3.82426e-17 | -0.15668   | 1.81964  | 2.72548 | 3.89235 |
| all_events             | real_only_unsupervised_boundary_score |   665902 | -2.52675e-17 | -0.260232  | 1.93025  | 3.55546 | 5.83941 |
| standard_quality_clean | B_boundary_hand_defined_z             |   604860 |  0.0530553   | -0.0983681 | 1.8745   | 2.76799 | 3.89327 |
| standard_quality_clean | real_only_unsupervised_boundary_score |   604860 | -0.0357684   | -0.29271   | 1.88215  | 3.42119 | 5.66218 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             |   651585 |  0.0143735   | -0.140823  | 1.82961  | 2.72913 | 3.85775 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score |   651585 | -0.0337247   | -0.277739  | 1.85604  | 3.4322  | 5.62461 |
| top_quality_failures   | B_boundary_hand_defined_z             |    61042 | -0.525721    | -0.567441  | 0.768423 | 1.42272 | 3.70535 |
| top_quality_failures   | real_only_unsupervised_boundary_score |    61042 |  0.354426    | -0.0686    | 2.42428  | 4.34033 | 7.10852 |

## Filters Removing Top-Boundary Events

| score                                 | tail   | filter                                  |   tail_events |   failed_in_tail |   failed_fraction_in_tail |   failed_fraction_all |
|:--------------------------------------|:-------|:----------------------------------------|--------------:|-----------------:|--------------------------:|----------------------:|
| real_only_unsupervised_boundary_score | top001 | pass_goodVertices                       |           666 |               92 |               0.138138    |           0.0206727   |
| real_only_unsupervised_boundary_score | top01  | pass_goodVertices                       |          6660 |              823 |               0.123574    |           0.0206727   |
| real_only_unsupervised_boundary_score | top01  | pass_HBHENoiseFilter                    |          6660 |              721 |               0.108258    |           0.0547183   |
| real_only_unsupervised_boundary_score | top05  | pass_goodVertices                       |         33296 |             3052 |               0.0916627   |           0.0206727   |
| B_boundary_hand_defined_z             | top001 | pass_EcalDeadCellTriggerPrimitiveFilter |           666 |               56 |               0.0840841   |           0.000783899 |
| real_only_unsupervised_boundary_score | top001 | pass_EcalDeadCellTriggerPrimitiveFilter |           666 |               51 |               0.0765766   |           0.000783899 |
| real_only_unsupervised_boundary_score | top05  | pass_HBHENoiseFilter                    |         33296 |             1663 |               0.0499459   |           0.0547183   |
| real_only_unsupervised_boundary_score | top001 | pass_HBHENoiseIsoFilter                 |           666 |               20 |               0.03003     |           0.0109761   |
| real_only_unsupervised_boundary_score | top05  | pass_globalSuperTightHalo2016Filter     |         33296 |              949 |               0.0285019   |           0.0195389   |
| real_only_unsupervised_boundary_score | top001 | pass_HBHENoiseFilter                    |           666 |               18 |               0.027027    |           0.0547183   |
| real_only_unsupervised_boundary_score | top05  | pass_HBHENoiseIsoFilter                 |         33296 |              580 |               0.0174195   |           0.0109761   |
| B_boundary_hand_defined_z             | top01  | pass_EcalDeadCellTriggerPrimitiveFilter |          6660 |               85 |               0.0127628   |           0.000783899 |
| real_only_unsupervised_boundary_score | top01  | pass_HBHENoiseIsoFilter                 |          6660 |               83 |               0.0124625   |           0.0109761   |
| real_only_unsupervised_boundary_score | top01  | pass_EcalDeadCellTriggerPrimitiveFilter |          6660 |               63 |               0.00945946  |           0.000783899 |
| real_only_unsupervised_boundary_score | top01  | pass_globalSuperTightHalo2016Filter     |          6660 |               47 |               0.00705706  |           0.0195389   |
| B_boundary_hand_defined_z             | top05  | pass_EcalDeadCellTriggerPrimitiveFilter |         33296 |              187 |               0.00561629  |           0.000783899 |
| real_only_unsupervised_boundary_score | top05  | pass_EcalDeadCellTriggerPrimitiveFilter |         33296 |              100 |               0.00300336  |           0.000783899 |
| B_boundary_hand_defined_z             | top05  | pass_HBHENoiseIsoFilter                 |         33296 |               56 |               0.00168188  |           0.0109761   |
| real_only_unsupervised_boundary_score | top001 | pass_globalSuperTightHalo2016Filter     |           666 |                1 |               0.0015015   |           0.0195389   |
| B_boundary_hand_defined_z             | top001 | pass_HBHENoiseIsoFilter                 |           666 |                1 |               0.0015015   |           0.0109761   |
| B_boundary_hand_defined_z             | top001 | pass_BadPFMuonFilter                    |           666 |                1 |               0.0015015   |           6.30723e-05 |
| B_boundary_hand_defined_z             | top05  | pass_globalSuperTightHalo2016Filter     |         33296 |               46 |               0.00138155  |           0.0195389   |
| B_boundary_hand_defined_z             | top05  | pass_HBHENoiseFilter                    |         33296 |               29 |               0.000870975 |           0.0547183   |
| B_boundary_hand_defined_z             | top01  | pass_HBHENoiseFilter                    |          6660 |                5 |               0.000750751 |           0.0547183   |
| B_boundary_hand_defined_z             | top01  | pass_BadPFMuonFilter                    |          6660 |                3 |               0.00045045  |           6.30723e-05 |
| B_boundary_hand_defined_z             | top01  | pass_HBHENoiseIsoFilter                 |          6660 |                3 |               0.00045045  |           0.0109761   |
| B_boundary_hand_defined_z             | top05  | pass_BadPFMuonFilter                    |         33296 |               13 |               0.000390437 |           6.30723e-05 |
| real_only_unsupervised_boundary_score | top01  | pass_BadPFMuonFilter                    |          6660 |                2 |               0.0003003   |           6.30723e-05 |
| real_only_unsupervised_boundary_score | top05  | pass_BadPFMuonFilter                    |         33296 |                9 |               0.000270303 |           6.30723e-05 |
| B_boundary_hand_defined_z             | top01  | pass_globalSuperTightHalo2016Filter     |          6660 |                1 |               0.00015015  |           0.0195389   |

## Tail Composition

| subset                 | score                                 | tail   | primary_dataset   |   tail_fraction |   baseline_fraction |   events |
|:-----------------------|:--------------------------------------|:-------|:------------------|----------------:|--------------------:|---------:|
| all_events             | B_boundary_hand_defined_z             | top05  | MET               |      0.564122   |          0.341556   |    18783 |
| all_events             | B_boundary_hand_defined_z             | top05  | JetHT             |      0.3392     |          0.147387   |    11294 |
| all_events             | B_boundary_hand_defined_z             | top05  | SingleMuon        |      0.0966783  |          0.511057   |     3219 |
| all_events             | B_boundary_hand_defined_z             | top01  | MET               |      0.551351   |          0.341556   |     3672 |
| all_events             | B_boundary_hand_defined_z             | top01  | JetHT             |      0.372372   |          0.147387   |     2480 |
| all_events             | B_boundary_hand_defined_z             | top01  | SingleMuon        |      0.0762763  |          0.511057   |      508 |
| all_events             | B_boundary_hand_defined_z             | top001 | MET               |      0.5        |          0.341556   |      333 |
| all_events             | B_boundary_hand_defined_z             | top001 | JetHT             |      0.435435   |          0.147387   |      290 |
| all_events             | B_boundary_hand_defined_z             | top001 | SingleMuon        |      0.0645646  |          0.511057   |       43 |
| all_events             | real_only_unsupervised_boundary_score | top05  | MET               |      0.442095   |          0.341556   |    14720 |
| all_events             | real_only_unsupervised_boundary_score | top05  | JetHT             |      0.359983   |          0.147387   |    11986 |
| all_events             | real_only_unsupervised_boundary_score | top05  | SingleMuon        |      0.197922   |          0.511057   |     6590 |
| all_events             | real_only_unsupervised_boundary_score | top01  | MET               |      0.492042   |          0.341556   |     3277 |
| all_events             | real_only_unsupervised_boundary_score | top01  | JetHT             |      0.357207   |          0.147387   |     2379 |
| all_events             | real_only_unsupervised_boundary_score | top01  | SingleMuon        |      0.150751   |          0.511057   |     1004 |
| all_events             | real_only_unsupervised_boundary_score | top001 | MET               |      0.448949   |          0.341556   |      299 |
| all_events             | real_only_unsupervised_boundary_score | top001 | JetHT             |      0.42042    |          0.147387   |      280 |
| all_events             | real_only_unsupervised_boundary_score | top001 | SingleMuon        |      0.130631   |          0.511057   |       87 |
| standard_quality_clean | B_boundary_hand_defined_z             | top05  | MET               |      0.561684   |          0.2873     |    16987 |
| standard_quality_clean | B_boundary_hand_defined_z             | top05  | JetHT             |      0.341963   |          0.150256   |    10342 |
| standard_quality_clean | B_boundary_hand_defined_z             | top05  | SingleMuon        |      0.0963529  |          0.562444   |     2914 |
| standard_quality_clean | B_boundary_hand_defined_z             | top01  | MET               |      0.557943   |          0.2873     |     3375 |
| standard_quality_clean | B_boundary_hand_defined_z             | top01  | JetHT             |      0.366342   |          0.150256   |     2216 |
| standard_quality_clean | B_boundary_hand_defined_z             | top01  | SingleMuon        |      0.075715   |          0.562444   |      458 |
| standard_quality_clean | B_boundary_hand_defined_z             | top001 | MET               |      0.533884   |          0.2873     |      323 |
| standard_quality_clean | B_boundary_hand_defined_z             | top001 | JetHT             |      0.395041   |          0.150256   |      239 |
| standard_quality_clean | B_boundary_hand_defined_z             | top001 | SingleMuon        |      0.0710744  |          0.562444   |       43 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top05  | MET               |      0.401085   |          0.2873     |    12130 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top05  | JetHT             |      0.367755   |          0.150256   |    11122 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top05  | SingleMuon        |      0.231161   |          0.562444   |     6991 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top01  | MET               |      0.414283   |          0.2873     |     2506 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top01  | JetHT             |      0.398909   |          0.150256   |     2413 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top01  | SingleMuon        |      0.186808   |          0.562444   |     1130 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top001 | JetHT             |      0.442975   |          0.150256   |      268 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top001 | MET               |      0.401653   |          0.2873     |      243 |
| standard_quality_clean | real_only_unsupervised_boundary_score | top001 | SingleMuon        |      0.155372   |          0.562444   |       94 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top05  | MET               |      0.562799   |          0.336067   |    18336 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top05  | JetHT             |      0.340117   |          0.141711   |    11081 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top05  | SingleMuon        |      0.0970841  |          0.522222   |     3163 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top01  | MET               |      0.554942   |          0.336067   |     3616 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top01  | JetHT             |      0.368938   |          0.141711   |     2404 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top01  | SingleMuon        |      0.0761203  |          0.522222   |      496 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top001 | MET               |      0.538344   |          0.336067   |      351 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top001 | JetHT             |      0.392638   |          0.141711   |      256 |
| relaxed_quality_clean  | B_boundary_hand_defined_z             | top001 | SingleMuon        |      0.0690184  |          0.522222   |       45 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top05  | MET               |      0.424401   |          0.336067   |    13827 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top05  | JetHT             |      0.353714   |          0.141711   |    11524 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top05  | SingleMuon        |      0.221885   |          0.522222   |     7229 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top01  | MET               |      0.455034   |          0.336067   |     2965 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top01  | JetHT             |      0.373849   |          0.141711   |     2436 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top01  | SingleMuon        |      0.171117   |          0.522222   |     1115 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top001 | JetHT             |      0.42638    |          0.141711   |      278 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top001 | MET               |      0.424847   |          0.336067   |      277 |
| relaxed_quality_clean  | real_only_unsupervised_boundary_score | top001 | SingleMuon        |      0.148773   |          0.522222   |       97 |
| top_quality_failures   | B_boundary_hand_defined_z             | top05  | MET               |      0.932525   |          0.879182   |     2847 |
| top_quality_failures   | B_boundary_hand_defined_z             | top05  | JetHT             |      0.0609237  |          0.118951   |      186 |
| top_quality_failures   | B_boundary_hand_defined_z             | top05  | SingleMuon        |      0.00655093 |          0.00186757 |       20 |
| top_quality_failures   | B_boundary_hand_defined_z             | top01  | MET               |      0.803601   |          0.879182   |      491 |
| top_quality_failures   | B_boundary_hand_defined_z             | top01  | JetHT             |      0.180033   |          0.118951   |      110 |
| top_quality_failures   | B_boundary_hand_defined_z             | top01  | SingleMuon        |      0.0163666  |          0.00186757 |       10 |
| top_quality_failures   | B_boundary_hand_defined_z             | top001 | JetHT             |      0.822581   |          0.118951   |       51 |
| top_quality_failures   | B_boundary_hand_defined_z             | top001 | MET               |      0.177419   |          0.879182   |       11 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top05  | MET               |      0.725188   |          0.879182   |     2214 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top05  | JetHT             |      0.268588   |          0.118951   |      820 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top05  | SingleMuon        |      0.00622339 |          0.00186757 |       19 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top01  | MET               |      0.770867   |          0.879182   |      471 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top01  | JetHT             |      0.204583   |          0.118951   |      125 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top01  | SingleMuon        |      0.0245499  |          0.00186757 |       15 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top001 | JetHT             |      0.806452   |          0.118951   |       50 |
| top_quality_failures   | real_only_unsupervised_boundary_score | top001 | MET               |      0.193548   |          0.879182   |       12 |