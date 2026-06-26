# Fitted N-Frame Parameter Interpretation For Darren

Date: 2026-06-08

## Data used

This uses real CMS collision MiniAOD data only. No simulated samples were used, no new data were downloaded, and this is not a discovery claim. The fitted parameterisation is based on the standard quality-clean matched-control analysis.

## Why matched contrasts were used

Raw high-boundary tails can be contaminated by trigger, run, source-file and data-quality structure. Matched contrasts compare each high-boundary event with nearby ordinary real events from the same CMS context, then ask what remains different. That is the fairer place to fit N-Frame boundary parameters.

## Fitted boundary parameters

The fitted N-Frame boundary equation is: `P_displacement_proxy=0.357, P_reconstruction=0.211, P_multiplicity=0.202, P_btag_structure=0.093, P_visible_energy=0.073, P_missing=0.059, P_compression=0.006`. The strongest fitted families are P_displacement_proxy, P_reconstruction, P_multiplicity. The weakest/secondary families are P_missing, P_compression.

## Weight table

| family               |   mean_abs_importance |   mean_signed_contrast |   sign_stability |   top3_rank_fraction |   median_rank |   stable_importance |   signed_weight_raw |     weight | role      |
|:---------------------|----------------------:|-----------------------:|-----------------:|---------------------:|--------------:|--------------------:|--------------------:|-----------:|:----------|
| P_displacement_proxy |             1.83816   |             1.83816    |         1        |             1        |             1 |           1.83816   |           1.83816   | 0.356578   | primary   |
| P_reconstruction     |             1.09954   |             1.09954    |         1        |             0.98     |             2 |           1.08855   |           1.08855   | 0.211164   | primary   |
| P_multiplicity       |             1.09591   |             1.09591    |         1        |             0.899333 |             3 |           1.04075   |           1.04075   | 0.201892   | primary   |
| P_btag_structure     |             0.851967  |             0.851967   |         1        |             0.120667 |             4 |           0.477385  |           0.477385  | 0.0926065  | primary   |
| P_visible_energy     |             0.750592  |             0.750592   |         1        |             0        |             5 |           0.375296  |           0.375296  | 0.0728025  | primary   |
| P_missing            |             0.61294   |             0.61294    |         1        |             0        |             6 |           0.30647   |           0.30647   | 0.0594511  | primary   |
| P_compression        |             0.0577683 |             0.00971743 |         0.982667 |             0        |             7 |           0.0283835 |           0.0283835 | 0.00550602 | secondary |

## What the parameters mean

- P_displacement_proxy: secondary-vertex/displacement-like proxy. This is not direct evidence of displaced particles.
- P_reconstruction: reconstruction complexity and event-building load.
- P_multiplicity: jet/lepton/object multiplicity.
- P_btag_structure: b-tag and heavy-flavour-like reconstruction structure.
- P_visible_energy: HT and visible-energy scale.
- P_missing: MET and missing-energy scale.
- P_compression: compression-like imbalance; currently secondary because its fitted weight is very small.

## Model checks

The regularised case/control model separates hand-defined high-boundary cases from their matched controls very strongly, with grouped AUC around 0.997-0.999 for hand-defined tails. Unsupervised tails are weaker but still above chance, with grouped AUC around 0.778-0.962. These are not SUSY labels; they only say the fitted parameter families separate high-boundary real events from matched ordinary real events.

## Applying the fitted equation back to real data

The fitted equation applied cleanly to the standard quality-clean real dataset. JetHT dominates the fitted top tails, MET remains enriched, and SingleMuon remains depleted. This supports a topology/reconstruction boundary interpretation more than a pure missing-energy interpretation.

| tail   | primary_dataset   |   tail_fraction |   baseline_fraction |   enrichment_ratio |   events |
|:-------|:------------------|----------------:|--------------------:|-------------------:|---------:|
| top05  | JetHT             |       0.507622  |            0.150256 |           3.37837  |    15352 |
| top05  | MET               |       0.382766  |            0.2873   |           1.33229  |    11576 |
| top05  | SingleMuon        |       0.109612  |            0.562444 |           0.194885 |     3315 |
| top01  | JetHT             |       0.551992  |            0.150256 |           3.67367  |     3339 |
| top01  | MET               |       0.370474  |            0.2873   |           1.28951  |     2241 |
| top01  | SingleMuon        |       0.0775335 |            0.562444 |           0.137851 |      469 |
| top001 | JetHT             |       0.502479  |            0.150256 |           3.34415  |      304 |
| top001 | MET               |       0.431405  |            0.2873   |           1.50159  |      261 |
| top001 | SingleMuon        |       0.0661157 |            0.562444 |           0.117551 |       40 |

## Comparison with previous scores

The fitted score remains close to the hand-defined score but is not identical. Its correlation is 0.896 with the hand-defined score and 0.701 with the unsupervised score.

## Concentration check

File concentration improves slightly compared with the previous hand-defined score at the most extreme tail, but run/lumi concentration does not fully disappear. This keeps the interpretation qualified.

| tail   | score        |   top_file_fraction |   top_run_fraction |   top_lumi_bin_fraction |
|:-------|:-------------|--------------------:|-------------------:|------------------------:|
| top05  | fitted       |            0.272294 |           0.225308 |                0.187382 |
| top05  | hand         |            0.276527 |           0.276527 |                0.172866 |
| top05  | unsupervised |            0.222531 |           0.183216 |                0.142446 |
| top01  | fitted       |            0.267648 |           0.274426 |                0.223177 |
| top01  | hand         |            0.280542 |           0.280542 |                0.199041 |
| top01  | unsupervised |            0.224831 |           0.186642 |                0.164325 |
| top001 | fitted       |            0.204959 |           0.295868 |                0.246281 |
| top001 | hand         |            0.271074 |           0.290909 |                0.244628 |
| top001 | unsupervised |            0.221488 |           0.216529 |                0.181818 |

## Meaning for N-Frame

The fitted N-Frame boundary is not a SUSY classifier. It is a real-data parameterisation of where CMS collision events become most boundary-stressed after controlling for trigger, run and quality conditions. The strongest current evidence is for an observer/reconstruction boundary involving event topology stress, secondary-vertex proxy structure, b-tag/reconstruction complexity, visible-energy scale and missing-energy scale.

## Meaning for hidden SUSY

This is not direct evidence of SUSY and does not show that SUSY was found. The result is trace-compatible only in a cautious sense: if Darren?s idea predicts indirect boundary stress rather than direct particles, these fitted parameters give a candidate follow-up region. At present, the evidence is stronger as event-topology/reconstruction boundary evidence than as hidden-particle evidence.

## What would make it stronger

Repeat the fitted equation on independent CMS data, add more primary datasets, test independent runs/years, compare against published SUSY signal-region residuals, inspect top fitted-boundary events manually, and add a NanoAOD cross-check if useful.