# Real-Only Full File Stability Report

Date: 2026-06-08

Exact source-file provenance is available for every event.

## Boundary Summary By File

| sample_id                         | primary_dataset   | source_file                               |   source_file_index |   events |    mean_B |   mean_unsup |   mean_MET |   mean_HT |   mean_N_jets_30 |   mean_N_leptons |   mean_N_btags_medium |   mean_secondary_vertex_count |   mean_packed_candidate_count |   top10_frac |   top05_frac |   top01_frac |   top001_frac |
|:----------------------------------|:------------------|:------------------------------------------|--------------------:|---------:|----------:|-------------:|-----------:|----------:|-----------------:|-----------------:|----------------------:|------------------------------:|------------------------------:|-------------:|-------------:|-------------:|--------------:|
| cms_jetht_run2016g_collision      | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |                   0 |    61353 |  0.345383 |     0.69267  |    42.5313 |  559.764  |          3.6299  |         0.850488 |              0.255146 |                      2.55357  |                       1514.36 |    0.15996   |   0.077486   |   0.0138869  |   0.00104314  |
| cms_jetht_run2016g_collision      | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |                   1 |    17433 |  0.841954 |     0.627417 |    76.2966 |  615.667  |          3.44966 |         0.897264 |              0.264384 |                      3.03075  |                       1698.89 |    0.324041  |   0.189812   |   0.0469225  |   0.00665405  |
| cms_jetht_run2016g_collision      | JetHT             | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |                   2 |     2937 |  0.397722 |     0.498192 |    42.5878 |  546.896  |          3.47463 |         0.898536 |              0.256725 |                      2.69867  |                       1525.66 |    0.160027  |   0.0810351  |   0.0132789  |   0.000340483 |
| cms_jetht_run2016g_collision      | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |                   3 |    16422 |  0.832603 |     0.600551 |    78.4516 |  706.655  |          3.45469 |         0.905249 |              0.254658 |                      2.93892  |                       1693.09 |    0.308428  |   0.182256   |   0.0469492  |   0.00663744  |
| cms_met_run2016g_collision        | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |                   0 |    85149 |  0.507993 |     0.223245 |    80.539  |  185.548  |          1.74189 |         0.634241 |              0.281119 |                      1.5897   |                       1889.07 |    0.177923  |   0.0888912  |   0.0171699  |   0.00158546  |
| cms_met_run2016g_collision        | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |                   1 |   113601 |  0.38562  |     0.239431 |    86.7998 |  204.275  |          1.79521 |         0.648956 |              0.265579 |                      1.49294  |                       1674.72 |    0.162842  |   0.0811172  |   0.0163291  |   0.00147886  |
| cms_met_run2016g_collision        | MET               | 0E1A8650-EA73-264D-8BA5-92902470681F.root |                   2 |    28693 |  0.306916 |     0.16067  |    81.8009 |  220.171  |          1.90262 |         0.75217  |              0.305162 |                      1.54024  |                       1430.54 |    0.146447  |   0.0696686  |   0.0123724  |   0.00104555  |
| cms_singlemuon_run2016g_collision | SingleMuon        | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root |                   0 |   172994 | -0.442477 |    -0.306437 |    33.5013 |   92.2037 |          1.41207 |         1.21533  |              0.195278 |                      0.792617 |                       1285.91 |    0.0216192 |   0.00900609 |   0.00141623 |   0.00010983  |
| cms_singlemuon_run2016g_collision | SingleMuon        | 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root |                   1 |   167320 | -0.418549 |    -0.373939 |    34.0643 |  102.619  |          1.51041 |         1.23237  |              0.204686 |                      0.828909 |                       1259.65 |    0.0239182 |   0.00992709 |   0.00157184 |   0.000143438 |

## Strongest Source-File Tail Enrichments

