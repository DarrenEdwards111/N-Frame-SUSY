# Top Boundary Event Composition Report

Date: 2026-06-08

This report inspects real-data-only top boundary event sets. No simulated samples are used.

## Pattern Judgement

| top_set         | score                                      |   events | pattern                                                                      |
|:----------------|:-------------------------------------------|---------:|:-----------------------------------------------------------------------------|
| hand_top100     | B_boundary_hand_defined_z                  |      100 | MET-dominant; HT/JetHT-dominant; secondary-vertex proxy                      |
| hand_top1000    | B_boundary_hand_defined_z                  |     1000 | MET-dominant; HT/JetHT-dominant; b-tag/heavy-flavour; secondary-vertex proxy |
| hand_top0p1pct  | B_boundary_hand_defined_z                  |      666 | MET-dominant; HT/JetHT-dominant; b-tag/heavy-flavour; secondary-vertex proxy |
| unsup_top100    | real_only_full_unsupervised_boundary_score |      100 | MET-dominant; HT/JetHT-dominant; secondary-vertex proxy                      |
| unsup_top1000   | real_only_full_unsupervised_boundary_score |     1000 | HT/JetHT-dominant; secondary-vertex proxy                                    |
| unsup_top0p1pct | real_only_full_unsupervised_boundary_score |      666 | HT/JetHT-dominant; secondary-vertex proxy                                    |

## Composition By Sample

| top_set         | sample_id                         |   count |   fraction |
|:----------------|:----------------------------------|--------:|-----------:|
| hand_top100     | cms_jetht_run2016g_collision      |      65 |  0.65      |
| hand_top100     | cms_met_run2016g_collision        |      34 |  0.34      |
| hand_top100     | cms_singlemuon_run2016g_collision |       1 |  0.01      |
| hand_top1000    | cms_met_run2016g_collision        |     518 |  0.518     |
| hand_top1000    | cms_jetht_run2016g_collision      |     417 |  0.417     |
| hand_top1000    | cms_singlemuon_run2016g_collision |      65 |  0.065     |
| hand_top0p1pct  | cms_met_run2016g_collision        |     333 |  0.5       |
| hand_top0p1pct  | cms_jetht_run2016g_collision      |     290 |  0.435435  |
| hand_top0p1pct  | cms_singlemuon_run2016g_collision |      43 |  0.0645646 |
| unsup_top100    | cms_jetht_run2016g_collision      |      72 |  0.72      |
| unsup_top100    | cms_met_run2016g_collision        |      26 |  0.26      |
| unsup_top100    | cms_singlemuon_run2016g_collision |       2 |  0.02      |
| unsup_top1000   | cms_met_run2016g_collision        |     458 |  0.458     |
| unsup_top1000   | cms_jetht_run2016g_collision      |     405 |  0.405     |
| unsup_top1000   | cms_singlemuon_run2016g_collision |     137 |  0.137     |
| unsup_top0p1pct | cms_met_run2016g_collision        |     299 |  0.448949  |
| unsup_top0p1pct | cms_jetht_run2016g_collision      |     280 |  0.42042   |
| unsup_top0p1pct | cms_singlemuon_run2016g_collision |      87 |  0.130631  |

## Main Driver Variables

