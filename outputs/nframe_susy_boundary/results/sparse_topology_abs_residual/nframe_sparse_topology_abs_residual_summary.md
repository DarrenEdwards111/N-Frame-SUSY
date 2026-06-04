# Exploratory Sparse-Topology Absolute-Residual Model

## Scope

This is exploratory model development using `signal_regions_verified_plus_imputed_scored.csv`. It is not confirmation of N-Frame, SUSY, hidden symmetry, or a physics discovery.

## Data

- Signal regions: 752
- Analyses: 40
- ATLAS rows: 555
- CMS rows: 197
- Nonzero `R_rare` rows: 73

## Primary Model

`abs_Z_capped_3 ~ B + R_rare + B_x_Rrare + C(experiment) + C(analysis)`

Primary key prediction: `B_x_Rrare > 0`.

Pooled primary result:

- `B_x_Rrare` coefficient: nan
- p-value: nan
- analysis-clustered p-value: nan
- R2: 0.187888
- adjusted R2: 0.140992

Split primary coefficients:

- ATLAS `B_x_Rrare`: nan, cluster p=nan
- CMS `B_x_Rrare`: nan, cluster p=nan

Cross-validation:

```text
                scheme   n  n_train        r2      mae     rmse      corr
GroupKFold_by_analysis 752      752  0.035623 0.826004 0.972738  0.217229
  ATLAS_train_CMS_test 197      555 -0.935731 0.925171 1.089724 -0.060091
  CMS_train_ATLAS_test 555      197 -0.125965 0.854708 1.087350  0.204330
```

Interaction diagnostic:

```text
dataset   n  n_analyses  R_rare_nonzero_rows  B_nonzero_rows  B_x_Rrare_nonzero_rows  B_x_Rrare_unique_values  mean_B_when_Rrare_nonzero  interaction_estimable
 pooled 752          40                   73             254                       0                        1                        0.0                  False
  ATLAS 555          32                   66             156                       0                        1                        0.0                  False
    CMS 197           8                    7              98                       0                        1                        0.0                  False
```

## Interpretation

Key interaction not estimable: `B_x_Rrare` has zero variance because all nonzero `R_rare` rows have `B = 0` in the current verified+imputed table. This prevents testing the stated prediction.

The cross-validation numbers are reported for the sparse-topology feature set, but because `B_x_Rrare` is constant zero, they do not validate the key interaction prediction.

Do not claim SUSY discovery. Do not claim N-Frame confirmed. This is exploratory fit development.
