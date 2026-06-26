# Update To Darren: Real-Data-Only Boundary Analysis

Date: 2026-06-08

## Stage 1: Real Data Used

We have now done the real-data-only version. No simulated SUSY samples were used in the main analysis.

The data used was real CMS Run2016G MiniAOD collision data:

- MET, record 30509: 50,000 events
- JetHT, record 30508: 50,000 events
- SingleMuon, record 30513: 50,000 events

Total analysed: 150,000 real CMS collision events.

## Stage 2: Why Docker/CMSSW Was Needed

CMS MiniAOD does not store the important event information as ordinary flat spreadsheet columns. MET, leptons, b-tags, vertices and event IDs are stored as CMS-specific C++ objects. Docker let us run the official CMS software environment, CMSSW, so those objects could be read properly.

## Stage 3: Boundary Variables Extracted

CMSSW extracted event IDs, MET, HT, jet counts, leading and subleading jet pT, muon/electron/lepton counts, b-tag counts, max b-tag discriminator, primary vertices, packed-candidate counts and secondary-vertex counts.

## Stage 4: What The Real-Data-Only Boundary Analysis Found

The high-boundary real events are structured. They are not just random high values. The hand-defined N-Frame boundary tail is driven by a combination of missing-energy stress, visible-energy stress, multiplicity, b-tag/heavy-flavour structure, reconstruction complexity and compression-like imbalance.

Sample-level hand-defined boundary summary:

| sample_id                         |   events |   mean_boundary_z |   top10_frac |   top05_frac |   top01_frac |
|:----------------------------------|---------:|------------------:|-------------:|-------------:|-------------:|
| cms_jetht_run2016g_collision      |    50000 |          0.269958 |      0.13956 |      0.06912 |      0.01354 |
| cms_met_run2016g_collision        |    50000 |          0.371202 |      0.14716 |      0.07536 |      0.0156  |
| cms_singlemuon_run2016g_collision |    50000 |         -0.64116  |      0.01328 |      0.00552 |      0.00086 |

The unsupervised real-only model found a related rare-event boundary tail:

| sample_id                         |   events |   mean_unsup_boundary |   top10_frac |   top05_frac |   top01_frac |
|:----------------------------------|---------:|----------------------:|-------------:|-------------:|-------------:|
| cms_jetht_run2016g_collision      |    50000 |              0.230144 |      0.15134 |      0.07968 |      0.01646 |
| cms_met_run2016g_collision        |    50000 |              0.071949 |      0.10222 |      0.05102 |      0.00996 |
| cms_singlemuon_run2016g_collision |    50000 |             -0.302093 |      0.04644 |      0.0193  |      0.00358 |

## Stage 5: Which Datasets Are Enriched

Hand-defined top 5% boundary enrichment:

| sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| cms_met_run2016g_collision        |          0.5024 |            0.333333 |             1.5072 |          3768 |
| cms_jetht_run2016g_collision      |          0.4608 |            0.333333 |             1.3824 |          3456 |
| cms_singlemuon_run2016g_collision |          0.0368 |            0.333333 |             0.1104 |           276 |

Unsupervised top 5% boundary enrichment:

| sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| cms_jetht_run2016g_collision      |        0.5312   |            0.333333 |             1.5936 |          3984 |
| cms_met_run2016g_collision        |        0.340133 |            0.333333 |             1.0204 |          2551 |
| cms_singlemuon_run2016g_collision |        0.128667 |            0.333333 |             0.386  |           965 |

In plain English: MET and JetHT dominate the hand-defined high-boundary tail, while the unsupervised rare-event score leans more strongly towards JetHT and still keeps a meaningful MET component. SingleMuon is consistently lower in the high-boundary tails.

## Stage 6: Is This Evidence Of SUSY?

No. This is not evidence that SUSY has been found, and it does not show that CERN missed supersymmetry particles.

The honest result is: we used real CMS collision MiniAOD only to estimate where high N-Frame boundary-stress conditions occur, and to identify whether high-boundary real events show structured, repeatable patterns across independent real CMS primary datasets.

## Stage 7: Next Step

The 50,000-event-per-sample run was stable. The next step is to decide whether to process the full downloaded real MiniAOD subset and add exact per-event file provenance to the analyzer before scaling further.
