# Real-Only CMSSW Extraction Report

Date: 2026-06-08

## Scope

This extraction used only real CMS Run2016G collision MiniAOD files from records 30509, 30508 and 30513. No simulated samples were processed.

## Extraction Size

- MET: 50,000 events
- JetHT: 50,000 events
- SingleMuon: 50,000 events
- Total real events: 150,000

The planned 50,000-event intermediate target ran successfully for all three real samples, so there was no need to stop at 20,000.

## Variables Extracted

Core event variables are present: run/lumi/event IDs, MET, HT, jet counts, leading/subleading jet pT, muon/electron/lepton counts, b-tag counts, max b-tag discriminator, primary-vertex count, packed-candidate count and secondary-vertex count.

The exact source ROOT file is not written per event by the current CMSSW analyzer. It is tracked at sample/log/manifest level. This is sufficient for the current real-only boundary analysis, but exact per-event file provenance should be added before a publication-grade follow-up.

## Outputs

- Combined event table: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_real_only_large\real_only_cmssw_event_features_combined.csv`
- Extraction summary: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\real_only_cmssw_extraction_summary.csv`
- Variable availability: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\real_only_cmssw_extracted_variable_availability.csv`
- Logs: `results/logs/real_only_cmssw_extract_MET.log`, `real_only_cmssw_extract_JetHT.log`, `real_only_cmssw_extract_SingleMuon.log`
