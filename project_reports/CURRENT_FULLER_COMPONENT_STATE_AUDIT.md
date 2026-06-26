# Current Fuller Component State Audit

Date: 2026-06-09

This audit checks the existing fuller-component MiniAODSIM background layer before the signal-side parity search.

Feature file exists: `True`

Scored file exists: `True`

## Summary

| sample_id              | process_label    | classification   |   events | has_P_displacement_proxy   | has_secondary_vertex_count   | has_P_reconstruction   | has_packed_candidate_count   |   mean_BNF |   median_BNF |   mean_P_displacement_proxy |   mean_P_reconstruction |   mean_P_missing |   mean_P_visible_energy | component_mode   |   q90_tail_fraction |   q95_tail_fraction |   q99_tail_fraction |   q999_tail_fraction | strongest_mimic_at_q95   | missing_piece                                                                                                             |
|:-----------------------|:-----------------|:-----------------|---------:|:---------------------------|:-----------------------------|:-----------------------|:-----------------------------|-----------:|-------------:|----------------------------:|------------------------:|-----------------:|------------------------:|:-----------------|--------------------:|--------------------:|--------------------:|---------------------:|:-------------------------|:--------------------------------------------------------------------------------------------------------------------------|
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    |      794 | True                       | True                         | True                   | True                         |   1.45927  |     1.3467   |                    2.53314  |               0.508833  |       -0.0689071 |               3.43985   | full-component   |           0.463476  |          0.24937    |           0.0440806 |           0.00125945 | True                     | No accessible full-component MiniAODSIM SUSY signal has yet been extracted, so signal-vs-background parity is incomplete. |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    |      196 | True                       | True                         | True                   | True                         |   0.975532 |     0.885344 |                    1.87309  |               0.2921    |       -0.316112  |               1.9497    | full-component   |           0.219388  |          0.0714286  |           0.0102041 |           0          | False                    | No accessible full-component MiniAODSIM SUSY signal has yet been extracted, so signal-vs-background parity is incomplete. |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    |      457 | True                       | True                         | True                   | True                         |   0.236943 |     0.13038  |                    0.667447 |              -0.0966588 |        0.27745   |              -0.0664587 | full-component   |           0.0306346 |          0.00218818 |           0         |           0          | False                    | No accessible full-component MiniAODSIM SUSY signal has yet been extracted, so signal-vs-background parity is incomplete. |

## Interpretation

The strongest current fuller-component Standard Model mimic is the sample with the largest q95 tail fraction. The missing piece is an accessible MiniAODSIM SUSY signal processed through the same CMSSW/full-component route.