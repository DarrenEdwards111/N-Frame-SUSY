# Run2016H MiniAOD Full Validation Report

Date: 2026-06-09

This validates independent real CMS Run2016H MiniAOD extraction outputs.

## Checks

| check                                          |   value | status   |
|:-----------------------------------------------|--------:|:---------|
| total_events                                   |   49143 | pass     |
| simulated_rows                                 |       0 | pass     |
| unique_files                                   |       3 | pass     |
| unique_runs                                    |       4 | pass     |
| duplicate_source_run_lumi_event                |       0 | pass     |
| key_component_available:secondary_vertex_count |       1 | pass     |
| key_component_available:packed_candidate_count |       1 | pass     |
| key_component_available:N_primary_vertices     |       1 | pass     |
| key_component_available:MET_pt                 |       1 | pass     |
| key_component_available:HT                     |       1 | pass     |
| key_component_available:N_jets_30              |       1 | pass     |
| key_component_available:N_jets_50              |       1 | pass     |
| key_component_available:N_leptons              |       1 | pass     |
| key_component_available:N_btags_medium         |       1 | pass     |
| key_component_available:max_btag_discriminator |       1 | pass     |

## Events By Sample

| sample_id                                        | primary_dataset   | source_file                               |   events |   runs |
|:-------------------------------------------------|:------------------|:------------------------------------------|---------:|-------:|
| validation_jetht_run2016h_miniaod_collision      | JetHT             | FC0EE8E8-8640-8649-B22A-F0C750DD5DE0.root |     9694 |      2 |
| validation_met_run2016h_miniaod_collision        | MET               | 6D1DA38B-AEFA-3849-B346-3B2653B46C9E.root |    13376 |      1 |
| validation_singlemuon_run2016h_miniaod_collision | SingleMuon        | E5768FBE-A1B2-F047-999D-0B5C0B051827.root |    26073 |      1 |

## Trigger/Filter Availability

| column                                  |   non_null_fraction |   mean_or_pass_fraction |
|:----------------------------------------|--------------------:|------------------------:|
| HLT_MET_paths_any                       |                   1 |               0.389822  |
| HLT_HT_paths_any                        |                   1 |               0.357955  |
| HLT_Mu_paths_any                        |                   1 |               0.734774  |
| HLT_Ele_paths_any                       |                   1 |               0.0335958 |
| pass_HBHENoiseFilter                    |                   1 |               0.931506  |
| pass_HBHENoiseIsoFilter                 |                   1 |               0.993814  |
| pass_goodVertices                       |                   1 |               0.99943   |
| pass_EcalDeadCellTriggerPrimitiveFilter |                   1 |               0.999512  |
| pass_BadPFMuonFilter                    |                   1 |               0.999837  |
| pass_globalSuperTightHalo2016Filter     |                   1 |               0.991047  |
| trigger_filter_extraction_status        |                   1 |               1         |

## Missingness

| column                                  |   missing_fraction |
|:----------------------------------------|-------------------:|
| sample_id                               |                  0 |
| primary_dataset                         |                  0 |
| record_id                               |                  0 |
| source_file                             |                  0 |
| source_file_stem                        |                  0 |
| source_file_index                       |                  0 |
| local_input_path_or_container_path      |                  0 |
| event_index_within_file                 |                  0 |
| event_index_global_within_sample        |                  0 |
| run                                     |                  0 |
| lumi                                    |                  0 |
| event                                   |                  0 |
| MET_pt                                  |                  0 |
| MET_phi                                 |                  0 |
| N_jets_all                              |                  0 |
| N_jets_30                               |                  0 |
| N_jets_50                               |                  0 |
| HT                                      |                  0 |
| jet_pt_sum                              |                  0 |
| leading_jet_pt                          |                  0 |
| subleading_jet_pt                       |                  0 |
| N_muons                                 |                  0 |
| N_electrons                             |                  0 |
| N_leptons                               |                  0 |
| lepton_pt_sum                           |                  0 |
| N_btags_loose                           |                  0 |
| N_btags_medium                          |                  0 |
| N_btags_tight                           |                  0 |
| max_btag_discriminator                  |                  0 |
| N_primary_vertices                      |                  0 |
| packed_candidate_count                  |                  0 |
| secondary_vertex_count                  |                  0 |
| btag_discriminator_status               |                  0 |
| vertex_status                           |                  0 |
| packed_candidate_status                 |                  0 |
| secondary_vertex_status                 |                  0 |
| HLT_MET_paths_any                       |                  0 |
| HLT_HT_paths_any                        |                  0 |
| HLT_Mu_paths_any                        |                  0 |
| HLT_Ele_paths_any                       |                  0 |
| pass_HBHENoiseFilter                    |                  0 |
| pass_HBHENoiseIsoFilter                 |                  0 |
| pass_goodVertices                       |                  0 |
| pass_EcalDeadCellTriggerPrimitiveFilter |                  0 |
| pass_BadPFMuonFilter                    |                  0 |
| pass_globalSuperTightHalo2016Filter     |                  0 |
| trigger_filter_extraction_status        |                  0 |
| is_real_collision                       |                  0 |
| is_simulated                            |                  0 |
| include_in_real_only_analysis           |                  0 |
| N_jets                                  |                  0 |
| validation_route                        |                  0 |
| extraction_limitations                  |                  0 |