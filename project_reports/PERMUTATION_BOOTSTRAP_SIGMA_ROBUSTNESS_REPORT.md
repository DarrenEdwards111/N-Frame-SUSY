# Permutation Bootstrap Sigma Robustness Report

Date: 2026-06-09

## Bootstrap

| signal_sample                | background_sample                | threshold   |   tail_diff_ci95_low |   tail_diff_median |   tail_diff_ci95_high |   tail_ratio_ci95_low |   tail_ratio_median |   tail_ratio_ci95_high |   mean_BNF_diff_ci95_low |   mean_BNF_diff_median |   mean_BNF_diff_ci95_high |   median_BNF_diff_ci95_low |   median_BNF_diff_median |   median_BNF_diff_ci95_high |
|:-----------------------------|:---------------------------------|:------------|---------------------:|-------------------:|----------------------:|----------------------:|--------------------:|-----------------------:|-------------------------:|-----------------------:|--------------------------:|---------------------------:|-------------------------:|----------------------------:|
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q90         |           0.450109   |            0.46408 |              0.479022 |               3.52518 |             3.6281  |                3.73187 |                 0.722688 |               0.736725 |                  0.750536 |                   0.724264 |                 0.741108 |                    0.759192 |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q95         |           0.137037   |            0.14904 |              0.15994  |               3.76482 |             4.03733 |                4.32793 |                 0.722688 |               0.736725 |                  0.750536 |                   0.724264 |                 0.741108 |                    0.759192 |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q99         |           0.0003195  |            0.00204 |              0.00428  |               1.10411 |             1.65644 |                2.48489 |                 0.722688 |               0.736725 |                  0.750536 |                   0.724264 |                 0.741108 |                    0.759192 |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q90         |           0.531439   |            0.54514 |              0.558784 |               6.47318 |             6.70706 |                6.92851 |                 0.968785 |               0.981947 |                  0.995738 |                   1.00246  |                 1.01827  |                    1.03506  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q95         |           0.161839   |            0.1735  |              0.184    |               7.45836 |             8.07803 |                8.71802 |                 0.968785 |               0.981947 |                  0.995738 |                   1.00246  |                 1.01827  |                    1.03506  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q99         |           0.00216    |            0.00388 |              0.006001 |               2.65756 |             4.17289 |                6.66667 |                 0.968785 |               0.981947 |                  0.995738 |                   1.00246  |                 1.01827  |                    1.03506  |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q90         |           0.491489   |            0.50445 |              0.517632 |               4.5896  |             4.70807 |                4.8342  |                 0.845854 |               0.859199 |                  0.872506 |                   0.867017 |                 0.883319 |                    0.900262 |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q95         |           0.149677   |            0.16092 |              0.172043 |               5.03899 |             5.3625  |                5.73035 |                 0.845854 |               0.859199 |                  0.872506 |                   0.867017 |                 0.883319 |                    0.900262 |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q99         |           0.00112975 |            0.003   |              0.005151 |               1.50431 |             2.40906 |                3.43439 |                 0.845854 |               0.859199 |                  0.872506 |                   0.867017 |                 0.883319 |                    0.900262 |

## Permutation

| signal_sample                | background_sample                | threshold   |   observed_tail_difference |   permutation_p_one_sided |   permutation_z_equivalent |   permutations |
|:-----------------------------|:---------------------------------|:------------|---------------------------:|--------------------------:|---------------------------:|---------------:|
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q90         |                    0.46384 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q95         |                    0.14872 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q99         |                    0.00214 |                0.0138986  |                    2.20014 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q90         |                    0.54492 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q95         |                    0.17334 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q99         |                    0.00398 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q90         |                    0.50438 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q95         |                    0.16103 |                9.999e-05  |                    3.71904 |          10000 |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q99         |                    0.00306 |                0.00019998 |                    3.54011 |          10000 |

## Equal-Size Subsampling

| signal_sample                | background_sample                | threshold   |   tail_diff_ci95_low |   tail_diff_median |   tail_diff_ci95_high |   z_ci95_low |   z_median |   z_ci95_high |
|:-----------------------------|:---------------------------------|:------------|---------------------:|-------------------:|----------------------:|-------------:|-----------:|--------------:|
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q90         |             0.453595 |             0.464  |              0.473605 |    46.0522   |   47.1988  |      48.2661  |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q95         |             0.142995 |             0.149  |              0.1544   |    21.5231   |   22.6594  |      23.7056  |
| sms_t5wg_mg1500_mlsp1_signal | ttjets_nanoaodsim_pilot          | q99         |             0.0006   |             0.0022 |              0.0034   |     0.429625 |    1.72144 |       2.87857 |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q90         |             0.5378   |             0.5452 |              0.5528   |    55.6492   |   56.5318  |      57.4459  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q95         |             0.1692   |             0.1734 |              0.1772   |    26.7014   |   27.589   |      28.4075  |
| sms_t5wg_mg1500_mlsp1_signal | qcd_ht700to1000_nanoaodsim_pilot | q99         |             0.003    |             0.004  |              0.0048   |     2.47056  |    3.5412  |       4.54194 |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q90         |             0.495    |             0.5044 |              0.5134   |    50.6762   |   51.7503  |      52.7878  |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q95         |             0.156    |             0.161  |              0.165805 |    24.0201   |   25.0173  |      25.9965  |
| sms_t5wg_mg1500_mlsp1_signal | pooled_sm_background             | q99         |             0.0018   |             0.0032 |              0.0042   |     1.37545  |    2.67148 |       3.77757 |