# N-Frame / CERN Boundary-Trace Handoff

## Audit of Gemini work, CMS normalisation claims, and independent-format checks

**Report date:** 23 June 2026  
**Audit scope:** `publication_evidence_package`, all scripts and outputs modified or used on 23 June, and the preceding corrected CMS likelihood/control-transfer outputs.

## Purpose of this report

This handoff records what was actually completed today, distinguishes verified outputs from claims that do not survive audit, and sets out the shortest defensible path toward a publishable result. It is deliberately conservative: a high numerical Z is only meaningful if the Standard Model prediction, event selection, nuisance model and control-region transfer have all been validated.

## Executive summary

- The project now has useful technical progress: an exact `GenFilterInfo` sumweight pass for W3Jets and two TT-associated records; an exact/metadata-hybrid normalisation ledger; an enhanced Run2012C AOD feature mapper; a newly extracted independent Run2016H NanoAOD slice; and a packaged archive of relevant outputs.
- The reported CMS `7.76 sigma` result is **not publication-grade discovery evidence**. Its script ranks the MC template into its own percentile bands, anchors that relative shape to the real-data 90-95% band, and then fits the result. This is a sideband shape comparison, not an absolute luminosity-weighted SM prediction in a fixed physical region.
- The strict `exact_completed_only` CMS model contains only W3Jets plus two TT-associated samples. It does not contain normalised Z-to-neutrinos, inclusive ttbar/top, QCD or diboson coverage, so it cannot represent the full MET background.
- A prior correction in the same workspace fixes reference thresholds and applies them unchanged. Under that non-tautological test, controls fail: exact-only control maximum `Z = 2.29`; including metadata-normalised records gives maximum `Z = 7.41`. Subsequent mixture and stream-matched transfer tests fail control closure in all three eras.
- Enhanced Run2012C AOD mapping works technically, but the frozen-score result is weak: shape `Z = 0.78`, shoulder `Z = 0.73`. It is a format-compatibility stress test, not replication.
- The Run2016H NanoAOD task extracted three real collision files successfully, but no reduced score, fixed validation test or statistical result was run. It is prepared input, not evidence yet.
- The ATLAS initial analogue did not replicate the CMS effect. The later `10.80 sigma` ATLAS value was selected after a four-variant scan on the same data. The selected 1-2 jet model has a severe 80-95% sideband mismatch (`observed/expected = 0.155`) and uses only five W/single-top MC samples, absolute MC weights, and no held-out test. It is exploratory diagnostic output, not an independent confirmation.

## Mathematical and statistical audit

The frozen CMS score recorded by the scripts is

$$B_{OPQ}=0.344828O+0.517241P-0.137931Q.$$

The claimed exact-hybrid likelihood uses a template fraction

$$r_b = \frac{N^{MC}_b}{N^{MC}_{90\text{--}95}},\qquad
\widehat N^{data}_b=N^{data}_{90\text{--}95}r_b.$$

However, `264_remote_opq_exact_hybrid_sm_sideband_likelihood_three_sample.py` defines the MC microband edges from the weighted MC quantiles themselves. The real-data vectors also come from rank microbands. Consequently, the likelihood primarily tests a relative rank-tail shape after anchoring, rather than predicting a yield in a fixed score interval. It is not the required model

$$N^{SM}_{r,b}=\mathcal L\sum_p\sigma_p\,\epsilon_{p,r,b}\,
\frac{\sum_{i\in p,r,b} w_i}{\sum_{i\in p}w_i},$$

with fixed numerical region boundaries, signed generator weights, complete SM processes and profiled correlated nuisance parameters.

The current script also removes all events with non-positive luminosity weights. That is not valid for NLO samples with negative generator weights because cancellations must be retained through the signed sum.

## Verified work completed today

### 1. CMS normalisation and archived likelihood outputs

The sumweight work is real and useful. Exact full-record `GenFilterInfo` totals are present for record 69548 (W3Jets) and records 68072 and 68082 (TT-associated). The normalisation table correctly labels these as final for those individual records. It does **not** make the complete SM prediction final.

The package README says it contains `1_exact_sm_normalisation`, but that folder is absent from the packaged directory. The canonical source remains `outputs_remote_opq_sm_background_build` in the main project.

### 2. Run2012C enhanced AOD mapper

The enhanced mapper adds AOD b-tag fallbacks and V0/secondary-vertex-like counts. The feature audit reports 60,000 rows, b-tag status available for all rows, medium b-tags nonzero in 14.245%, and secondary-vertex proxy nonzero in 92.142%.

This improved feature availability did not create a strong replication: `shape_Z = 0.7819` and `shoulder_Z = 0.7269`. The 2012 result must remain a reduced-format compatibility check and must not be Fisher-combined with MiniAOD evidence as if it were an equivalent independent measurement.

