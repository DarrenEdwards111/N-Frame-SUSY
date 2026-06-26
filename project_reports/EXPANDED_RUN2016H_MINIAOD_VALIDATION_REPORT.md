# Expanded Run2016H MiniAOD Validation Report

Date: 2026-06-09

## Checks

| check                            |   value | status   |
|:---------------------------------|--------:|:---------|
| total_events                     |  156975 | pass     |
| simulated_rows                   |       0 | pass     |
| source_files                     |       8 | pass     |
| runs                             |       8 | pass     |
| available:secondary_vertex_count |       1 | pass     |
| available:packed_candidate_count |       1 | pass     |
| available:MET_pt                 |       1 | pass     |
| available:HT                     |       1 | pass     |
| available:N_jets_30              |       1 | pass     |
| available:N_jets_50              |       1 | pass     |
| available:N_leptons              |       1 | pass     |
| available:N_btags_medium         |       1 | pass     |
| available:max_btag_discriminator |       1 | pass     |

## Events By Dataset

| primary_dataset   |   events |   files |   runs |   lumis |
|:------------------|---------:|--------:|-------:|--------:|
| JetHT             |    64120 |       3 |      3 |      25 |
| MET               |    40283 |       3 |      3 |      24 |
| SingleMuon        |    52572 |       2 |      2 |      12 |

## Events By File

| primary_dataset   | source_file                               |   events |   runs |
|:------------------|:------------------------------------------|---------:|-------:|
| JetHT             | 1BD17693-3DDC-FF45-B182-2DF67A370449.root |    26844 |      1 |
| JetHT             | CDDAB30D-6EA2-4F40-A648-674377A54D4D.root |    27582 |      1 |
| JetHT             | FC0EE8E8-8640-8649-B22A-F0C750DD5DE0.root |     9694 |      2 |
| MET               | 3F9003A7-A5F9-2840-B22E-8052CE346AF7.root |    13789 |      1 |
| MET               | 6D1DA38B-AEFA-3849-B346-3B2653B46C9E.root |    13376 |      1 |
| MET               | EC639C0B-5433-EF46-8E04-A9088379E5BE.root |    13118 |      1 |
| SingleMuon        | DA9B9166-C273-E54C-8957-7E54DACC6999.root |    26499 |      1 |
| SingleMuon        | E5768FBE-A1B2-F047-999D-0B5C0B051827.root |    26073 |      1 |

## Trigger/Filter Availability

| variable                                |   non_null_fraction |   mean_or_pass_fraction |
|:----------------------------------------|--------------------:|------------------------:|
| HLT_MET_paths_any                       |                   1 |               0.308176  |
| HLT_HT_paths_any                        |                   1 |               0.507469  |
| HLT_Mu_paths_any                        |                   1 |               0.529212  |
| HLT_Ele_paths_any                       |                   1 |               0.0417009 |
| pass_HBHENoiseFilter                    |                   1 |               0.920127  |
| pass_HBHENoiseIsoFilter                 |                   1 |               0.992164  |
| pass_goodVertices                       |                   1 |               0.999172  |
| pass_EcalDeadCellTriggerPrimitiveFilter |                   1 |               0.999388  |
| pass_BadPFMuonFilter                    |                   1 |               0.999847  |
| pass_globalSuperTightHalo2016Filter     |                   1 |               0.988457  |

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