# Frozen-Reference Control-Mixture Transfer Test

## Purpose

This is the next validity test after the fixed-reference OPQ model showed that
the broad SM template did not close controls. For each held-out CMS era, the
non-negative process mixture is fitted using only JetHT and SingleMuon
microbands. The MET 0-jet microbands are then predicted without being used in
the fit.

The score calibration and numerical microband boundaries are frozen from the
original Run2016G reference sample.

## Control Closure

| sample_validation_id              | fit_scope                 |   control_chi2 |   control_dof |    control_p |   control_Z | controls_closed_at_p_ge_0_05   |
|:----------------------------------|:--------------------------|---------------:|--------------:|-------------:|------------:|:-------------------------------|
| Run2015D_remote_mht_aware_holdout | JetHT_and_SingleMuon_only |       2011.77  |             9 | 0            |     38.4674 | False                          |
| Run2016H_remote_mht_aware         | JetHT_and_SingleMuon_only |        428.134 |             9 | 1.34997e-86  |     19.6886 | False                          |
| Run2016G_remote_mht_aware_fresh   | JetHT_and_SingleMuon_only |       1010.66  |             9 | 8.67703e-212 |     31.0365 | False                          |

## MET Transfer Prediction

| sample_validation_id              | control_fit_closed   |   met_all_bands_chi2 |   met_all_bands_dof |   met_all_bands_p |   met_all_bands_Z |   met_upper_observed |   met_upper_expected |   met_upper_obs_over_exp |   met_upper_naive_signed_Z_no_systematics | valid_MET_transfer_test   |
|:----------------------------------|:---------------------|---------------------:|--------------------:|------------------:|------------------:|---------------------:|---------------------:|-------------------------:|------------------------------------------:|:--------------------------|
| Run2015D_remote_mht_aware_holdout | False                |              1097.27 |                   4 |      2.95156e-236 |           32.7999 |                  273 |              80.9929 |                  3.37066 |                                   21.335  | False                     |
| Run2016H_remote_mht_aware         | False                |             23801.9  |                   4 |      0            |           38.4674 |                 3606 |             503.311  |                  7.16456 |                                  138.299  | False                     |
| Run2016G_remote_mht_aware_fresh   | False                |              3196.24 |                   4 |      0            |           38.4674 |                  802 |             154.166  |                  5.2022  |                                   52.1759 | False                     |

## Interpretation Rule

A MET discrepancy is meaningful only for rows with `control_fit_closed=True`.
If the control fit does not close, a MET difference can still be ordinary
process-mixture, trigger, or detector-transfer mismatch. The naive signed Z is
diagnostic only: it has no systematic uncertainty model and is not a discovery
significance.
