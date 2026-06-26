# Fuller Component Frozen B_NF Application Report

Date: 2026-06-09

The Run2016G-derived fitted B_NF equation was applied unchanged. No simulated sample was used to refit it.

| sample_id              | process_label    | classification   | component_mode   |   events |   mean_BNF |   median_BNF |   mean_displacement |   mean_reconstruction |   mean_missing |   mean_visible |
|:-----------------------|:-----------------|:-----------------|:-----------------|---------:|-----------:|-------------:|--------------------:|----------------------:|---------------:|---------------:|
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | full-component   |      794 |   1.45927  |     1.3467   |            2.53314  |             0.508833  |     -0.0689071 |      3.43985   |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | full-component   |      196 |   0.975532 |     0.885344 |            1.87309  |             0.2921    |     -0.316112  |      1.9497    |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | full-component   |      457 |   0.236943 |     0.13038  |            0.667447 |            -0.0966588 |      0.27745   |     -0.0664587 |

## Feature Availability

| sample_id              | process_label    | classification   | parameter_family     | available   | available_variables                                              | missing_variables   |   weight |
|:-----------------------|:-----------------|:-----------------|:---------------------|:------------|:-----------------------------------------------------------------|:--------------------|---------:|
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_displacement_proxy | True        | secondary_vertex_count;displacement_proxy_raw                    |                     |   0.3566 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_displacement_proxy | True        | secondary_vertex_count;displacement_proxy_raw                    |                     |   0.3566 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_displacement_proxy | True        | secondary_vertex_count;displacement_proxy_raw                    |                     |   0.3566 |
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_reconstruction     | True        | packed_candidate_count;N_primary_vertices;secondary_vertex_count |                     |   0.2112 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_reconstruction     | True        | packed_candidate_count;N_primary_vertices;secondary_vertex_count |                     |   0.2112 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_reconstruction     | True        | packed_candidate_count;N_primary_vertices;secondary_vertex_count |                     |   0.2112 |
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                                    |                     |   0.2019 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                                    |                     |   0.2019 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                                    |                     |   0.2019 |
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator              |                     |   0.0926 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator              |                     |   0.0926 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator              |                     |   0.0926 |
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                              |                     |   0.0728 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                              |                     |   0.0728 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                              |                     |   0.0728 |
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_missing            | True        | MET_pt                                                           |                     |   0.0595 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_missing            | True        | MET_pt                                                           |                     |   0.0595 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_missing            | True        | MET_pt                                                           |                     |   0.0595 |
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | P_compression        | True        | compression_proxy_raw                                            |                     |   0.0055 |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | P_compression        | True        | compression_proxy_raw                                            |                     |   0.0055 |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | P_compression        | True        | compression_proxy_raw                                            |                     |   0.0055 |