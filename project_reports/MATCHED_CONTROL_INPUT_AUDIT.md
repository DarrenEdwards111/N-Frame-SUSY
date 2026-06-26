# Matched Control Input Audit

Date: 2026-06-08

This audit checks the full real CMS collision trigger/filter-scored table before matched-control analysis. No simulated samples are used.

Input: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_trigger_filter_full\real_only_full_event_features_with_trigger_filter_scored.csv`

## Audit

| check                                                     | value                                                                                                                                                                                       | status   |
|:----------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| input_exists                                              | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_trigger_filter_full\real_only_full_event_features_with_trigger_filter_scored.csv | pass     |
| total_rows                                                | 665902                                                                                                                                                                                      | pass     |
| simulated_rows                                            | 0                                                                                                                                                                                           | pass     |
| unique_source_files                                       | 9                                                                                                                                                                                           | pass     |
| unique_runs                                               | 21                                                                                                                                                                                          | pass     |
| duplicate_source_run_lumi_event_rows                      | 0                                                                                                                                                                                           | pass     |
| column:sample_id                                          | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:primary_dataset                                    | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:source_file                                        | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:source_file_stem                                   | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:source_file_index                                  | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:run                                                | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:lumi                                               | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:event                                              | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:MET_pt                                             | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:HT                                                 | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:N_jets_30                                          | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:N_jets_50                                          | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:N_leptons                                          | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:N_btags_medium                                     | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:max_btag_discriminator                             | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:N_primary_vertices                                 | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:packed_candidate_count                             | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:secondary_vertex_count                             | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:B_boundary_hand_defined_z                          | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:real_only_unsupervised_boundary_score              | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:HLT_MET_paths_any                                  | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:HLT_HT_paths_any                                   | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:HLT_Mu_paths_any                                   | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:HLT_Ele_paths_any                                  | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:pass_HBHENoiseFilter                               | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:pass_HBHENoiseIsoFilter                            | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:pass_goodVertices                                  | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:pass_EcalDeadCellTriggerPrimitiveFilter            | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:pass_BadPFMuonFilter                               | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| column:pass_globalSuperTightHalo2016Filter                | present=True; missing_fraction=0                                                                                                                                                            | pass     |
| HLT_MET_paths_any_non_null_fraction                       | 1.0                                                                                                                                                                                         | pass     |
| HLT_HT_paths_any_non_null_fraction                        | 1.0                                                                                                                                                                                         | pass     |
| HLT_Mu_paths_any_non_null_fraction                        | 1.0                                                                                                                                                                                         | pass     |
| HLT_Ele_paths_any_non_null_fraction                       | 1.0                                                                                                                                                                                         | pass     |
| pass_HBHENoiseFilter_non_null_fraction                    | 1.0                                                                                                                                                                                         | pass     |
| pass_HBHENoiseIsoFilter_non_null_fraction                 | 1.0                                                                                                                                                                                         | pass     |
| pass_goodVertices_non_null_fraction                       | 1.0                                                                                                                                                                                         | pass     |
| pass_EcalDeadCellTriggerPrimitiveFilter_non_null_fraction | 1.0                                                                                                                                                                                         | pass     |
| pass_BadPFMuonFilter_non_null_fraction                    | 1.0                                                                                                                                                                                         | pass     |
| pass_globalSuperTightHalo2016Filter_non_null_fraction     | 1.0                                                                                                                                                                                         | pass     |

## Samples

| sample_id                         | primary_dataset   |   events |   files |   runs |
|:----------------------------------|:------------------|---------:|--------:|-------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |       4 |     12 |
| cms_met_run2016g_collision        | MET               |   227443 |       3 |      4 |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |       2 |      6 |

## Note

The requested `real_only_unsupervised_boundary_score` is provided as an alias of the actual scored column `trigger_filter_unsupervised_boundary_score`.