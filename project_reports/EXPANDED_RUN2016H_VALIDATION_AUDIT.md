# Expanded Run2016H Validation Audit

Date: 2026-06-09

This audits the current one-file-per-dataset Run2016H MiniAOD validation before adding more real collision files.

## Existing Reports

| report                                                                                                                                               | exists   |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| ['D:\\Gamer File\\My Work\\The PhD\\Extra\\Nframe\\nframe_cms_stage2_event_boundary\\reports\\RUN2016H_MINIAOD_INDEPENDENT_VALIDATION_REPORT.md']    | [True]   |
| ['D:\\Gamer File\\My Work\\The PhD\\Extra\\Nframe\\nframe_cms_stage2_event_boundary\\reports\\MINIAOD_VS_NANOAOD_VALIDATION_COMPARISON.md']          | [True]   |
| ['D:\\Gamer File\\My Work\\The PhD\\Extra\\Nframe\\nframe_cms_stage2_event_boundary\\reports\\UPDATE_TO_DARREN_RUN2016H_MINIAOD_VALIDATION.md']      | [True]   |
| ['D:\\Gamer File\\My Work\\The PhD\\Extra\\Nframe\\nframe_cms_stage2_event_boundary\\reports\\FITTED_NFRAME_PARAMETER_INTERPRETATION_FOR_DARREN.md'] | [True]   |
| ['D:\\Gamer File\\My Work\\The PhD\\Extra\\Nframe\\nframe_cms_stage2_event_boundary\\reports\\FITTED_NFRAME_BOUNDARY_EQUATION.md']                   | [True]   |

## Current Events

| sample_id                                        | primary_dataset   | source_file                               |   events |   runs |   lumis |   mean_fitted |
|:-------------------------------------------------|:------------------|:------------------------------------------|---------:|-------:|--------:|--------------:|
| validation_jetht_run2016h_miniaod_collision      | JetHT             | FC0EE8E8-8640-8649-B22A-F0C750DD5DE0.root |     9694 |      2 |       4 |      0.770321 |
| validation_met_run2016h_miniaod_collision        | MET               | 6D1DA38B-AEFA-3849-B346-3B2653B46C9E.root |    13376 |      1 |       7 |      0.181414 |
| validation_singlemuon_run2016h_miniaod_collision | SingleMuon        | E5768FBE-A1B2-F047-999D-0B5C0B051827.root |    26073 |      1 |       7 |     -0.379476 |

## Current Top-Tail Composition

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

## Current Parameter Drivers

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

## Current Limitations

- Only one independent Run2016H MiniAOD file per dataset has been tested.
- JetHT enrichment and SingleMuon depletion replicated, but MET remained mixed.
- The next check is whether more MET and JetHT files make the MET result clearer or show it is file-specific.