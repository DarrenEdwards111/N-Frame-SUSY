# Real-Only High Boundary Tail Analysis

Date: 2026-06-08

This analysis uses real CMS collision MiniAOD only. It asks where high N-Frame boundary-stress conditions occur inside real data.

## Tail Summary

| score                                 | tail   |   threshold |   events |   mean_MET_pt |   median_MET_pt |   mean_HT |   median_HT |   mean_N_jets_30 |   mean_N_leptons |   mean_N_btags_medium |   mean_packed_candidate_count |
|:--------------------------------------|:-------|------------:|---------:|--------------:|----------------:|----------:|------------:|-----------------:|-----------------:|----------------------:|------------------------------:|
| B_boundary_hand_defined_z             | top10  |     1.33955 |    15000 |       90.6927 |         75.1381 |   605.713 |     542.889 |          4.51547 |          1.7102  |              1.00027  |                       1798.41 |
| B_boundary_hand_defined_z             | top05  |     1.76205 |     7500 |       96.3812 |         80.6031 |   659.255 |     588.823 |          4.866   |          1.93253 |              1.25213  |                       1817.29 |
| B_boundary_hand_defined_z             | top01  |     2.58519 |     1500 |      110.823  |         92.8319 |   795.707 |     691.996 |          5.64333 |          2.486   |              1.70333  |                       1866.54 |
| B_boundary_hand_defined_z             | top001 |     3.61797 |      150 |      151.122  |        112.477  |  1034.35  |     900.779 |          6.58    |          3.25333 |              2.21333  |                       1918.65 |
| real_only_unsupervised_boundary_score | top10  |     1.30702 |    15000 |       65.6478 |         42.2996 |   506.756 |     465.662 |          3.86887 |          1.43553 |              0.950733 |                       1635.66 |
| real_only_unsupervised_boundary_score | top05  |     1.93147 |     7500 |       68.9864 |         41.6975 |   548.173 |     508.794 |          4.19413 |          1.58213 |              1.14747  |                       1655.23 |
| real_only_unsupervised_boundary_score | top01  |     3.31881 |     1500 |       82.1063 |         42.1069 |   630.315 |     594.014 |          4.65733 |          1.908   |              1.49133  |                       1673.12 |
| real_only_unsupervised_boundary_score | top001 |     5.22838 |      150 |      175.611  |         59.5394 |   634.374 |     515.372 |          4.30667 |          2.02667 |              1.28667  |                       1460.21 |

## Sample Enrichment

| score                                 | tail   | sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:--------------------------------------|:-------|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| B_boundary_hand_defined_z             | top10  | cms_met_run2016g_collision        |       0.490533  |            0.333333 |             1.4716 |          7358 |
| B_boundary_hand_defined_z             | top10  | cms_jetht_run2016g_collision      |       0.4652    |            0.333333 |             1.3956 |          6978 |
| B_boundary_hand_defined_z             | top10  | cms_singlemuon_run2016g_collision |       0.0442667 |            0.333333 |             0.1328 |           664 |
| B_boundary_hand_defined_z             | top05  | cms_met_run2016g_collision        |       0.5024    |            0.333333 |             1.5072 |          3768 |
| B_boundary_hand_defined_z             | top05  | cms_jetht_run2016g_collision      |       0.4608    |            0.333333 |             1.3824 |          3456 |
| B_boundary_hand_defined_z             | top05  | cms_singlemuon_run2016g_collision |       0.0368    |            0.333333 |             0.1104 |           276 |
| B_boundary_hand_defined_z             | top01  | cms_met_run2016g_collision        |       0.52      |            0.333333 |             1.56   |           780 |
| B_boundary_hand_defined_z             | top01  | cms_jetht_run2016g_collision      |       0.451333  |            0.333333 |             1.354  |           677 |
| B_boundary_hand_defined_z             | top01  | cms_singlemuon_run2016g_collision |       0.0286667 |            0.333333 |             0.086  |            43 |
| B_boundary_hand_defined_z             | top001 | cms_met_run2016g_collision        |       0.586667  |            0.333333 |             1.76   |            88 |
| B_boundary_hand_defined_z             | top001 | cms_jetht_run2016g_collision      |       0.386667  |            0.333333 |             1.16   |            58 |
| B_boundary_hand_defined_z             | top001 | cms_singlemuon_run2016g_collision |       0.0266667 |            0.333333 |             0.08   |             4 |
| real_only_unsupervised_boundary_score | top10  | cms_jetht_run2016g_collision      |       0.504467  |            0.333333 |             1.5134 |          7567 |
| real_only_unsupervised_boundary_score | top10  | cms_met_run2016g_collision        |       0.340733  |            0.333333 |             1.0222 |          5111 |
| real_only_unsupervised_boundary_score | top10  | cms_singlemuon_run2016g_collision |       0.1548    |            0.333333 |             0.4644 |          2322 |
| real_only_unsupervised_boundary_score | top05  | cms_jetht_run2016g_collision      |       0.5312    |            0.333333 |             1.5936 |          3984 |
| real_only_unsupervised_boundary_score | top05  | cms_met_run2016g_collision        |       0.340133  |            0.333333 |             1.0204 |          2551 |
| real_only_unsupervised_boundary_score | top05  | cms_singlemuon_run2016g_collision |       0.128667  |            0.333333 |             0.386  |           965 |
| real_only_unsupervised_boundary_score | top01  | cms_jetht_run2016g_collision      |       0.548667  |            0.333333 |             1.646  |           823 |
| real_only_unsupervised_boundary_score | top01  | cms_met_run2016g_collision        |       0.332     |            0.333333 |             0.996  |           498 |
| real_only_unsupervised_boundary_score | top01  | cms_singlemuon_run2016g_collision |       0.119333  |            0.333333 |             0.358  |           179 |
| real_only_unsupervised_boundary_score | top001 | cms_jetht_run2016g_collision      |       0.52      |            0.333333 |             1.56   |            78 |
| real_only_unsupervised_boundary_score | top001 | cms_met_run2016g_collision        |       0.34      |            0.333333 |             1.02   |            51 |
| real_only_unsupervised_boundary_score | top001 | cms_singlemuon_run2016g_collision |       0.14      |            0.333333 |             0.42   |            21 |

