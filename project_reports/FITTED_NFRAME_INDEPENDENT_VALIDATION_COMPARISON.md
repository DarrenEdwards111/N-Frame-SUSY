# Fitted N-Frame Independent Validation Comparison

Date: 2026-06-09

## Derivation Data

The fitted equation was derived from standard quality-clean Run2016G MET, JetHT and SingleMuon MiniAOD real collision events after matched-control analysis.

## Validation Data

The intended full validation route was independent Run2016H MiniAOD. The files downloaded successfully, but CMSSW extraction was blocked because Docker Desktop was not running/available. The completed validation therefore uses the fallback Route B: independent Run2016H NanoAOD real collision data extracted with Python/uproot.

| sample_id                                        | primary_dataset   |   events |   mean_score |   median_score |
|:-------------------------------------------------|:------------------|---------:|-------------:|---------------:|
| validation_jetht_run2016h_nanoaod_collision      | JetHT             |   291528 |     0.222121 |       0.212878 |
| validation_met_run2016h_nanoaod_collision        | MET               |   101107 |    -0.483213 |      -0.400145 |
| validation_singlemuon_run2016h_nanoaod_collision | SingleMuon        |    14113 |    -1.1265   |      -1.21461  |

## Component Availability

| parameter_family     | available   | available_variables                                 | missing_variables                             |     weight |
|:---------------------|:------------|:----------------------------------------------------|:----------------------------------------------|-----------:|
| P_displacement_proxy | False       | nan                                                 | secondary_vertex_count;displacement_proxy_raw | 0.356578   |
| P_reconstruction     | True        | N_primary_vertices                                  | packed_candidate_count;secondary_vertex_count | 0.211164   |
| P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                       | nan                                           | 0.201892   |
| P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator | nan                                           | 0.0926065  |
| P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                 | nan                                           | 0.0728025  |
| P_missing            | True        | MET_pt                                              | nan                                           | 0.0594511  |
| P_compression        | True        | compression_proxy_raw                               | nan                                           | 0.00550602 |

## Replication Check

| tail   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| top05  | JetHT             |     0.873881    |           0.716729  |          1.21926   |    17773 |
| top05  | MET               |     0.125725    |           0.248574  |          0.505786  |     2557 |
| top05  | SingleMuon        |     0.000393352 |           0.0346972 |          0.0113367 |        8 |
| top01  | JetHT             |     0.856441    |           0.716729  |          1.19493   |     3484 |
| top01  | MET               |     0.143068    |           0.248574  |          0.575554  |      582 |
| top01  | SingleMuon        |     0.000491642 |           0.0346972 |          0.0141695 |        2 |
| top001 | JetHT             |     0.837838    |           0.716729  |          1.16897   |      341 |
| top001 | MET               |     0.162162    |           0.248574  |          0.65237   |       66 |

## Driver Parameters

| tail   | parameter_family     |    top_mean |     rest_mean |   top_minus_rest |
|:-------|:---------------------|------------:|--------------:|-----------------:|
| top001 | P_missing            |   3.37081   |  -0.00337627  |        3.37418   |
| top001 | P_reconstruction     |   3.17211   |  -0.00317726  |        3.17529   |
| top001 | P_multiplicity       |   1.34716   |  -0.00134934  |        1.3485    |
| top001 | P_visible_energy     |   1.27991   |  -0.00128199  |        1.2812    |
| top001 | P_btag_structure     |   0.762315  |  -0.000763551 |        0.763078  |
| top001 | P_compression        |   0.338562  |  -0.000339111 |        0.338901  |
| top001 | P_displacement_proxy | nan         | nan           |      nan         |
| top01  | P_reconstruction     |   2.14523   |  -0.0216717   |        2.1669    |
| top01  | P_multiplicity       |   1.29014   |  -0.0130334   |        1.30318   |
| top01  | P_missing            |   1.07905   |  -0.0109009   |        1.08995   |
| top01  | P_visible_energy     |   0.869232  |  -0.00878125  |        0.878013  |
| top01  | P_btag_structure     |   0.810932  |  -0.00819229  |        0.819124  |
| top01  | P_compression        |   0.0519826 |  -0.000525145 |        0.0525077 |
| top01  | P_displacement_proxy | nan         | nan           |      nan         |
| top05  | P_reconstruction     |   1.42808   |  -0.0751644   |        1.50324   |
| top05  | P_multiplicity       |   1.10864   |  -0.0583511   |        1.16699   |
| top05  | P_visible_energy     |   0.704254  |  -0.0370672   |        0.741322  |
| top05  | P_btag_structure     |   0.672064  |  -0.0353729   |        0.707437  |
| top05  | P_missing            |   0.540235  |  -0.0284343   |        0.568669  |
| top05  | P_compression        |  -0.0990424 |   0.00521292  |       -0.104255  |
| top05  | P_displacement_proxy | nan         | nan           |      nan         |

## Concentration

| tail   | score                            |   top_file_fraction |   top_run_fraction |   top_lumi_bin_fraction |   events |
|:-------|:---------------------------------|--------------------:|-------------------:|------------------------:|---------:|
| top05  | B_NF_available_components_only_z |            0.873881 |           0.873881 |                0.187973 |    20338 |
| top01  | B_NF_available_components_only_z |            0.856441 |           0.856441 |                0.232301 |     4068 |
| top001 | B_NF_available_components_only_z |            0.837838 |           0.837838 |                0.292383 |      407 |

## Judgement

Classification: **Weak/partial validation**. JetHT remains enriched and SingleMuon remains depleted, but MET does not remain enriched in this NanoAOD reduced-score validation. The most important fitted component, `P_displacement_proxy`, is unavailable in NanoAOD, so this is not a fair full-equation validation. The result qualifies the N-Frame interpretation rather than strengthening it. It does not support any discovery claim and is not evidence that SUSY was found.

## Exact Next Step

Start Docker Desktop and rerun the downloaded Run2016H MiniAOD extraction. That is the proper full-variable independent validation because it can include secondary vertices and packed-candidate counts.