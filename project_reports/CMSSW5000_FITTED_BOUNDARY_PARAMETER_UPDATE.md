# CMSSW Fitted Boundary Parameter Update

Date: 2026-06-08

## What this answers

Darren asked what kind of parameters would bring about the boundary conditions, and whether the data can be used to find those parameters. This run fits those parameters directly from CMSSW MiniAOD features, using real CMS events as controls and two simulated signal samples as the SUSY-like target class.

## Holdout performance

- Test AUC: **0.909**
- Test average precision: **0.843**
- Test F1 at 0.5 threshold: **0.799**
- Confusion matrix on holdout: TN=3962, FP=539, FN=385, TP=1833

## Strongest fitted boundary parameters

| Rank | Parameter | Direction | Weight |
|---:|---|---|---:|
| 1 | `log1p_MET_pt` | toward signal/boundary | 2.100 |
| 2 | `MET_fraction` | toward real/control | -2.089 |
| 3 | `S_event_proxy` | toward real/control | -1.868 |
| 4 | `log1p_HT` | toward real/control | -1.811 |
| 5 | `N_jets_50` | toward signal/boundary | 1.472 |
| 6 | `N_jets_30` | toward signal/boundary | 1.122 |
| 7 | `log1p_leading_jet_pt` | toward real/control | -0.971 |
| 8 | `N_btags_medium` | toward signal/boundary | 0.880 |
| 9 | `N_btags_tight` | toward signal/boundary | 0.634 |
| 10 | `N_leptons` | toward signal/boundary | 0.366 |

## Sample-level fitted boundary result

| Sample | Type | Events | Median fitted boundary score | In fitted real top 5% tail | In fitted real top 1% tail |
|---|---:|---:|---:|---:|---:|
| CMS JetHT Run2016G | real | 5000 | 0.201 | 7.4% | 1.7% |
| CMS MET Run2016G | real | 5000 | 0.233 | 6.0% | 1.2% |
| CMS SingleMuon Run2016G | real | 5000 | 0.072 | 1.6% | 0.1% |
| SUSY SMS T5Wg mGluino1500 mLSP1 | signal | 5000 | 0.931 | 86.3% | 35.3% |
| SUSY HToAA4B mA12 | signal | 2394 | 0.487 | 26.2% | 1.4% |

## Plain-English interpretation

The learned boundary is much stronger than the original hand-built boundary score. In simple terms, the model learns that SUSY-like traces in these samples mostly look like unusual combinations of missing energy, total jet energy, jet/lepton multiplicity, and b-tag structure. It then marks events as closer to the fitted boundary when they have those combinations.

This is still not evidence that CERN missed real SUSY particles. It is evidence that, when we use proper CMS software on raw MiniAOD, N-frame-style boundary parameters can be fitted from the data and can separate simulated SUSY-like event topologies from multiple independent real CMS control samples.

## Files produced

- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_fitted_boundary_model_metrics.csv`
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_fitted_boundary_parameters.csv`
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_fitted_boundary_summary_by_sample.csv`
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw5000_combined_event_features_with_fitted_boundary.csv`
- `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\cmssw5000_top_200_fitted_boundary_events.csv`