# Source File Provenance Implementation

Date: 2026-06-08

The current C++ analyser does not directly write the input ROOT file name per event. To make provenance exact, extraction is now run one ROOT file at a time using `NFRAME_INPUT_FILES`.

After each file is extracted, the runner injects these metadata columns into every row before saving the per-file CSV:

- `sample_id`
- `primary_dataset`
- `record_id`
- `source_file`
- `source_file_stem`
- `source_file_index`
- `local_input_path_or_container_path`
- `event_index_within_file`
- `event_index_global_within_sample`

This gives exact per-event source-file provenance without relying on CMSSW internals to expose the file name.

Manifest: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\real_only_file_by_file_manifest.csv`

Files prepared:

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