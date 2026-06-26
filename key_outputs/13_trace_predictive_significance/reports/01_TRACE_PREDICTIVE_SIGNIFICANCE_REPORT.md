# Trace Predictive Significance Report

## Question

Do N-Frame trace variables add predictive information beyond standard CMS-like kinematic variables in the existing benchmark layer?

This is a trace-pattern significance test. It asks whether N-Frame is identifying an observable boundary/topology trace associated with SUSY-like or hidden-sector benchmark structure. It is not a SUSY particle discovery significance and it does not claim a real-data excess.

## Headline result

Comparison: standard CMS-like variables versus standard CMS-like variables plus the displacement/reconstruction trace axis.

- Standard CMS-like AUC: 0.984994
- Standard + trace-axis AUC: 0.985426
- Delta AUC: 0.000432
- DeLong one-sided Z: 3.071 sigma
- DeLong one-sided p: 0.00106578
- Bootstrap one-sided Z: 2.968 sigma (empirical_fraction_delta_le_zero)
- Permutation one-sided Z: 3.353 sigma (plus_one_permutation_p_value)

Plain-English version: on the held-out benchmark test set, adding the N-Frame displacement/reconstruction trace score makes the classifier better at identifying SUSY-like or hidden-sector topology traces in the observable CMS boundary than standard CMS-style variables alone.

## Important limits

- This is a predictive-superiority / trace-pattern result, not a discovery of a new particle.
- The test uses simulated benchmark labels against weighted SM background rows; it does not prove an observed collision-data excess.
- The result should be quoted as evidence that the N-Frame trace score carries additional benchmark-topology information beyond standard CMS-style variables.
- The decisive physics-discovery test still requires control-region-closed, luminosity-weighted SM prediction versus real observed data in frozen signal regions.

## Dataset audit

| item                           |   value | note                                                                                                       |
|:-------------------------------|--------:|:-----------------------------------------------------------------------------------------------------------|
| weighted_sm_input_rows         |  251921 | outputs_breakthrough_full_push_nframe_susy\sources\best_available_full_plus_reduced_weighted_sm_events.csv |
| deduplicated_signal_input_rows |   61795 | all available signal benchmark rows                                                                        |
| trace_available_signal_rows    |   54401 | signal rows with fitted displacement/reconstruction trace axis                                             |
| primary_analysis_rows          |  108802 | balanced trace-available SM plus signal sample                                                             |
| primary_analysis_signal_rows   |   54401 |                                                                                                            |
| primary_analysis_sm_rows       |   54401 |                                                                                                            |
| heldout_test_rows              |   32641 | stratified event-level holdout                                                                             |
| heldout_test_signal_rows       |   16321 |                                                                                                            |
| heldout_test_sm_rows           |   16320 |                                                                                                            |

## Model AUCs

| model                          | features                                                                                                                          |   n_train |   n_test |   test_positive |   test_negative |      auc |   pr_auc |   delta_auc_vs_standard_CMS_like |
|:-------------------------------|:----------------------------------------------------------------------------------------------------------------------------------|----------:|---------:|----------------:|----------------:|---------:|---------:|---------------------------------:|
| standard_CMS_like              | MET_pt+HT+N_jets_30+N_btags_medium+N_muons+N_electrons                                                                            |     76161 |    32641 |           16321 |           16320 | 0.984994 | 0.985682 |                      0           |
| standard_plus_trace_axis       | MET_pt+HT+N_jets_30+N_btags_medium+N_muons+N_electrons+displacement_reconstruction_axis                                           |     76161 |    32641 |           16321 |           16320 | 0.985426 | 0.986151 |                      0.000431673 |
| standard_plus_BNF              | MET_pt+HT+N_jets_30+N_btags_medium+N_muons+N_electrons+B_NF_z                                                                     |     76161 |    32641 |           16321 |           16320 | 0.98567  | 0.986344 |                      0.000676175 |
| standard_plus_full_NFrame_axes | MET_pt+HT+N_jets_30+N_btags_medium+N_muons+N_electrons+B_NF_z+displacement_reconstruction_axis+missing_visible_axis+qcd_like_axis |     76161 |    32641 |           16321 |           16320 | 0.990094 | 0.989559 |                      0.00509999  |
| trace_axis_alone               | displacement_reconstruction_axis                                                                                                  |     76161 |    32641 |           16321 |           16320 | 0.603852 | 0.567453 |                     -0.381142    |
| BNF_alone                      | B_NF_z                                                                                                                            |     76161 |    32641 |           16321 |           16320 | 0.498158 | 0.491472 |                     -0.486836    |

