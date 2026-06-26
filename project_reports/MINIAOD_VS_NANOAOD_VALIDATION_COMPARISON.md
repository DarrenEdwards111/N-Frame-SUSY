# MiniAOD Versus NanoAOD Validation Comparison

Date: 2026-06-09

MiniAOD includes the secondary-vertex and packed-candidate components required to test the full fitted equation. NanoAOD was only a partial fallback because those components were unavailable.

## MiniAOD Event Counts

| sample_id                                        | primary_dataset   |   events |   mean_score |   median_score |
|:-------------------------------------------------|:------------------|---------:|-------------:|---------------:|
| validation_jetht_run2016h_miniaod_collision      | JetHT             |     9694 |     0.770321 |     0.682442   |
| validation_met_run2016h_miniaod_collision        | MET               |    13376 |     0.181414 |    -0.00793002 |
| validation_singlemuon_run2016h_miniaod_collision | SingleMuon        |    26073 |    -0.379476 |    -0.618846   |

## MiniAOD Tail Composition

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

## NanoAOD Fallback Event Counts

| sample_id                                        | primary_dataset   | source_file                               |   events |   runs |
|:-------------------------------------------------|:------------------|:------------------------------------------|---------:|-------:|
| validation_jetht_run2016h_nanoaod_collision      | JetHT             | 1CD54B78-99CC-7C4F-A89C-7A9103D28135.root |   291528 |      1 |
| validation_met_run2016h_nanoaod_collision        | MET               | C42412D7-7FA8-FA44-B636-9DDB703D1559.root |   101107 |      1 |
| validation_singlemuon_run2016h_nanoaod_collision | SingleMuon        | 61FC1E38-F75C-6B44-AD19-A9894155874E.root |    14113 |      1 |

## NanoAOD Fallback Tail Composition

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

## Judgement

MiniAOD validation classification: **Partial validation**. NanoAOD should be treated only as partial validation.