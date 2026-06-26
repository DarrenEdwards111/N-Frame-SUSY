# Run2016H MiniAOD Independent Validation Report

Date: 2026-06-09

This report analyses the full fitted N-Frame boundary equation on independent real CMS Run2016H MiniAOD data.

## Boundary Summary

| sample_id                                        | primary_dataset   |   events |   mean_score |   median_score |
|:-------------------------------------------------|:------------------|---------:|-------------:|---------------:|
| validation_jetht_run2016h_miniaod_collision      | JetHT             |     9694 |     0.770321 |     0.682442   |
| validation_met_run2016h_miniaod_collision        | MET               |    13376 |     0.181414 |    -0.00793002 |
| validation_singlemuon_run2016h_miniaod_collision | SingleMuon        |    26073 |    -0.379476 |    -0.618846   |

## Top Tail Composition

| tail_label   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-------------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| top05        | JetHT             |        0.607404 |            0.197261 |           3.07919  |     1493 |
| top05        | MET               |        0.242067 |            0.272185 |           0.889345 |      595 |
| top05        | SingleMuon        |        0.150529 |            0.530554 |           0.28372  |      370 |
| top01        | JetHT             |        0.638211 |            0.197261 |           3.23536  |      314 |
| top01        | MET               |        0.231707 |            0.272185 |           0.851285 |      114 |
| top01        | SingleMuon        |        0.130081 |            0.530554 |           0.24518  |       64 |
| top001       | JetHT             |        0.62     |            0.197261 |           3.14304  |       31 |
| top001       | MET               |        0.28     |            0.272185 |           1.02871  |       14 |
| top001       | SingleMuon        |        0.1      |            0.530554 |           0.188482 |        5 |

## Parameter Drivers

| tail_label   | parameter_family     |   top_mean |    rest_mean |   top_minus_rest |
|:-------------|:---------------------|-----------:|-------------:|-----------------:|
| top001       | P_displacement_proxy |   5.50069  | -0.00560231  |         5.50629  |
| top001       | P_visible_energy     |   2.94392  | -0.00299831  |         2.94692  |
| top001       | P_multiplicity       |   2.69664  | -0.00274646  |         2.69939  |
| top001       | P_reconstruction     |   2.03415  | -0.00207173  |         2.03622  |
| top001       | P_btag_structure     |   1.61781  | -0.0016477   |         1.61946  |
| top001       | P_missing            |   0.883723 | -0.00090005  |         0.884623 |
| top001       | P_compression        |  -0.888394 |  0.000904808 |        -0.889299 |
| top01        | P_displacement_proxy |   4.0611   | -0.0410693   |         4.10217  |
| top01        | P_visible_energy     |   2.10293  | -0.0212666   |         2.1242   |
| top01        | P_multiplicity       |   1.95867  | -0.0198077   |         1.97848  |
| top01        | P_reconstruction     |   1.47912  | -0.0149581   |         1.49408  |
| top01        | P_btag_structure     |   1.22555  | -0.0123938   |         1.23795  |
| top01        | P_missing            |   0.505587 | -0.00511292  |         0.5107   |
| top01        | P_compression        |  -0.868175 |  0.00877971  |        -0.876954 |
| top05        | P_displacement_proxy |   2.80604  | -0.14774     |         2.95378  |
| top05        | P_visible_energy     |   1.62812  | -0.0857218   |         1.71384  |
| top05        | P_multiplicity       |   1.50673  | -0.0793305   |         1.58606  |
| top05        | P_reconstruction     |   1.04355  | -0.0549435   |         1.09849  |
| top05        | P_btag_structure     |   0.853049 | -0.0449136   |         0.897962 |
| top05        | P_missing            |   0.395279 | -0.0208118   |         0.416091 |
| top05        | P_compression        |  -0.796811 |  0.0419527   |        -0.838764 |

## File/Run/Lumi Concentration

