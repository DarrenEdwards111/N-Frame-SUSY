# ATLAS Score Variant Scan

## Purpose

The first ATLAS one-lepton analogue did not reproduce the CMS 1-2 jet Q99 excess. This scan checks whether that depends on the exact visible-axis definition.

## Variants

| variant             | visible_columns                                                   |
|:--------------------|:------------------------------------------------------------------|
| lepton_aware_resid  | log1p_HT, N_jets_30, N_btags_medium, N_leptons, leading_lepton_pt |
| jets_only_resid     | log1p_HT, N_jets_30, N_btags_medium                               |
| jetcount_only_resid | N_jets_30                                                         |
| raw_missing_z       | none/raw missing z                                                |

## Result

| variant             | jet_bin   |   real_events |   sideband_80_95_obs_exp |    q99_observed |   q99_expected_shape |   q99_obs_exp |   sideband_log_rms |   relative_uncertainty_used |      q99_Z |
|:--------------------|:----------|--------------:|-------------------------:|----------------:|---------------------:|--------------:|-------------------:|----------------------------:|-----------:|
| lepton_aware_resid  | 0jet      |       7050055 |                 1.25323  |     6.46675e+06 |          8.14431e+06 |    0.794021   |          0.0564208 |                    0.305259 | -0.674767  |
| lepton_aware_resid  | 1to2jets  |       2560282 |                 4.69359  |    23           |       3305.91        |    0.00695724 |          0.551177  |                    0.627532 | -1.58185   |
| lepton_aware_resid  | 3to4jets  |        167033 |                 1.71217  |   132           |        242.236       |    0.544923   |          0.214407  |                    0.368742 | -1.21582   |
| lepton_aware_resid  | 5plusjets |         19039 |                 0.813253 |  1749           |        960.566       |    1.8208     |          0.263355  |                    0.399194 |  2.04946   |
| jets_only_resid     | 0jet      |       7050055 |                 1.02864  |     6.52001e+06 |          6.35999e+06 |    1.02516    |          0.0838083 |                    0.311486 |  0.0807725 |
| jets_only_resid     | 1to2jets  |       2560282 |                 6.57735  |    55           |        605.557       |    0.0908255  |          0.6205    |                    0.689217 | -1.31685   |
| jets_only_resid     | 3to4jets  |        167033 |                 1.70101  |   273           |        116.173       |    2.34994    |          0.26343   |                    0.399243 |  3.29349   |
| jets_only_resid     | 5plusjets |         19039 |                 0.774616 |  2291           |        935.276       |    2.44954    |          0.282943  |                    0.412379 |  3.50408   |
| jetcount_only_resid | 0jet      |       7050055 |                 0.918136 |     3           |          0.674663    |    4.44667    |          0.146869  |                    0.334022 |  2.73013   |
| jetcount_only_resid | 1to2jets  |       2560282 |                 0.154882 |    22           |          1.84031     |   11.9545     |          0.628617  |                    0.696534 | 10.8014    |
| jetcount_only_resid | 3to4jets  |        167033 |                 0.873005 |    42           |         32.6687      |    1.28563    |          0.0766058 |                    0.309626 |  0.803156  |
| jetcount_only_resid | 5plusjets |         19039 |                 0.973474 |  2531           |       2238.74        |    1.13055    |          0.0586012 |                    0.30567  |  0.426065  |
| raw_missing_z       | 0jet      |       7050055 |                 0.923672 | 64688           |      70246.6         |    0.92087    |          0.219695  |                    0.371841 | -0.212795  |
| raw_missing_z       | 1to2jets  |       2560282 |                 0.827017 | 20496           |      20063.1         |    1.02158    |          0.0928435 |                    0.314038 |  0.0686882 |
| raw_missing_z       | 3to4jets  |        167033 |                 0.925882 |  1556           |       1507.39        |    1.03225    |          0.052447  |                    0.30455  |  0.105515  |
| raw_missing_z       | 5plusjets |         19039 |                 0.957503 |   188           |        178.805       |    1.05143    |          0.0857335 |                    0.31201  |  0.160285  |

## Interpretation

The key row is `1to2jets` for each variant. If none is strongly positive, the public ATLAS exactly-one-lepton channel does not replicate the CMS MET-stream Q99 1-2 jet trace.
