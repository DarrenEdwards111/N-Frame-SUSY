# Full Trigger/Filter Extraction Report

Date: 2026-06-08

This report covers the full real-data-only CMSSW extraction after enabling broad HLT category flags and event-quality filter flags. No simulated events were used.

Combined output: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_trigger_filter_full\real_only_full_event_features_with_trigger_filter.csv`

## Extraction Status

| sample_id                         | primary_dataset   | source_file                               | status   |   events_written |   returncode |
|:----------------------------------|:------------------|:------------------------------------------|:---------|-----------------:|-------------:|
| cms_jetht_run2016g_collision      | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | success  |            61353 |            0 |
| cms_jetht_run2016g_collision      | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | success  |            17433 |            0 |
| cms_jetht_run2016g_collision      | JetHT             | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root | success  |             2937 |            0 |
| cms_jetht_run2016g_collision      | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root | success  |            16422 |            0 |
| cms_met_run2016g_collision        | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root | success  |            85149 |            0 |
| cms_met_run2016g_collision        | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root | success  |           113601 |            0 |
| cms_met_run2016g_collision        | MET               | 0E1A8650-EA73-264D-8BA5-92902470681F.root | success  |            28693 |            0 |
| cms_singlemuon_run2016g_collision | SingleMuon        | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root | success  |           172994 |            0 |
| cms_singlemuon_run2016g_collision | SingleMuon        | 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root | success  |           167320 |            0 |

## Summary

| primary_dataset   | status   |   files |   events_written |
|:------------------|:---------|--------:|-----------------:|
| JetHT             | success  |       4 |            98145 |
| MET               | success  |       3 |           227443 |
| SingleMuon        | success  |       2 |           340314 |

## Result

All 9 source files completed successfully, producing 665,902 real CMS collision events with trigger/filter diagnostics.