| top_set         | variable               |     top_mean |     rest_mean |   mean_difference |   top_median |   rest_median |      top_p90 |    rest_p90 |
|:----------------|:-----------------------|-------------:|--------------:|------------------:|-------------:|--------------:|-------------:|------------:|
| hand_top0p1pct  | HT                     |  6510.81     |  199.019      |        6311.79    |   985.861    |     86.7536   |  2792.43     |  582.778    |
| hand_top0p1pct  | packed_candidate_count |  2002.76     | 1471.43       |         531.331   |  1901.5      |   1445        |  2556.5      | 1988        |
| hand_top0p1pct  | MET_pt                 |   209.583    |   53.7764     |         155.807   |   141.514    |     38.8209   |   415.439    |  110.893    |
| hand_top0p1pct  | secondary_vertex_count |     9.0961   |    1.32976    |           7.76634 |     9        |      1        |    14        |    4        |
| hand_top0p1pct  | N_jets_30              |     8.81532  |    1.87567    |           6.93965 |     6        |      1        |    10        |    4        |
| hand_top0p1pct  | N_primary_vertices     |    24.6817   |   18.1811     |           6.50055 |    24        |     17        |    33        |   28        |
| hand_top0p1pct  | N_jets_50              |     7.34084  |    1.16489    |           6.17595 |     5        |      1        |     8        |    3        |
| hand_top0p1pct  | max_btag_discriminator |     0.934864 |   -4.32256    |           5.25742 |     0.982685 |      0.553357 |     0.997974 |    0.952797 |
| hand_top100     | HT                     | 37426.3      |  199.741      |       37226.6     |  3509.41     |     86.9153   | 75446.7      |  585.036    |
| hand_top100     | packed_candidate_count |  2554.94     | 1471.8        |        1083.14    |  2547.5      |   1446        |  3342.6      | 1989        |
| hand_top100     | MET_pt                 |   479.27     |   53.8683     |         425.401   |   346.924    |     38.8522   |  1002.82     |  111.139    |
| hand_top100     | N_jets_30              |    23.64     |    1.87934    |          21.7607  |    11        |      1        |    43        |    4        |
| hand_top100     | N_jets_50              |    22.26     |    1.1679     |          21.0921  |     9        |      1        |    42        |    3        |
| hand_top100     | N_leptons              |    12.23     |    0.976053   |          11.2539  |     8.5      |      1        |    26.1      |    2        |
| hand_top100     | N_primary_vertices     |    25.53     |   18.1865     |           7.34347 |    25        |     17        |    33.1      |   28        |
| hand_top100     | secondary_vertex_count |     6.48     |    1.33675    |           5.14325 |     7        |      1        |    15        |    4        |
| hand_top1000    | HT                     |  4643.45     |  198.656      |        4444.79    |   916.434    |     86.6677   |  2061.3      |  581.611    |
| hand_top1000    | packed_candidate_count |  1956.25     | 1471.23       |         485.024   |  1883.5      |   1445        |  2473.1      | 1988        |
| hand_top1000    | MET_pt                 |   191.579    |   53.7252     |         137.854   |   135.276    |     38.8048   |   368.694    |  110.744    |
| hand_top1000    | secondary_vertex_count |     8.854    |    1.32622    |           7.52778 |     9        |      1        |    13        |    4        |
| hand_top1000    | N_primary_vertices     |    24.574    |   18.178      |           6.39598 |    24        |     17        |    33        |   28        |
| hand_top1000    | N_jets_30              |     7.76     |    1.87377    |           5.88623 |     6        |      1        |     9        |    4        |
| hand_top1000    | max_btag_discriminator |     0.939769 |   -4.32521    |           5.26498 |     0.981032 |      0.553336 |     0.997923 |    0.952502 |
| hand_top1000    | N_jets_50              |     6.308    |    1.16334    |           5.14466 |     5        |      1        |     7        |    3        |
| unsup_top0p1pct | HT                     |  6193.4      |  199.336      |        5994.06    |   669.773    |     86.8512   |  2624.94     |  583.776    |
| unsup_top0p1pct | packed_candidate_count |  1719.39     | 1471.71       |         247.681   |  1773        |   1446        |  2806.5      | 1988        |
| unsup_top0p1pct | MET_pt                 |   150.034    |   53.836      |          96.1984  |    78.5192   |     38.8392   |   299.758    |  111.029    |
| unsup_top0p1pct | secondary_vertex_count |     7.51952  |    1.33133    |           6.18819 |     9        |      1        |    14        |    4        |
| unsup_top0p1pct | N_jets_30              |     7.52703  |    1.87696    |           5.65007 |     6        |      1        |    11        |    4        |
| unsup_top0p1pct | N_jets_50              |     6.35135  |    1.16588    |           5.18547 |     4        |      1        |     9        |    3        |
| unsup_top0p1pct | displacement_proxy_raw |     3.57331  |   -0.00357742 |           3.57689 |     4.42906  |     -0.195095 |     7.31916  |    1.53896  |
| unsup_top0p1pct | N_primary_vertices     |    20.7763   |   18.185      |           2.59124 |    21        |     17        |    34        |   28        |
| unsup_top100    | HT                     | 37387.4      |  199.747      |       37187.6     |  3784.2      |     86.9166   | 75446.7      |  585.063    |
| unsup_top100    | packed_candidate_count |  2595.8      | 1471.79       |        1124.01    |  2769        |   1446        |  3342.6      | 1989        |
| unsup_top100    | MET_pt                 |   424.611    |   53.8765     |         370.734   |   237.285    |     38.8539   |  1002.82     |  111.155    |
| unsup_top100    | N_jets_30              |    23.81     |    1.87931    |          21.9307  |    11.5      |      1        |    43        |    4        |
| unsup_top100    | N_jets_50              |    22.35     |    1.16788    |          21.1821  |    10        |      1        |    42        |    3        |
| unsup_top100    | N_leptons              |    11.38     |    0.976181   |          10.4038  |     6        |      1        |    26.1      |    2        |
| unsup_top100    | N_primary_vertices     |    26        |   18.1865     |           7.81354 |    25        |     17        |    36.1      |   28        |
| unsup_top100    | secondary_vertex_count |     7.03     |    1.33667    |           5.69333 |     7.5      |      1        |    16        |    4        |
| unsup_top1000   | HT                     |  4356.53     |  199.088      |        4157.44    |   651.296    |     86.8059   |  1943.88     |  583.02     |
| unsup_top1000   | packed_candidate_count |  1723.66     | 1471.58       |         252.079   |  1756.5      |   1445        |  2599.2      | 1988        |
| unsup_top1000   | MET_pt                 |   129.713    |   53.8182     |          75.8946  |    68.0896   |     38.8367   |   244.484    |  110.994    |
| unsup_top1000   | secondary_vertex_count |     7.292    |    1.32857    |           5.96343 |     8        |      1        |    13        |    4        |
| unsup_top1000   | N_jets_30              |     6.544    |    1.8756     |           4.6684  |     6        |      1        |    10        |    4        |
| unsup_top1000   | N_jets_50              |     5.386    |    1.16473    |           4.22127 |     4        |      1        |     8        |    3        |
| unsup_top1000   | displacement_proxy_raw |     3.4418   |   -0.00517641 |           3.44698 |     3.85104  |     -0.195095 |     6.74114  |    1.53896  |
| unsup_top1000   | N_primary_vertices     |    21.415    |   18.1828     |           3.23222 |    21        |     17        |    35        |   28        |