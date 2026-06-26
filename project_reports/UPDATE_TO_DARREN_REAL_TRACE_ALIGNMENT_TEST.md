# Update To Darren: Real Trace Alignment Test

Date: 2026-06-09

We used the >=5 sigma benchmark result only to define a SUSY-like trace direction, then applied that direction back to real CMS Run2016G and Run2016H data.

## Main Finding

Real high-B_NF events show very strong SMS-like trace-projection enrichment in both Run2016G and Run2016H. This supports an indirect, model-dependent trace-alignment layer: as real events move deeper into the frozen N-Frame boundary tail, they move along the benchmark SMS-vs-SM contrast direction.

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

## Important Qualification

However, the distance-to-centroid test qualifies the result: the high-B_NF real events remain much closer in absolute component space to TTJets/QCD/pooled-SM centroids than to the SMS-T5Wg centroid. So the current result is best described as trace-direction alignment, not real events becoming SMS-like events.

## Plain English Interpretation

The real high-boundary events do not become direct SUSY candidates. But they do move strongly along the SMS-like disappearance-compatible direction as B_NF increases. That is indirect, model-dependent boundary-stress trace evidence, not direct particle detection.

## Candidate Events

Top-100 Run2016G, Run2016H and combined candidate lists were produced, and the available quality filters pass for those candidate sets.

## Next Step

Inspect the top real events visually and repeat with a broader/full-component SM benchmark set.