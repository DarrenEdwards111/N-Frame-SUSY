# Dynamic Feature-State Boundary Test

## Purpose

This is the first explicit test of Darren's dynamical-boundary idea against the current blocker. Instead of assuming one static score works identically across all detector/feature states, the script separates samples into:

- `mht_aware`: samples with the richer MHT-aware boundary feature set.
- `met_only_or_recomputed`: samples where axes had to be recomputed from a reduced MET-only MiniAOD-style feature set.

The test then asks whether a feature-state-specific N-Frame boundary can be learned on one sample and predict the held-out sample inside the same feature state.

## Fixed Baseline Scores

| candidate_id   | sample_validation_id      | feature_state          |   shape_Z |   shoulder_Z |   trace_95_99_over_90_95_density_ratio |   control_95_99_over_90_95_density_ratio | shoulder_above_control   |
|:---------------|:--------------------------|:-----------------------|----------:|-------------:|---------------------------------------:|-----------------------------------------:|:-------------------------|
| clean_op       | Run2015D_pilot            | met_only_or_recomputed |   7.32778 |   7.64497    |                               2.43697  |                                 0.995509 | True                     |
| clean_op       | Run2016G_reference        | mht_aware              |  16.3858  |  14.3702     |                               1.31143  |                                 1.0004   | True                     |
| clean_op       | Run2016H_expanded_miniaod | met_only_or_recomputed |   5.08685 |  -1.35496    |                               0.987354 |                                 0.997845 | False                    |
| clean_op       | Run2016H_fresh_mht        | mht_aware              |   6.83938 |   5.35721    |                               1.21601  |                                 1.00037  | True                     |
| scan_best_opq  | Run2015D_pilot            | met_only_or_recomputed |  14.1411  |  12.068      |                               5.08065  |                                 0.995509 | True                     |
| scan_best_opq  | Run2016G_reference        | mht_aware              |  26.5008  |  19.1342     |                               1.41634  |                                 1.0004   | True                     |
| scan_best_opq  | Run2016H_expanded_miniaod | met_only_or_recomputed |   1.30608 |  -0.00496591 |                               1.0424   |                                 0.997845 | True                     |
| scan_best_opq  | Run2016H_fresh_mht        | mht_aware              |   8.00346 |   6.36       |                               1.24225  |                                 1.00037  | True                     |

## Feature-State Winners

| candidate_id   |   training_samples |   training_shoulder_passes |   training_min_shape_Z |   training_median_shape_Z |   training_min_shoulder_delta |   training_score | feature_state          |   observer_projection |   physical_projection |   algebraic_projection |   ordinary_qcd_axis |   leptonic_control_axis |
|:---------------|-------------------:|---------------------------:|-----------------------:|--------------------------:|------------------------------:|-----------------:|:-----------------------|----------------------:|----------------------:|-----------------------:|--------------------:|------------------------:|
| grid_opq_0010  |                  2 |                          2 |                5.46184 |                   10.3084 |                      0.239511 |          2005.7  | met_only_or_recomputed |              0.454545 |              0.454545 |                      0 |          -0.0909091 |                       0 |
| grid_opq_0018  |                  2 |                          2 |                9.16823 |                   16.2336 |                      0.323963 |          2009.49 | mht_aware              |              0.318182 |              0.590909 |                      0 |          -0.0909091 |                       0 |

## Leave-One-Sample-Out Dynamic Boundary Test

| feature_state          | holdout_sample            | chosen_candidate_id   |   train_training_samples |   train_training_shoulder_passes |   train_training_min_shape_Z |   train_training_median_shape_Z |   train_training_min_shoulder_delta |   train_training_score |   holdout_shape_Z |   holdout_shoulder_Z |   holdout_trace_95_99_over_90_95_density_ratio |   holdout_control_95_99_over_90_95_density_ratio | holdout_shoulder_above_control   |   observer_projection |   physical_projection |   algebraic_projection |   ordinary_qcd_axis |   leptonic_control_axis |
|:-----------------------|:--------------------------|:----------------------|-------------------------:|---------------------------------:|-----------------------------:|--------------------------------:|------------------------------------:|-----------------------:|------------------:|---------------------:|-----------------------------------------------:|-------------------------------------------------:|:---------------------------------|----------------------:|----------------------:|-----------------------:|--------------------:|------------------------:|
| met_only_or_recomputed | Run2015D_pilot            | grid_opq_0010         |                        1 |                                1 |                      5.46184 |                         5.46184 |                            0.239511 |                1005.7  |          15.1549  |            12.4373   |                                        4.92857 |                                         0.995509 | True                             |              0.454545 |              0.454545 |                      0 |          -0.0909091 |                       0 |
| met_only_or_recomputed | Run2016H_expanded_miniaod | grid_opq_0004         |                        1 |                                1 |                     18.9292  |                        18.9292  |                            3.33376  |                1022.26 |          -2.79687 |            -0.659073 |                                        1.01187 |                                         0.997845 | True                             |              0.481481 |              0.259259 |                      0 |          -0.259259  |                       0 |
| mht_aware              | Run2016G_reference        | grid_opq_0018         |                        1 |                                1 |                      9.16823 |                         9.16823 |                            0.323963 |                1009.49 |          23.2989  |            16.9904   |                                        1.43137 |                                         1.0004   | True                             |              0.318182 |              0.590909 |                      0 |          -0.0909091 |                       0 |
| mht_aware              | Run2016H_fresh_mht        | grid_opq_0004         |                        1 |                                1 |                     31.811   |                        31.811   |                            0.423961 |                1020.42 |           3.73762 |             3.80278  |                                        1.12741 |                                         1.00037  | True                             |              0.481481 |              0.259259 |                      0 |          -0.259259  |                       0 |

## Interpretation

This is not a discovery claim. It is a blocker-resolution test. A positive result would mean the boundary can be made feature-state dependent without simply tuning to the weak sample. A negative or mixed result means the next required step is not more weighting, but feature-equivalent extraction: all samples need the same MHT-aware variables before a universal or dynamical boundary claim is publishable.

For Darren's framing, the useful question is whether $\Omega(t, s)$ depends on detector/feature state $s$. This script turns that into a concrete test by allowing the $[O, P, Q]$ projection to vary by feature state while preserving held-out validation.
