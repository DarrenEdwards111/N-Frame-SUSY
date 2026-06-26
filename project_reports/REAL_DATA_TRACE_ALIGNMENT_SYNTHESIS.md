# Real Data Trace Alignment Synthesis

Date: 2026-06-09

## How The Benchmark Trace Direction Was Defined

SMS-T5Wg was contrasted against TTJets, QCD and pooled SM using shared reduced components: P_missing, P_visible_energy, P_multiplicity, P_btag_structure and P_compression. Simulation was used only to define this direction; B_NF was not refitted.

| direction                               | component        |   raw_contrast |   unit_weight |   signal_mean |   background_mean |
|:----------------------------------------|:-----------------|---------------:|--------------:|--------------:|------------------:|
| sms_vs_pooledSM                         | P_missing        |       9.88332  |     0.898724  |      9.82685  |        -0.056469  |
| sms_vs_pooledSM                         | P_visible_energy |       4.1702   |     0.379211  |      5.28199  |         1.11178   |
| sms_vs_pooledSM                         | P_multiplicity   |       2.23395  |     0.203141  |      3.06615  |         0.832202  |
| sms_vs_pooledSM                         | P_btag_structure |      -0.258152 |    -0.0234746 |      0.353516 |         0.611668  |
| sms_vs_pooledSM                         | P_compression    |       0.898551 |     0.0817084 |     -1.56647  |        -2.46502   |
| sms_vs_TTJets_nanoaodsim_pilot          | P_missing        |       9.70147  |     0.868262  |      9.82685  |         0.125378  |
| sms_vs_TTJets_nanoaodsim_pilot          | P_visible_energy |       5.03948  |     0.451023  |      5.28199  |         0.242506  |
| sms_vs_TTJets_nanoaodsim_pilot          | P_multiplicity   |       2.08457  |     0.186565  |      3.06615  |         0.981584  |
| sms_vs_TTJets_nanoaodsim_pilot          | P_btag_structure |      -0.932727 |    -0.0834772 |      0.353516 |         1.28624   |
| sms_vs_TTJets_nanoaodsim_pilot          | P_compression    |       0.339689 |     0.0304015 |     -1.56647  |        -1.90616   |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_missing        |      10.0652   |     0.918126  |      9.82685  |        -0.238316  |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_visible_energy |       3.30093  |     0.301105  |      5.28199  |         1.98106   |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_multiplicity   |       2.38333  |     0.217403  |      3.06615  |         0.682819  |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_btag_structure |       0.416423 |     0.0379854 |      0.353516 |        -0.0629075 |
| sms_vs_QCD_ht700to1000_nanoaodsim_pilot | P_compression    |       1.45741  |     0.132943  |     -1.56647  |        -3.02389   |

## Real High-BNF Trace Alignment

| dataset   | bnf_tail   |   high_events |   mean_trace_high |   mean_trace_rest |   mean_diff |   welch_gaussian_z |   fraction_high_above_trace_q90 |   fraction_rest_above_trace_q90 |   trace_q90_enrichment_ratio |   trace_q90_prop_z |
|:----------|:-----------|--------------:|------------------:|------------------:|------------:|-------------------:|--------------------------------:|--------------------------------:|-----------------------------:|-------------------:|
| Run2016G  | top05      |         30243 |          1.4416   |       -0.0758737  |    1.51747  |           inf      |                        0.401349 |                       0.0841395 |                      4.77004 |           179.225  |
| Run2016G  | top01      |          6049 |          1.80341  |       -0.0182175  |    1.82163  |           inf      |                        0.505373 |                       0.0959051 |                      5.26951 |           105.623  |
| Run2016G  | top001     |           605 |          2.33952  |       -0.00234241 |    2.34186  |            25.8851 |                        0.636364 |                       0.099463  |                      6.398   |            43.998  |
| Run2016H  | top05      |          7849 |          0.921672 |       -0.0485107  |    0.970183 |           inf      |                        0.300166 |                       0.089468  |                      3.35501 |            60.6458 |
| Run2016H  | top01      |          1570 |          1.26035  |       -0.0127329  |    1.27309  |            17.6757 |                        0.380892 |                       0.0971655 |                      3.92003 |            37.2854 |
| Run2016H  | top001     |           157 |          2.18833  |       -0.00219087 |    2.19052  |             3.9125 |                        0.477707 |                       0.099625  |                      4.79505 |            15.7831 |
| combined  | top05      |         38092 |          1.3382   |       -0.0704321  |    1.40863  |           inf      |                        0.385041 |                       0.0849984 |                      4.52998 |           190.257  |
| combined  | top01      |          7619 |          1.70869  |       -0.017261   |    1.72595  |           inf      |                        0.487466 |                       0.0960865 |                      5.07319 |           113.303  |
| combined  | top001     |           762 |          2.35479  |       -0.00235766 |    2.35715  |            17.1852 |                        0.62336  |                       0.0994767 |                      6.26639 |            48.1806 |

