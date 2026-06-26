# Top Boundary Pattern Classification Report

Date: 2026-06-08

This is an exploratory descriptive categorisation, not a particle classifier.

Thresholds use full real-data 95th percentiles for relevant variables.

## Thresholds

|   high_MET |   high_HT |   high_jets |   high_btags |   high_secondary_vertices |   high_candidates |   high_compression |
|-----------:|----------:|------------:|-------------:|--------------------------:|------------------:|-------------------:|
|    151.658 |    782.32 |           5 |            1 |                         5 |              2162 |            1.66685 |

## Pattern Summary

| top_set       |   flag_missing_energy_dominant |   flag_visible_energy_jetht_dominant |   flag_heavy_flavour_reconstruction |   flag_displacement_secondary_vertex_proxy |   flag_reconstruction_complexity |   flag_mixed_high_boundary |   flag_possible_data_quality_trigger_followup |
|:--------------|-------------------------------:|-------------------------------------:|------------------------------------:|-------------------------------------------:|---------------------------------:|---------------------------:|----------------------------------------------:|
| hand_top1000  |                          0.004 |                                0.887 |                               0.879 |                                      0.931 |                            0.24  |                      0.805 |                                             1 |
| unsup_top1000 |                          0.073 |                                0.64  |                               0.638 |                                      0.685 |                            0.242 |                      0.558 |                                             1 |

Events may have multiple flags. The displacement category is a secondary-vertex proxy, not proof of displaced particles.