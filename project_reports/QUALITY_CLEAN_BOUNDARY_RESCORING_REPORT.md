# Quality-Clean Boundary Rescoring Report

Date: 2026-06-08

Boundary z-scores and quantile tails were recomputed within each quality-clean subset.

## Summary

| subset                 | score                          |   events |         mean |     p95 |     p99 |    p999 |
|:-----------------------|:-------------------------------|---------:|-------------:|--------:|--------:|--------:|
| standard_quality_clean | mc_B_boundary_hand_defined_z   |   604860 |  1.50364e-16 | 1.80855 | 2.68763 | 3.7931  |
| standard_quality_clean | mc_unsupervised_boundary_score |   604860 | -6.85286e-16 | 1.86804 | 3.46071 | 5.88262 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   |   651585 |  5.86244e-17 | 1.82123 | 2.7195  | 3.84498 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score |   651585 |  3.34019e-15 | 1.89285 | 3.57434 | 5.94234 |

## Tail Enrichment

| subset                 | score                          | tail   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-----------------------|:-------------------------------|:-------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05  | MET               |       0.563238  |            0.2873   |           1.96045  |    17034 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05  | JetHT             |       0.342228  |            0.150256 |           2.27763  |    10350 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top05  | SingleMuon        |       0.0945343 |            0.562444 |           0.168078 |     2859 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01  | MET               |       0.559431  |            0.2873   |           1.94721  |     3384 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01  | JetHT             |       0.366507  |            0.150256 |           2.43921  |     2217 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top01  | SingleMuon        |       0.0740618 |            0.562444 |           0.131679 |      448 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001 | MET               |       0.540496  |            0.2873   |           1.8813   |      327 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001 | JetHT             |       0.396694  |            0.150256 |           2.64012  |      240 |
| standard_quality_clean | mc_B_boundary_hand_defined_z   | top001 | SingleMuon        |       0.0628099 |            0.562444 |           0.111673 |       38 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05  | MET               |       0.393248  |            0.2873   |           1.36877  |    11893 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05  | JetHT             |       0.329928  |            0.150256 |           2.19577  |     9978 |
| standard_quality_clean | mc_unsupervised_boundary_score | top05  | SingleMuon        |       0.276824  |            0.562444 |           0.492181 |     8372 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01  | MET               |       0.483882  |            0.2873   |           1.68424  |     2927 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01  | JetHT             |       0.309803  |            0.150256 |           2.06183  |     1874 |
| standard_quality_clean | mc_unsupervised_boundary_score | top01  | SingleMuon        |       0.206315  |            0.562444 |           0.366819 |     1248 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001 | MET               |       0.543802  |            0.2873   |           1.8928   |      329 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001 | JetHT             |       0.256198  |            0.150256 |           1.70508  |      155 |
| standard_quality_clean | mc_unsupervised_boundary_score | top001 | SingleMuon        |       0.2       |            0.562444 |           0.355591 |      121 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top05  | MET               |       0.562922  |            0.336067 |           1.67503  |    18340 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top05  | JetHT             |       0.341037  |            0.141711 |           2.40656  |    11111 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top05  | SingleMuon        |       0.0960405 |            0.522222 |           0.183907 |     3129 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01  | MET               |       0.555709  |            0.336067 |           1.65357  |     3621 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01  | JetHT             |       0.368324  |            0.141711 |           2.59911  |     2400 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top01  | SingleMuon        |       0.0759669 |            0.522222 |           0.145469 |      495 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top001 | MET               |       0.539877  |            0.336067 |           1.60646  |      352 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top001 | JetHT             |       0.391104  |            0.141711 |           2.75987  |      255 |
| relaxed_quality_clean  | mc_B_boundary_hand_defined_z   | top001 | SingleMuon        |       0.0690184 |            0.522222 |           0.132163 |       45 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top05  | MET               |       0.441559  |            0.336067 |           1.3139   |    14386 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top05  | JetHT             |       0.31814   |            0.141711 |           2.24499  |    10365 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top05  | SingleMuon        |       0.240301  |            0.522222 |           0.460151 |     7829 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01  | MET               |       0.521179  |            0.336067 |           1.55082  |     3396 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01  | JetHT             |       0.300798  |            0.141711 |           2.12261  |     1960 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top01  | SingleMuon        |       0.178023  |            0.522222 |           0.340896 |     1160 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top001 | MET               |       0.575153  |            0.336067 |           1.71143  |      375 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top001 | JetHT             |       0.260736  |            0.141711 |           1.83991  |      170 |
| relaxed_quality_clean  | mc_unsupervised_boundary_score | top001 | SingleMuon        |       0.16411   |            0.522222 |           0.314254 |      107 |