Real high-B_NF events show very strong SMS-like trace-projection enrichment in both Run2016G and Run2016H. This supports an indirect, model-dependent trace-alignment layer: as real events move deeper into the frozen N-Frame boundary tail, they move along the benchmark SMS-vs-SM contrast direction.

## SMS Versus SM Centroid Distance

| dataset   | bnf_tail   |   events |   mean_distance_to_SMS |   mean_distance_to_TTJets |   mean_distance_to_QCD |   mean_distance_to_pooledSM |   fraction_closer_to_SMS_than_pooledSM_high |   enrichment_ratio |   gaussian_z |
|:----------|:-----------|---------:|-----------------------:|--------------------------:|-----------------------:|----------------------------:|--------------------------------------------:|-------------------:|-------------:|
| Run2016G  | top05      |    30243 |               10.2623  |                   2.93184 |                3.53545 |                     2.99901 |                                  0.00790266 |            18.7645 |     28.1     |
| Run2016G  | top01      |     6049 |               10.0078  |                   3.34209 |                3.9137  |                     3.41536 |                                  0.0176889  |            28.3216 |     21.9786  |
| Run2016G  | top001     |      605 |                9.74702 |                   4.12518 |                4.65396 |                     4.21271 |                                  0.031405   |            41.0749 |     10.1065  |
| Run2016H  | top05      |     7849 |               10.8262  |                   2.70041 |                3.49512 |                     2.86454 |                                  0.00955536 |             5.2776 |     10.7295  |
| Run2016H  | top01      |     1570 |               10.6865  |                   3.0555  |                3.85822 |                     3.24705 |                                  0.0203822  |            10.1198 |      9.3324  |
| Run2016H  | top001     |      157 |               11.0539  |                   4.22723 |                4.99679 |                     4.4259  |                                  0.0382166  |            17.6786 |      4.66525 |
| combined  | top05      |    38092 |               10.3739  |                   2.88544 |                3.52681 |                     2.97176 |                                  0.0081907  |            11.533  |     28.7625  |
| combined  | top01      |     7619 |               10.1317  |                   3.29256 |                3.90741 |                     3.38812 |                                  0.0182439  |            20.0288 |     23.3673  |
| combined  | top001     |      762 |                9.97603 |                   4.18683 |                4.74647 |                     4.28856 |                                  0.0354331  |            33.7511 |     11.6593  |

However, the distance-to-centroid test qualifies the result: the high-B_NF real events remain much closer in absolute component space to TTJets/QCD/pooled-SM centroids than to the SMS-T5Wg centroid. So the current result is best described as trace-direction alignment, not real events becoming SMS-like events.

## Candidate Events

| candidate_set   | path                                                                                                                              |   events |
|:----------------|:----------------------------------------------------------------------------------------------------------------------------------|---------:|
| Run2016G        | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\top_real_trace_candidates_run2016g.csv |      100 |
| Run2016H        | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\top_real_trace_candidates_run2016h.csv |      100 |
| combined        | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\top_real_trace_candidates_combined.csv |      100 |

All top-100 candidate sets passed the available quality-filter checks in the generated tables.

## Interpretation For Darren's Hypothesis

This strengthens the N-Frame interpretation in a qualified way. It supports boundary-stress trace dynamics because the real high-boundary tail aligns strongly with the disappearance-compatible SMS-vs-SM direction. It does not prove hidden particles, and the centroid-distance test shows that the real data still look more SM-like in absolute benchmark space.

## What Remains Weak

The benchmark direction is reduced-component, the SM benchmark set is still small, there is no published signal-region residual integration yet, and the top real trace candidates have not been manually/event-display inspected.

## Exact Next Step

Manually inspect the top combined trace-candidate events, then repeat the trace-direction test with fuller MiniAODSIM TTJets/QCD and additional SM backgrounds.