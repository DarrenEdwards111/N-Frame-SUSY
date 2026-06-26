# Matched Control N-Frame Interpretation

Date: 2026-06-08

## Why matched controls were needed

The earlier high-boundary tail was structured, but it was also concentrated by run/luminosity context and showed event-quality warning signs. A matched-control test is the fair next check because it asks whether high-boundary events still look unusual when compared with ordinary events from the same CMS data-taking context.

## What was matched

Controls were selected from real CMS collision events outside each high-boundary tail. Matching prioritised the same primary dataset, source file, run, broad trigger combination, primary-vertex count, packed-candidate load and luminosity bin. The standard-clean matched sets averaged 5.00 controls per case, 1.00 same-source-file fraction, 0.96 same-run fraction and 0.99 same-trigger-combination fraction.

## Quality-clean data

Standard quality cleaning retained 604,860 events. Relaxed quality cleaning retained 651,585 events. Explicit standard-filter failures accounted for 61,042 events. Boundary tails persisted after recomputing thresholds inside the cleaned subsets.

## Main matched-control result

High-boundary cases remain different from matched controls after quality cleaning and matching. The strongest surviving hand-defined top-1% differences are reconstruction complexity, secondary-vertex proxy, multiplicity, b-tag/reconstruction structure, visible energy and missing energy. Compression-like imbalance is weak after matching.

## Hand-defined top-1% paired differences

| feature                     |   case_mean |   control_mean |   paired_mean_difference |   standardised_paired_mean_difference |   bootstrap_ci_low |   bootstrap_ci_high |   wilcoxon_p |
|:----------------------------|------------:|---------------:|-------------------------:|--------------------------------------:|-------------------:|--------------------:|-------------:|
| MET_pt                      |  139.474    |      98.6267   |                40.8468   |                             0.499399  |        38.7628     |          42.6438    |  0           |
| HT                          |  808.679    |     476.563    |               332.116    |                             0.719552  |       321.347      |         344.128     |  0           |
| N_jets_30                   |    5.29129  |       3.23954  |                 2.05174  |                             1.1222    |         2.00914    |           2.0968    |  0           |
| N_btags_medium              |    1.53579  |       0.326335 |                 1.20946  |                             1.1937    |         1.18419    |           1.23404   |  0           |
| secondary_vertex_count      |    7.15292  |       2.58906  |                 4.56386  |                             1.82984   |         4.50615    |           4.62789   |  0           |
| R_missing                   |    1.32598  |       0.800247 |                 0.525737 |                             0.737895  |         0.508569   |           0.541458  |  0           |
| R_visible_energy            |    1.30276  |       0.889583 |                 0.413175 |                             0.748647  |         0.398848   |           0.427175  |  0           |
| R_multiplicity              |    1.89504  |       0.724606 |                 1.17043  |                             1.36992   |         1.15079    |           1.19168   |  0           |
| R_btag_structure            |    1.77296  |       0.280792 |                 1.49217  |                             1.28846   |         1.46286    |           1.52188   |  0           |
| R_reconstruction_complexity |    1.98786  |       0.584197 |                 1.40366  |                             2.38631   |         1.38963    |           1.41942   |  0           |
| R_compression_proxy         |   -0.128948 |      -0.155283 |                 0.026335 |                             0.0343393 |         0.00746263 |           0.0460737 |  3.88642e-06 |
| R_displacement_proxy        |    3.36141  |       0.72341  |                 2.638    |                             1.82984   |         2.60464    |           2.67501   |  0           |

## Unsupervised top-1% paired differences

| feature                     |   case_mean |   control_mean |   paired_mean_difference |   standardised_paired_mean_difference |   bootstrap_ci_low |   bootstrap_ci_high |   wilcoxon_p |
|:----------------------------|------------:|---------------:|-------------------------:|--------------------------------------:|-------------------:|--------------------:|-------------:|
| MET_pt                      |  65.3112    |     64.3239    |                0.987209  |                            0.0128314  |         -0.98779   |           2.86903   | 1.04583e-63  |
| HT                          | 503.805     |    322.335     |              181.47      |                            0.378151   |        169.694     |         193.951     | 1.14233e-80  |
| N_jets_30                   |   3.31972   |      2.47466   |                0.845065  |                            0.355141   |          0.786497  |           0.906947  | 2.53208e-100 |
| N_btags_medium              |   0.819144  |      0.26206   |                0.557084  |                            0.503535   |          0.527538  |           0.585603  | 9.48331e-257 |
| secondary_vertex_count      |   4.62589   |      1.96214   |                2.66375   |                            0.754684   |          2.57607   |           2.74614   | 0            |
| R_missing                   |  -0.262414  |      0.219831  |               -0.482245  |                           -0.365224   |         -0.516435  |          -0.448063  | 2.04738e-113 |
| R_visible_energy            |  -0.140154  |      0.293108  |               -0.433261  |                           -0.345862   |         -0.462989  |          -0.401951  | 4.23821e-77  |
| R_multiplicity              |   0.828929  |      0.308113  |                0.520816  |                            0.469372   |          0.490857  |           0.548473  | 1.58625e-167 |
| R_btag_structure            |   0.7201    |      0.174191  |                0.54591   |                            0.427564   |          0.512606  |           0.575632  | 1.94032e-133 |
| R_reconstruction_complexity |   1.01363   |      0.318375  |                0.695253  |                            0.772812   |          0.672747  |           0.717905  | 0            |
| R_compression_proxy         |  -0.0828322 |     -0.0858258 |                0.0029936 |                            0.00178578 |         -0.0431916 |           0.0467277 | 0.519192     |
| R_displacement_proxy        |   1.90074   |      0.361042  |                1.5397    |                            0.754684   |          1.48902   |           1.58732   | 0            |

## Components that survive matching

MET_pt, HT, N_jets_30, N_btags_medium, secondary_vertex_count, R_missing, R_visible_energy, R_multiplicity, R_btag_structure, R_reconstruction_complexity, R_displacement_proxy

## Components that mostly disappear or become weak

R_compression_proxy

## Suspect run/source sensitivity

Excluding the strongest suspect run or source file changes the sample composition, but does not remove the broad MET/JetHT enrichment pattern in the quality-clean hand-defined boundary tails. This supports a real detector/reconstruction boundary structure, but it does not by itself establish hidden physics.

## N-Frame judgement

Classification: **Strengthened real-data boundary evidence, but still qualified**. The matched-control result is stronger than the previous trigger/filter-only check because important boundary components survive quality cleaning and close controls. However, the surviving structure is dominated by reconstruction, secondary-vertex, multiplicity and b-tag complexity, so the interpretation remains cautious and qualified.

## Darren hidden-SUSY interpretation

The current evidence is not direct evidence of SUSY and not evidence that SUSY was found. At most, it is trace-compatible boundary-stress structure: high-boundary real events remain unusual after matching, but the unusualness currently looks more like detector/reconstruction and event-topology stress than a clean hidden-particle signature.

## Next step

Fit the N-Frame parameters on these matched case-control contrasts rather than on raw top tails. The first parameters to focus on are reconstruction complexity, secondary-vertex/displacement proxy, b-tag structure, multiplicity, visible energy and missing energy. Compression-like imbalance should be treated as secondary unless a stronger matched effect appears.