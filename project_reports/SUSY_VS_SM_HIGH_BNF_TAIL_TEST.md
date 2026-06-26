# SUSY Versus SM High B_NF Tail Test

Date: 2026-06-09

The fitted B_NF equation is frozen from real data. Available local samples include SUSY-like benchmarks but no local SM simulated background samples, so SUSY-vs-SM specificity is not yet testable.

## Real-Data Thresholds

| threshold_source                    | threshold   |   quantile |   value |
|:------------------------------------|:------------|-----------:|--------:|
| Run2016G_standard_quality_real_data | q90         |      0.9   | 1.42074 |
| Run2016G_standard_quality_real_data | q95         |      0.95  | 1.968   |
| Run2016G_standard_quality_real_data | q99         |      0.99  | 3.0529  |
| Run2016G_standard_quality_real_data | q999        |      0.999 | 4.46877 |

## Benchmark Tail Fractions

| sample_id                    | classification   | process_label              | threshold   |   threshold_value |   events |   tail_fraction |     ci_low |    ci_high |   mean_BNF |   median_BNF |
|:-----------------------------|:-----------------|:---------------------------|:------------|------------------:|---------:|----------------:|-----------:|-----------:|-----------:|-------------:|
| sms_t5wg_mg1500_mlsp1_signal | signal           | SMS-T5Wg mGluino1500 mLSP1 | q90         |           1.42074 |     5000 |          0.6404 | 0.627098   | 0.653702   |  1.6124    |    1.57143   |
| sms_t5wg_mg1500_mlsp1_signal | signal           | SMS-T5Wg mGluino1500 mLSP1 | q95         |           1.968   |     5000 |          0.1978 | 0.186759   | 0.208841   |  1.6124    |    1.57143   |
| sms_t5wg_mg1500_mlsp1_signal | signal           | SMS-T5Wg mGluino1500 mLSP1 | q99         |           3.0529  |     5000 |          0.0052 | 0.00320639 | 0.00719361 |  1.6124    |    1.57143   |
| sms_t5wg_mg1500_mlsp1_signal | signal           | SMS-T5Wg mGluino1500 mLSP1 | q999        |           4.46877 |     5000 |          0      | 0          | 0          |  1.6124    |    1.57143   |
| susy_htoaa4b_m12_signal      | signal           | SUSY HToAA4B mA12          | q90         |           1.42074 |     2394 |          0      | 0          | 0          |  0.0390909 |    0.0403913 |
| susy_htoaa4b_m12_signal      | signal           | SUSY HToAA4B mA12          | q95         |           1.968   |     2394 |          0      | 0          | 0          |  0.0390909 |    0.0403913 |
| susy_htoaa4b_m12_signal      | signal           | SUSY HToAA4B mA12          | q99         |           3.0529  |     2394 |          0      | 0          | 0          |  0.0390909 |    0.0403913 |
| susy_htoaa4b_m12_signal      | signal           | SUSY HToAA4B mA12          | q999        |           4.46877 |     2394 |          0      | 0          | 0          |  0.0390909 |    0.0403913 |

## Parameter Drivers

| sample_id                    | parameter_family     |   q95_tail_mean |   rest_mean |   top_minus_rest |   tail_events |
|:-----------------------------|:---------------------|----------------:|------------:|-----------------:|--------------:|
| sms_t5wg_mg1500_mlsp1_signal | P_displacement_proxy |      nan        |  nan        |       nan        |           989 |
| sms_t5wg_mg1500_mlsp1_signal | P_reconstruction     |      nan        |  nan        |       nan        |           989 |
| sms_t5wg_mg1500_mlsp1_signal | P_multiplicity       |        3.93228  |    2.85259  |         1.07969  |           989 |
| sms_t5wg_mg1500_mlsp1_signal | P_btag_structure     |        0.989996 |    0.196578 |         0.793419 |           989 |
| sms_t5wg_mg1500_mlsp1_signal | P_visible_energy     |        6.20937  |    5.05332  |         1.15605  |           989 |
| sms_t5wg_mg1500_mlsp1_signal | P_missing            |       16.0434   |    8.29403  |         7.74934  |           989 |
| sms_t5wg_mg1500_mlsp1_signal | P_compression        |       -1.20319  |   -1.65605  |         0.452859 |           989 |
| susy_htoaa4b_m12_signal      | P_displacement_proxy |      nan        |  nan        |       nan        |             0 |
| susy_htoaa4b_m12_signal      | P_reconstruction     |      nan        |  nan        |       nan        |             0 |
| susy_htoaa4b_m12_signal      | P_multiplicity       |      nan        |   -0.339148 |       nan        |             0 |
| susy_htoaa4b_m12_signal      | P_btag_structure     |      nan        |    1.84995  |       nan        |             0 |
| susy_htoaa4b_m12_signal      | P_visible_energy     |      nan        |   -0.344395 |       nan        |             0 |
| susy_htoaa4b_m12_signal      | P_missing            |      nan        |   -0.51539  |       nan        |             0 |
| susy_htoaa4b_m12_signal      | P_compression        |      nan        |   -1.45505  |       nan        |             0 |

## Interpretation

This is benchmark-level evidence only. It is not discovery evidence and not evidence that SUSY was found. A true SUSY > SM test requires ttbar/QCD/W/Z background simulations processed with the same frozen equation.