# N-Frame Parameter Fit Report

Date: 2026-06-08

Parameters were fitted from matched real-data case-control contrasts. Labels mean high-boundary case versus matched ordinary control, not SUSY.

## Parameter Importance

| tail         | family               |   mean_standardised_contrast |   abs_mean_standardised_contrast |   bootstrap_ci_low |   bootstrap_ci_high |   sign |   cases |
|:-------------|:---------------------|-----------------------------:|---------------------------------:|-------------------:|--------------------:|-------:|--------:|
| hand_top001  | P_displacement_proxy |                   2.18029    |                       2.18029    |         2.05523    |           2.32998   |      1 |     605 |
| hand_top001  | P_reconstruction     |                   1.32623    |                       1.32623    |         1.25718    |           1.39524   |      1 |     605 |
| hand_top001  | P_multiplicity       |                   1.28508    |                       1.28508    |         1.22481    |           1.35891   |      1 |     605 |
| hand_top001  | P_btag_structure     |                   0.963575   |                       0.963575   |         0.902291   |           1.49031   |      1 |     605 |
| hand_top001  | P_visible_energy     |                   0.860683   |                       0.860683   |         0.790002   |           0.948905  |      1 |     605 |
| hand_top001  | P_missing            |                   0.634277   |                       0.634277   |         0.558639   |           0.726536  |      1 |     605 |
| hand_top001  | P_compression        |                  -0.0720763  |                       0.0720763  |        -0.150007   |           0.0118129 |     -1 |     605 |
| hand_top01   | P_displacement_proxy |                   1.82984    |                       1.82984    |         1.79046    |           1.86778   |      1 |    6049 |
| hand_top01   | P_reconstruction     |                   1.09721    |                       1.09721    |         1.07653    |           1.11717   |      1 |    6049 |
| hand_top01   | P_multiplicity       |                   1.07703    |                       1.07703    |         1.0543     |           1.09657   |      1 |    6049 |
| hand_top01   | P_btag_structure     |                   0.863486   |                       0.863486   |         0.84235    |           0.883618  |      1 |    6049 |
| hand_top01   | P_visible_energy     |                   0.7341     |                       0.7341     |         0.713483   |           0.758418  |      1 |    6049 |
| hand_top01   | P_missing            |                   0.618647   |                       0.618647   |         0.594696   |           0.644871  |      1 |    6049 |
| hand_top01   | P_compression        |                   0.0343393  |                       0.0343393  |         0.00973643 |           0.0560779 |      1 |    6049 |
| hand_top05   | P_displacement_proxy |                   1.50433    |                       1.50433    |         1.48911    |           1.51899   |      1 |   30243 |
| hand_top05   | P_multiplicity       |                   0.925628   |                       0.925628   |         0.915888   |           0.934383  |      1 |   30243 |
| hand_top05   | P_reconstruction     |                   0.875186   |                       0.875186   |         0.867711   |           0.882464  |      1 |   30243 |
| hand_top05   | P_btag_structure     |                   0.728839   |                       0.728839   |         0.721423   |           0.7365    |      1 |   30243 |
| hand_top05   | P_visible_energy     |                   0.656994   |                       0.656994   |         0.646159   |           0.666816  |      1 |   30243 |
| hand_top05   | P_missing            |                   0.585897   |                       0.585897   |         0.574677   |           0.597476  |      1 |   30243 |
| hand_top05   | P_compression        |                   0.0668893  |                       0.0668893  |         0.0564728  |           0.0768333 |      1 |   30243 |
| unsup_top001 | P_displacement_proxy |                   0.852765   |                       0.852765   |         0.788947   |           0.930063  |      1 |     605 |
| unsup_top001 | P_reconstruction     |                   0.459561   |                       0.459561   |         0.415995   |           0.505015  |      1 |     605 |
| unsup_top001 | P_multiplicity       |                   0.375802   |                       0.375802   |         0.324638   |           0.439675  |      1 |     605 |
| unsup_top001 | P_compression        |                   0.320671   |                       0.320671   |         0.237894   |           0.399945  |      1 |     605 |
| unsup_top001 | P_missing            |                  -0.155708   |                       0.155708   |        -0.226914   |          -0.0870102 |     -1 |     605 |
| unsup_top001 | P_visible_energy     |                  -0.0795042  |                       0.0795042  |        -0.133712   |          -0.0164822 |     -1 |     605 |
| unsup_top001 | P_btag_structure     |                   0.0502158  |                       0.0502158  |        -0.00447327 |           0.104488  |      1 |     605 |
| unsup_top01  | P_displacement_proxy |                   0.754684   |                       0.754684   |         0.734882   |           0.776573  |      1 |    6049 |
| unsup_top01  | P_reconstruction     |                   0.45468    |                       0.45468    |         0.442243   |           0.465801  |      1 |    6049 |
| unsup_top01  | P_multiplicity       |                   0.394025   |                       0.394025   |         0.376077   |           0.41161   |      1 |    6049 |
| unsup_top01  | P_btag_structure     |                   0.186675   |                       0.186675   |         0.173283   |           0.201499  |      1 |    6049 |
| unsup_top01  | P_missing            |                  -0.176197   |                       0.176197   |        -0.197314   |          -0.154392  |     -1 |    6049 |
| unsup_top01  | P_visible_energy     |                   0.0161445  |                       0.0161445  |        -0.0033698  |           0.0342851 |      1 |    6049 |
| unsup_top01  | P_compression        |                   0.00178578 |                       0.00178578 |        -0.0218159  |           0.0294517 |      1 |    6049 |
| unsup_top05  | P_displacement_proxy |                   0.717109   |                       0.717109   |         0.707617   |           0.727204  |      1 |   30243 |
| unsup_top05  | P_reconstruction     |                   0.452115   |                       0.452115   |         0.44672    |           0.457739  |      1 |   30243 |
| unsup_top05  | P_multiplicity       |                   0.419448   |                       0.419448   |         0.411667   |           0.428284  |      1 |   30243 |
| unsup_top05  | P_btag_structure     |                   0.267042   |                       0.267042   |         0.261096   |           0.272979  |      1 |   30243 |
| unsup_top05  | P_compression        |                  -0.241578   |                       0.241578   |        -0.251583   |          -0.230826  |     -1 |   30243 |
| unsup_top05  | P_missing            |                  -0.169363   |                       0.169363   |        -0.17977    |          -0.160178  |     -1 |   30243 |
| unsup_top05  | P_visible_energy     |                   0.128287   |                       0.128287   |         0.120265   |           0.137815  |      1 |   30243 |

## Logistic Performance

| tail         | model                       |   mean_auc |   mean_accuracy |   folds |
|:-------------|:----------------------------|-----------:|----------------:|--------:|
| hand_top001  | l1_logistic_grouped_by_case |   0.998648 |        0.983471 |       5 |
| hand_top01   | l1_logistic_grouped_by_case |   0.997863 |        0.979417 |       5 |
| hand_top05   | l1_logistic_grouped_by_case |   0.99708  |        0.972589 |       5 |
| unsup_top001 | l1_logistic_grouped_by_case |   0.961779 |        0.920661 |       5 |
| unsup_top01  | l1_logistic_grouped_by_case |   0.842514 |        0.798561 |       5 |
| unsup_top05  | l1_logistic_grouped_by_case |   0.778141 |        0.709602 |       5 |

## Ranking Accuracy

| tail         |   ranking_accuracy_case_above_controls |   cases |
|:-------------|---------------------------------------:|--------:|
| hand_top001  |                               1        |     605 |
| hand_top01   |                               0.998016 |    6049 |
| hand_top05   |                               0.997355 |   30243 |
| unsup_top001 |                               0.966942 |     605 |
| unsup_top01  |                               0.865102 |    6049 |
| unsup_top05  |                               0.811394 |   30243 |