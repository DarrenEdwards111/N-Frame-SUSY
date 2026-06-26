# Fitted Versus Previous Boundary Score Comparison

Date: 2026-06-08

The fitted score is compared with the previous hand-defined and unsupervised boundary scores on standard quality-clean real CMS events.

## Correlations

|              |   fitted |     hand |   unsupervised |
|:-------------|---------:|---------:|---------------:|
| fitted       | 1        | 0.895919 |       0.701384 |
| hand         | 0.895919 | 1        |       0.557013 |
| unsupervised | 0.701384 | 0.557013 |       1        |

## Top-Tail Overlap

| tail   | score_a      | score_b      |   jaccard_overlap |   a_in_b_fraction |
|:-------|:-------------|:-------------|------------------:|------------------:|
| top05  | fitted       | fitted       |          1        |          1        |
| top05  | fitted       | hand         |          0.524806 |          0.688358 |
| top05  | fitted       | unsupervised |          0.37537  |          0.545845 |
| top05  | hand         | fitted       |          0.524806 |          0.688358 |
| top05  | hand         | hand         |          1        |          1        |
| top05  | hand         | unsupervised |          0.337417 |          0.50458  |
| top05  | unsupervised | fitted       |          0.37537  |          0.545845 |
| top05  | unsupervised | hand         |          0.337417 |          0.50458  |
| top05  | unsupervised | unsupervised |          1        |          1        |
| top01  | fitted       | fitted       |          1        |          1        |
| top01  | fitted       | hand         |          0.45269  |          0.623244 |
| top01  | fitted       | unsupervised |          0.329743 |          0.49595  |
| top01  | hand         | fitted       |          0.45269  |          0.623244 |
| top01  | hand         | hand         |          1        |          1        |
| top01  | hand         | unsupervised |          0.282927 |          0.441065 |
| top01  | unsupervised | fitted       |          0.329743 |          0.49595  |
| top01  | unsupervised | hand         |          0.282927 |          0.441065 |
| top01  | unsupervised | unsupervised |          1        |          1        |
| top001 | fitted       | fitted       |          1        |          1        |
| top001 | fitted       | hand         |          0.425206 |          0.596694 |
| top001 | fitted       | unsupervised |          0.379704 |          0.550413 |
| top001 | hand         | fitted       |          0.425206 |          0.596694 |
| top001 | hand         | hand         |          1        |          1        |
| top001 | hand         | unsupervised |          0.310943 |          0.47438  |
| top001 | unsupervised | fitted       |          0.379704 |          0.550413 |
| top001 | unsupervised | hand         |          0.310943 |          0.47438  |
| top001 | unsupervised | unsupervised |          1        |          1        |

## Tail Composition

| tail   | score        | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-------|:-------------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| top05  | fitted       | JetHT             |       0.507622  |            0.150256 |           3.37837  |    15352 |
| top05  | fitted       | MET               |       0.382766  |            0.2873   |           1.33229  |    11576 |
| top05  | fitted       | SingleMuon        |       0.109612  |            0.562444 |           0.194885 |     3315 |
| top05  | hand         | MET               |       0.561684  |            0.2873   |           1.95505  |    16987 |
| top05  | hand         | JetHT             |       0.341963  |            0.150256 |           2.27587  |    10342 |
| top05  | hand         | SingleMuon        |       0.0963529 |            0.562444 |           0.171311 |     2914 |
| top05  | unsupervised | MET               |       0.401085  |            0.2873   |           1.39605  |    12130 |
| top05  | unsupervised | JetHT             |       0.367755  |            0.150256 |           2.44752  |    11122 |
| top05  | unsupervised | SingleMuon        |       0.231161  |            0.562444 |           0.410994 |     6991 |
| top01  | fitted       | JetHT             |       0.551992  |            0.150256 |           3.67367  |     3339 |
| top01  | fitted       | MET               |       0.370474  |            0.2873   |           1.28951  |     2241 |
| top01  | fitted       | SingleMuon        |       0.0775335 |            0.562444 |           0.137851 |      469 |
| top01  | hand         | MET               |       0.557943  |            0.2873   |           1.94203  |     3375 |
| top01  | hand         | JetHT             |       0.366342  |            0.150256 |           2.43811  |     2216 |
| top01  | hand         | SingleMuon        |       0.075715  |            0.562444 |           0.134618 |      458 |
| top01  | unsupervised | MET               |       0.414283  |            0.2873   |           1.44199  |     2506 |
| top01  | unsupervised | JetHT             |       0.398909  |            0.150256 |           2.65486  |     2413 |
| top01  | unsupervised | SingleMuon        |       0.186808  |            0.562444 |           0.332136 |     1130 |
| top001 | fitted       | JetHT             |       0.502479  |            0.150256 |           3.34415  |      304 |
| top001 | fitted       | MET               |       0.431405  |            0.2873   |           1.50159  |      261 |
| top001 | fitted       | SingleMuon        |       0.0661157 |            0.562444 |           0.117551 |       40 |
| top001 | hand         | MET               |       0.533884  |            0.2873   |           1.85828  |      323 |
| top001 | hand         | JetHT             |       0.395041  |            0.150256 |           2.62912  |      239 |
| top001 | hand         | SingleMuon        |       0.0710744 |            0.562444 |           0.126367 |       43 |
| top001 | unsupervised | JetHT             |       0.442975  |            0.150256 |           2.94813  |      268 |
| top001 | unsupervised | MET               |       0.401653  |            0.2873   |           1.39803  |      243 |
| top001 | unsupervised | SingleMuon        |       0.155372  |            0.562444 |           0.276244 |       94 |

## Concentration

| tail   | score        |   top_file_fraction |   top_run_fraction |   top_lumi_bin_fraction |
|:-------|:-------------|--------------------:|-------------------:|------------------------:|
| top05  | fitted       |            0.272294 |           0.225308 |                0.187382 |
| top05  | hand         |            0.276527 |           0.276527 |                0.172866 |
| top05  | unsupervised |            0.222531 |           0.183216 |                0.142446 |
| top01  | fitted       |            0.267648 |           0.274426 |                0.223177 |
| top01  | hand         |            0.280542 |           0.280542 |                0.199041 |
| top01  | unsupervised |            0.224831 |           0.186642 |                0.164325 |
| top001 | fitted       |            0.204959 |           0.295868 |                0.246281 |
| top001 | hand         |            0.271074 |           0.290909 |                0.244628 |
| top001 | unsupervised |            0.221488 |           0.216529 |                0.181818 |