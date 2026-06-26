# Top Boundary Event Inspection Audit

Date: 2026-06-08

## Files Found

| path                                                                                                                                                                                            | exists   |   size_mb |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|----------:|
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_full_file_by_file\real_only_full_cmssw_event_features_scored.csv                     | True     |   832.112 |
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_full_file_by_file\real_only_full_cmssw_event_features_with_unsupervised_boundary.csv | True     |   978.42  |
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\real_only_full_top_1000_hand_boundary_events.csv                                                     | True     |     1.427 |
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\reports\UPDATE_TO_DARREN_FULL_REAL_ONLY_BOUNDARY.md                                                                 | True     |     0.003 |
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\reports\REAL_ONLY_FULL_BOUNDARY_SYNTHESIS_FOR_NFRAME.md                                                             | True     |     0.008 |
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\reports\REAL_ONLY_FULL_FILE_STABILITY_REPORT.md                                                                     | True     |     0.01  |
| D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\reports\REAL_ONLY_FULL_NEXT_STEP_DECISION.md                                                                        | True     |     0.002 |

## Most Complete Dataset

The most complete scored dataset is:

`D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_full_file_by_file\real_only_full_cmssw_event_features_with_unsupervised_boundary.csv`

It includes both `B_boundary_hand_defined_z` and `real_only_full_unsupervised_boundary_score`, exact source-file provenance, event IDs, N-Frame hand-defined components and unsupervised boundary axes.

## Event Counts

| sample_id                         |   events |
|:----------------------------------|---------:|
| cms_jetht_run2016g_collision      |    98145 |
| cms_met_run2016g_collision        |   227443 |
| cms_singlemuon_run2016g_collision |   340314 |

Total events: 665,902

## Available Columns

| column                                     |
|:-------------------------------------------|
| sample_id                                  |
| primary_dataset                            |
| record_id                                  |
| source_file                                |
| source_file_stem                           |
| source_file_index                          |
| local_input_path_or_container_path         |
| event_index_within_file                    |
| event_index_global_within_sample           |
| run                                        |
| lumi                                       |
| event                                      |
| MET_pt                                     |
| MET_phi                                    |
| N_jets_all                                 |
| N_jets_30                                  |
| N_jets_50                                  |
| HT                                         |
| jet_pt_sum                                 |
| leading_jet_pt                             |
| subleading_jet_pt                          |
| N_muons                                    |
| N_electrons                                |
| N_leptons                                  |
| lepton_pt_sum                              |
| N_btags_loose                              |
| N_btags_medium                             |
| N_btags_tight                              |
| max_btag_discriminator                     |
| N_primary_vertices                         |
| packed_candidate_count                     |
| secondary_vertex_count                     |
| btag_discriminator_status                  |
| vertex_status                              |
| packed_candidate_status                    |
| secondary_vertex_status                    |
| is_real_collision                          |
| is_simulated                               |
| include_in_real_only_analysis              |
| N_jets                                     |
| extraction_limitations                     |
| log1p_MET_pt                               |
| log1p_HT                                   |
| log1p_leading_jet_pt                       |
| log1p_subleading_jet_pt                    |
| compression_proxy_raw                      |
| displacement_proxy_raw                     |
| MET_z                                      |
| HT_z                                       |
| leading_jet_z                              |
| subleading_jet_z                           |
| N_jets_30_z                                |
| N_jets_50_z                                |
| N_leptons_z                                |
| N_objects_z                                |
| N_btags_loose_z                            |
| N_btags_medium_z                           |
| N_btags_tight_z                            |
| max_btag_discriminator_z                   |
| N_primary_vertices_z                       |
| packed_candidate_count_z                   |
| secondary_vertex_count_z                   |
| compression_proxy_z                        |
| displacement_proxy_z                       |
| R_missing                                  |
| R_visible_energy                           |
| R_multiplicity                             |
| R_btag_structure                           |
| R_reconstruction_complexity                |
| R_compression_proxy                        |
| R_displacement_proxy                       |
| available_component_count                  |
| B_boundary_hand_defined                    |
| B_boundary_hand_defined_z                  |
| scoring_limitations                        |
| real_boundary_top_50                       |
| real_boundary_top_25                       |
| real_boundary_top_10                       |
| real_boundary_top_05                       |
| real_boundary_top_01                       |
| real_boundary_top_001                      |
| real_only_full_pca_axis_1                  |
| real_only_full_pca_axis_2                  |
| real_only_full_pca_axis_3                  |
| real_only_full_pca_axis_4                  |
| real_only_full_pca_axis_5                  |
| real_only_full_factor_axis_1               |
| real_only_full_factor_axis_2               |
| real_only_full_factor_axis_3               |
| real_only_full_isolation_anomaly_score_raw |
| real_only_full_isolation_anomaly_score_z   |
| real_only_full_unsupervised_boundary_score |
| real_only_full_unsup_top_10                |
| real_only_full_unsup_top_05                |
| real_only_full_unsup_top_01                |
| real_only_full_unsup_top_001               |
| real_only_full_kmeans_cluster              |

## Trigger/Filter Variables

Detected trigger/filter-like columns: none.

Named HLT/event-quality filter information is therefore not yet present in the full scored table.

## Event IDs And Source Provenance

Run/lumi/event IDs are present. `source_file` is usable and has 9 unique real ROOT files.

## Existing Top-1000 Tables

Existing top-1000 hand-boundary table status: present. This task will rebuild all top tables from the most complete full scored dataset so the top-event inspection is internally consistent.
