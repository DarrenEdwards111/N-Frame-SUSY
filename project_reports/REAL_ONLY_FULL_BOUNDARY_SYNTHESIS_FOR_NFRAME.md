# Real-Only Full Boundary Synthesis For N-Frame

Date: 2026-06-08

## Real Data Used

This full analysis used only real CMS Run2016G MiniAOD collision data:

| sample_id                         | primary_dataset   |   events |   files |
|:----------------------------------|:------------------|---------:|--------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |       4 |
| cms_met_run2016g_collision        | MET               |   227443 |       3 |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |       2 |

Total real events analysed: **665,902** from **9 ROOT files**. No simulated SUSY, T5Wg, HToAA or signal-labelled samples were used.

## Why CMSSW/Docker Was Required

MiniAOD stores MET, leptons, b-tags, vertices, packed candidates and event IDs as CMS-specific objects. Docker let us run the official CMSSW environment so those objects could be read properly.

## Boundary Variables Extracted

The full file-by-file extraction includes exact source file provenance, run/lumi/event IDs, MET, HT, jet counts, leading/subleading jet pT, muons/electrons/leptons, b-tags, max b-tag discriminator, primary vertices, packed-candidate counts and secondary-vertex counts.

## What Parameters Define The Boundary

The hand-defined N-Frame boundary combines missing-information stress, visible-energy stress, multiplicity, b-tag/reconstruction structure, reconstruction complexity, compression-like imbalance and secondary-vertex displacement proxy.

Full hand-defined summary by sample:

| sample_id                         |   events |   mean_boundary_z |   top10_frac |   top05_frac |   top01_frac |   top001_frac |
|:----------------------------------|---------:|------------------:|-------------:|-------------:|-------------:|--------------:|
| cms_jetht_run2016g_collision      |    98145 |          0.516676 |    0.213949  |   0.115075   |   0.0252687  |   0.00295481  |
| cms_met_run2016g_collision        |   227443 |          0.421504 |    0.16642   |   0.0825833  |   0.0161447  |   0.0014641   |
| cms_singlemuon_run2016g_collision |   340314 |         -0.430712 |    0.0227496 |   0.00945891 |   0.00149274 |   0.000126354 |

Full unsupervised summary by sample:

| sample_id                         |   events |   mean_unsup_boundary |   top10_frac |   top05_frac |   top01_frac |   top001_frac |
|:----------------------------------|---------:|----------------------:|-------------:|-------------:|-------------:|--------------:|
| cms_jetht_run2016g_collision      |    98145 |              0.659846 |    0.235611  |    0.122125  |   0.0242396  |   0.00285292  |
| cms_met_run2016g_collision        |   227443 |              0.223435 |    0.125675  |    0.0647195 |   0.014408   |   0.00131462  |
| cms_singlemuon_run2016g_collision |   340314 |             -0.339626 |    0.0437331 |    0.0193645 |   0.00295022 |   0.000255646 |

Leading PCA axis 1 loadings:

| feature                |   loading |   explained_variance_ratio |
|:-----------------------|----------:|---------------------------:|
| N_jets_30              |  0.401081 |                   0.353098 |
| N_jets_50              |  0.391514 |                   0.353098 |
| secondary_vertex_count |  0.39005  |                   0.353098 |
| displacement_proxy_raw |  0.39005  |                   0.353098 |
| log1p_HT               |  0.356933 |                   0.353098 |
| N_btags_medium         |  0.255297 |                   0.353098 |
| compression_proxy_raw  | -0.246358 |                   0.353098 |
| N_btags_tight          |  0.210837 |                   0.353098 |

Leading PCA axis 2 loadings:

| feature                |    loading |   explained_variance_ratio |
|:-----------------------|-----------:|---------------------------:|
| N_primary_vertices     |  0.539783  |                    0.17241 |
| packed_candidate_count |  0.531729  |                    0.17241 |
| compression_proxy_raw  |  0.415819  |                    0.17241 |
| log1p_MET_pt           |  0.400128  |                    0.17241 |
| N_leptons              | -0.246211  |                    0.17241 |
| log1p_HT               | -0.107179  |                    0.17241 |
| N_jets_30              | -0.0796345 |                    0.17241 |
| displacement_proxy_raw |  0.0722468 |                    0.17241 |

## High-Boundary Tail Structure

Hand-defined top 5% sample enrichment:

| sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| cms_met_run2016g_collision        |       0.564122  |            0.341556 |           1.65162  |         18783 |
| cms_jetht_run2016g_collision      |       0.3392    |            0.147387 |           2.30143  |         11294 |
| cms_singlemuon_run2016g_collision |       0.0966783 |            0.511057 |           0.189173 |          3219 |

Unsupervised top 5% sample enrichment:

| sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| cms_met_run2016g_collision        |        0.442095 |            0.341556 |           1.29436  |         14720 |
| cms_jetht_run2016g_collision      |        0.359983 |            0.147387 |           2.44244  |         11986 |
| cms_singlemuon_run2016g_collision |        0.197922 |            0.511057 |           0.387279 |          6590 |

The hand-defined top 5% tail is enriched in MET and JetHT and depleted in SingleMuon. The unsupervised rare-event score is strongest in JetHT, still keeps a meaningful MET contribution, and remains depleted in SingleMuon.

## Source-File Stability

Exact source-file provenance is now present. The boundary pattern is not caused by a single file. MET and JetHT enrichment appears across multiple files, although some JetHT files have stronger high-boundary fractions than others.

Top hand-defined top 5% file enrichments:

| sample_id                         | source_file                               |   observed |   expected |   enrichment_ratio |
|:----------------------------------|:------------------------------------------|-----------:|-----------:|-------------------:|
| cms_jetht_run2016g_collision      | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root |       3309 |    871.674 |           3.79615  |
| cms_jetht_run2016g_collision      | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root |       2993 |    821.122 |           3.64501  |
| cms_met_run2016g_collision        | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root |       7569 |   4257.57  |           1.77778  |
| cms_met_run2016g_collision        | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root |       9215 |   5680.2   |           1.6223   |
| cms_jetht_run2016g_collision      | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root |        238 |    146.854 |           1.62066  |
| cms_jetht_run2016g_collision      | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root |       4754 |   3067.73  |           1.54968  |
| cms_met_run2016g_collision        | 0E1A8650-EA73-264D-8BA5-92902470681F.root |       1999 |   1434.69  |           1.39333  |
| cms_singlemuon_run2016g_collision | 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root |       1661 |   8366.23  |           0.198536 |
| cms_singlemuon_run2016g_collision | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root |       1558 |   8649.93  |           0.180117 |

## N-Frame Connection

This gives a real-data boundary map: high-boundary events correspond to observer/reconstruction stress, missing information, event complexity, secondary-vertex structure and compression-like imbalance. These are trace-compatible follow-up regions, not evidence of a discovered particle.

## Relation To Earlier Signal-Region Finding

The earlier published signal-region result suggested rare/topology-stressed rows had higher anomaly magnitudes, but it had robustness caveats. This real-data MiniAOD result is separate and stronger as a boundary-map layer because it uses real collision events directly and does not rely on simulation labels.

## Limitations

- Trigger/filter names are still not unpacked.
- The source-file pattern is interpretable but not perfectly uniform; file-level differences need physics/data-quality follow-up.
- This is not a SUSY discovery claim.

## Next Steps

Inspect the top boundary events manually, add trigger/filter variables if feasible, and compare the file-level high-boundary pattern against known CMS event-quality conditions.
