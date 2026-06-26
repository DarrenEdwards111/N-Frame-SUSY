# Real Collision Boundary Structure Analysis

## Scope

This is a real-data-only analysis using `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\real_collision_20gb_event_features_scored.csv`. No simulated signal outcome is used.

## Main Result

The current boundary score is a visible-jet boundary score only. It describes high visible activity and reconstruction complexity in real CMS collision events, not a full missing-energy or SUSY-like boundary score.

## Summary By Sample

| sample_id                         |   n_events |   mean_B_boundary_equal_weight_z |   sd_B_boundary_equal_weight_z |   median_B_boundary_equal_weight_z |   iqr_B_boundary_equal_weight_z |   pct_global_top_10 |   pct_global_top_05 |   pct_global_top_01 |   mean_MET_pt |   mean_HT |   mean_N_jets_30 |   mean_N_btags_medium |   mean_N_muons |   mean_N_electrons |
|:----------------------------------|-----------:|---------------------------------:|-------------------------------:|-----------------------------------:|--------------------------------:|--------------------:|--------------------:|--------------------:|--------------:|----------:|-----------------:|----------------------:|---------------:|-------------------:|
| cms_jetht_run2016g_collision      |      98145 |                         0.997849 |                       1.78834  |                          0.946645  |                        1.35956  |            42.5034  |           24.4781   |            5.0782   |           nan |  593.887  |          3.56392 |                   nan |            nan |                nan |
| cms_met_run2016g_collision        |     227443 |                        -0.014098 |                       0.769541 |                         -0.0487723 |                        1.31042  |             7.51529 |            2.88512  |            0.559701 |           nan |  199.269  |          1.7888  |                   nan |            nan |                nan |
| cms_singlemuon_run2016g_collision |     340314 |                        -0.278353 |                       0.523312 |                         -0.528344  |                        0.510809 |             2.28701 |            0.796323 |            0.11842  |           nan |   97.3247 |          1.46042 |                   nan |            nan |                nan |

## High-Boundary Tail Enrichment

Top 5% enrichment, sorted by residual:

| tail            | sample_id                         |   observed |   expected |   standardised_residual_simple |   chi_square |   p_value |
|:----------------|:----------------------------------|-----------:|-----------:|-------------------------------:|-------------:|----------:|
| boundary_top_05 | cms_jetht_run2016g_collision      |      24024 |    4907.38 |                       272.889  |      93190.6 |         0 |
| boundary_top_05 | cms_met_run2016g_collision        |       6562 |   11372.5  |                       -45.1086 |      93190.6 |         0 |
| boundary_top_05 | cms_singlemuon_run2016g_collision |       2710 |   17016.2  |                      -109.671  |      93190.6 |         0 |

## Interpretation

High-boundary events in this fallback analysis are driven by jet multiplicity and HT-like visible activity. MET, lepton, b-tag discriminator, trigger, lifetime, and displacement components are unavailable until CMSSW extraction works.

## Outputs

- `results/tables/real_collision_boundary_summary_by_sample.csv`
- `results/tables/real_collision_boundary_summary_by_file.csv`
- `results/tables/high_boundary_tail_enrichment_by_sample.csv`
- `results/tables/real_collision_pairwise_boundary_tests.csv`
- `results/tables/boundary_component_driver_summary.csv`
- `results/tables/top_1000_boundary_events.csv`
- `results/figures/*.png`
