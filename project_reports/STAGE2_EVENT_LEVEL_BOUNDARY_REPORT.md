# Stage 2 Event-Level Boundary Validation

This is a validation test, not a SUSY discovery test. It asks whether an N-Frame boundary score separates official simulated SUSY-like events from real CMS collision control samples.

## Summary By Sample

| sample | type | events | mean score z | top 10% | top 5% | top 1% |
|---|---|---:|---:|---:|---:|---:|
| `cms_jetht_run2016g_collision` | real_collision | 17433 | 0.6884 | 7.49 | 0.56 | 0.10 |
| `cms_met_run2016g_collision` | real_collision | 85149 | -0.1925 | 0.72 | 0.06 | 0.01 |
| `cms_singlemuon_run2016g_collision` | real_collision | 172994 | -0.3426 | 0.16 | 0.01 | 0.00 |
| `sms_t5wg_mg1500_mlsp1_signal` | simulated_signal | 30214 | 2.1195 | 94.73 | 50.43 | 10.11 |
| `susy_htoaa4b_m12_signal` | simulated_signal | 2394 | -0.1549 | 0.04 | 0.04 | 0.00 |

## Pairwise Signal Versus Real Tests

| signal | real | mean diff | Welch p | MW p | KS p | Cohen d |
|---|---|---:|---:|---:|---:|---:|
| `sms_t5wg_mg1500_mlsp1_signal` | `cms_met_run2016g_collision` | 2.3120 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 2.998 |
| `sms_t5wg_mg1500_mlsp1_signal` | `cms_jetht_run2016g_collision` | 1.4311 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 2.434 |
| `sms_t5wg_mg1500_mlsp1_signal` | `cms_singlemuon_run2016g_collision` | 2.4621 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 4.364 |
| `susy_htoaa4b_m12_signal` | `cms_met_run2016g_collision` | 0.0376 | 2.530e-03 | 7.787e-04 | 1.825e-56 | 0.044 |
| `susy_htoaa4b_m12_signal` | `cms_jetht_run2016g_collision` | -0.8433 | 0.000e+00 | 0.000e+00 | 0.000e+00 | -1.068 |
| `susy_htoaa4b_m12_signal` | `cms_singlemuon_run2016g_collision` | 0.1877 | 2.767e-51 | 2.132e-125 | 3.809e-195 | 0.319 |

## Logistic Model

The score and its component variables are not fitted in the same model because that would be mathematically redundant. Two models are reported instead.

Predictors used:

- `score_only: B_boundary_equal_weight_z`
- `components_only: R_multiplicity;R_reconstruction`

| model | AUC | 5-fold CV AUC | predictors |
|---|---:|---:|---|
| `score_only` | 0.9660 | 0.9660 | `B_boundary_equal_weight_z` |
| `components_only` | 0.9662 | 0.9662 | `R_multiplicity;R_reconstruction` |

| model | term | beta | p | odds ratio |
|---|---|---:|---:|---:|
| `score_only` | `const` | -5.4240 | 0.000e+00 | 0.0044 |
| `score_only` | `B_boundary_equal_weight_z` | 3.6079 | 0.000e+00 | 36.8899 |
| `components_only` | `const` | -5.7090 | 0.000e+00 | 0.0033 |
| `components_only` | `R_multiplicity` | 1.6345 | 0.000e+00 | 5.1269 |
| `components_only` | `R_reconstruction` | 2.4261 | 0.000e+00 | 11.3150 |

## Caution

The simulated signal data are not evidence of real observed SUSY. This test only checks whether the boundary score identifies known SUSY-like simulated structures. A stronger later test would apply the fitted boundary model to real collision data only and look for high-boundary anomalies.
