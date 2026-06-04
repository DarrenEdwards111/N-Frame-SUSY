# N-Frame Boundary-Selection Reanalysis: Expanded Public ATLAS+CMS SUSY Corpus

## Data

This run excludes the synthetic demo file and supersedes the earlier 466-row interim result.

Rows were built from public `dataInfo.txt` files in `SModelS/smodels-database-release`, restricted to 13 TeV ATLAS/CMS SUSY analyses and excluding obvious control/validation regions. The extracted fields are `observedN`, `expectedBG`, and `bgError`, with signal-region labels and coarse kinematic metadata inferred only from explicit SR names/comments.

- Signal regions: 752
- Analyses: 40
- ATLAS rows: 555
- CMS rows: 197
- Raw CSV: `data/raw/real_smodels_signal_regions_full.csv`
- Processed CSV: `data/processed/real_signal_regions_full.csv`
- Scored CSV: `data/processed/real_signal_regions_full_scored.csv`
- Regression JSON: `results/tables/real_full_regression_results.json`
- Robustness JSON: `results/tables/real_full_robustness_results.json`

## Boundary-Access Definition

`Delta_N = N_obs - N_exp`

`Z = (N_obs - N_exp) / sigma_exp`

`B_access = z(MET) + z(HT_or_meff) + z(N_jets) + z(N_leptons) + z(N_btags) + category_bonus`

Missing kinematic features contribute zero after z-scoring. Category bonuses are assigned for labels indicating compressed spectra, disappearing tracks, long-lived particles, displaced vertices, high-MET regions, and high-multiplicity regions.

## Pooled Regression: Z ~ B_access_z

- Beta: 0.1829
- Standard error: 0.1005
- OLS p-value: 0.0692
- Bootstrap 95% CI, 10,000 row resamples: [0.0429, 0.3720]
- Permutation p-value, 10,000 permutations: 0.0693
- R^2: 0.0044
- Spearman rho: 0.0901
- Spearman p-value: 0.0135

## Pooled Regression: Delta_N ~ B_access_z

- Beta: -5.7435
- Standard error: 1.3351
- OLS p-value: 1.92e-05
- Bootstrap 95% CI, 10,000 row resamples: [-13.3266, -1.2493]
- Permutation p-value: 0.0071
- R^2: 0.0241

## Robustness Checks for Z

- Row bootstrap CI remains positive: [0.0470, 0.3806]
- Analysis-cluster bootstrap crosses zero: [-0.1169, 1.0085]
- ATLAS-only: beta = 0.8159, p = 1.94e-06, Spearman p = 0.0021
- CMS-only: beta = -0.1497, p = 0.2809, Spearman p = 0.1243
- Trimmed |Z| <= 3: beta = 0.0220, p = 0.6425
- Trimmed |Z| <= 5: beta = 0.0499, p = 0.4182
- Trimmed |Z| <= 10: beta = 0.0928, p = 0.2273

## Interpretation

The full public ATLAS+CMS SModelS-derived corpus gives a weak positive pooled association between standardized residual `Z` and `B_access_z`, but it is not robust enough to claim strong support.

Under the original simple row-bootstrap rule, the positive direction survives. Under stricter checks, the result is fragile:

- the OLS and permutation p-values are borderline rather than below 0.05,
- the effect size is very small,
- the analysis-cluster bootstrap includes zero,
- the trend is ATLAS-driven and not reproduced in CMS,
- trimming large residuals removes the association,
- raw count deviations point in the opposite direction.

Best cautious conclusion:

> The expanded public signal-region analysis gives limited, fragile evidence for a positive standardized-deviation trend with boundary access. It justifies a covariance-aware HEPData/SModelS follow-up with better SR metadata extraction, but it does not yet justify a physics claim or a detector-level raw CERN Open Data campaign.

This is not a discovery claim for SUSY, hidden symmetry, or physics beyond the Standard Model.
