# Trigger/Filter Boundary Rescoring Report

Date: 2026-06-08

The boundary scores were recomputed on the full real CMS collision table with trigger/filter diagnostics present. Trigger/filter flags were not used as score inputs; they are reserved for later interpretation.

## Sample Summary

| sample_id                         | primary_dataset   |   events |   mean_boundary_z |   top05_frac |   mean_unsup_boundary |   unsup_top05_frac |
|:----------------------------------|:------------------|---------:|------------------:|-------------:|----------------------:|-------------------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |          0.516676 |   0.115075   |              0.659846 |          0.122125  |
| cms_met_run2016g_collision        | MET               |   227443 |          0.421504 |   0.0825833  |              0.223435 |          0.0647195 |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |         -0.430712 |   0.00945891 |             -0.339626 |          0.0193645 |

## Boundary Components

| component                   | available_inputs                                                                                                |   missing_fraction |
|:----------------------------|:----------------------------------------------------------------------------------------------------------------|-------------------:|
| R_missing                   | MET_z                                                                                                           |                  0 |
| R_visible_energy            | HT_z;leading_jet_z;subleading_jet_z                                                                             |                  0 |
| R_multiplicity              | N_jets_30_z;N_jets_50_z;N_leptons_z;N_objects_z;packed_candidate_count_z                                        |                  0 |
| R_btag_structure            | N_btags_loose_z;N_btags_medium_z;N_btags_tight_z;max_btag_discriminator_z                                       |                  0 |
| R_reconstruction_complexity | N_primary_vertices_z;packed_candidate_count_z;secondary_vertex_count_z;N_objects_z;N_leptons_z;N_btags_medium_z |                  0 |
| R_compression_proxy         | compression_proxy_z                                                                                             |                  0 |
| R_displacement_proxy        | displacement_proxy_z                                                                                            |                  0 |