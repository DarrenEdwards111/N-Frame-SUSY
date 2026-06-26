# Updated Master Audit After Signal-Side Parity

Date: 2026-06-09

The frozen B_NF equation remains unchanged. This audit consolidates the latest full-component signal-side parity result with the prior real-data and benchmark evidence.

## Audit Findings

| category   | finding                                                                                                   | evidence                                                                                                                                                                                                                                               | status                   |
|:-----------|:----------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------|
| resolved   | Full-component signal-side parity was achieved for three accessible MiniAODSIM SUSY-like benchmark files. | 4401 extracted signal events; full components available.                                                                                                                                                                                               | resolved                 |
| resolved   | One full-component SUSY-like benchmark beats the strongest existing QCD mimic.                            | [{'signal_process': 'neutralino', 'signal_tail_fraction': 0.622, 'background_tail_fraction': 0.2493702770780856, 'bonferroni_z': 17.5743495301251}]                                                                                                    | positive_model_dependent |
| unresolved | Not all SUSY-like signals beat QCD HT1000to1500.                                                          | [{'signal_process': 'SMS-T2tt', 'signal_tail_fraction': 0.0915347556779077, 'background_tail_fraction': 0.2493702770780856}, {'signal_process': 'gluino', 'signal_tail_fraction': 0.0432489451476793, 'background_tail_fraction': 0.2493702770780856}] | qualified                |
| unresolved | SMS-T5Wg/T1 high-MET MiniAODSIM remains the most important missing signal-side test.                      | The restored positive result is for an accessible gluino-to-neutralino benchmark, not the original SMS-T5Wg/T1 family.                                                                                                                                 | missing_target           |
| unresolved | Broader SM coverage remains needed.                                                                       | Existing full-component backgrounds are QCD HT1000to1500, QCD HT700to1000 and WJets only.                                                                                                                                                              | needs_more_SM_mimics     |
| caveat     | B_NF does not currently add strongly beyond simpler energy/recoil structure.                              | Best median AUC: P_missing_plus_visible=0.919; full B_NF median AUC=0.444.                                                                                                                                                                             | qualified                |
| baseline   | Strongest current full-component SM mimic remains QCD HT1000to1500.                                       | [{'process_label': 'QCD HT1000to1500', 'q95_tail_fraction': 0.2493702770780856, 'q99_tail_fraction': 0.044080604534005}]                                                                                                                               | baseline                 |

## Report Inventory

| report                                                   | status   |
|:---------------------------------------------------------|:---------|
| FULL_COMPONENT_SIGNAL_SIDE_PARITY_SYNTHESIS.md           | present  |
| UPDATE_TO_DARREN_FULL_COMPONENT_SIGNAL_SIDE_PARITY.md    | present  |
| FULL_COMPONENT_SIGNAL_VS_QCD_COMPARISON_REPORT.md        | present  |
| FULL_COMPONENT_REAL_TRACE_ALIGNMENT_REPORT.md            | present  |
| FULLER_COMPONENT_BENCHMARK_SYNTHESIS.md                  | present  |
| EXPANDED_BENCHMARK_AND_TRACE_ROBUSTNESS_SYNTHESIS.md     | present  |
| REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md                   | present  |
| REAL_TRACE_CANDIDATE_SANITY_CHECK_SYNTHESIS.md           | present  |
| FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md | present  |

## Interpretation

The signal-side parity run strengthens the N-Frame/SUSY interpretation in a qualified, model-dependent way: one accessible full-component gluino-to-neutralino benchmark beats QCD HT1000to1500 strongly, but other SUSY-like samples do not, and B_NF remains largely energy/recoil-driven in incrementality tests.