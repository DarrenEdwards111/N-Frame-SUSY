# SUSY Versus SM Specificity Test Report

Date: 2026-06-09

## Tail Fractions

| sample_id                        | process_label              | classification   | threshold   |   threshold_value |   events |   mean_BNF |   median_BNF |   tail_fraction |    ci_low |   ci_high |
|:---------------------------------|:---------------------------|:-----------------|:------------|------------------:|---------:|-----------:|-------------:|----------------:|----------:|----------:|
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | q90         |           1.42074 |    50000 |  0.630491  |    0.55262   |         0.09548 | 0.093197  | 0.09818   |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | q95         |           1.968   |    50000 |  0.630491  |    0.55262   |         0.02446 | 0.02324   | 0.0257905 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | q99         |           3.0529  |    50000 |  0.630491  |    0.55262   |         0.00122 | 0.00096   | 0.0015305 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | q999        |           4.46877 |    50000 |  0.630491  |    0.55262   |         0       | 0         | 0         |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | q90         |           1.42074 |     5000 |  1.6124    |    1.57143   |         0.6404  | 0.6282    | 0.653905  |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | q95         |           1.968   |     5000 |  1.6124    |    1.57143   |         0.1978  | 0.186095  | 0.208905  |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | q99         |           3.0529  |     5000 |  1.6124    |    1.57143   |         0.0052  | 0.003295  | 0.0072    |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | q999        |           4.46877 |     5000 |  1.6124    |    1.57143   |         0       | 0         | 0         |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | q90         |           1.42074 |     2394 |  0.0390909 |    0.0403913 |         0       | 0         | 0         |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | q95         |           1.968   |     2394 |  0.0390909 |    0.0403913 |         0       | 0         | 0         |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | q99         |           3.0529  |     2394 |  0.0390909 |    0.0403913 |         0       | 0         | 0         |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | q999        |           4.46877 |     2394 |  0.0390909 |    0.0403913 |         0       | 0         | 0         |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | q90         |           1.42074 |    50000 |  0.875909  |    0.830251  |         0.17656 | 0.173119  | 0.18021   |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | q95         |           1.968   |    50000 |  0.875909  |    0.830251  |         0.04908 | 0.047199  | 0.050781  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | q99         |           3.0529  |    50000 |  0.875909  |    0.830251  |         0.00306 | 0.0025695 | 0.00346   |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | q999        |           4.46877 |    50000 |  0.875909  |    0.830251  |         8e-05   | 2e-05     | 0.00016   |

## Tail Ratios

| threshold   | signal_sample                | sm_background_sample             |   signal_tail_fraction |   sm_tail_fraction |   tail_ratio_signal_over_sm |   signal_minus_sm |
|:------------|:-----------------------------|:---------------------------------|-----------------------:|-------------------:|----------------------------:|------------------:|
| q90         | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                 0.6404 |            0.09548 |                     6.70716 |           0.54492 |
| q90         | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                 0.6404 |            0.17656 |                     3.6271  |           0.46384 |
| q90         | susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot |                 0      |            0.09548 |                     0       |          -0.09548 |
| q90         | susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          |                 0      |            0.17656 |                     0       |          -0.17656 |
| q95         | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                 0.1978 |            0.02446 |                     8.08667 |           0.17334 |
| q95         | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                 0.1978 |            0.04908 |                     4.03015 |           0.14872 |
| q95         | susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot |                 0      |            0.02446 |                     0       |          -0.02446 |
| q95         | susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          |                 0      |            0.04908 |                     0       |          -0.04908 |
| q99         | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                 0.0052 |            0.00122 |                     4.2623  |           0.00398 |
| q99         | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                 0.0052 |            0.00306 |                     1.69935 |           0.00214 |
| q99         | susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot |                 0      |            0.00122 |                     0       |          -0.00122 |
| q99         | susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          |                 0      |            0.00306 |                     0       |          -0.00306 |
| q999        | sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot |                 0      |            0       |                   nan       |           0       |
| q999        | sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          |                 0      |            8e-05   |                     0       |          -8e-05   |
| q999        | susy_htoaa4b_m12_signal      | qcd_ht700to1000_nanoaodsim_pilot |                 0      |            0       |                   nan       |           0       |
| q999        | susy_htoaa4b_m12_signal      | ttjets_nanoaodsim_pilot          |                 0      |            8e-05   |                     0       |          -8e-05   |

## Parameter Drivers In q95 Tail

| sample_id                        | process_label              | classification   | parameter_family     |   q95_tail_mean |   rest_mean |   top_minus_rest |   tail_events |
|:---------------------------------|:---------------------------|:-----------------|:---------------------|----------------:|------------:|-----------------:|--------------:|
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_displacement_proxy |       4.33178   |   0.939708  |        3.39207   |          1223 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_reconstruction     |       1.51232   |   0.0608901 |        1.45143   |          1223 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_multiplicity       |       1.29545   |   0.667459  |        0.627989  |          1223 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_btag_structure     |       0.851955  |  -0.0858461 |        0.937801  |          1223 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_visible_energy     |       2.03912   |   1.9796    |        0.0595232 |          1223 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_missing            |      -0.0812332 |  -0.242255  |        0.161022  |          1223 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | P_compression        |      -2.94797   |  -3.02579   |        0.0778221 |          1223 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_displacement_proxy |     nan         | nan         |      nan         |           989 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_reconstruction     |     nan         | nan         |      nan         |           989 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_multiplicity       |       3.93228   |   2.85259   |        1.07969   |           989 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_btag_structure     |       0.989996  |   0.196578  |        0.793419  |           989 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_visible_energy     |       6.20937   |   5.05332   |        1.15605   |           989 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_missing            |      16.0434    |   8.29403   |        7.74934   |           989 |
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | P_compression        |      -1.20319   |  -1.65605   |        0.452859  |           989 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_displacement_proxy |     nan         | nan         |      nan         |             0 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_reconstruction     |     nan         | nan         |      nan         |             0 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_multiplicity       |     nan         |  -0.339148  |      nan         |             0 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_btag_structure     |     nan         |   1.84995   |      nan         |             0 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_visible_energy     |     nan         |  -0.344395  |      nan         |             0 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_missing            |     nan         |  -0.51539   |      nan         |             0 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | P_compression        |     nan         |  -1.45505   |      nan         |             0 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_displacement_proxy |       3.8842    |   1.2524    |        2.6318    |          2454 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_reconstruction     |       1.3124    |   0.187818  |        1.12459   |          2454 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_multiplicity       |       1.99553   |   0.929251  |        1.06628   |          2454 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_btag_structure     |       2.29026   |   1.23442   |        1.05583   |          2454 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_visible_energy     |       1.1271    |   0.196849  |        0.930252  |          2454 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_missing            |       0.466838  |   0.107754  |        0.359084  |          2454 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | P_compression        |      -2.3267    |  -1.88446   |       -0.442246  |          2454 |

## Interpretation

At q95, at least one SUSY benchmark has higher high-B_NF occupancy than at least one SM background. This is benchmark-level SUSY-relevant enrichment only, not a discovery claim.