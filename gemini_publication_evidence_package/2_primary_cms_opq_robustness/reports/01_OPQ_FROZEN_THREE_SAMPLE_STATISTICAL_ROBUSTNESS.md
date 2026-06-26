# OPQ Frozen Three-Sample Remote Statistical Robustness

## Purpose

This extends the frozen OPQ boundary-trace check to three remote real-CMS
validation samples:

- `Run2015D_remote_mht_aware_holdout`
- `Run2016H_remote_mht_aware`
- `Run2016G_remote_mht_aware_fresh`

The score was not retuned:

$$B_{OPQ} = 0.344828O + 0.517241P - 0.137931Q.$$

The trace region is MET 0jet. Controls are JetHT and SingleMuon in the same
microband construction.

## Per-Sample Results

| candidate_id                               | sample_validation_id              |   trace_total |   control_total |   shape_chi2 |   shape_dof |     shape_p |   shape_Z |   shoulder_chi2 |   shoulder_p |   shoulder_Z |   bootstrap_shoulder_delta_median |   bootstrap_shoulder_delta_ci95_low |   bootstrap_shoulder_delta_ci95_high |   bootstrap_one_sided_p_delta_not_positive |   bootstrap_one_sided_Z | passes_shape_Z5   | passes_positive_bootstrap_ci   |
|:-------------------------------------------|:----------------------------------|--------------:|----------------:|-------------:|------------:|------------:|----------:|----------------:|-------------:|-------------:|----------------------------------:|------------------------------------:|-------------------------------------:|-------------------------------------------:|------------------------:|:------------------|:-------------------------------|
| observer_physical_qcd_suppressed_scan_best | Run2015D_remote_mht_aware_holdout |           848 |            2490 |     140.155  |           4 | 2.61466e-29 |  11.1779  |        23.5919  |  1.19087e-06 |      4.718   |                          0.544111 |                           0.308642  |                             0.815435 |                                1.99996e-05 |                 4.10748 | True              | True                           |
| observer_physical_qcd_suppressed_scan_best | Run2016H_remote_mht_aware         |          2025 |            6450 |      41.7889 |           4 | 1.845e-08   |   5.50508 |        13.1494  |  0.000287609 |      3.44304 |                          0.220024 |                           0.0978364 |                             0.35109  |                                0.000139997 |                 3.63314 | True              | True                           |
| observer_physical_qcd_suppressed_scan_best | Run2016G_remote_mht_aware_fresh   |           493 |            2990 |      17.3421 |           4 | 0.00165838  |   2.93675 |         7.05754 |  0.00789322  |      2.41382 |                          0.322097 |                           0.0757301 |                             0.61147  |                                0.00443991  |                 2.61665 | False             | True                           |

## Combined Result

| candidate_id                               | validation_samples                                                                          |   sample_count |   fisher_shape_statistic |   fisher_shape_p |   fisher_shape_Z |   fisher_shoulder_statistic |   fisher_shoulder_p |   fisher_shoulder_Z |   min_sample_shape_Z |   samples_shape_Z_ge_5 |   samples_positive_bootstrap_ci |
|:-------------------------------------------|:--------------------------------------------------------------------------------------------|---------------:|-------------------------:|-----------------:|-----------------:|----------------------------:|--------------------:|--------------------:|---------------------:|-----------------------:|--------------------------------:|
| observer_physical_qcd_suppressed_scan_best | Run2015D_remote_mht_aware_holdout;Run2016H_remote_mht_aware;Run2016G_remote_mht_aware_fresh |              3 |                  180.048 |      3.31459e-36 |          12.5094 |                      53.273 |         1.03377e-09 |             5.99241 |              2.93675 |                      2 |                               3 |

## Interpretation

The added Run2016G sample preserves the same sign of the MET-vs-control
boundary-trace effect, but it is weaker than the earlier Run2015D and Run2016H
held-out samples. This strengthens the repeatability argument because the
pattern now appears in a third real-CMS remote sample, but it also qualifies the
claim because the weakest individual sample is below 5 sigma in the asymptotic
shape screen.

This remains evidence for a repeatable N-Frame boundary-trace pattern, not
direct SUSY-particle detection and not yet an official CMS discovery
significance.
