# Improved Real Collision Boundary Analysis Report

## Main Questions

1. Once MET and other features are available, does the boundary tail still just reflect JetHT?

   MET is still not available in the non-Docker route tested here. The improved score includes jets, packed candidates, vertices, and encoded displacement-like proxies. JetHT remains enriched, but less purely as a jet-only story because packed-candidate and vertex complexity now contribute.

2. Are there MET-rich high-boundary events?

   Cannot answer yet: MET pt/phi are not readable with the tested non-Docker tools.

3. Are high-boundary events distributed across MET, JetHT, and SingleMuon in a meaningful way?

| sample_id                         |   n_events |   mean_B_z |   sd_B_z |   median_B_z |   top10_pct |   top05_pct |   top01_pct |   mean_HT |   mean_N_jets_30 |   mean_N_packed_pf_candidates |   mean_N_primary_vertices |   mean_R_displacement_proxy |
|:----------------------------------|-----------:|-----------:|---------:|-------------:|------------:|------------:|------------:|----------:|-----------------:|------------------------------:|--------------------------:|----------------------------:|
| cms_jetht_run2016g_collision      |      98145 |   0.575736 | 1.11468  |     0.803618 |   30.5782   |   16.9871   |   3.78827   |  593.887  |          3.56392 |                       1577.38 |                   19.1763 |                  -0.0120672 |
| cms_met_run2016g_collision        |     227443 |   0.309787 | 1.17064  |     0.49633  |   14.8389   |    6.90371  |   1.24295   |  199.269  |          1.7888  |                       1724.16 |                   22.7402 |                   0.168775  |
| cms_singlemuon_run2016g_collision |     340314 |  -0.373081 | 0.619347 |    -0.370038 |    0.831585 |    0.270926 |   0.0337923 |   97.3247 |          1.46042 |                       1273    |                   14.8598 |                  -0.109318  |

4. Which variables drive the boundary score?

| component            | available   |   correlation_with_B_z |          mean |         sd |
|:---------------------|:------------|-----------------------:|--------------:|-----------:|
| R_missing            | False       |             nan        | nan           | nan        |
| R_multiplicity       | True        |               0.95344  |   1.47644e-15 |   0.731495 |
| R_reconstruction     | True        |               0.9051   |   8.99726e-16 |   0.641628 |
| R_compression_proxy  | False       |             nan        | nan           | nan        |
| R_lifetime_proxy     | False       |             nan        | nan           | nan        |
| R_displacement_proxy | True        |               0.847772 |   1.0348e-14  |   0.853712 |

5. Does the result become closer to Darren's missing-information/boundary-stress idea?

Partially. The improved score adds reconstruction/track/vertex stress information, including encoded packed-candidate dxy/dz proxies. It still lacks the missing-information component because MET is not extracted.
