# Top Boundary Events N-Frame Interpretation

Date: 2026-06-08

## Scope

This inspection used real CMS collision data only. No simulated samples were used and no discovery claim is made.

## What The Top Boundary Events Look Like

The top boundary events are not random. They are mainly mixed boundary-stress events involving visible activity, jet multiplicity, b-tag/heavy-flavour structure, secondary-vertex proxy structure and reconstruction complexity. Missing-energy dominance appears, but it is not the only or main pattern in the top-1000 sets.

Pattern classification for top-1000 sets:

| top_set       |   flag_missing_energy_dominant |   flag_visible_energy_jetht_dominant |   flag_heavy_flavour_reconstruction |   flag_displacement_secondary_vertex_proxy |   flag_reconstruction_complexity |   flag_mixed_high_boundary |   flag_possible_data_quality_trigger_followup |
|:--------------|-------------------------------:|-------------------------------------:|------------------------------------:|-------------------------------------------:|---------------------------------:|---------------------------:|----------------------------------------------:|
| hand_top1000  |                          0.004 |                                0.887 |                               0.879 |                                      0.931 |                            0.24  |                      0.805 |                                             1 |
| unsup_top1000 |                          0.073 |                                0.64  |                               0.638 |                                      0.685 |                            0.242 |                      0.558 |                                             1 |

Driver-variable summaries show that the top events differ strongly from the rest of the data in HT, secondary vertices, b-tags, jet multiplicity and packed-candidate complexity:

| top_set         | variable               |     top_mean |     rest_mean |   mean_difference |   top_median |   rest_median |      top_p90 |    rest_p90 |
|:----------------|:-----------------------|-------------:|--------------:|------------------:|-------------:|--------------:|-------------:|------------:|
| hand_top0p1pct  | HT                     |  6510.81     |  199.019      |        6311.79    |   985.861    |     86.7536   |  2792.43     |  582.778    |
| hand_top0p1pct  | packed_candidate_count |  2002.76     | 1471.43       |         531.331   |  1901.5      |   1445        |  2556.5      | 1988        |
| hand_top0p1pct  | MET_pt                 |   209.583    |   53.7764     |         155.807   |   141.514    |     38.8209   |   415.44     |  110.893    |
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
| hand_top1000    | max_btag_discriminator |     0.939769 |   -4.32521    |           5.26498 |     0.981031 |      0.553336 |     0.997923 |    0.952502 |
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
| unsup_top100    | MET_pt                 |   424.611    |   53.8765     |         370.734   |   237.286    |     38.8539   |  1002.82     |  111.155    |
| unsup_top100    | N_jets_30              |    23.81     |    1.87931    |          21.9307  |    11.5      |      1        |    43        |    4        |
| unsup_top100    | N_jets_50              |    22.35     |    1.16788    |          21.1821  |    10        |      1        |    42        |    3        |
| unsup_top100    | N_leptons              |    11.38     |    0.976181   |          10.4038  |     6        |      1        |    26.1      |    2        |
| unsup_top100    | N_primary_vertices     |    26        |   18.1865     |           7.81354 |    25        |     17        |    36.1      |   28        |
| unsup_top100    | secondary_vertex_count |     7.03     |    1.33667    |           5.69333 |     7.5      |      1        |    16        |    4        |
| unsup_top1000   | HT                     |  4356.53     |  199.088      |        4157.44    |   651.296    |     86.8059   |  1943.88     |  583.02     |
| unsup_top1000   | packed_candidate_count |  1723.66     | 1471.58       |         252.079   |  1756.5      |   1445        |  2599.2      | 1988        |
| unsup_top1000   | MET_pt                 |   129.713    |   53.8182     |          75.8946  |    68.0896   |     38.8368   |   244.484    |  110.994    |
| unsup_top1000   | secondary_vertex_count |     7.292    |    1.32857    |           5.96343 |     8        |      1        |    13        |    4        |
| unsup_top1000   | N_jets_30              |     6.544    |    1.8756     |           4.6684  |     6        |      1        |    10        |    4        |
| unsup_top1000   | N_jets_50              |     5.386    |    1.16473    |           4.22127 |     4        |      1        |     8        |    3        |
| unsup_top1000   | displacement_proxy_raw |     3.4418   |   -0.00517641 |           3.44698 |     3.85104  |     -0.195095 |     6.74114  |    1.53896  |
| unsup_top1000   | N_primary_vertices     |    21.415    |   18.1828     |           3.23222 |    21        |     17        |    35        |   28        |

## Sample Composition

Hand-defined top-1000 composition:

| top_set      | sample_id                         |   count |   fraction |
|:-------------|:----------------------------------|--------:|-----------:|
| hand_top1000 | cms_met_run2016g_collision        |     518 |      0.518 |
| hand_top1000 | cms_jetht_run2016g_collision      |     417 |      0.417 |
| hand_top1000 | cms_singlemuon_run2016g_collision |      65 |      0.065 |

Unsupervised top-1000 composition:

| top_set       | sample_id                         |   count |   fraction |
|:--------------|:----------------------------------|--------:|-----------:|
| unsup_top1000 | cms_met_run2016g_collision        |     458 |      0.458 |
| unsup_top1000 | cms_jetht_run2016g_collision      |     405 |      0.405 |
| unsup_top1000 | cms_singlemuon_run2016g_collision |     137 |      0.137 |

## File/Run/Lumi Concentration

The strongest caution is concentration. The very top boundary events are strongly concentrated by run/lumi and partly by source file.