## Main Driver Variables

| score                                 | variable                              |   top01_mean |    rest_mean |   mean_difference |   top01_median |   rest_median |
|:--------------------------------------|:--------------------------------------|-------------:|-------------:|------------------:|---------------:|--------------:|
| B_boundary_hand_defined_z             | HT                                    |   795.707    |  272.685     |         523.022   |     691.996    |    135.312    |
| B_boundary_hand_defined_z             | packed_candidate_count                |  1866.54     | 1484.05      |         382.492   |    1853        |   1452        |
| B_boundary_hand_defined_z             | MET_pt                                |   110.823    |   50.9996    |          59.8237  |      92.8319   |     37.709    |
| B_boundary_hand_defined_z             | secondary_vertex_count                |     7.356    |    1.54801   |           5.80799 |       7        |      1        |
| B_boundary_hand_defined_z             | N_primary_vertices                    |    23.6907   |   17.908     |           5.78265 |      23        |     17        |
| B_boundary_hand_defined_z             | max_btag_discriminator                |     0.944199 |   -3.5137    |           4.4579  |       0.981012 |      0.55529  |
| B_boundary_hand_defined_z             | N_jets_30                             |     5.64333  |    2.18892   |           3.45441 |       6        |      2        |
| B_boundary_hand_defined_z             | real_only_unsupervised_boundary_score |     3.25682  |   -0.0328972 |           3.28972 |       3.10707  |     -0.229787 |
| B_boundary_hand_defined_z             | B_boundary_hand_defined_z             |     3.04909  |   -0.0307989 |           3.07989 |       2.91865  |     -0.123891 |
| B_boundary_hand_defined_z             | N_jets_50                             |     4.24067  |    1.48618   |           2.75449 |       4        |      1        |
| real_only_unsupervised_boundary_score | HT                                    |   630.315    |  274.355     |         355.96    |     594.014    |    137        |
| real_only_unsupervised_boundary_score | packed_candidate_count                |  1673.12     | 1486         |         187.125   |    1736.5      |   1455        |
| real_only_unsupervised_boundary_score | MET_pt                                |    82.1063   |   51.2897    |          30.8167  |      42.1069   |     37.9799   |
| real_only_unsupervised_boundary_score | secondary_vertex_count                |     5.802    |    1.5637    |           4.2383  |       6        |      1        |
| real_only_unsupervised_boundary_score | real_only_unsupervised_boundary_score |     4.14607  |   -0.0418795 |           4.18795 |       3.85414  |     -0.229787 |
| real_only_unsupervised_boundary_score | N_primary_vertices                    |    20.7393   |   17.9378    |           2.80151 |      20        |     17        |
| real_only_unsupervised_boundary_score | N_jets_30                             |     4.65733  |    2.19888   |           2.45845 |       5        |      2        |
| real_only_unsupervised_boundary_score | N_jets_50                             |     3.45667  |    1.49409   |           1.96257 |       4        |      1        |
| real_only_unsupervised_boundary_score | B_boundary_hand_defined_z             |     1.81584  |   -0.0183418 |           1.83418 |       2.2997   |     -0.119057 |
| real_only_unsupervised_boundary_score | N_btags_medium                        |     1.49133  |    0.23033   |           1.261   |       2        |      0        |

## Source File Stability

Exact per-event source file was not recorded by the analyzer; source-file stability is therefore limited to sample/log-level provenance in this run.

## Interpretation

The high-boundary tail is structured, not random: it is dominated by combinations of missing energy, visible energy, multiplicity and reconstruction complexity. The real-only result should be used as a boundary map for follow-up, not as a discovery claim.