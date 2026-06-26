# Real-Only Unsupervised Boundary Model Report

Date: 2026-06-08

This model uses only real CMS collision events. No simulated samples or signal labels are used.

## Methods

- PCA on standardised event/boundary variables.
- FactorAnalysis on the same real-only feature space.
- IsolationForest and LocalOutlierFactor for rare-event boundary scoring.
- KMeans and GaussianMixture clustering to group event families.

## Features Used

`log1p_MET_pt`, `log1p_HT`, `N_jets_30`, `N_jets_50`, `N_leptons`, `N_btags_medium`, `N_btags_tight`, `max_btag_discriminator`, `N_primary_vertices`, `packed_candidate_count`, `secondary_vertex_count`, `compression_proxy_raw`, `displacement_proxy_raw`

## PCA Axes

| axis   | feature                |    loading |   explained_variance_ratio |
|:-------|:-----------------------|-----------:|---------------------------:|
| PC1    | N_jets_30              |  0.406486  |                  0.347067  |
| PC1    | N_jets_50              |  0.399233  |                  0.347067  |
| PC1    | displacement_proxy_raw |  0.396464  |                  0.347067  |
| PC1    | secondary_vertex_count |  0.396464  |                  0.347067  |
| PC1    | log1p_HT               |  0.362808  |                  0.347067  |
| PC1    | N_btags_medium         |  0.241093  |                  0.347067  |
| PC1    | N_btags_tight          |  0.197165  |                  0.347067  |
| PC1    | N_leptons              |  0.164057  |                  0.347067  |
| PC2    | N_primary_vertices     |  0.541817  |                  0.18445   |
| PC2    | packed_candidate_count |  0.52459   |                  0.18445   |
| PC2    | compression_proxy_raw  |  0.423262  |                  0.18445   |
| PC2    | log1p_MET_pt           |  0.410363  |                  0.18445   |
| PC2    | displacement_proxy_raw |  0.0913669 |                  0.18445   |
| PC2    | secondary_vertex_count |  0.0913669 |                  0.18445   |
| PC2    | N_btags_medium         |  0.0738933 |                  0.18445   |
| PC2    | N_btags_tight          |  0.0456987 |                  0.18445   |
| PC3    | N_btags_tight          |  0.613829  |                  0.119588  |
| PC3    | N_btags_medium         |  0.582749  |                  0.119588  |
| PC3    | compression_proxy_raw  |  0.111338  |                  0.119588  |
| PC3    | displacement_proxy_raw |  0.104815  |                  0.119588  |
| PC3    | secondary_vertex_count |  0.104815  |                  0.119588  |
| PC3    | N_leptons              |  0.0837066 |                  0.119588  |
| PC3    | max_btag_discriminator | -0.0849448 |                  0.119588  |
| PC3    | N_primary_vertices     | -0.0929652 |                  0.119588  |
| PC4    | log1p_MET_pt           |  0.669759  |                  0.0875794 |
| PC4    | compression_proxy_raw  |  0.385428  |                  0.0875794 |
| PC4    | N_leptons              |  0.258882  |                  0.0875794 |
| PC4    | log1p_HT               |  0.236308  |                  0.0875794 |
| PC4    | N_btags_tight          |  0.111475  |                  0.0875794 |
| PC4    | N_jets_50              |  0.10812   |                  0.0875794 |
| PC4    | N_jets_30              |  0.104857  |                  0.0875794 |
| PC4    | N_btags_medium         |  0.0708689 |                  0.0875794 |
| PC5    | max_btag_discriminator |  0.955509  |                  0.0775198 |
| PC5    | N_leptons              |  0.134331  |                  0.0775198 |
| PC5    | N_btags_tight          |  0.0847518 |                  0.0775198 |
| PC5    | N_btags_medium         |  0.0657305 |                  0.0775198 |
| PC5    | N_primary_vertices     |  0.0645158 |                  0.0775198 |
| PC5    | packed_candidate_count |  0.0514401 |                  0.0775198 |
| PC5    | log1p_HT               |  0.0312553 |                  0.0775198 |
| PC5    | log1p_MET_pt           | -0.0137896 |                  0.0775198 |

## Anomaly Summary By Sample

| sample_id                         | primary_dataset   |   events |   mean_unsup_boundary |   median_unsup_boundary |   top10_frac |   top05_frac |   top01_frac |   top001_frac |
|:----------------------------------|:------------------|---------:|----------------------:|------------------------:|-------------:|-------------:|-------------:|--------------:|
| cms_jetht_run2016g_collision      | JetHT             |    50000 |              0.230144 |               0.0247227 |      0.15134 |      0.07968 |      0.01646 |       0.00156 |
| cms_met_run2016g_collision        | MET               |    50000 |              0.071949 |              -0.150875  |      0.10222 |      0.05102 |      0.00996 |       0.00102 |
| cms_singlemuon_run2016g_collision | SingleMuon        |    50000 |             -0.302093 |              -0.496308  |      0.04644 |      0.0193  |      0.00358 |       0.00042 |

## Interpretation

The unsupervised boundary score estimates rare structure inside real collision data only. It is a map of unusual real event conditions, not evidence for a new particle.