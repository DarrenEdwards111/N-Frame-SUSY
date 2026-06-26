# Full Real-Only Scale-Up Audit

Date: 2026-06-08

## What Already Worked

The previous real-only CMSSW extraction successfully processed 150,000 real CMS collision events: 50,000 each from MET, JetHT and SingleMuon Run2016G. It extracted event IDs, MET, HT, jets, leptons, b-tags, vertices, packed candidates and secondary vertices.

## Existing Processed Files

- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_large\real_only_cmssw_event_features_combined.csv`: exists
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_large\real_only_cmssw_event_features_scored.csv`: exists
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_large\real_only_cmssw_event_features_with_unsupervised_boundary.csv`: exists

## Existing Event Counts

| sample_id                         |   events |
|:----------------------------------|---------:|
| cms_jetht_run2016g_collision      |    50000 |
| cms_met_run2016g_collision        |    50000 |
| cms_singlemuon_run2016g_collision |    50000 |

## Variables Available

| column                        |
|:------------------------------|
| sample_id                     |
| primary_dataset               |
| record_id                     |
| event_index                   |
| source_file                   |
| run                           |
| lumi                          |
| event                         |
| MET_pt                        |
| MET_phi                       |
| N_jets_all                    |
| N_jets_30                     |
| N_jets_50                     |
| HT                            |
| jet_pt_sum                    |
| leading_jet_pt                |
| subleading_jet_pt             |
| N_muons                       |
| N_electrons                   |
| N_leptons                     |
| lepton_pt_sum                 |
| N_btags_loose                 |
| N_btags_medium                |
| N_btags_tight                 |
| max_btag_discriminator        |
| N_primary_vertices            |
| packed_candidate_count        |
| secondary_vertex_count        |
| btag_discriminator_status     |
| vertex_status                 |
| packed_candidate_status       |
| secondary_vertex_status       |
| is_real_collision             |
| is_simulated                  |
| include_in_real_only_analysis |
| N_jets                        |
| extraction_limitations        |

## Source File Status

`source_file` exists but is not usable for stability: every row contains the same placeholder value from the earlier sample-level extraction. Exact file-level provenance therefore must be fixed before making file-stability claims.

## Full Processing Readiness

Full processing can safely continue after the file-by-file provenance test succeeds. Current file manifest contains 9 real ROOT files:

| sample_id                         | primary_dataset   |   record_id |   source_file_index | source_file                               |   size_gib |
|:----------------------------------|:------------------|------------:|--------------------:|:------------------------------------------|-----------:|
| cms_met_run2016g_collision        | MET               |       30509 |                   0 | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |   3.0574   |
| cms_met_run2016g_collision        | MET               |       30509 |                   1 | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |   3.64066  |
| cms_met_run2016g_collision        | MET               |       30509 |                   2 | 0E1A8650-EA73-264D-8BA5-92902470681F.root |   0.769154 |
| cms_jetht_run2016g_collision      | JetHT             |       30508 |                   0 | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |   2.09686  |
| cms_jetht_run2016g_collision      | JetHT             |       30508 |                   1 | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |   1.22226  |
| cms_jetht_run2016g_collision      | JetHT             |       30508 |                   2 | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |   0.114814 |
| cms_jetht_run2016g_collision      | JetHT             |       30508 |                   3 | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |   2.42286  |
| cms_singlemuon_run2016g_collision | SingleMuon        |       30513 |                   0 | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root |   3.90245  |
| cms_singlemuon_run2016g_collision | SingleMuon        |       30513 |                   1 | 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root |   3.56271  |

No simulated samples are included in this manifest.
