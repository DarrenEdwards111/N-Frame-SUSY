# Publication-Grade Readiness Assessment

**Date:** 24 June 2026  
**Scope:** frozen OPQ CMS Open Data analysis, full-background likelihood readiness, and control closure.

## Direct conclusion

The project cannot yet support a breakthrough or discovery-style claim. It can be advanced substantially with the available infrastructure, but no legitimate workflow can guarantee that the JetHT and SingleMuon controls will close or that a final MET residual will remain significant. Those are empirical tests, not parameters to optimise.

## Work completed in this pass

Docker Desktop was restarted and the remote CMSSW `GenFilterInfo` workflow was verified. Ten additional full-online QCD MiniAODSIM files from record 63102 completed successfully with `status = 0`; their exact event totals and generator-weight sums were appended to:

- `outputs_remote_opq_sm_background_build/tables/16_exact_genfilter_sumweights_resumable.csv`
- `outputs_remote_opq_sm_background_build/tables/17_exact_hybrid_sm_normalisation_tiers.csv`

This validates the remote, resumable extraction route without downloading the input ROOT files locally.

## Current normalisation coverage

| Process family | Exact files complete | Planned full-online files | Final records | Status |
|---|---:|---:|---:|---|
| W+jets | 288 | 289 | 1 | one complete record |
| TT-associated | 91 | 93 | 2 | two complete records |
| QCD | 10 | 1,868 | 0 | scan started, incomplete |
| Diboson | 0 | 135 | 0 | not started |
| Z to neutrinos | 0 | 2 | 0 | only partial-online probe records in current manifest |
| Inclusive ttbar/top | 0 | 0 | 0 | no full-online exact target in current manifest |

The existing exact-only likelihood is therefore necessarily incomplete: it lacks a complete normalised Z-to-neutrinos and inclusive top component, both essential for a MET result.

## Why controls are not currently closed

The corrected fixed-reference and transfer analyses show that the MC mixture does not predict the controls:

- fixed-reference exact-only maximum control `Z = 2.29`;
- fixed-reference metadata-expanded maximum control `Z = 7.41`;
- process-mixture transfer control Z values `38.47`, `19.69`, `31.04` for Run2015D, Run2016H and fresh Run2016G;
- stream-matched plateau transfer control Z values `14.62`, `38.47`, `31.27`.

This cannot be fixed by changing a nuisance width or reweighting until it looks good. The likely causes must be separately tested: incomplete process coverage, generator normalisation, mismatched stream/trigger efficiency, object/quality definitions, and detector/reconstruction effects.

## What is feasible now

1. Continue the resumable QCD and diboson full-online sumweight scans. The current sequential rate is about 10 files in 14 minutes; completing the remaining 1,993 QCD/diboson files sequentially would take roughly two days of remote processing. It can be parallelised cautiously once per-file error and rate behaviour has been measured.
2. Complete the exact SingleMuon trigger-family extraction and derive fixed, documented plateaus for every stream.
3. Build the simultaneous pyhf/HistFactory workspace once the necessary record-level normalisations and matched selections exist. It must use fixed numerical OPQ boundaries, signed generator weights, certified luminosity, finite-MC uncertainties and correlated trigger/object/process nuisances.
4. Use MET as the blinded target only after JetHT and SingleMuon validation regions close in an era not used to construct the model.

## What requires additional inputs or access

1. **Complete Z-to-neutrinos and inclusive top MC records.** The current public manifest contains only partial-online probes for the required records. A publication-grade result needs either complete accessible UL16 record manifests plus all `sumGenWeights`, or collaboration/official metadata that gives the exact denominators for the released production.
2. **Full data/MC trigger and object corrections.** Broad trigger flags are insufficient. The analysis needs stream-specific efficiency scale factors or independently derived data efficiencies, with uncertainty correlations.
3. **Independent held-out validation.** NanoAOD and Run2012 AOD may provide separate reduced-feature studies, but they cannot be numerically combined with the MiniAOD test. A clean new-era dataset or an untouched file/run split remains necessary for a final test.

## Required decision rule

The study can move toward a publishable anomaly only if all of the following are predeclared and pass:

$$\begin{aligned}
N_{r,b}^{\mathrm{SM}} &= \mathcal{L}\sum_p \sigma_p\epsilon_{p,r,b}
\frac{\sum_{i\in p,r,b} w_i}{\sum_{i\in p}w_i},\\
\text{controls and validation bins} &\text{ agree with the profiled model},\\
\text{the held-out MET region} &\text{ is evaluated once with no score or region retuning.}
\end{aligned}$$

If the controls close and a held-out MET residual survives the complete nuisance model, that is meaningful evidence for an unexplained boundary-correlated residual. If controls remain open, the correct scientific result is that the current OPQ score/model does not isolate a new-physics residual from SM/detector effects.
