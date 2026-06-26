# Fitted N-Frame Boundary Equation

Date: 2026-06-08

The fitted equation is derived from stable matched-control parameter importance in real CMS collision data. It is a boundary equation, not a SUSY classifier.

## Equation

`B_NF_fitted = 0.3566*P_displacement_proxy + 0.2112*P_reconstruction + 0.2019*P_multiplicity + 0.0926*P_btag_structure + 0.0728*P_visible_energy + 0.0595*P_missing + 0.0055*P_compression`

## Weights

| family               |   mean_abs_importance |   mean_signed_contrast |   sign_stability |   top3_rank_fraction |   median_rank |   stable_importance |   signed_weight_raw |     weight | role      |
|:---------------------|----------------------:|-----------------------:|-----------------:|---------------------:|--------------:|--------------------:|--------------------:|-----------:|:----------|
| P_displacement_proxy |             1.83816   |             1.83816    |         1        |             1        |             1 |           1.83816   |           1.83816   | 0.356578   | primary   |
| P_reconstruction     |             1.09954   |             1.09954    |         1        |             0.98     |             2 |           1.08855   |           1.08855   | 0.211164   | primary   |
| P_multiplicity       |             1.09591   |             1.09591    |         1        |             0.899333 |             3 |           1.04075   |           1.04075   | 0.201892   | primary   |
| P_btag_structure     |             0.851967  |             0.851967   |         1        |             0.120667 |             4 |           0.477385  |           0.477385  | 0.0926065  | primary   |
| P_visible_energy     |             0.750592  |             0.750592   |         1        |             0        |             5 |           0.375296  |           0.375296  | 0.0728025  | primary   |
| P_missing            |             0.61294   |             0.61294    |         1        |             0        |             6 |           0.30647   |           0.30647   | 0.0594511  | primary   |
| P_compression        |             0.0577683 |             0.00971743 |         0.982667 |             0        |             7 |           0.0283835 |           0.0283835 | 0.00550602 | secondary |

## Meaning

- P_reconstruction: reconstruction complexity and event-building load.
- P_displacement_proxy: secondary-vertex/displacement-like proxy, not direct evidence of displaced particles.
- P_multiplicity: jet/lepton/object multiplicity.
- P_btag_structure: b-tag and heavy-flavour-like reconstruction structure.
- P_visible_energy: HT and visible-energy scale.
- P_missing: MET and missing-energy scale.
- P_compression: compression-like imbalance; treated as secondary because it is weak after matching.

## Next Test

Apply the equation to quality-clean real events and compare it with the previous hand-defined and unsupervised boundary scores.