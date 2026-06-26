# N-Frame Parameter Stability Report

Date: 2026-06-08

Uncertainty was estimated by bootstrapping case IDs, not raw matched rows.

| tail         | family               |   mean_standardised_contrast |      ci_low |     ci_high |   sign_stability |   median_abs_rank |   top3_rank_fraction |
|:-------------|:---------------------|-----------------------------:|------------:|------------:|-----------------:|------------------:|---------------------:|
| hand_top001  | P_displacement_proxy |                   2.18029    |  2.0555     |  2.32826    |            1     |                 1 |                1     |
| hand_top001  | P_reconstruction     |                   1.32623    |  1.26143    |  1.3945     |            1     |                 2 |                0.94  |
| hand_top001  | P_multiplicity       |                   1.28508    |  1.22196    |  1.35718    |            1     |                 3 |                0.698 |
| hand_top001  | P_btag_structure     |                   0.963575   |  0.89997    |  1.49268    |            1     |                 4 |                0.362 |
| hand_top001  | P_visible_energy     |                   0.860683   |  0.790361   |  0.946738   |            1     |                 5 |                0     |
| hand_top001  | P_missing            |                   0.634277   |  0.563557   |  0.724436   |            1     |                 6 |                0     |
| hand_top001  | P_compression        |                  -0.0720763  | -0.150157   |  0.00953809 |            0.952 |                 7 |                0     |
| hand_top01   | P_displacement_proxy |                   1.82984    |  1.79279    |  1.86982    |            1     |                 1 |                1     |
| hand_top01   | P_reconstruction     |                   1.09721    |  1.07822    |  1.11672    |            1     |                 2 |                1     |
| hand_top01   | P_multiplicity       |                   1.07703    |  1.05374    |  1.09483    |            1     |                 3 |                1     |
| hand_top01   | P_btag_structure     |                   0.863486   |  0.844369   |  0.883728   |            1     |                 4 |                0     |
| hand_top01   | P_visible_energy     |                   0.7341     |  0.711842   |  0.757921   |            1     |                 5 |                0     |
| hand_top01   | P_missing            |                   0.618647   |  0.591546   |  0.645338   |            1     |                 6 |                0     |
| hand_top01   | P_compression        |                   0.0343393  |  0.00871932 |  0.0567821  |            0.996 |                 7 |                0     |
| hand_top05   | P_displacement_proxy |                   1.50433    |  1.48933    |  1.51948    |            1     |                 1 |                1     |
| hand_top05   | P_multiplicity       |                   0.925628   |  0.916018   |  0.935565   |            1     |                 2 |                1     |
| hand_top05   | P_reconstruction     |                   0.875186   |  0.867538   |  0.882473   |            1     |                 3 |                1     |
| hand_top05   | P_btag_structure     |                   0.728839   |  0.721982   |  0.736327   |            1     |                 4 |                0     |
| hand_top05   | P_visible_energy     |                   0.656994   |  0.647036   |  0.666848   |            1     |                 5 |                0     |
| hand_top05   | P_missing            |                   0.585897   |  0.575386   |  0.597781   |            1     |                 6 |                0     |
| hand_top05   | P_compression        |                   0.0668893  |  0.0563141  |  0.077152   |            1     |                 7 |                0     |
| unsup_top001 | P_displacement_proxy |                   0.852765   |  0.786229   |  0.916948   |            1     |                 1 |                1     |
| unsup_top001 | P_reconstruction     |                   0.459561   |  0.414614   |  0.503803   |            1     |                 2 |                1     |
| unsup_top001 | P_multiplicity       |                   0.375802   |  0.315147   |  0.435781   |            1     |                 3 |                0.814 |
| unsup_top001 | P_compression        |                   0.320671   |  0.24897    |  0.395533   |            1     |                 4 |                0.186 |
| unsup_top001 | P_missing            |                  -0.155708   | -0.227496   | -0.0800619  |            1     |                 5 |                0     |
| unsup_top001 | P_visible_energy     |                  -0.0795042  | -0.140413   | -0.019197   |            0.996 |                 6 |                0     |
| unsup_top001 | P_btag_structure     |                   0.0502158  | -0.00221311 |  0.106555   |            0.968 |                 7 |                0     |
| unsup_top01  | P_displacement_proxy |                   0.754684   |  0.733216   |  0.777576   |            1     |                 1 |                1     |
| unsup_top01  | P_reconstruction     |                   0.45468    |  0.441992   |  0.468031   |            1     |                 2 |                1     |
| unsup_top01  | P_multiplicity       |                   0.394025   |  0.375654   |  0.410158   |            1     |                 3 |                1     |
| unsup_top01  | P_btag_structure     |                   0.186675   |  0.170837   |  0.200881   |            1     |                 4 |                0     |
| unsup_top01  | P_missing            |                  -0.176197   | -0.199095   | -0.154422   |            1     |                 5 |                0     |
| unsup_top01  | P_visible_energy     |                   0.0161445  | -0.00287386 |  0.0333161  |            0.96  |                 6 |                0     |
| unsup_top01  | P_compression        |                   0.00178578 | -0.0218403  |  0.0273957  |            0.554 |                 7 |                0     |
| unsup_top05  | P_displacement_proxy |                   0.717109   |  0.707995   |  0.727946   |            1     |                 1 |                1     |
| unsup_top05  | P_reconstruction     |                   0.452115   |  0.446843   |  0.457904   |            1     |                 2 |                1     |
| unsup_top05  | P_multiplicity       |                   0.419448   |  0.410697   |  0.427346   |            1     |                 3 |                1     |
| unsup_top05  | P_btag_structure     |                   0.267042   |  0.260723   |  0.273066   |            1     |                 4 |                0     |
| unsup_top05  | P_compression        |                  -0.241578   | -0.253191   | -0.231038   |            1     |                 5 |                0     |
| unsup_top05  | P_missing            |                  -0.169363   | -0.179215   | -0.160163   |            1     |                 6 |                0     |
| unsup_top05  | P_visible_energy     |                   0.128287   |  0.119631   |  0.136754   |            1     |                 7 |                0     |