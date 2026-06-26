# Real-Only Hand-Defined Boundary Scoring Report

Date: 2026-06-08

The hand-defined boundary score uses only real CMS collision data. It does not use simulated samples, signal labels or supervised classification.

## Component Availability

| component                   | available   | available_inputs                                                                                    |   missing_fraction |
|:----------------------------|:------------|:----------------------------------------------------------------------------------------------------|-------------------:|
| R_missing                   | True        | MET_z                                                                                               |                  0 |
| R_visible_energy            | True        | HT_z;leading_jet_z;subleading_jet_z                                                                 |                  0 |
| R_multiplicity              | True        | N_jets_30_z;N_jets_50_z;N_leptons_z;N_objects_z                                                     |                  0 |
| R_btag_structure            | True        | N_btags_loose_z;N_btags_medium_z;N_btags_tight_z;max_btag_discriminator_z                           |                  0 |
| R_reconstruction_complexity | True        | N_primary_vertices_z;packed_candidate_count_z;secondary_vertex_count_z;N_objects_z;N_btags_medium_z |                  0 |
| R_compression_proxy         | True        | compression_proxy_z                                                                                 |                  0 |
| R_displacement_proxy        | True        | displacement_proxy_z                                                                                |                  0 |

## Sample Summary

| sample_id                         | primary_dataset   |   events |   mean_boundary_z |   median_boundary_z |   top10_frac |   top05_frac |   top01_frac |   mean_R_missing |   mean_R_visible_energy |   mean_R_multiplicity |   mean_R_btag_structure |   mean_R_reconstruction_complexity |   mean_R_compression_proxy |
|:----------------------------------|:------------------|---------:|------------------:|--------------------:|-------------:|-------------:|-------------:|-----------------:|------------------------:|----------------------:|------------------------:|-----------------------------------:|---------------------------:|
| cms_jetht_run2016g_collision      | JetHT             |    50000 |          0.269958 |            0.225066 |      0.13956 |      0.06912 |      0.01354 |        -0.129841 |                0.727844 |              0.518803 |              -0.0425346 |                           0.178028 |                 -0.757146  |
| cms_met_run2016g_collision        | MET               |    50000 |          0.371202 |            0.383519 |      0.14716 |      0.07536 |      0.0156  |         0.609913 |               -0.197803 |             -0.256004 |               0.174126  |                           0.296127 |                  0.69787   |
| cms_singlemuon_run2016g_collision | SingleMuon        |    50000 |         -0.64116  |           -0.695491 |      0.01328 |      0.00552 |      0.00086 |        -0.480073 |               -0.530041 |             -0.262799 |              -0.13297   |                          -0.474155 |                  0.0592769 |

## Interpretation

The score is a transparent stress estimate across missing information, visible energy, multiplicity, b-tag/reconstruction structure, compression-like imbalance and secondary-vertex displacement proxy. It is not a discovery statistic.