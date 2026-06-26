# Fitted N-Frame Boundary Application Report

Date: 2026-06-08

The fitted N-Frame boundary equation was applied to standard quality-clean real CMS collision events.

## Sample Summary

| sample_id                         | primary_dataset   |   events |   mean_fitted_z |      top05 |     top01 |      top001 |
|:----------------------------------|:------------------|---------:|----------------:|-----------:|----------:|------------:|
| cms_jetht_run2016g_collision      | JetHT             |    90884 |        0.898618 | 0.168919   | 0.0367391 | 0.00334492  |
| cms_met_run2016g_collision        | MET               |   173776 |        0.418694 | 0.0666145  | 0.0128959 | 0.00150193  |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340200 |       -0.453936 | 0.00974427 | 0.0013786 | 0.000117578 |

## Top Tail Composition

| tail   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| top05  | JetHT             |       0.507622  |            0.150256 |           3.37837  |    15352 |
| top05  | MET               |       0.382766  |            0.2873   |           1.33229  |    11576 |
| top05  | SingleMuon        |       0.109612  |            0.562444 |           0.194885 |     3315 |
| top01  | JetHT             |       0.551992  |            0.150256 |           3.67367  |     3339 |
| top01  | MET               |       0.370474  |            0.2873   |           1.28951  |     2241 |
| top01  | SingleMuon        |       0.0775335 |            0.562444 |           0.137851 |      469 |
| top001 | JetHT             |       0.502479  |            0.150256 |           3.34415  |      304 |
| top001 | MET               |       0.431405  |            0.2873   |           1.50159  |      261 |
| top001 | SingleMuon        |       0.0661157 |            0.562444 |           0.117551 |       40 |

## Top 0.1% File/Run Concentration

| source_file                               |    run |   events |   mean_fitted_z |
|:------------------------------------------|-------:|---------:|----------------:|
| 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root | 279931 |      124 |         5.12958 |
| 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | 280007 |       99 |         5.04374 |
| 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root | 278969 |       83 |         5.07179 |
| EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root | 280007 |       80 |         5.15061 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 280330 |       37 |         4.97114 |
| 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root | 278962 |       35 |         5.04718 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 278820 |       24 |         4.9064  |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 279588 |       20 |         5.15517 |
| 0E1A8650-EA73-264D-8BA5-92902470681F.root | 280194 |       19 |         5.28273 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 278923 |       12 |         5.13535 |
| 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root | 280017 |       12 |         4.95643 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 280249 |       12 |         4.92896 |
| 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root | 280018 |       11 |         5.27939 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 279716 |        8 |         5.15729 |
| 001FDE5F-A989-2F48-A280-D4D0F7766D95.root | 280242 |        7 |         4.93386 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 279071 |        5 |         4.91817 |
| 001FDE5F-A989-2F48-A280-D4D0F7766D95.root | 280249 |        5 |         4.95708 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 280363 |        3 |         5.5535  |
| 001FDE5F-A989-2F48-A280-D4D0F7766D95.root | 280018 |        3 |         4.82438 |
| 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | 279767 |        2 |         4.61082 |

## Top-1000 Parameter Drivers

| parameter_family            |   mean_top1000_value |
|:----------------------------|---------------------:|
| fitted_P_reconstruction     |             2.83708  |
| fitted_P_displacement_proxy |             5.32721  |
| fitted_P_multiplicity       |             2.63989  |
| fitted_P_btag_structure     |             1.60724  |
| fitted_P_visible_energy     |             2.3682   |
| fitted_P_missing            |             0.960767 |
| fitted_P_compression        |            -0.67173  |