Concentration summary:

| top_set         |   events |   top_1_source_file_fraction |   top_2_source_file_fraction |   top_3_source_file_fraction |   top_1_run_fraction |   top_5_run_fraction |   top_10_run_fraction |   top_1_lumi_bin_fraction |   top_5_lumi_bin_fraction | judgement                                                                    |
|:----------------|---------:|-----------------------------:|-----------------------------:|-----------------------------:|---------------------:|---------------------:|----------------------:|--------------------------:|--------------------------:|:-----------------------------------------------------------------------------|
| hand_top100     |      100 |                     0.43     |                     0.61     |                     0.79     |             0.61     |             0.95     |              1        |                  0.62     |                  0.85     | strongly file/run/lumi concentrated; requires data-quality/trigger follow-up |
| hand_top1000    |     1000 |                     0.247    |                     0.47     |                     0.639    |             0.323    |             0.841    |              0.946    |                  0.364    |                  0.713    | strongly file/run/lumi concentrated; requires data-quality/trigger follow-up |
| hand_top0p1pct  |      666 |                     0.252252 |                     0.454955 |                     0.629129 |             0.339339 |             0.839339 |              0.938438 |                  0.376877 |                  0.711712 | strongly file/run/lumi concentrated; requires data-quality/trigger follow-up |
| unsup_top100    |      100 |                     0.43     |                     0.6      |                     0.72     |             0.6      |             0.87     |              0.97     |                  0.61     |                  0.83     | strongly file/run/lumi concentrated; requires data-quality/trigger follow-up |
| unsup_top1000   |     1000 |                     0.245    |                     0.433    |                     0.597    |             0.245    |             0.683    |              0.871    |                  0.325    |                  0.653    | strongly file/run/lumi concentrated; requires data-quality/trigger follow-up |
| unsup_top0p1pct |      666 |                     0.252252 |                     0.421922 |                     0.572072 |             0.252252 |             0.713213 |              0.882883 |                  0.373874 |                  0.668168 | strongly file/run/lumi concentrated; requires data-quality/trigger follow-up |

For hand-defined top 1000, the top source file contributes 24.7%, the top run contributes 32.3%, and the top lumi bin contributes 36.4%.

For unsupervised top 1000, the top source file contributes 24.5%, the top run contributes 24.5%, and the top lumi bin contributes 32.5%.

This means the top boundary tail is suitable as a follow-up candidate region, but it requires trigger/data-quality follow-up before being interpreted as physics-like.

## Trigger/Filter Extraction

Trigger/filter extraction is technically feasible. A small 1,000-event-per-sample probe extracted broad HLT category flags and common filter flags. However, the trigger table only covers the probe events, so join coverage with the full top-1000 tables is very low:

| top_set      |   events |   trigger_rows_matched |   coverage_fraction |   HLT_MET_paths_any_mean_matched |   HLT_HT_paths_any_mean_matched |   HLT_Mu_paths_any_mean_matched |   HLT_Ele_paths_any_mean_matched |   pass_HBHENoiseFilter_mean_matched |   pass_HBHENoiseIsoFilter_mean_matched |   pass_goodVertices_mean_matched |   pass_EcalDeadCellTriggerPrimitiveFilter_mean_matched |   pass_BadPFMuonFilter_mean_matched |   pass_globalSuperTightHalo2016Filter_mean_matched |   trigger_filter_extraction_status_mean_matched |
|:-------------|---------:|-----------------------:|--------------------:|---------------------------------:|--------------------------------:|--------------------------------:|---------------------------------:|------------------------------------:|---------------------------------------:|---------------------------------:|-------------------------------------------------------:|------------------------------------:|---------------------------------------------------:|------------------------------------------------:|
| hand         |     1000 |                      5 |               0.005 |                         1        |                               1 |                             1   |                         0        |                                   1 |                                      1 |                                1 |                                                      1 |                                   1 |                                                  1 |                                               1 |
| unsupervised |     1000 |                      6 |               0.006 |                         0.666667 |                               1 |                             0.5 |                         0.166667 |                                   1 |                                      1 |                                1 |                                                      1 |                                   1 |                                                  1 |                                               1 |

Full trigger/filter coverage would require re-running the full file-by-file extraction with the patched analyser.

## Physics-Like Or Artefact-Like?

Current judgement: **unclear, but follow-up-worthy**.

The top events look structured and boundary-like rather than random: they are mixed high-stress events involving HT/JetHT activity, heavy-flavour/reconstruction structure and secondary-vertex proxies. However, the strong run/lumi concentration means a trigger-selection or data-quality explanation remains plausible. We should not call this physics-like until the trigger/filter and data-quality checks are complete.

## N-Frame Interpretation

The strongest careful N-Frame interpretation is that the real-data boundary map identifies a boundary-stress tail where missing information, visible activity, object multiplicity, secondary-vertex proxy structure and reconstruction complexity co-occur. This is a trace-compatible follow-up region, not a discovery claim.

## What Remains Weak

- Full trigger/filter coverage is not yet joined to all top events.
- The top 100 and top 0.1% sets are strongly run/lumi concentrated.
- Secondary-vertex counts are only displacement-like proxies, not proof of displaced particles.
- File/run/lumi concentration needs CMS data-quality and trigger context.

## Next Step

Re-run the full file-by-file extraction with the patched trigger/filter analyser enabled, then repeat the top-boundary concentration and classification reports with full trigger/filter coverage.
