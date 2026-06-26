# Improved Non-Docker Boundary Scoring Report

## Input

`D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\real_collision_20gb_non_docker_event_features.csv`

## What Improved

The improved non-Docker extraction added packed-candidate and primary-vertex leaves to the earlier jet-only table. This allows a broader visible/reconstruction score and an encoded displacement-like proxy.

## What Still Did Not Improve

MET, event IDs, muon/electron counts, experimental b-tag discriminators, and named trigger decisions remain unavailable with the tested non-Docker tools.

## Components

| component            | available   | inputs                                                                                                                                                            | notes                                                                                        |
|:---------------------|:------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------|
| R_missing            | False       |                                                                                                                                                                   | MET pt not readable with tested non-Docker tools                                             |
| R_multiplicity       | True        | N_jets_30;N_jets_50;object_multiplicity;N_pfc_pt_gt_1;N_primary_vertices                                                                                          | available multiplicity variables, log-scaled before z-scoring where count-like               |
| R_reconstruction     | True        | HT;sum_jet_pt;jet_mass_sum_30;N_b_hadron_flavour_proxy;N_b_parton_flavour_proxy;N_packed_pf_candidates;N_primary_vertices;primary_vertex_chi2;primary_vertex_ndof | visible/reconstruction complexity plus labelled flavour proxies                              |
| R_compression_proxy  | False       |                                                                                                                                                                   | requires MET plus visible activity                                                           |
| R_lifetime_proxy     | False       |                                                                                                                                                                   | no validated lifetime variable extracted                                                     |
| R_displacement_proxy | True        | max_abs_pfc_dxy;max_abs_pfc_dz;N_pfc_abs_dxy_gt_0p05;N_pfc_abs_dxy_gt_0p10;N_pfc_abs_dz_gt_0p10                                                                   | encoded packed-candidate dxy/dz proxy; readable but not CMS-calibrated physical displacement |

## Interpretation

This score improves beyond pure jet/HT by adding packed-candidate and vertex information. It still does not reach the full N-Frame boundary model because the missing-information component is absent.
