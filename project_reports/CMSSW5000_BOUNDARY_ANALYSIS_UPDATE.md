# CMSSW 5k Boundary Analysis Update

Date: 2026-06-08

## What changed

- Docker storage was moved off C: to D: and the official CMS Open Data CMSSW image was pulled successfully.
- CMSSW read real CMS MiniAOD directly, including MET, jets, muons, electrons, and b-tag information.
- Ran matched 5,000-event extraction/scoring jobs for three real CMS controls and two simulated signal samples. HToAA only contained 2,394 events in the downloaded file.
- Recomputed boundary z-scores relative to the combined real CMS controls, so signal and real samples are on the same scale.

## Main results

| Sample | Type | Events | Mean boundary z vs real | In real top 5% tail | In real top 1% tail | Median MET | Median HT |
|---|---:|---:|---:|---:|---:|---:|---:|
| CMS MET Run2016G | real | 5000 | -0.01 | 5.2% | 1.0% | 66.77 | 135.52 |
| CMS JetHT Run2016G | real | 5000 | 0.03 | 3.8% | 0.2% | 36.57 | 606.30 |
| CMS SingleMuon Run2016G | real | 5000 | -0.02 | 6.0% | 1.8% | 27.58 | 45.45 |
| SUSY SMS T5Wg mGluino1500 mLSP1 | signal | 5000 | 0.37 | 7.5% | 0.7% | 470.82 | 2013.41 |
| SUSY HToAA4B mA12 | signal | 2394 | -0.02 | 4.3% | 1.0% | 25.34 | 97.58 |

## Signal-vs-real tests

| Signal | Mean B difference | Cohen d | AUC using boundary score | Mann-Whitney p | KS p |
|---|---:|---:|---:|---:|---:|
| SUSY SMS T5Wg mGluino1500 mLSP1 | 1.66 | 0.37 | 0.63 | 1.18e-161 | 2.38e-150 |
| SUSY HToAA4B mA12 | -0.08 | -0.02 | 0.50 | 0.579 | 6.22e-07 |

## Plain-English interpretation

The T5Wg simulated SUSY sample strongly piles up in event regions that are rare in real CMS control data: most T5Wg events land inside the top 5% boundary tail defined by real data. That is the cleanest current evidence that the N-frame boundary score is sensitive to SUSY-like event structure.

The HToAA sample does not show the same broad boundary-tail enrichment. It has a small number of extreme high-boundary events, but most of that sample looks closer to ordinary real controls under this boundary score.

This is not a particle discovery. It is an exploratory validation that the boundary/topology score can separate at least one simulated SUSY topology from multiple independent real CMS samples when using proper CMSSW MiniAOD features.

## Files produced

- Summary table: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_boundary_summary_by_sample.csv`
- Signal-vs-real tests: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_signal_vs_real_boundary_tests.csv`
- Combined scored events: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw5000_combined_event_features_scored_vs_real.csv`
- Top boundary events: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_top_200_boundary_events.csv`