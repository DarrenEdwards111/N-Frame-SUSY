# SM Background Feature Extraction Report

Date: 2026-06-09

## Feature Family Availability

| sample_id                        | process_label    | parameter_family     | available   | available_variables                                 | missing_variables      |   weight |
|:---------------------------------|:-----------------|:---------------------|:------------|:----------------------------------------------------|:-----------------------|---------:|
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_displacement_proxy | True        | secondary_vertex_count;displacement_proxy_raw       |                        |   0.3566 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_reconstruction     | True        | N_primary_vertices;secondary_vertex_count           | packed_candidate_count |   0.2112 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                       |                        |   0.2019 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator |                        |   0.0926 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                 |                        |   0.0728 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_missing            | True        | MET_pt                                              |                        |   0.0595 |
| ttjets_nanoaodsim_pilot          | TTJets inclusive | P_compression        | True        | compression_proxy_raw                               |                        |   0.0055 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_displacement_proxy | True        | secondary_vertex_count;displacement_proxy_raw       |                        |   0.3566 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_reconstruction     | True        | N_primary_vertices;secondary_vertex_count           | packed_candidate_count |   0.2112 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                       |                        |   0.2019 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator |                        |   0.0926 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                 |                        |   0.0728 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_missing            | True        | MET_pt                                              |                        |   0.0595 |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000  | P_compression        | True        | compression_proxy_raw                               |                        |   0.0055 |

## Interpretation

These are NanoAODSIM-derived features. Packed candidate count is unavailable, so P_reconstruction is reduced. Secondary-vertex count is available only when nSV exists in the NanoAODSIM file.