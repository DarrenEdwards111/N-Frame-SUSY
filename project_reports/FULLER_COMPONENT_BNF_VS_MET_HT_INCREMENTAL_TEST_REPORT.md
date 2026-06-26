# Fuller Component B_NF Versus MET/HT Incremental Test Report

Date: 2026-06-09

This checks whether the fitted N-Frame score adds separation beyond simpler MET/visible-energy/multiplicity components.

| signal_sample                        | background_sample      | score                                    |          auc |   signal_mean |   background_mean |   mean_difference |
|:-------------------------------------|:-----------------------|:-----------------------------------------|-------------:|--------------:|------------------:|------------------:|
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | B_NF_fitted                              |   0.121018   |    0.38747    |         1.45927   |        -1.0718    |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | P_missing_only                           |   0.992643   |    4.86883    |        -0.0689071 |         4.93774   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | P_visible_energy_only                    |   0.0159519  |    0.599504   |         3.43985   |        -2.84035   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | P_multiplicity_only                      |   0.136229   |    0.00280818 |         1.10234   |        -1.09953   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | P_missing_plus_visible                   |   0.694231   |    2.73417    |         1.68547   |         1.04869   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | P_missing_plus_visible_plus_multiplicity |   0.528449   |    1.82371    |         1.4911    |         0.332619  |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | P_displacement_plus_reconstruction       |   0.11761    |    0.0665226  |         1.52099   |        -1.45446   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | B_NF_without_missing                     |   0.0568448  |    0.0977741  |         1.46337   |        -1.3656    |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht1000to1500_63078 | B_NF_without_displacement_reconstruction |   0.296624   |    0.315444   |         0.448491  |        -0.133047  |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | B_NF_fitted                              |   0.236667   |    0.38747    |         0.975532  |        -0.588063  |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | P_missing_only                           |   0.998466   |    4.86883    |        -0.316112  |         5.18494   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | P_visible_energy_only                    |   0.0867347  |    0.599504   |         1.9497    |        -1.3502    |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | P_multiplicity_only                      |   0.195833   |    0.00280818 |         0.737563  |        -0.734754  |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | P_missing_plus_visible                   |   0.918015   |    2.73417    |         0.816794  |         1.91737   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | P_missing_plus_visible_plus_multiplicity |   0.815377   |    1.82371    |         0.790383  |         1.03333   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | P_displacement_plus_reconstruction       |   0.184425   |    0.0665226  |         1.08259   |        -1.01607   |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | B_NF_without_missing                     |   0.129629   |    0.0977741  |         0.994341  |        -0.896567  |
| sms_t2tt_compressed_nanoaodsim_pilot | qcd_ht700to1000_63139  | B_NF_without_displacement_reconstruction |   0.540911   |    0.315444   |         0.245899  |         0.0695454 |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | B_NF_fitted                              |   0.586975   |    0.38747    |         0.236943  |         0.150527  |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | P_missing_only                           |   0.972954   |    4.86883    |         0.27745   |         4.59138   |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | P_visible_energy_only                    |   0.804931   |    0.599504   |        -0.0664587 |         0.665963  |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | P_multiplicity_only                      |   0.447395   |    0.00280818 |         0.153059  |        -0.150251  |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | P_missing_plus_visible                   |   0.963885   |    2.73417    |         0.105496  |         2.62867   |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | P_missing_plus_visible_plus_multiplicity |   0.937119   |    1.82371    |         0.12135   |         1.70236   |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | P_displacement_plus_reconstruction       |   0.405537   |    0.0665226  |         0.285394  |        -0.218871  |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | B_NF_without_missing                     |   0.432708   |    0.0977741  |         0.220435  |        -0.122661  |
| sms_t2tt_compressed_nanoaodsim_pilot | wjetstolnu_69550       | B_NF_without_displacement_reconstruction |   0.829331   |    0.315444   |         0.0193458 |         0.296098  |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | B_NF_fitted                              |   0.598354   |    1.6124     |         1.45927   |         0.153129  |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | P_missing_only                           |   0.99108    |    9.82685    |        -0.0689071 |         9.89576   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | P_visible_energy_only                    |   0.850772   |    5.28199    |         3.43985   |         1.84213   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | P_multiplicity_only                      |   0.925199   |    3.06615    |         1.10234   |         1.96382   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | P_missing_plus_visible                   |   0.995309   |    7.55442    |         1.68547   |         5.86895   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | P_missing_plus_visible_plus_multiplicity |   0.99835    |    6.05833    |         1.4911    |         4.56724   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | P_displacement_plus_reconstruction       | nan          |  nan          |         1.52099   |       nan         |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | B_NF_without_missing                     |   0.338169   |    1.0277     |         1.46337   |        -0.435669  |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht1000to1500_63078 | B_NF_without_displacement_reconstruction |   0.995006   |    1.6124     |         0.448491  |         1.16391   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | B_NF_fitted                              |   0.794752   |    1.6124     |         0.975532  |         0.63687   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | P_missing_only                           |   0.995212   |    9.82685    |        -0.316112  |        10.143     |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | P_visible_energy_only                    |   0.989067   |    5.28199    |         1.9497    |         3.33229   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | P_multiplicity_only                      |   0.974342   |    3.06615    |         0.737563  |         2.32859   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | P_missing_plus_visible                   |   0.999695   |    7.55442    |         0.816794  |         6.73763   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | P_missing_plus_visible_plus_multiplicity |   0.999965   |    6.05833    |         0.790383  |         5.26795   |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | P_displacement_plus_reconstruction       | nan          |  nan          |         1.08259   |       nan         |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | B_NF_without_missing                     |   0.53426    |    1.0277     |         0.994341  |         0.0333639 |
| sms_t5wg_mg1500_mlsp1_signal         | qcd_ht700to1000_63139  | B_NF_without_displacement_reconstruction |   0.99981    |    1.6124     |         0.245899  |         1.3665    |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | B_NF_fitted                              |   0.966405   |    1.6124     |         0.236943  |         1.37546   |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | P_missing_only                           |   0.98219    |    9.82685    |         0.27745   |         9.5494    |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | P_visible_energy_only                    |   0.99817    |    5.28199    |        -0.0664587 |         5.34844   |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | P_multiplicity_only                      |   0.992249   |    3.06615    |         0.153059  |         2.91309   |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | P_missing_plus_visible                   |   0.998481   |    7.55442    |         0.105496  |         7.44892   |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | P_missing_plus_visible_plus_multiplicity |   0.999411   |    6.05833    |         0.12135   |         5.93698   |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | P_displacement_plus_reconstruction       | nan          |  nan          |         0.285394  |       nan         |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | B_NF_without_missing                     |   0.902512   |    1.0277     |         0.220435  |         0.80727   |
| sms_t5wg_mg1500_mlsp1_signal         | wjetstolnu_69550       | B_NF_without_displacement_reconstruction |   0.999796   |    1.6124     |         0.0193458 |         1.59306   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | B_NF_fitted                              |   0.0226158  |    0.0390909  |         1.45927   |        -1.42018   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | P_missing_only                           |   0.281419   |   -0.51539    |        -0.0689071 |        -0.446483  |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | P_visible_energy_only                    |   0.00128102 |   -0.344395   |         3.43985   |        -3.78425   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | P_multiplicity_only                      |   0.0698277  |   -0.339148   |         1.10234   |        -1.44149   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | P_missing_plus_visible                   |   0.00280456 |   -0.429892   |         1.68547   |        -2.11537   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | P_missing_plus_visible_plus_multiplicity |   0.00396352 |   -0.399644   |         1.4911    |        -1.89074   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | P_displacement_plus_reconstruction       | nan          |  nan          |         1.52099   |       nan         |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | B_NF_without_missing                     |   0.0240663  |    0.0697566  |         1.46337   |        -1.39362   |
| susy_htoaa4b_m12_signal              | qcd_ht1000to1500_63078 | B_NF_without_displacement_reconstruction |   0.0928439  |    0.0390909  |         0.448491  |        -0.4094    |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | B_NF_fitted                              |   0.0924185  |    0.0390909  |         0.975532  |        -0.936441  |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | P_missing_only                           |   0.379358   |   -0.51539    |        -0.316112  |        -0.199278  |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | P_visible_energy_only                    |   0.00612927 |   -0.344395   |         1.9497    |        -2.29409   |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | P_multiplicity_only                      |   0.104756   |   -0.339148   |         0.737563  |        -1.07671   |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | P_missing_plus_visible                   |   0.0126677  |   -0.429892   |         0.816794  |        -1.24669   |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | P_missing_plus_visible_plus_multiplicity |   0.0195536  |   -0.399644   |         0.790383  |        -1.19003   |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | P_displacement_plus_reconstruction       | nan          |  nan          |         1.08259   |       nan         |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | B_NF_without_missing                     |   0.0956217  |    0.0697566  |         0.994341  |        -0.924584  |
| susy_htoaa4b_m12_signal              | qcd_ht700to1000_63139  | B_NF_without_displacement_reconstruction |   0.241578   |    0.0390909  |         0.245899  |        -0.206808  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | B_NF_fitted                              |   0.413442   |    0.0390909  |         0.236943  |        -0.197852  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | P_missing_only                           |   0.202945   |   -0.51539    |         0.27745   |        -0.79284   |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | P_visible_energy_only                    |   0.320552   |   -0.344395   |        -0.0664587 |        -0.277936  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | P_multiplicity_only                      |   0.306847   |   -0.339148   |         0.153059  |        -0.492207  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | P_missing_plus_visible                   |   0.184284   |   -0.429892   |         0.105496  |        -0.535388  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | P_missing_plus_visible_plus_multiplicity |   0.200999   |   -0.399644   |         0.12135   |        -0.520994  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | P_displacement_plus_reconstruction       | nan          |  nan          |         0.285394  |       nan         |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | B_NF_without_missing                     |   0.441765   |    0.0697566  |         0.220435  |        -0.150678  |
| susy_htoaa4b_m12_signal              | wjetstolnu_69550       | B_NF_without_displacement_reconstruction |   0.532085   |    0.0390909  |         0.0193458 |         0.0197451 |

## Median AUC By Score

| score                                    |      auc |
|:-----------------------------------------|---------:|
| P_missing_only                           | 0.98219  |
| P_missing_plus_visible                   | 0.918015 |
| P_missing_plus_visible_plus_multiplicity | 0.815377 |
| B_NF_without_displacement_reconstruction | 0.540911 |
| B_NF_fitted                              | 0.413442 |
| B_NF_without_missing                     | 0.338169 |
| P_visible_energy_only                    | 0.320552 |
| P_multiplicity_only                      | 0.306847 |
| P_displacement_plus_reconstruction       | 0.184425 |