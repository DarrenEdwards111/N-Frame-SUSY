# SUSY Relevance Feature Extraction Report

Date: 2026-06-09

| sample_id                    | parameter_family     | available   | available_variables                 | missing_variables                                                |   weight |
|:-----------------------------|:---------------------|:------------|:------------------------------------|:-----------------------------------------------------------------|---------:|
| sms_t5wg_mg1500_mlsp1_signal | P_displacement_proxy | False       |                                     | secondary_vertex_count;displacement_proxy_raw                    |   0.3566 |
| sms_t5wg_mg1500_mlsp1_signal | P_reconstruction     | False       |                                     | packed_candidate_count;N_primary_vertices;secondary_vertex_count |   0.2112 |
| sms_t5wg_mg1500_mlsp1_signal | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons       |                                                                  |   0.2019 |
| sms_t5wg_mg1500_mlsp1_signal | P_btag_structure     | True        | N_btags_medium;N_btags_tight        | max_btag_discriminator                                           |   0.0926 |
| sms_t5wg_mg1500_mlsp1_signal | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt |                                                                  |   0.0728 |
| sms_t5wg_mg1500_mlsp1_signal | P_missing            | True        | MET_pt                              |                                                                  |   0.0595 |
| sms_t5wg_mg1500_mlsp1_signal | P_compression        | True        | compression_proxy_raw               |                                                                  |   0.0055 |
| susy_htoaa4b_m12_signal      | P_displacement_proxy | False       |                                     | secondary_vertex_count;displacement_proxy_raw                    |   0.3566 |
| susy_htoaa4b_m12_signal      | P_reconstruction     | False       |                                     | packed_candidate_count;N_primary_vertices;secondary_vertex_count |   0.2112 |
| susy_htoaa4b_m12_signal      | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons       |                                                                  |   0.2019 |
| susy_htoaa4b_m12_signal      | P_btag_structure     | True        | N_btags_medium;N_btags_tight        | max_btag_discriminator                                           |   0.0926 |
| susy_htoaa4b_m12_signal      | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt |                                                                  |   0.0728 |
| susy_htoaa4b_m12_signal      | P_missing            | True        | MET_pt                              |                                                                  |   0.0595 |
| susy_htoaa4b_m12_signal      | P_compression        | True        | compression_proxy_raw               |                                                                  |   0.0055 |