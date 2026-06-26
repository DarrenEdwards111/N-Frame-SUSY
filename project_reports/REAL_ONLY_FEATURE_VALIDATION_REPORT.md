# Real-Only Feature Validation Report

Date: 2026-06-08

Input: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_large\real_only_cmssw_event_features_combined.csv`

## Event Counts

| sample_id                         |   events |
|:----------------------------------|---------:|
| cms_jetht_run2016g_collision      |    50000 |
| cms_met_run2016g_collision        |    50000 |
| cms_singlemuon_run2016g_collision |    50000 |

## Validation Checks

| check                        | status   |   value | notes                                                                                                      |
|:-----------------------------|:---------|--------:|:-----------------------------------------------------------------------------------------------------------|
| total_events                 | pass     |  150000 |                                                                                                            |
| events_by_sample             | pass     |   50000 | cms_jetht_run2016g_collision                                                                               |
| events_by_sample             | pass     |   50000 | cms_met_run2016g_collision                                                                                 |
| events_by_sample             | pass     |   50000 | cms_singlemuon_run2016g_collision                                                                          |
| no_simulated_labels          | pass     |       0 | Checked sample identity fields only; numeric event IDs can coincidentally contain excluded record numbers. |
| duplicate_run_lumi_event     | pass     |       0 | Duplicates may indicate overlap between primary datasets if non-zero.                                      |
| range_MET_pt                 | pass     |       0 | Expected MET_pt >= 0.                                                                                      |
| range_HT                     | pass     |       0 | Expected HT >= 0.                                                                                          |
| range_N_jets                 | pass     |       0 | Expected N_jets >= 0.                                                                                      |
| range_N_jets_30              | pass     |       0 | Expected N_jets_30 >= 0.                                                                                   |
| range_N_jets_50              | pass     |       0 | Expected N_jets_50 >= 0.                                                                                   |
| range_N_muons                | pass     |       0 | Expected N_muons >= 0.                                                                                     |
| range_N_electrons            | pass     |       0 | Expected N_electrons >= 0.                                                                                 |
| range_N_leptons              | pass     |       0 | Expected N_leptons >= 0.                                                                                   |
| range_N_btags_loose          | pass     |       0 | Expected N_btags_loose >= 0.                                                                               |
| range_N_btags_medium         | pass     |       0 | Expected N_btags_medium >= 0.                                                                              |
| range_N_btags_tight          | pass     |       0 | Expected N_btags_tight >= 0.                                                                               |
| range_N_primary_vertices     | pass     |       0 | Expected N_primary_vertices >= 0.                                                                          |
| range_packed_candidate_count | pass     |       0 | Expected packed_candidate_count >= 0.                                                                      |
| range_secondary_vertex_count | pass     |       0 | Expected secondary_vertex_count >= 0.                                                                      |

## Missingness

Full missingness table written to `results/tables/real_only_cmssw_missingness_summary.csv`.

## Notes

No simulated samples are used in this validation. Extreme values are flagged in a separate table, not removed.