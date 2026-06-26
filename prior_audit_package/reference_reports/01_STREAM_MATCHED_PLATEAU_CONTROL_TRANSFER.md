# Stream-Matched Plateau Control Transfer

## Fixed Selections

- MET: observed MET trigger and MET >= 150 GeV.
- JetHT: observed HT trigger, HT >= 900 GeV and at least one jet.
- SingleMuon: observed muon trigger and at least one reconstructed muon.

The same offline cuts are applied to MC. Trigger bits are retained only for
data because the broad MC trigger aggregates are known to be non-discriminating.

## Control Closure

| sample_validation_id              |   control_chi2 |   control_dof |    control_p |   control_Z | controls_closed_at_p_ge_0_05   |
|:----------------------------------|---------------:|--------------:|-------------:|------------:|:-------------------------------|
| Run2015D_remote_mht_aware_holdout |        249.792 |             9 | 1.10391e-48  |     14.6164 | False                          |
| Run2016H_remote_mht_aware         |       3371.76  |             9 | 0            |     38.4674 | False                          |
| Run2016G_remote_mht_aware_fresh   |       1025.48  |             9 | 5.52869e-215 |     31.2725 | False                          |

## MET Transfer

| sample_validation_id              | control_fit_closed   |   met_chi2 |   met_dof |       met_p |    met_Z |   met_upper_observed |   met_upper_expected |   met_upper_ratio | valid_transfer   |
|:----------------------------------|:---------------------|-----------:|----------:|------------:|---------:|---------------------:|---------------------:|------------------:|:-----------------|
| Run2015D_remote_mht_aware_holdout | False                |   180.423  |         4 | 6.05005e-38 | 12.8236  |                  107 |              45.9936 |          2.32641  | False            |
| Run2016H_remote_mht_aware         | False                |    68.1702 |         4 | 5.5226e-14  |  7.42776 |                  235 |             166.607  |          1.41051  | False            |
| Run2016G_remote_mht_aware_fresh   | False                |    22.7539 |         4 | 0.000141796 |  3.62984 |                   76 |              98.5636 |          0.771076 | False            |

## Interpretation Rule

Only rows with `control_fit_closed=True` can be read as a valid transfer test.
If none close, the remaining limitation is MC selection/process modelling, not
the N-Frame score itself.