## Formal significance tests

| comparison                                          | tested_model                   | test                           |    delta_auc |   standard_error |   p_one_sided |   sigma_one_sided_Z | p_value_note                     |        ci_025 |        ci_975 |   n_resamples |   count_delta_le_zero |   count_delta_ge_observed |
|:----------------------------------------------------|:-------------------------------|:-------------------------------|-------------:|-----------------:|--------------:|--------------------:|:---------------------------------|--------------:|--------------:|--------------:|----------------------:|--------------------------:|
| standard_plus_trace_axis_vs_standard_CMS_like       | standard_plus_trace_axis       | delong_correlated_auc          |  0.000431673 |      0.000140552 |   0.00106578  |             3.07126 | analytic_normal_approximation    | nan           | nan           |           nan |                   nan |                       nan |
| standard_plus_trace_axis_vs_standard_CMS_like       | standard_plus_trace_axis       | paired_test_set_bootstrap      |  0.000431673 |      0.000142972 |   0.0015      |             2.96774 | empirical_fraction_delta_le_zero |   0.000147706 |   0.000703913 |          2000 |                     3 |                       nan |
| standard_plus_trace_axis_vs_standard_CMS_like       | standard_plus_trace_axis       | paired_score_label_permutation |  0.000431673 |      0.000140914 |   0.00039992  |             3.35285 | plus_one_permutation_p_value     | nan           | nan           |          5000 |                   nan |                         1 |
| standard_plus_BNF_vs_standard_CMS_like              | standard_plus_BNF              | delong_correlated_auc          |  0.000676175 |      0.000168435 |   2.97929e-05 |             4.01444 | analytic_normal_approximation    | nan           | nan           |           nan |                   nan |                       nan |
| standard_plus_BNF_vs_standard_CMS_like              | standard_plus_BNF              | paired_test_set_bootstrap      |  0.000676175 |      0.000170787 |   0.00049975  |             3.29067 | floor_1_over_n_plus_1            |   0.000333725 |   0.00100374  |          2000 |                     0 |                       nan |
| standard_plus_BNF_vs_standard_CMS_like              | standard_plus_BNF              | paired_score_label_permutation |  0.000676175 |      0.000168481 |   0.00019996  |             3.54014 | plus_one_permutation_p_value     | nan           | nan           |          5000 |                   nan |                         0 |
| standard_plus_full_NFrame_axes_vs_standard_CMS_like | standard_plus_full_NFrame_axes | delong_correlated_auc          |  0.00509999  |      0.000342556 |   1.97056e-50 |            14.888   | analytic_normal_approximation    | nan           | nan           |           nan |                   nan |                       nan |
| standard_plus_full_NFrame_axes_vs_standard_CMS_like | standard_plus_full_NFrame_axes | paired_test_set_bootstrap      |  0.00509999  |      0.000349483 |   0.00049975  |             3.29067 | floor_1_over_n_plus_1            |   0.00441514  |   0.00578354  |          2000 |                     0 |                       nan |
| standard_plus_full_NFrame_axes_vs_standard_CMS_like | standard_plus_full_NFrame_axes | paired_score_label_permutation |  0.00509999  |      0.000298533 |   0.00019996  |             3.54014 | plus_one_permutation_p_value     | nan           | nan           |          5000 |                   nan |                         0 |
| trace_axis_alone_vs_standard_CMS_like               | trace_axis_alone               | delong_correlated_auc          | -0.381142    |      0.0031889   |   1           |          -119.522   | analytic_normal_approximation    | nan           | nan           |           nan |                   nan |                       nan |
| trace_axis_alone_vs_standard_CMS_like               | trace_axis_alone               | paired_test_set_bootstrap      | -0.381142    |      0.00323304  |   1           |          -inf       | empirical_fraction_delta_le_zero |  -0.387623    |  -0.374795    |          2000 |                  2000 |                       nan |
| trace_axis_alone_vs_standard_CMS_like               | trace_axis_alone               | paired_score_label_permutation | -0.381142    |      0.00296449  |   1           |          -inf       | plus_one_permutation_p_value     | nan           | nan           |          5000 |                   nan |                      5000 |
| BNF_alone_vs_standard_CMS_like                      | BNF_alone                      | delong_correlated_auc          | -0.486836    |      0.00326531  |   1           |          -149.093   | analytic_normal_approximation    | nan           | nan           |           nan |                   nan |                       nan |
| BNF_alone_vs_standard_CMS_like                      | BNF_alone                      | paired_test_set_bootstrap      | -0.486836    |      0.00325325  |   1           |          -inf       | empirical_fraction_delta_le_zero |  -0.493246    |  -0.480594    |          2000 |                  2000 |                       nan |
| BNF_alone_vs_standard_CMS_like                      | BNF_alone                      | paired_score_label_permutation | -0.486836    |      0.00346027  |   1           |          -inf       | plus_one_permutation_p_value     | nan           | nan           |          5000 |                   nan |                      5000 |

