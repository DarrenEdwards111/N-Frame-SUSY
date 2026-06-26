# Run2012C Enhanced AOD OPQ Cross-Era Validation

## Purpose

This reruns the frozen OPQ boundary-trace score on Run2012C AOD after adding
AOD b-tag fallbacks and V0 secondary-vertex-like counts to the CMSSW mapper.
The frozen score remains:

$$B_{OPQ} = 0.344828O + 0.517241P - 0.137931Q.$$

## Feature Audit

|   rows |   btag_status_nonzero_fraction |   medium_btag_nonzero_fraction |   secondary_vertex_status_nonzero_fraction |   secondary_vertex_nonzero_fraction |   packed_candidate_nonzero_fraction |
|-------:|-------------------------------:|-------------------------------:|-------------------------------------------:|------------------------------------:|------------------------------------:|
|  60000 |                              1 |                        0.14245 |                                          1 |                            0.921417 |                                   1 |

## Enhanced Run2012C OPQ Result

| sample_validation_id            | feature_scope    |   trace_total |   control_total |   shape_chi2 |   shape_dof |   shape_p |   shape_Z |   shoulder_chi2 |   shoulder_p |   shoulder_Z |   trace_95_99_over_90_95_density_ratio |   control_95_99_over_90_95_density_ratio |   trace_99_over_95_99_density_ratio |   control_99_over_95_99_density_ratio | shoulder_above_control   | feature_mapping                                         |
|:--------------------------------|:-----------------|--------------:|----------------:|-------------:|------------:|----------:|----------:|----------------:|-------------:|-------------:|---------------------------------------:|-----------------------------------------:|------------------------------------:|--------------------------------------:|:-------------------------|:--------------------------------------------------------|
| Run2012C_AOD_enhanced_cross_era | enhanced_AOD_OPQ |           847 |            3000 |      5.76828 |           4 |  0.217135 |  0.781906 |         1.41848 |     0.233654 |     0.726866 |                                1.10406 |                                        1 |                              1.2069 |                                     1 | True                     | AOD btag fallbacks plus V0 secondary-vertex-like counts |

## Optional Cross-Era Combination Stress

| combination                                           |   sample_count |   fisher_statistic |    fisher_p |   fisher_Z | enhanced_aod_included_as_stress_only   |
|:------------------------------------------------------|---------------:|-------------------:|------------:|-----------:|:---------------------------------------|
| three_miniaod_like_samples_plus_run2012c_enhanced_aod |              4 |            183.102 | 2.29601e-35 |    12.3547 | True                                   |

## Interpretation

This is the fairer Run2012C cross-era stress test. It is still an AOD-era
feature mapping, not full MiniAOD equivalence, but it no longer forces the
b-tag and secondary-vertex-like terms to zero when AOD products are available.
