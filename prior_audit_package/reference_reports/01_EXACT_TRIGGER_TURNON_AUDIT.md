# Exact Trigger Turn-On Audit

## Plateau Summary

| primary_dataset   | trigger                       | offline_variable   |   first_observed_95pct_plateau_low_edge | has_95pct_plateau_in_5000_events   |
|:------------------|:------------------------------|:-------------------|----------------------------------------:|:-----------------------------------|
| MET               | HLT_MET_high_union            | MET_pt             |                                 200.461 | True                               |
| MET               | HLT_PFMET110_PFMHT110_IDTight | MET_pt             |                                 nan     | False                              |
| JetHT             | HLT_PFHT800                   | HT                 |                                 900.097 | True                               |
| JetHT             | HLT_PFHT900                   | HT                 |                                1000.07  | True                               |
| SingleMuon        | HLT_SingleMuon_high_union     | leading_muon_pt    |                                 nan     | False                              |
| SingleMuon        | HLT_IsoMu24                   | leading_muon_pt    |                                 nan     | False                              |
| SingleMuon        | HLT_IsoTkMu24                 | leading_muon_pt    |                                 nan     | False                              |
| SingleMuon        | HLT_Mu50                      | leading_muon_pt    |                                 nan     | False                              |

## Interpretation

The sampled primary datasets are trigger-stream unions. A path can only define
a common offline plateau if its observed efficiency reaches a stable high value
in the relevant offline variable. Missing plateaus mean the current exact path
set is incomplete and must be expanded before stream-matched MC transfer can
be considered resolved.
