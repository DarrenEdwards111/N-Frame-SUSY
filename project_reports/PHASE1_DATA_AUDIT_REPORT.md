# Phase 1 Data Audit Report

## Plain-English Summary

The real-data folder contains 9 ROOT files. The validated manifest contains 9 expected files, of which 9 validate cleanly.

Total validated size is 20.789 GiB. This satisfies Darren's request for at least 10 GB of real CERN/CMS data, and it is close to the intended 20 GB target while staying below 25 GB.

These files are real CMS Run2016G collision MiniAOD files from MET, JetHT, and SingleMuon primary datasets. They are not simulated signal samples. MiniAOD is not the lowest-level RAW detector readout, but it is real collision event-level CMS Open Data suitable for physics-style event extraction.

## Sample Coverage

- `cms_met_run2016g_collision`: 3/3 files present (MET, record 30509)
- `cms_jetht_run2016g_collision`: 4/4 files present (JetHT, record 30508)
- `cms_singlemuon_run2016g_collision`: 2/2 files present (SingleMuon, record 30513)

## Size By Sample

| sample_id | primary_dataset | record_id | sample_type | files | GiB |
|---|---|---:|---|---:|---:|
| `cms_jetht_run2016g_collision` | JetHT | 30508 | real_collision_JetHT | 4 | 5.857 |
| `cms_met_run2016g_collision` | MET | 30509 | real_collision_MET | 3 | 7.467 |
| `cms_singlemuon_run2016g_collision` | SingleMuon | 30513 | real_collision_SingleMuon | 2 | 7.465 |

## Validation Checks

- All expected ROOT files exist: yes
- File sizes approximately match the manifest: yes
- Simulated signal files mixed into this real-data folder: no
- MET, JetHT, and SingleMuon samples present: yes

## What Still Remains Technically Necessary

The next necessary step is event-level extraction. Python/uproot can inspect the ROOT files and may extract some MiniAOD branches, but MiniAOD is CMS EDM format rather than flat NanoAOD. For serious boundary-variable extraction, CMSSW is the correct route for MET, leptons, b-tags, trigger decisions, and reconstruction-quality variables.

## Source Inputs Read

- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_next_stage_package\REAL_COLLISION_DOWNLOAD_REPORT.md`
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_next_stage_package\real_collision_20gb_manifest.csv`
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\filelists_real_collision_20gb`
- `D:\cern_open_data\nframe_stage2_real_collision_20gb`
