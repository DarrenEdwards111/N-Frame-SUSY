# Grouped Record-Holdout Predictive Test

## Purpose

This replaces the earlier event-randomised benchmark split. Every fold holds out
one complete signal benchmark record and a disjoint set of SM records. No
source record appears in both model fitting and evaluation.

## Record-fold manifest

|   target |   fold |   record_id | process_label                                                |   sampled_events |
|---------:|-------:|------------:|:-------------------------------------------------------------|-----------------:|
|        0 |      0 |       36928 | ggZH_ZToQQ_HToInvisible_M125_TuneCP5_13TeV_powheg_pythia8    |              187 |
|        0 |      0 |       63102 | QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8  |              489 |
|        0 |      0 |       63139 | QCD HT700to1000                                              |              196 |
|        0 |      0 |       72753 | WZ                                                           |             1000 |
|        0 |      1 |       38502 | WW                                                           |              323 |
|        0 |      1 |       63118 | QCD_HT300to500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8   |             3000 |
|        0 |      1 |       67733 | TTJets inclusive                                             |             3000 |
|        0 |      1 |       74909 | ZJetsToNuNu                                                  |               66 |
|        0 |      2 |       63078 | QCD HT1000to1500                                             |              794 |
|        0 |      2 |       63126 | QCD_HT500to700_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8   |             1191 |
|        0 |      2 |       69548 | W3JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8                |              866 |
|        0 |      2 |       75592 | ZZ_TuneCP5_13TeV-pythia8                                     |             1000 |
|        0 |      3 |       63079 | QCD HT1000to1500                                             |             3000 |
|        0 |      3 |       63127 | QCD HT500to700                                               |             3000 |
|        0 |      3 |       69550 | WJetsToLNu                                                   |              457 |
|        0 |      4 |       63094 | QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8 |              737 |
|        0 |      4 |       63138 | QCD HT700to1000                                              |             3000 |
|        0 |      4 |       69747 | WJetsToLNu                                                   |             3000 |
|        1 |      0 |       40117 | neutralino                                                   |             2000 |
|        1 |      1 |       63454 | SMS-T2tt                                                     |             1453 |
|        1 |      2 |       63465 | SMS-T5Wg mGluino1500 mLSP1                                   |             3000 |
|        1 |      3 |       63579 | gluino                                                       |              948 |
|        1 |      4 |       64906 | SUSY HToAA4B mA12                                            |             2394 |

## Fold AUCs

|   fold | model                          |   n_train |   n_test |   heldout_signal_records | heldout_sm_records              |      auc |
|-------:|:-------------------------------|----------:|---------:|-------------------------:|:--------------------------------|---------:|
|      0 | standard_CMS_like              |     31229 |     3872 |             40117.000000 | 36928.0;63102.0;63139.0;72753.0 | 0.563937 |
|      0 | standard_plus_trace_axis       |     31229 |     3872 |             40117.000000 | 36928.0;63102.0;63139.0;72753.0 | 0.590324 |
|      0 | standard_plus_BNF              |     31229 |     3872 |             40117.000000 | 36928.0;63102.0;63139.0;72753.0 | 0.606132 |
|      0 | standard_plus_full_NFrame_axes |     31229 |     3872 |             40117.000000 | 36928.0;63102.0;63139.0;72753.0 | 0.589142 |
|      1 | standard_CMS_like              |     27259 |     7842 |             63454.000000 | 38502.0;63118.0;67733.0;74909.0 | 0.859937 |
|      1 | standard_plus_trace_axis       |     27259 |     7842 |             63454.000000 | 38502.0;63118.0;67733.0;74909.0 | 0.837601 |
|      1 | standard_plus_BNF              |     27259 |     7842 |             63454.000000 | 38502.0;63118.0;67733.0;74909.0 | 0.821379 |
|      1 | standard_plus_full_NFrame_axes |     27259 |     7842 |             63454.000000 | 38502.0;63118.0;67733.0;74909.0 | 0.910396 |
|      2 | standard_CMS_like              |     28250 |     6851 |             63465.000000 | 63078.0;63126.0;69548.0;75592.0 | 0.983053 |
|      2 | standard_plus_trace_axis       |     28250 |     6851 |             63465.000000 | 63078.0;63126.0;69548.0;75592.0 | 0.988182 |
|      2 | standard_plus_BNF              |     28250 |     6851 |             63465.000000 | 63078.0;63126.0;69548.0;75592.0 | 0.994958 |
|      2 | standard_plus_full_NFrame_axes |     28250 |     6851 |             63465.000000 | 63078.0;63126.0;69548.0;75592.0 | 0.999881 |
|      3 | standard_CMS_like              |     27696 |     7405 |             63579.000000 | 63079.0;63127.0;69550.0         | 0.641947 |
|      3 | standard_plus_trace_axis       |     27696 |     7405 |             63579.000000 | 63079.0;63127.0;69550.0         | 0.665694 |
|      3 | standard_plus_BNF              |     27696 |     7405 |             63579.000000 | 63079.0;63127.0;69550.0         | 0.690309 |
|      3 | standard_plus_full_NFrame_axes |     27696 |     7405 |             63579.000000 | 63079.0;63127.0;69550.0         | 0.772520 |
|      4 | standard_CMS_like              |     25970 |     9131 |             64906.000000 | 63094.0;63138.0;69747.0         | 0.320355 |
|      4 | standard_plus_trace_axis       |     25970 |     9131 |             64906.000000 | 63094.0;63138.0;69747.0         | 0.331428 |
|      4 | standard_plus_BNF              |     25970 |     9131 |             64906.000000 | 63094.0;63138.0;69747.0         | 0.454832 |
|      4 | standard_plus_full_NFrame_axes |     25970 |     9131 |             64906.000000 | 63094.0;63138.0;69747.0         | 0.515081 |

## Incrementality summary

| tested_model                   |   mean_delta_auc |   median_delta_auc |   folds_positive |   fold_count |   cluster_sign_flip_p_one_sided |   cluster_sign_flip_Z_one_sided |
|:-------------------------------|-----------------:|-------------------:|-----------------:|-------------:|--------------------------------:|--------------------------------:|
| standard_plus_trace_axis       |         0.008800 |           0.011073 |                4 |            5 |                        0.181818 |                        0.908458 |
| standard_plus_BNF              |         0.039676 |           0.042196 |                4 |            5 |                        0.121212 |                        1.168949 |
| standard_plus_full_NFrame_axes |         0.083558 |           0.050459 |                5 |            5 |                        0.060606 |                        1.549706 |

## Interpretation rule

This is a benchmark-method generalisation test, not a collision-data anomaly
test and not a SUSY discovery. The cluster sign-flip statistic is deliberately
conservative because there are only five independent signal benchmark records.
Only a consistent positive increment across held-out records supports a claim
that the N-Frame features generalise beyond standard CMS-like variables.