| tail   | sample_id                    | primary_dataset   | source_file                               |   observed |   expected |   enrichment_ratio |
|:-------|:-----------------------------|:------------------|:------------------------------------------|-----------:|-----------:|-------------------:|
| top001 | cms_jetht_run2016g_collision | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |        116 |    17.4356 |            6.65307 |
| top001 | cms_jetht_run2016g_collision | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |        109 |    16.4244 |            6.63646 |
| top01  | cms_jetht_run2016g_collision | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |        771 |   164.244  |            4.69423 |
| top01  | cms_jetht_run2016g_collision | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |        818 |   174.356  |            4.69156 |
| top05  | cms_jetht_run2016g_collision | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |       3309 |   871.674  |            3.79615 |
| top05  | cms_jetht_run2016g_collision | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |       2993 |   821.122  |            3.64501 |
| top10  | cms_jetht_run2016g_collision | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |       5649 |  1743.32   |            3.24037 |
| top10  | cms_jetht_run2016g_collision | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |       5065 |  1642.22   |            3.08424 |
| top10  | cms_met_run2016g_collision   | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |      15150 |  8515      |            1.77921 |
| top05  | cms_met_run2016g_collision   | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |       7569 |  4257.57   |            1.77778 |
| top01  | cms_met_run2016g_collision   | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |       1462 |   851.615  |            1.71674 |
| top01  | cms_met_run2016g_collision   | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |       1855 |  1136.18   |            1.63267 |
| top10  | cms_met_run2016g_collision   | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |      18499 | 11360.2    |            1.6284  |
| top05  | cms_met_run2016g_collision   | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |       9215 |  5680.2    |            1.6223  |
| top05  | cms_jetht_run2016g_collision | JetHT             | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |        238 |   146.854  |            1.62066 |
| top10  | cms_jetht_run2016g_collision | JetHT             | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |        470 |   293.704  |            1.60025 |
| top10  | cms_jetht_run2016g_collision | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |       9814 |  6135.37   |            1.59958 |
| top001 | cms_met_run2016g_collision   | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |        135 |    85.1615 |            1.58522 |
| top05  | cms_jetht_run2016g_collision | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |       4754 |  3067.73   |            1.54968 |
| top001 | cms_met_run2016g_collision   | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |        168 |   113.618  |            1.47864 |

## Leave-One-File-Out Stability

| left_out_source_file                      |   threshold_without_file |   held_out_top05_frac |   tail_fraction_cms_jetht_run2016g_collision |   tail_fraction_cms_met_run2016g_collision |   tail_fraction_cms_singlemuon_run2016g_collision |
|:------------------------------------------|-------------------------:|----------------------:|---------------------------------------------:|-------------------------------------------:|--------------------------------------------------:|
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |                  1.78167 |            0.0825388  |                                     0.337159 |                                   0.565086 |                                         0.0977559 |
| 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |                  1.77064 |            0.202375   |                                     0.336727 |                                   0.56492  |                                         0.0983534 |
| 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |                  1.81804 |            0.0813756  |                                     0.339164 |                                   0.564334 |                                         0.0965017 |
| EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |                  1.77693 |            0.189989   |                                     0.336798 |                                   0.565095 |                                         0.0981064 |
| 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |                  1.74249 |            0.100072   |                                     0.335925 |                                   0.565058 |                                         0.0990175 |
| 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |                  1.73044 |            0.093714   |                                     0.335267 |                                   0.565078 |                                         0.099655  |
| 0E1A8650-EA73-264D-8BA5-92902470681F.root |                  1.80734 |            0.0709232  |                                     0.339126 |                                   0.564137 |                                         0.0967371 |
| 001FDE5F-A989-2F48-A280-D4D0F7766D95.root |                  1.9763  |            0.00667075 |                                     0.344961 |                                   0.562597 |                                         0.0924419 |
| 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root |                  1.96769 |            0.00746474 |                                     0.344818 |                                   0.562627 |                                         0.0925551 |

## Interpretation

The file-level tables show whether the high-boundary tail is spread across files or dominated by individual files. This is a robustness check, not a discovery statistic.