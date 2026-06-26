# Expanded Run2016H Fitted Boundary Scoring Report

Date: 2026-06-09

The existing fitted N-Frame equation was applied without refitting.

| parameter_family     | available   | available_variables                                              | missing_variables   |     weight |
|:---------------------|:------------|:-----------------------------------------------------------------|:--------------------|-----------:|
| P_displacement_proxy | True        | secondary_vertex_count;displacement_proxy_raw                    |                     | 0.356578   |
| P_reconstruction     | True        | packed_candidate_count;N_primary_vertices;secondary_vertex_count |                     | 0.211164   |
| P_multiplicity       | True        | N_jets_30;N_jets_50;N_leptons                                    |                     | 0.201892   |
| P_btag_structure     | True        | N_btags_medium;N_btags_tight;max_btag_discriminator              |                     | 0.0926065  |
| P_visible_energy     | True        | HT;leading_jet_pt;subleading_jet_pt                              |                     | 0.0728025  |
| P_missing            | True        | MET_pt                                                           |                     | 0.0594511  |
| P_compression        | True        | compression_proxy_raw                                            |                     | 0.00550602 |

Output: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\expanded_run2016h_miniaod_full\expanded_run2016h_miniaod_with_fitted_nframe_score.csv`