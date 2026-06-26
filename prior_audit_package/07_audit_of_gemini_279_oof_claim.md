# Audit of Gemini Script 279 and the Claimed 36.9 Sigma OOF Result

## Verdict

The claimed `36.9 sigma` predictive-superiority result is not valid. Script 279 takes out-of-fold predictions from five different record-holdout tasks, pools them as though they came from one fixed model on one IID test population, then applies event-level DeLong/bootstrap/permutation tests. This is pseudo-replication.

The valid independent units are the held-out source-record folds, not the 35,101 events. The previously reported cluster-level sign-flip result remains the appropriate inference:

| N-Frame addition | Independent held-out records with positive increment | Record-level one-sided Z | p |
|---|---:|---:|---:|
| Trace axis | 4 / 5 | 0.91 | 0.182 |
| BNF | 4 / 5 | 1.17 | 0.121 |
| Full N-Frame axes | 5 / 5 | 1.55 | 0.061 |

## Why pooled OOF DeLong is invalid here

1. **Different fitted models:** every fold uses a separately fitted logistic-regression model. A probability of 0.8 from fold 0 is not automatically rank-comparable with a probability of 0.8 from fold 4.
2. **Different test distributions:** each fold holds out a different signal benchmark and different mixture of SM records. The per-fold standard AUC ranges from 0.320 to 0.983, demonstrating that these are not draws from one fixed classification task.
3. **Non-random source selection:** the five signal records are a small, deliberately assembled benchmark collection, not 35,101 independently sampled signal topologies.
4. **Event-level resampling:** DeLong, bootstrap and label-swap permutation in script 279 resample events. They measure conditional precision within the already selected records, not generalisation uncertainty to another source topology.
5. **Finite-resample floor:** the bootstrap/permutation p-value is exactly `1/(10000+1)`, therefore it only says no event-level resample reversed the sign. It does not establish a 36-sigma physical or model-generalisation effect.

## What can be reported

The following is accurate:

> Across five disjoint source-record holdouts, the full N-Frame feature set increased AUC in every held-out benchmark record, with mean increment 0.0836. The small number of independent benchmark records means this consistency is suggestive but not statistically decisive (conservative one-sided p = 0.061).

Do not report the pooled AUC, pooled DeLong Z, or event-level bootstrap/permutation Z as discovery or publication-grade significance.

## How to strengthen this result validly

1. Add many independently generated signal records covering predeclared topology families and mass/lifetime points.
2. Add matched, complete SM source records; assign whole records to development or test before any model fit.
3. Freeze the exact N-Frame axis construction before adding test records.
4. Estimate uncertainty by source-record clusters or hierarchical modelling, not individual event resampling.
5. Compare against stronger standard baselines and report per-topology effects, not a pooled event score.

Only a larger collection of independently held-out source records can turn the promising 5/5 directional pattern into a strong generalisation finding.