## Per-signal-family DeLong checks

| test                  |    delta_auc |   standard_error |   p_one_sided |   sigma_one_sided_Z | p_value_note                  | process_label                             | tested_model             |   n_signal_test |   n_sm_test |   auc_standard |   auc_tested |
|:----------------------|-------------:|-----------------:|--------------:|--------------------:|:------------------------------|:------------------------------------------|:-------------------------|----------------:|------------:|---------------:|-------------:|
| delong_correlated_auc | -0.00116793  |      0.000465985 |   0.993901    |           -2.50637  | analytic_normal_approximation | SMS-T2tt                                  | standard_plus_trace_axis |             429 |       16320 |       0.99045  |     0.989282 |
| delong_correlated_auc |  0.000278098 |      5.96566e-05 |   1.56839e-06 |            4.66165  | analytic_normal_approximation | SMS-T2tt compressed stop mStop300 mLSP290 | standard_plus_trace_axis |           15027 |       16320 |       0.992454 |     0.992732 |
| delong_correlated_auc |  0.000647013 |      0.00332453  |   0.422846    |            0.194618 | analytic_normal_approximation | gluino                                    | standard_plus_trace_axis |             270 |       16320 |       0.742035 |     0.742682 |
| delong_correlated_auc |  0.0053659   |      0.00313657  |   0.0435632   |            1.71075  | analytic_normal_approximation | neutralino                                | standard_plus_trace_axis |             595 |       16320 |       0.902906 |     0.908271 |
| delong_correlated_auc | -0.00133276  |      0.000671587 |   0.976399    |           -1.98449  | analytic_normal_approximation | SMS-T2tt                                  | standard_plus_BNF        |             429 |       16320 |       0.99045  |     0.989117 |
| delong_correlated_auc |  0.000341909 |      6.98323e-05 |   4.88681e-07 |            4.89614  | analytic_normal_approximation | SMS-T2tt compressed stop mStop300 mLSP290 | standard_plus_BNF        |           15027 |       16320 |       0.992454 |     0.992796 |
| delong_correlated_auc |  0.00793755  |      0.00388124  |   0.0204222   |            2.04511  | analytic_normal_approximation | gluino                                    | standard_plus_BNF        |             270 |       16320 |       0.742035 |     0.749972 |
| delong_correlated_auc |  0.00727159  |      0.00378739  |   0.0274322   |            1.91995  | analytic_normal_approximation | neutralino                                | standard_plus_BNF        |             595 |       16320 |       0.902906 |     0.910177 |
