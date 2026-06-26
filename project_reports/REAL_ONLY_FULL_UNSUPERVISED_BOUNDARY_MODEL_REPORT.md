# Real-Only Full Unsupervised Boundary Model Report

Date: 2026-06-08

This full model uses only real CMS collision events.

## Features

`log1p_MET_pt`, `log1p_HT`, `N_jets_30`, `N_jets_50`, `N_leptons`, `N_btags_medium`, `N_btags_tight`, `max_btag_discriminator`, `N_primary_vertices`, `packed_candidate_count`, `secondary_vertex_count`, `compression_proxy_raw`, `displacement_proxy_raw`

## Sample Summary

| sample_id                         | primary_dataset   |   events |   mean_unsup_boundary |   median_unsup_boundary |   top10_frac |   top05_frac |   top01_frac |   top001_frac |
|:----------------------------------|:------------------|---------:|----------------------:|------------------------:|-------------:|-------------:|-------------:|--------------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |              0.659846 |               0.443034  |    0.235611  |    0.122125  |   0.0242396  |   0.00285292  |
| cms_met_run2016g_collision        | MET               |   227443 |              0.223435 |              -0.0855699 |    0.125675  |    0.0647195 |   0.014408   |   0.00131462  |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |             -0.339626 |              -0.591351  |    0.0437331 |    0.0193645 |   0.00295022 |   0.000255646 |

## Leading PCA Loadings

| axis   | feature                |    loading |   explained_variance_ratio |   abs_loading |
|:-------|:-----------------------|-----------:|---------------------------:|--------------:|
| PC1    | N_jets_30              |  0.401081  |                  0.353098  |     0.401081  |
| PC1    | N_jets_50              |  0.391514  |                  0.353098  |     0.391514  |
| PC1    | secondary_vertex_count |  0.39005   |                  0.353098  |     0.39005   |
| PC1    | displacement_proxy_raw |  0.39005   |                  0.353098  |     0.39005   |
| PC1    | log1p_HT               |  0.356933  |                  0.353098  |     0.356933  |
| PC1    | N_btags_medium         |  0.255297  |                  0.353098  |     0.255297  |
| PC1    | compression_proxy_raw  | -0.246358  |                  0.353098  |     0.246358  |
| PC1    | N_btags_tight          |  0.210837  |                  0.353098  |     0.210837  |
| PC2    | N_primary_vertices     |  0.539783  |                  0.17241   |     0.539783  |
| PC2    | packed_candidate_count |  0.531729  |                  0.17241   |     0.531729  |
| PC2    | compression_proxy_raw  |  0.415819  |                  0.17241   |     0.415819  |
| PC2    | log1p_MET_pt           |  0.400128  |                  0.17241   |     0.400128  |
| PC2    | N_leptons              | -0.246211  |                  0.17241   |     0.246211  |
| PC2    | log1p_HT               | -0.107179  |                  0.17241   |     0.107179  |
| PC2    | N_jets_30              | -0.0796345 |                  0.17241   |     0.0796345 |
| PC2    | displacement_proxy_raw |  0.0722468 |                  0.17241   |     0.0722468 |
| PC3    | N_btags_tight          |  0.602204  |                  0.11727   |     0.602204  |
| PC3    | N_btags_medium         |  0.573554  |                  0.11727   |     0.573554  |
| PC3    | log1p_HT               | -0.290107  |                  0.11727   |     0.290107  |
| PC3    | N_jets_50              | -0.240822  |                  0.11727   |     0.240822  |
| PC3    | N_jets_30              | -0.232463  |                  0.11727   |     0.232463  |
| PC3    | compression_proxy_raw  |  0.155545  |                  0.11727   |     0.155545  |
| PC3    | displacement_proxy_raw |  0.140651  |                  0.11727   |     0.140651  |
| PC3    | secondary_vertex_count |  0.140651  |                  0.11727   |     0.140651  |
| PC4    | log1p_MET_pt           |  0.664417  |                  0.0929706 |     0.664417  |
| PC4    | compression_proxy_raw  |  0.449234  |                  0.0929706 |     0.449234  |
| PC4    | N_primary_vertices     | -0.370585  |                  0.0929706 |     0.370585  |
| PC4    | packed_candidate_count | -0.342651  |                  0.0929706 |     0.342651  |
| PC4    | log1p_HT               |  0.176862  |                  0.0929706 |     0.176862  |
| PC4    | max_btag_discriminator | -0.148756  |                  0.0929706 |     0.148756  |
| PC4    | N_jets_50              |  0.121008  |                  0.0929706 |     0.121008  |
| PC4    | N_leptons              |  0.108152  |                  0.0929706 |     0.108152  |
| PC5    | max_btag_discriminator |  0.874073  |                  0.0783675 |     0.874073  |
| PC5    | secondary_vertex_count | -0.217503  |                  0.0783675 |     0.217503  |
| PC5    | displacement_proxy_raw | -0.217503  |                  0.0783675 |     0.217503  |
| PC5    | N_leptons              |  0.2035    |                  0.0783675 |     0.2035    |
| PC5    | N_btags_tight          |  0.193894  |                  0.0783675 |     0.193894  |
| PC5    | N_btags_medium         |  0.149219  |                  0.0783675 |     0.149219  |
| PC5    | log1p_MET_pt           |  0.136279  |                  0.0783675 |     0.136279  |
| PC5    | N_jets_50              | -0.0909698 |                  0.0783675 |     0.0909698 |