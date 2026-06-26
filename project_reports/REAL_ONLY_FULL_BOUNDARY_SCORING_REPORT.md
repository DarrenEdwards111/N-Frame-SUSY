# Real-Only Full Boundary Scoring Report

Date: 2026-06-08

No simulated samples were used.

## Component Availability

| component                   | available   | available_inputs                                                                                                |   missing_fraction |
|:----------------------------|:------------|:----------------------------------------------------------------------------------------------------------------|-------------------:|
| R_missing                   | True        | MET_z                                                                                                           |                  0 |
| R_visible_energy            | True        | HT_z;leading_jet_z;subleading_jet_z                                                                             |                  0 |
| R_multiplicity              | True        | N_jets_30_z;N_jets_50_z;N_leptons_z;N_objects_z;packed_candidate_count_z                                        |                  0 |
| R_btag_structure            | True        | N_btags_loose_z;N_btags_medium_z;N_btags_tight_z;max_btag_discriminator_z                                       |                  0 |
| R_reconstruction_complexity | True        | N_primary_vertices_z;packed_candidate_count_z;secondary_vertex_count_z;N_objects_z;N_leptons_z;N_btags_medium_z |                  0 |
| R_compression_proxy         | True        | compression_proxy_z                                                                                             |                  0 |
| R_displacement_proxy        | True        | displacement_proxy_z                                                                                            |                  0 |

## Summary

| sample_id                         | primary_dataset   |   events |   mean_boundary_z |   median_boundary_z |   top10_frac |   top05_frac |   top01_frac |   top001_frac |   mean_R_missing |   mean_R_visible_energy |   mean_R_multiplicity |   mean_R_btag_structure |   mean_R_reconstruction_complexity |   mean_R_compression_proxy |   mean_R_displacement_proxy |
|:----------------------------------|:------------------|---------:|------------------:|--------------------:|-------------:|-------------:|-------------:|--------------:|-----------------:|------------------------:|----------------------:|------------------------:|-----------------------------------:|---------------------------:|----------------------------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |          0.516676 |            0.470603 |    0.213949  |   0.115075   |   0.0252687  |   0.00295481  |       0.00813852 |              0.964194   |              0.616848 |               0.0567111 |                           0.310797 |                 -0.921633  |                    0.79167  |
| cms_met_run2016g_collision        | MET               |   227443 |          0.421504 |            0.448913 |    0.16642   |   0.0825833  |   0.0161447  |   0.0014641   |       0.579796   |             -0.00844091 |              0.014534 |               0.116725  |                           0.146435 |                  0.526864  |                    0.114222 |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |         -0.430712 |           -0.49189  |    0.0227496 |   0.00945891 |   0.00149274 |   0.000126354 |      -0.389844   |             -0.272428   |             -0.18761  |              -0.0955053 |                          -0.1875   |                 -0.0863255 |                   -0.304652 |