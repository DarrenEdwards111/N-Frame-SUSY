# Real Trace Candidate Sanity Check Synthesis

Date: 2026-06-09

## Category Counts

| candidate_set   | primary_category                     |   events |   total |   fraction |
|:----------------|:-------------------------------------|---------:|--------:|-----------:|
| combined        | likely_SM_top_heavy_flavour_like     |       10 |     100 |       0.1  |
| combined        | trace_compatible_follow_up_candidate |        6 |     100 |       0.06 |
| combined        | trace_direction_aligned_but_SM_like  |       82 |     100 |       0.82 |
| combined        | unclear_follow_up_needed             |        2 |     100 |       0.02 |
| run2016g        | likely_SM_top_heavy_flavour_like     |       14 |     100 |       0.14 |
| run2016g        | trace_compatible_follow_up_candidate |        6 |     100 |       0.06 |
| run2016g        | trace_direction_aligned_but_SM_like  |       79 |     100 |       0.79 |
| run2016g        | unclear_follow_up_needed             |        1 |     100 |       0.01 |
| run2016h        | likely_SM_top_heavy_flavour_like     |       25 |     100 |       0.25 |
| run2016h        | trace_compatible_follow_up_candidate |        2 |     100 |       0.02 |
| run2016h        | trace_direction_aligned_but_SM_like  |       34 |     100 |       0.34 |
| run2016h        | unclear_follow_up_needed             |       39 |     100 |       0.39 |

## Plain-English Summary

- Combined candidates classified: 100.
- Trace-compatible follow-up candidates: 6.
- Trace-direction aligned but still SM-like/provenance-caveated: 82.
- Clearly SM/top-like candidates in combined set: 92.
- Available quality-filter failures: 0.

The automated sanity check does not identify direct particle evidence. It does identify a small follow-up subset that is high-B_NF, high trace-direction, quality-passing and not caught by the simple SM-centroid rules. Most candidates remain better described as trace-direction aligned but still SM-like or provenance-caveated.

## Quality, Trigger And Concentration

All top candidate sets pass the available compact quality-filter flag, but many candidates are concentrated in source files/runs/lumis. That is a provenance warning, not by itself proof of an artefact.

| flag                                     |   events |   fraction |
|:-----------------------------------------|---------:|-----------:|
| passes_available_quality_filters         |      300 |          1 |
| fails_any_available_quality_filter       |        0 |          0 |
| missing_quality_filter_info              |        0 |          0 |
| fails_HBHENoiseFilter                    |        0 |          0 |
| fails_HBHENoiseIsoFilter                 |        0 |          0 |
| fails_goodVertices                       |        0 |          0 |
| fails_EcalDeadCellTriggerPrimitiveFilter |        0 |          0 |
| fails_BadPFMuonFilter                    |        0 |          0 |
| fails_globalSuperTightHalo2016Filter     |        0 |          0 |

| trigger_category     |   events |   fraction |
|:---------------------|---------:|-----------:|
| trigger_category_MET |      129 |  0.43      |
| trigger_category_HT  |      161 |  0.536667  |
| trigger_category_Mu  |       10 |  0.0333333 |
| trigger_category_Ele |        0 |  0         |

| warning                            |   events |   fraction |
|:-----------------------------------|---------:|-----------:|
| source_file_overconcentration_flag |      268 |   0.893333 |
| run_overconcentration_flag         |      261 |   0.87     |
| lumi_overconcentration_flag        |      175 |   0.583333 |
| extreme_MET                        |      255 |   0.85     |
| extreme_HT                         |      208 |   0.693333 |
| extreme_jet_multiplicity           |       70 |   0.233333 |
| high_reconstruction_complexity     |       67 |   0.223333 |
| high_secondary_vertex_proxy        |      296 |   0.986667 |
| high_btag_structure                |      174 |   0.58     |
| SM_centroid_like                   |       84 |   0.28     |

## Matched-Control Result

Compared with nearby ordinary real controls, candidates have much higher B_NF, trace score, MET, HT, secondary-vertex count, and are closer to the SMS centroid while farther from pooled SM. This supports that they are unusual relative to ordinary events from similar data-taking context.

| metric                                         |   median_candidate_minus_control |   mean_candidate_minus_control |
|:-----------------------------------------------|---------------------------------:|-------------------------------:|
| candidate_minus_control_B_NF_trace_base        |                          3.01568 |                        3.13631 |
| candidate_minus_control_Trace_sms_vs_pooledSM  |                          5.75118 |                        6.34805 |
| candidate_minus_control_MET_pt                 |                        311.239   |                      335.654   |
| candidate_minus_control_HT                     |                        988.921   |                     1174.81    |
| candidate_minus_control_N_jets_30              |                          0       |                        0.078   |
| candidate_minus_control_N_btags_medium         |                          0.4     |                        0.542   |
| candidate_minus_control_N_leptons              |                          2.6     |                        3.24    |
| candidate_minus_control_secondary_vertex_count |                          4.5     |                        5.06    |
| candidate_minus_control_packed_candidate_count |                          0.2     |                        7.604   |
| candidate_minus_control_distance_to_SMS        |                         -4.73466 |                       -4.86884 |
| candidate_minus_control_distance_to_pooledSM   |                          4.94615 |                        5.45537 |

## Top Candidate Cards

Plain-English cards for the top 25 combined candidates are available in `reports/TOP25_TRACE_CANDIDATE_CARDS.md`.

## Effect On Darren's Hypothesis

This strengthens the disappearance-trace interpretation in a qualified way: the follow-up subset is quality-passing, trace-direction aligned, and unusual relative to matched controls. But most candidates are still SM-like/provenance-caveated, and this remains indirect model-dependent evidence rather than direct particle detection.

## Exact Next Step

Ask a particle-physics expert to review the 6 combined trace-compatible follow-up candidates and the top-25 cards, focusing first on source/run/lumi concentration and whether the event shapes have ordinary SM explanations.