| tail_label   |   top_file_fraction |   top_run_fraction |   top_lumi_bin_fraction |   events |
|:-------------|--------------------:|-------------------:|------------------------:|---------:|
| top05        |            0.607404 |           0.372661 |                0.372661 |     2458 |
| top01        |            0.638211 |           0.398374 |                0.398374 |      492 |
| top001       |            0.62     |           0.4      |                0.4      |       50 |

## Trigger/Filter Top Tail Summary

| tail_label   | variable                                |   top_mean |   rest_mean |   top_minus_rest |
|:-------------|:----------------------------------------|-----------:|------------:|-----------------:|
| top05        | HLT_MET_paths_any                       |   0.328316 |   0.39306   |     -0.0647442   |
| top05        | HLT_HT_paths_any                        |   0.920667 |   0.328328  |      0.592339    |
| top05        | HLT_Mu_paths_any                        |   0.425549 |   0.751055  |     -0.325506    |
| top05        | HLT_Ele_paths_any                       |   0.12856  |   0.0285959 |      0.0999639   |
| top05        | pass_HBHENoiseFilter                    |   0.998373 |   0.927985  |      0.0703872   |
| top05        | pass_HBHENoiseIsoFilter                 |   0.997559 |   0.993617  |      0.0039422   |
| top05        | pass_goodVertices                       |   1        |   0.9994    |      0.000599764 |
| top05        | pass_EcalDeadCellTriggerPrimitiveFilter |   0.998373 |   0.999572  |     -0.00119894  |
| top05        | pass_BadPFMuonFilter                    |   0.999186 |   0.999871  |     -0.000685149 |
| top05        | pass_globalSuperTightHalo2016Filter     |   0.999186 |   0.990618  |      0.00856836  |
| top01        | HLT_MET_paths_any                       |   0.335366 |   0.390372  |     -0.0550064   |
| top01        | HLT_HT_paths_any                        |   0.947154 |   0.351997  |      0.595158    |
| top01        | HLT_Mu_paths_any                        |   0.416667 |   0.737991  |     -0.321324    |
| top01        | HLT_Ele_paths_any                       |   0.162602 |   0.0322912 |      0.13031     |
| top01        | pass_HBHENoiseFilter                    |   0.995935 |   0.930854  |      0.0650805   |
| top01        | pass_HBHENoiseIsoFilter                 |   1        |   0.993751  |      0.00624859  |
| top01        | pass_goodVertices                       |   1        |   0.999424  |      0.000575528 |
| top01        | pass_EcalDeadCellTriggerPrimitiveFilter |   0.995935 |   0.999548  |     -0.00361284  |
| top01        | pass_BadPFMuonFilter                    |   1        |   0.999836  |      0.000164436 |
| top01        | pass_globalSuperTightHalo2016Filter     |   1        |   0.990956  |      0.00904401  |
| top001       | HLT_MET_paths_any                       |   0.42     |   0.389791  |      0.0302092   |
| top001       | HLT_HT_paths_any                        |   0.98     |   0.357322  |      0.622678    |
| top001       | HLT_Mu_paths_any                        |   0.5      |   0.735013  |     -0.235013    |
| top001       | HLT_Ele_paths_any                       |   0.3      |   0.0333245 |      0.266675    |
| top001       | pass_HBHENoiseFilter                    |   1        |   0.931436  |      0.0685637   |
| top001       | pass_HBHENoiseIsoFilter                 |   1        |   0.993808  |      0.00619233  |
| top001       | pass_goodVertices                       |   1        |   0.99943   |      0.000570346 |
| top001       | pass_EcalDeadCellTriggerPrimitiveFilter |   1        |   0.999511  |      0.000488868 |
| top001       | pass_BadPFMuonFilter                    |   1        |   0.999837  |      0.000162956 |
| top001       | pass_globalSuperTightHalo2016Filter     |   1        |   0.991037  |      0.00896258  |

Classification: **Partial validation**.

Top-1% dominant parameter families: P_displacement_proxy, P_visible_energy, P_multiplicity.
Compression weak relative to median driver magnitude: True.
MET enrichment is mixed: it is depleted in the top 5% and top 1% tails, but slightly enriched in the top 0.1% tail.