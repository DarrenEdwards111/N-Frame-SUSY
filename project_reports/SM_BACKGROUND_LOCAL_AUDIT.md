# SM Background Local Audit

Date: 2026-06-09

## Local Candidates

| sample_id                        | process_label   | record_id   | local_path                                                                                                              |   file_count |   total_size_bytes | data_tier   | mini_or_nano   | simulated_or_real   | suitability                   | cmssw_extraction_needed   | all_fitted_components_likely_available   | feature_tables_already_exist   |
|:---------------------------------|:----------------|:------------|:------------------------------------------------------------------------------------------------------------------------|-------------:|-------------------:|:------------|:---------------|:--------------------|:------------------------------|:--------------------------|:-----------------------------------------|:-------------------------------|
| qcd_ht700to1000_nanoaodsim_pilot | QCD             |             | D:\cern_open_data\nframe_sm_background_pilot\qcd_ht700to1000_nanoaodsim_pilot\64FAD11D-E6E7-574E-9F11-A5C82A832B90.root |            1 |          964557926 | NANOAODSIM  | NanoAOD        | simulated candidate | candidate; inspect before use | False                     | False                                    | False                          |
| ttjets_nanoaodsim_pilot          | ttbar/TTJets    |             | D:\cern_open_data\nframe_sm_background_pilot\ttjets_nanoaodsim_pilot\94B34017-F84D-0E48-9A6C-D2D4D1F97DE3.root          |            1 |          218469276 | NANOAODSIM  | NanoAOD        | simulated candidate | candidate; inspect before use | False                     | False                                    | False                          |

## Conclusion

No suitable already-processed local SM simulated background feature tables were found. The pilot therefore uses small CERN Open Data NanoAODSIM downloads.