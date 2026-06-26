# Full Trigger/Filter Analyser Audit

Date: 2026-06-08

## Patched Files

- Analyser: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction\NFrame\NFrameMiniAOD\plugins\NFrameMiniAODAnalyzer.cc`
- CMSSW config: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction\NFrame\NFrameMiniAOD\python\run_nframe_miniAOD_cfg.py`

## Trigger/Filter Columns Extracted

The patched analyser reads `edm::TriggerResults` from three MiniAOD processes:

- `TriggerResults::HLT`
- `TriggerResults::RECO`
- `TriggerResults::PAT`

It writes these event-level columns:

- `HLT_MET_paths_any`
- `HLT_HT_paths_any`
- `HLT_Mu_paths_any`
- `HLT_Ele_paths_any`
- `pass_HBHENoiseFilter`
- `pass_HBHENoiseIsoFilter`
- `pass_goodVertices`
- `pass_EcalDeadCellTriggerPrimitiveFilter`
- `pass_BadPFMuonFilter`
- `pass_globalSuperTightHalo2016Filter`
- `trigger_filter_extraction_status`

## Meaning

The HLT columns are broad category booleans. They are set when an accepted HLT path name contains broad tokens such as MET/PFMET, HT/PFHT, Mu/IsoMu, Ele/Photon.

The filter columns are event-level booleans for common CMS event-quality filter names where those names appear in TriggerResults. A value of `1` means a matching accepted filter bit was found. A value of `-1` means the named filter was not found as an accepted bit in the scanned TriggerResults collections. `trigger_filter_extraction_status=1` means at least one TriggerResults collection was readable.

## Safety For Full Extraction

The patch is safe for full extraction because it adds read-only TriggerResults handles and simple boolean summaries. It does not change the existing physics variables or the boundary score inputs.

## Limitations

- The HLT columns are broad trigger categories, not exact path-name lists.
- The analyser does not write every fired HLT path name.
- Filter bits depend on the exact TriggerResults names present in the MiniAOD file.
- Trigger/filter fields are diagnostic variables only; they should not be included in the main N-Frame boundary score.
