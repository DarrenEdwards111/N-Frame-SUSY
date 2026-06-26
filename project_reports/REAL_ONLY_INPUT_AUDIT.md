# Real-Only Input Audit

Date: 2026-06-08

## Scope

Input root: `D:\cern_open_data\nframe_stage2_real_collision_20gb`

This audit isolates the real CMS collision MiniAOD inputs for the real-data-only N-Frame boundary analysis.

## Folder Check

Expected folders:

- `cms_met_run2016g_collision` record 30509
- `cms_jetht_run2016g_collision` record 30508
- `cms_singlemuon_run2016g_collision` record 30513

Observed folders:

- `cms_jetht_run2016g_collision`
- `cms_met_run2016g_collision`
- `cms_singlemuon_run2016g_collision`

Unexpected folders: none

## Manifest Summary

- Files included: 9
- Total size: 20.789 GiB
- Simulated samples included: 0

| sample_id                         | primary_dataset   |   record_id |   files |   size_gib |
|:----------------------------------|:------------------|------------:|--------:|-----------:|
| cms_jetht_run2016g_collision      | JetHT             |       30508 |       4 |    5.8568  |
| cms_met_run2016g_collision        | MET               |       30509 |       3 |    7.46721 |
| cms_singlemuon_run2016g_collision | SingleMuon        |       30513 |       2 |    7.46516 |

## Decision

Only real CMS Run2016G collision files are included in the main analysis. Simulated samples, signal labels, and simulated record IDs 63465/64906 are excluded.

Manifest: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\real_only_cmssw_manifest.csv`
