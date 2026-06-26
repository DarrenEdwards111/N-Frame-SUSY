# Goal Description

The goal is to build a mathematically sound "secondary stream of evidence." Since we cannot retune the primary `OPQ` score without violating statistical integrity (p-hacking), we will establish a completely separate, parallel analysis stream. This stream will be explicitly designed around "reduced-feature" datasets that lack modern MiniAOD packed candidates (like 2012 AOD, NanoAOD, and ATLAS open data flat ntuples). 

## User Review Required

> [!WARNING]
> This secondary stream of evidence will be conceptually separate from the primary $7.76\sigma$ CMS MiniAOD claim. It serves to prove that the boundary stress principle holds across different detectors and formats, even if the absolute significance is lower due to reduced feature fidelity.

## Open Questions

> [!IMPORTANT]
> The ATLAS Open Data utilizes a 1-lepton preselected channel, which differs from the CMS purely inclusive/MET triggers used so far. Are you comfortable with the ATLAS analogue test being restricted to the 1-lepton topology?
> The NanoAOD download script (`53c`) targets about 500MB of data. Should we proceed with downloading this independent slice to your local machine?

## Proposed Changes

### Phase 1: Independent NanoAOD Validation
We will extract the alternative CMS NanoAOD format data, which mimics the reduced-feature environment of the 2012 AOD data.
- Run `53c_download_and_extract_independent_nanoaod_validation.py` to pull the independent Run2016H NanoAOD slice.
- Test how the current boundary rules behave when stripped of secondary-vertex data.

### Phase 2: ATLAS Open Data Analogue
We will run an equivalent boundary trace test on completely independent detector data from ATLAS.
- Run `178_atlas_open_data_q99_analogue.py`. This script downloads the ATLAS 13 TeV Open Data (1-lepton channel) and its corresponding Standard Model MC. It fits an analogue of the missing-vs-visible residual score.
- Run `180_atlas_score_variant_scan.py` to scan through reduced-feature variants on the ATLAS data. This will tell us if a "reduced OPQ" formula natively emerges in an independent detector.

## Verification Plan

### Automated Tests
- Verify the ATLAS control regions (0 jets, 3-4 jets, 5+ jets) remain closed or behave as expected under the analogue boundary score.
- Check if the signal region (1-2 jets) shows a positive Q99 tail trace in both NanoAOD and ATLAS formats.

### Manual Verification
- Review the generated reports (`01_ATLAS_OPEN_DATA_Q99_ANALOGUE_REPORT.md` and the NanoAOD summaries) to ensure the secondary stream of evidence is coherent before we synthesize it into the final manuscript.
