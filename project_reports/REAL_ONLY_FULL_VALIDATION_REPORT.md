# Real-Only Full Validation Report

Date: 2026-06-08

Input: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_full_file_by_file\real_only_full_cmssw_event_features_with_source_file.csv`

## Validation Checks

| check                                    | pass   | value   |
|:-----------------------------------------|:-------|:--------|
| total_events                             | True   | 665902  |
| source_file_present_every_row            | True   | 0       |
| no_simulated_sample_labels               | True   |         |
| duplicate_run_lumi_event                 | True   | 0       |
| has_MET_pt                               | True   |         |
| has_HT                                   | True   |         |
| has_N_jets_30                            | True   |         |
| has_N_jets_50                            | True   |         |
| has_N_leptons                            | True   |         |
| has_N_btags_medium                       | True   |         |
| has_max_btag_discriminator               | True   |         |
| has_N_primary_vertices                   | True   |         |
| has_packed_candidate_count               | True   |         |
| has_secondary_vertex_count               | True   |         |
| range_MET_pt_nonnegative                 | True   | 0       |
| range_HT_nonnegative                     | True   | 0       |
| range_N_jets_30_nonnegative              | True   | 0       |
| range_N_jets_50_nonnegative              | True   | 0       |
| range_N_leptons_nonnegative              | True   | 0       |
| range_N_btags_medium_nonnegative         | True   | 0       |
| range_N_primary_vertices_nonnegative     | True   | 0       |
| range_packed_candidate_count_nonnegative | True   | 0       |
| range_secondary_vertex_count_nonnegative | True   | 0       |

## Events By Sample

| sample_id                         | primary_dataset   |   events |   files |
|:----------------------------------|:------------------|---------:|--------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |       4 |
| cms_met_run2016g_collision        | MET               |   227443 |       3 |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |       2 |

## Events By Source File

| sample_id                         | primary_dataset   | source_file                               |   source_file_index |   events |   first_global_index |   last_global_index |   source_missing |
|:----------------------------------|:------------------|:------------------------------------------|--------------------:|---------:|---------------------:|--------------------:|-----------------:|
| cms_jetht_run2016g_collision      | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |                   0 |    61353 |                    0 |               61352 |                0 |
| cms_jetht_run2016g_collision      | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |                   1 |    17433 |                61353 |               78785 |                0 |
| cms_jetht_run2016g_collision      | JetHT             | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |                   2 |     2937 |                78786 |               81722 |                0 |
| cms_jetht_run2016g_collision      | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |                   3 |    16422 |                81723 |               98144 |                0 |
| cms_met_run2016g_collision        | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |                   0 |    85149 |                    0 |               85148 |                0 |
| cms_met_run2016g_collision        | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |                   1 |   113601 |                85149 |              198749 |                0 |
| cms_met_run2016g_collision        | MET               | 0E1A8650-EA73-264D-8BA5-92902470681F.root |                   2 |    28693 |               198750 |              227442 |                0 |
| cms_singlemuon_run2016g_collision | SingleMuon        | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root |                   0 |   172994 |                    0 |              172993 |                0 |
| cms_singlemuon_run2016g_collision | SingleMuon        | 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root |                   1 |   167320 |               172994 |              340313 |                0 |

No simulated sample labels are present in sample identity fields. Exact `source_file` provenance is populated for every event.