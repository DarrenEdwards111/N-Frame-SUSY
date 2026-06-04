# Iterative Exploratory N-Frame Model Search

## Scope

This is exploratory model development. It intentionally searches candidate feature definitions, so it must not be treated as confirmation.

## Data

- Signal regions: 752
- Analyses: 40
- Nonzero R_rare rows: 73

## Search Design

Candidate models used defensible variants of the boundary score:

- current verified+imputed B
- label-derived numeric boundary intensity
- core-or-label boundary intensity
- label-plus-core boundary intensity
- metadata-stress controls
- sparse topology interactions

Models were ranked by GroupKFold-by-analysis R2, with ATLAS/CMS transfer reported separately.

## Best Held-Out Model For abs_Z_capped_3

- feature set: `baseline_metadata`
- model: `ridge`
- GroupKFold R2: 0.0627677
- MAE: 0.81305
- RMSE: 0.95895
- correlation: 0.254622

Cross-experiment transfer for the same model:

```text
       outcome       feature_set model               scheme   n        r2      mae     rmse     corr
abs_Z_capped_3 baseline_metadata ridge ATLAS_train_CMS_test 197 -0.518254 0.845486 0.965087 0.154153
abs_Z_capped_3 baseline_metadata ridge CMS_train_ATLAS_test 555 -0.126618 0.865534 1.087666 0.201447
```

Top GroupKFold leaderboard:

```text
       outcome          feature_set      model                 scheme   n       r2      mae     rmse     corr
abs_Z_capped_3    baseline_metadata      ridge GroupKFold_by_analysis 752 0.062768 0.813050 0.958950 0.254622
abs_Z_capped_3    baseline_metadata        ols GroupKFold_by_analysis 752 0.062639 0.812967 0.959016 0.256428
abs_Z_capped_3    baseline_metadata elasticnet GroupKFold_by_analysis 752 0.058720 0.814432 0.961019 0.246470
abs_Z_capped_3    baseline_metadata     forest GroupKFold_by_analysis 752 0.047421 0.814077 0.966770 0.232749
abs_Z_capped_3    baseline_metadata      huber GroupKFold_by_analysis 752 0.042438 0.805425 0.969295 0.240973
abs_Z_capped_3         label_B_rare elasticnet GroupKFold_by_analysis 752 0.039318 0.810011 0.970873 0.217603
abs_Z_capped_3       current_B_rare      ridge GroupKFold_by_analysis 752 0.028632 0.816491 0.976257 0.218938
abs_Z_capped_3       current_B_rare     forest GroupKFold_by_analysis 752 0.014874 0.824303 0.983147 0.179949
abs_Z_capped_3   core_or_label_rare elasticnet GroupKFold_by_analysis 752 0.011765 0.823274 0.984697 0.198492
abs_Z_capped_3       current_B_rare elasticnet GroupKFold_by_analysis 752 0.010714 0.825304 0.985221 0.209485
abs_Z_capped_3       current_B_rare        ols GroupKFold_by_analysis 752 0.009582 0.825051 0.985784 0.214519
abs_Z_capped_3 label_plus_core_rare elasticnet GroupKFold_by_analysis 752 0.005829 0.828510 0.987650 0.195894
```

In-sample fixed-effect fit:

```text
         feature_set       r2   adj_r2         aic         bic
   components_sparse 0.197757 0.145412 2048.091107 2265.359715
      current_B_rare 0.192399 0.144558 2045.096903 2243.874565
  core_or_label_rare 0.191268 0.142150 2048.149779 2251.550178
   baseline_metadata 0.187096 0.141363 2046.019031 2235.551220
        label_B_rare 0.188470 0.139183 2050.746190 2254.146588
label_plus_core_rare 0.178582 0.128694 2059.853631 2263.254030
```

## Interpretation

No robust good fit found under held-out tests; apparent in-sample fit is likely overfit or experiment-specific.

Do not claim SUSY discovery. Do not claim N-Frame confirmed. If we keep iterating, the next useful improvement is external validation or better verified metadata for the rare-topology rows, not more flexible curve fitting.
