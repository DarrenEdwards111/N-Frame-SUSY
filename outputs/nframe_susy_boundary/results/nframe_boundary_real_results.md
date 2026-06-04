# N-Frame Boundary-Selection Reanalysis: Real Public SUSY Rows

## Data

This run excludes the synthetic demo file.

Input rows were built from public SModelS `dataInfo.txt` files in the `SModelS/smodels-database-release` repository, restricted to `13TeV/ATLAS` and `13TeV/CMS` SUSY analyses and excluding obvious control/validation regions. These files contain signal-region-level `observedN`, `expectedBG`, and `bgError` values and are linked to public ATLAS/CMS reinterpretation material.

- Signal regions: 466
- Analyses: 30
- Raw real CSV: `data/raw/real_smodels_signal_regions.csv`
- Processed real CSV: `data/processed/real_signal_regions.csv`
- Scored real CSV: `data/processed/real_signal_regions_scored.csv`
- Regression JSON: `results/tables/real_regression_results.json`

## Boundary-Access Definition

`Delta_N = N_obs - N_exp`

`Z = (N_obs - N_exp) / sigma_exp`

`B_access = z(MET) + z(HT_or_meff) + z(N_jets) + z(N_leptons) + z(N_btags) + category_bonus`

The SModelS-derived run infers coarse kinematic features from signal-region names when explicitly encoded there, such as `Meff`, `MHT`, `MET`, `MT2`, `NJet`, `Nb`, and jet-count tokens. Missing features contribute zero after z-scoring.

## Regression: Z ~ B_access_z

- Beta: 0.3822
- Standard error: 0.1319
- OLS p-value: 0.00395
- Bootstrap 95% CI, 10,000 resamples: [0.1499, 0.6774]
- Permutation p-value, 10,000 permutations: 0.00620
- R^2: 0.0178

## Regression: Delta_N ~ B_access_z

- Beta: -0.1389
- Standard error: 0.4757
- OLS p-value: 0.7705
- Bootstrap 95% CI, 10,000 resamples: [-1.3374, 0.9139]
- Permutation p-value, 10,000 permutations: 0.7520
- R^2: 0.00018

## Spearman Correlation

- Spearman rho between `B_access_z` and `Z`: 0.0772
- Spearman p-value: 0.0959

## Directional Interpretation

For `Z`, the fitted beta is positive, the bootstrap confidence interval excludes zero, and the permutation p-value is below 0.05. Under the prespecified rule, this is preliminary support for N-Frame boundary-selection in this SModelS-derived public signal-region sample.

The effect size is small by variance explained (`R^2 = 0.0178`), and Spearman correlation is weak and not conventionally significant. The `Delta_N` regression gives no evidence for a positive relationship. So the cautious read is: a positive standardized-deviation trend is present in this real SR sample, but it is modest and depends on the chosen standardized residual statistic.

This is not a discovery claim for SUSY, hidden symmetry, or physics beyond the Standard Model. It is a meta-analysis of published/public signal-region deviations.
