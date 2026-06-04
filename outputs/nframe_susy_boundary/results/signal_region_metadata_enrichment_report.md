# Signal-Region Metadata Enrichment Report

## Purpose

This pass improves the existing SModelS-derived ATLAS/CMS SUSY signal-region table by extracting richer region metadata from explicit signal-region names, SModelS `comment:` fields, source paths, and analysis-level `globalInfo.txt` metadata.

It is an enrichment of the existing public signal-region meta-analysis, not a detector-level reinterpretation and not a SUSY discovery claim.

## Inputs

- Input table: `data/raw/real_smodels_signal_regions_full.csv`
- Rows: 752
- Analyses: 40
- Source family: public `SModelS/smodels-database-release` 13 TeV ATLAS/CMS SUSY entries

## Outputs

- Enriched metadata table: `data/processed/signal_regions_metadata_enriched.csv`
- Enriched scored outcomes: `data/processed/signal_regions_metadata_enriched_scored_outcomes.csv`
- Missingness table: `results/tables/signal_region_metadata_missingness.csv`
- Analysis source manifest: `results/tables/analysis_source_manifest.csv`
- Enriched regression results: `results/tables/enriched_metadata_regression_results.json`
- Enriched robustness checks: `results/tables/enriched_metadata_robustness_results.json`

## Extracted Metadata

The enrichment parser extracts or flags:

- `MET_enriched`
- `HT_or_meff_enriched`
- `N_jets_enriched`
- `N_leptons_enriched`
- `N_btags_enriched`
- `MET_threshold`
- `HT_meff_threshold`
- `Njets_threshold`
- `Nb_threshold`
- `MT2_low`, `MT2_high`
- `is_compressed`
- `is_disappearing_track`
- `is_long_lived`
- `is_displaced`
- `is_high_MET_label`
- `is_high_multiplicity_label`
- `category_enriched`

Analysis-level source links are stored in `analysis_source_manifest.csv`, including available auxiliary/paper URLs, arXiv links, publication DOI strings, luminosity, and a generated HEPData search URL.

## Missingness Before and After

| Stage | Column | Missing Count | Missing Fraction |
|---|---:|---:|---:|
| before | MET | 676 | 0.8989 |
| before | HT_or_meff | 668 | 0.8883 |
| before | N_jets | 552 | 0.7340 |
| before | N_leptons | 580 | 0.7713 |
| before | N_btags | 668 | 0.8883 |
| before | category | 620 | 0.8245 |
| after | MET_enriched | 629 | 0.8364 |
| after | HT_or_meff_enriched | 564 | 0.7500 |
| after | N_jets_enriched | 513 | 0.6822 |
| after | N_leptons_enriched | 580 | 0.7713 |
| after | N_btags_enriched | 629 | 0.8364 |
| after | category_enriched | 620 | 0.8245 |

The parser materially improves `MET`, `HT/meff`, `Njets`, and `Nb` coverage. Lepton and special-category coverage remain poor because many SModelS entries do not encode enough SR definition text. Those fields require direct HEPData/paper table extraction.

## Enriched Regression Result

Using the enriched metadata to recompute `B_access_z`:

### `Z ~ B_access_z`

- Signal regions: 752
- Analyses: 40
- Beta: 0.1179
- OLS p-value: 0.2418
- Bootstrap 95% CI: [-0.0126, 0.3097]
- Permutation p-value: 0.2209
- Spearman rho: 0.0922
- Spearman p-value: 0.0114
- R^2: 0.0018

### `Delta_N ~ B_access_z`

- Beta: -6.9444
- OLS p-value: 2.19e-07
- Bootstrap 95% CI: [-16.2299, -1.5905]
- Permutation p-value: 0.0038
- R^2: 0.0352

## Robustness Findings

The enriched result does not support a strong pooled positive `Z` association:

- Row-bootstrap CI crosses zero.
- Analysis-cluster bootstrap crosses zero.
- ATLAS-only remains positive and significant.
- CMS-only remains non-significant and slightly negative.
- Trimming large residuals removes the pooled association.
- Raw count deviations are significantly negative.

## Interpretation

Better signal-region metadata weakens the original pooled N-Frame result rather than strengthening it. The honest conclusion is:

> The existing public SModelS-derived signal-region table benefits from metadata enrichment, but the enriched pooled result gives no robust evidence for a positive `Z ~ B_access_z` relationship. The remaining limitation is missing or incomplete signal-region definition metadata, especially lepton counts, b-tag definitions, special categories, and exact MET/HT/meff thresholds.

The next necessary step is direct HEPData/paper-level extraction for each analysis, prioritizing analyses with many rows and high residual leverage.

## Priority Manual/API Extraction Queue

Start with the analyses contributing the most rows or driving robustness differences:

- `ATLAS-SUSY-2018-16-eff`
- `ATLAS-SUSY-2018-22-multibin-eff`
- `ATLAS-SUSY-2019-02-eff`
- `ATLAS-SUSY-2019-09-eff`
- `ATLAS-SUSY-2018-42-eff`
- `CMS-SUS-19-006-agg`
- `CMS-SUS-16-050-agg`
- `CMS-SUS-21-002-eff`
- `CMS-SUS-20-004-eff`
- `CMS-SUS-16-048-ma5`

For each, use `analysis_source_manifest.csv` to open the ATLAS/CMS auxiliary page, paper, and HEPData search URL, then extract exact SR definitions and merge by `analysis` plus `signal_region` or `source_comment`.

This remains a public signal-region meta-analysis. Do not claim SUSY discovery or hidden-symmetry evidence.