### 3. Independent Run2016H NanoAOD extraction

Three public UL2016 NanoAOD real-collision files were downloaded and extracted:

| Stream | Record | File size | Status |
|---|---:|---:|---|
| JetHT | 30558 | 407.9 MB | extracted |
| MET | 30559 | 94.4 MB | extracted |
| SingleMuon | 30563 | 14.7 MB | extracted |

The combined CSV is 223.4 MB. NanoAOD has no packed-candidate or equivalent MiniAOD secondary-vertex inputs used by the full score. No statistical validation was performed today, so this remains prepared data for a predeclared reduced-score test.

### 4. ATLAS public one-lepton exploratory checks

The direct ATLAS analogue underfluctuated (`Z = -0.75`), so it did not replicate the CMS result. A second script tested four variants: lepton-aware residual, jets-only residual, jet-count-only residual, and raw missing-energy Z.

The selected jet-count-only result reported `22` Q99 events against `1.84` after a same-data sideband correction, giving `Z = 10.80`. This number is not valid evidence because it is post-selection and because its own adjacent sideband is not modelled: the 80-95% observed/expected ratio is `0.1549`. The MC set in that scan includes only a single-top sample and four W-to-muon samples, excludes major one-lepton backgrounds, and replaces signed event weights with their absolute values.

## Critical comparison with the corrected CMS control tests

| Test | Result | Audit interpretation |
|---|---:|---|
| Historical rank-tail exact-hybrid likelihood | MET Fisher `Z = 7.76`; combined controls `Z = -0.25` | Not a discovery likelihood: self-ranked template bands and sideband anchoring make apparent closure non-diagnostic. |
| Fixed-reference CMS shape test, exact-only | MET Fisher `Z = 17.12`; control maximum `Z = 2.29` | Controls fail the stated `Z <= 2` criterion. |
| Fixed-reference CMS shape test, metadata-expanded | MET Fisher `Z = 25.00`; control maximum `Z = 7.41` | Strong control failure. |
| Control-mixture transfer | control Z: 38.47, 19.69, 31.04 for 2015D, 2016H, 2016G | MC process mixture does not predict controls. |
| Stream-matched plateau transfer | control Z: 14.62, 38.47, 31.27 | Even after basic plateau selections, controls do not close. |

## Breakthrough-readiness status

There is not currently a publishable breakthrough or a physics discovery claim. The defensible status is:

> A set of exploratory, repeatable high-tail patterns exists in several CMS Open Data streams under OPQ-style scores. The present Standard Model/control model does not yet close, so no residual can be identified as unexplained new physics or as evidence for hidden-sector/SUSY-like topology.

This does not erase the methodological lead. It identifies exactly what must improve: the background/trigger/reconstruction transfer model, rather than another coefficient scan.

## Exact continuation plan

1. Freeze a data-processing protocol before reading new signal-region results: certified JSON/luminosity, quality flags, object definitions, trigger plateaus, score formula and numerical score boundaries.
2. Build a complete, signed-weight UL2016 MC ledger for the same streams: Z-to-neutrinos, W+jets, inclusive ttbar and single top, diboson, QCD/multijet and relevant rare processes. For each record, calculate full `sumGenWeights`, use documented cross sections/filter efficiencies, and retain negative weights.
3. Apply matching offline selections to data and MC. Derive trigger efficiencies from independent tag-and-probe or published corrections; do not use broad trigger aggregates as an MC proxy.
4. Build one simultaneous HistFactory/pyhf model with MET signal region, JetHT and SingleMuon control regions, and 90-95%, 95-97%, 97-98%, 98-99% validation bins. Include correlated luminosity, cross-section, generator, trigger, jet/MET, process-mixture and finite-MC nuisance parameters.
5. Do not read a discovery Z until every blinded control and validation region closes under predeclared criteria on an era held out from model construction.
6. Treat NanoAOD and AOD as separate reduced-feature studies. Calibrate any reduced score only on a development era and apply it once, unchanged, to a disjoint file/run split. Do not combine it numerically with full MiniAOD results.
7. Redo ATLAS only as a separate analysis with the full official public-background set, signed weights, an analysis-note-matched one-lepton selection, a frozen score selected on CMS/development data, and an independent ATLAS holdout. The current ATLAS scan should be retained as exploratory only.

## What Darren should take from today

The exact weight and independent-format preparation are worthwhile additions, but the reported `7.76 sigma` CMS and `10.80 sigma` ATLAS values do not meet the conditions for a discovery or a publishable anomaly claim. The strongest correct conclusion is that N-Frame-inspired high-tail structure remains a live methodological candidate, while the decisive SM process-composition and control-transfer tests remain unresolved.
