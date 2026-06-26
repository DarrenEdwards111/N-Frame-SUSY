# Project Chronology and Findings

## Stage A: Initial N-Frame feature and topology work

Initial work extracted real CMS events and constructed fitted N-Frame components. Independent Run2016G/Run2016H MiniAOD work showed that reconstruction/displacement-like features could be extracted and that high boundary-score tails differed by dataset. This was a methodological observation, not a particle claim.

## Stage B: Exploratory boundary and SUSY-shape scans

Multiple fitted-score, BNF, OPQ, dynamic-boundary and benchmark studies were run. Some early result tables had large Z values. Subsequent audits found that several relied on score/rank boundaries recomputed inside individual samples, post-hoc region selection, incomplete backgrounds or ordinary event-level random splits. Those results are retained for provenance but invalidated for inference.

## Stage C: Data-quality and trigger work

Quality-filter work showed that unclean tails can collapse after CMS-style filters, especially in 2015. Exact trigger-path extraction established approximate MET and JetHT plateaus in a limited Run2016G sample. The SingleMuon exact trigger union remains incomplete. These outputs establish that detector/reconstruction state matters and must be controlled.

## Stage D: SM normalisation and control-transfer attempts

Exact `GenFilterInfo` sums were completed for W3Jets record 69548 and TT-associated records 68072/68082. QCD/diboson scanning is resumable and underway. However, the complete background model is still unavailable because current Z-to-neutrinos and inclusive-top records are partial or metadata-tier only. Fixed-reference and stream-transfer tests failed to close controls, so no MET residual could be interpreted as new physics.

## Stage E: Corrected independent tests

The Run2016G reference and Run2016H holdout data-driven pyhf prototype removed the earlier high MET claim, returning `Z = 0.77`. It is a useful null cross-era shape comparison, but not a complete SM likelihood. A grouped source-record benchmark test likewise weakened early large predictive Z values to a weak-but-positive generalisation signal (`Z = 1.55`).
