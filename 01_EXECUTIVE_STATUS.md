# Executive Status

## Research question

The project explores whether N-Frame/tri-aspect boundary concepts can define measurable collider-event structure that is not captured by ordinary CMS kinematic summaries, and whether such structure can explain the absence of direct SUSY observations. The scientifically valid version is a falsifiable modelling problem, not a search for a high significance by score/cut iteration.

## What has been built

- CMSSW/Docker/XRootD extraction pipelines for CMS Open Data MiniAOD, AOD and selected NanoAOD files.
- Event-level N-Frame feature construction, including visible/missing, multiplicity, b-tag, reconstruction, packed-candidate and secondary-vertex proxies where the format provides them.
- Fitted N-Frame score variants, OPQ variants, tri-aspect dynamic models, trigger-aware tests and multiple independent validation extracts.
- Remote `GenFilterInfo` sumweight tooling for MC records, with resumable per-file output.
- pyhf prototypes, a data-driven cross-era test, and benchmark predictive-superiority tests.

## What remains true after audit

- Run2012C enhanced AOD mapping works technically but is weak (`shape Z = 0.78`), so it is not a replication.
- Independent Run2016H NanoAOD extraction exists, but only as reduced-feature input; no discovery conclusion follows.
- ATLAS analyses were exploratory and do not provide independent confirmation.
- The corrected data-driven Run2016G-reference / Run2016H-holdout MET comparison is compatible with the reference shape (`Z = 0.77` under that model).
- The grouped benchmark model test has a directional N-Frame advantage across five records, but only `Z = 1.55`, p = 0.061 at the source-record level.

## Current live computation

The remote exact-sumweight campaign is resumable. Its latest state and logs are in `key_outputs/outputs_remote_opq_sm_background_build/`. It has confirmed the workflow on additional QCD files, but is incomplete: full online QCD/diboson coverage is still being scanned and full Z-to-neutrinos/inclusive-top exact coverage is unavailable in the present public manifest.
