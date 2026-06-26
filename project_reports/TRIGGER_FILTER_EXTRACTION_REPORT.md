# Trigger/Filter Extraction Report

Date: 2026-06-08

Status: **success**

## Notes

- Event-content probe found TriggerResults in HLT, RECO and PAT.
- Extracted trigger/filter summary columns: HLT_MET_paths_any, HLT_HT_paths_any, HLT_Mu_paths_any, HLT_Ele_paths_any, pass_HBHENoiseFilter, pass_HBHENoiseIsoFilter, pass_goodVertices, pass_EcalDeadCellTriggerPrimitiveFilter, pass_BadPFMuonFilter, pass_globalSuperTightHalo2016Filter, trigger_filter_extraction_status

## Summary

| column                                  |   mean_or_pass_fraction |   non_null |
|:----------------------------------------|------------------------:|-----------:|
| HLT_MET_paths_any                       |               0.371     |       3000 |
| HLT_HT_paths_any                        |               0.513333  |       3000 |
| HLT_Mu_paths_any                        |               0.569333  |       3000 |
| HLT_Ele_paths_any                       |               0.0563333 |       3000 |
| pass_HBHENoiseFilter                    |               0.886667  |       3000 |
| pass_HBHENoiseIsoFilter                 |               0.98      |       3000 |
| pass_goodVertices                       |               0.999333  |       3000 |
| pass_EcalDeadCellTriggerPrimitiveFilter |               1         |       3000 |
| pass_BadPFMuonFilter                    |               1         |       3000 |
| pass_globalSuperTightHalo2016Filter     |               0.962     |       3000 |
| trigger_filter_extraction_status        |               1         |       3000 |

## Limitation

The current extraction records broad trigger categories and common filter-name pass flags where names are available in TriggerResults. It does not write the full fired HLT path-name list per event.