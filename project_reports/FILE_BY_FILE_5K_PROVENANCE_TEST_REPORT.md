# File-By-File 5k Provenance Test Report

Date: 2026-06-08

## Result

Status: **passed**

The provenance test used one real ROOT file each from MET, JetHT and SingleMuon, capped at 5,000 events per file. No simulated samples were used.

## Event Counts

| sample_id                         | primary_dataset   | source_file                               |   events |
|:----------------------------------|:------------------|:------------------------------------------|---------:|
| cms_jetht_run2016g_collision      | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |     5000 |
| cms_met_run2016g_collision        | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |     5000 |
| cms_singlemuon_run2016g_collision | SingleMuon        | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root |     5000 |

## Validation Checks

| check                                  | pass   | value   |
|:---------------------------------------|:-------|:--------|
| rows                                   | True   | 15000   |
| source_file_populated                  | True   | 3       |
| event_ids_populated                    | True   |         |
| no_simulated_sample_labels             | True   |         |
| has_sample_id                          | True   |         |
| has_primary_dataset                    | True   |         |
| has_record_id                          | True   |         |
| has_source_file                        | True   |         |
| has_source_file_stem                   | True   |         |
| has_source_file_index                  | True   |         |
| has_local_input_path_or_container_path | True   |         |
| has_run                                | True   |         |
| has_lumi                               | True   |         |
| has_event                              | True   |         |
| has_event_index_within_file            | True   |         |
| has_event_index_global_within_sample   | True   |         |
| has_MET_pt                             | True   |         |
| has_HT                                 | True   |         |
| has_N_jets_30                          | True   |         |
| has_N_jets_50                          | True   |         |
| has_N_leptons                          | True   |         |
| has_N_btags_medium                     | True   |         |
| has_max_btag_discriminator             | True   |         |
| has_N_primary_vertices                 | True   |         |
| has_packed_candidate_count             | True   |         |
| has_secondary_vertex_count             | True   |         |
| boundary_scoring_works                 | True   | 0.0     |

## Decision

The test succeeded. `source_file`, `source_file_stem`, `source_file_index`, local/container path and per-file/global event indexes are populated per row. Full real-only file-by-file extraction can proceed.

Combined test output: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_file_by_file_test\real_only_file_by_file_test_combined.csv`
