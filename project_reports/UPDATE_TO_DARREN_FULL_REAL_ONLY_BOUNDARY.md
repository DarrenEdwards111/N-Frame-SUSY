# Update To Darren: Full Real-Data-Only Boundary Analysis

Date: 2026-06-08

## What We Used

We used only real CMS collision data. No simulated SUSY samples were used in the main analysis.

We processed the full downloaded real MiniAOD subset:

- MET: 3 files, 227,443 events
- JetHT: 4 files, 98,145 events
- SingleMuon: 2 files, 340,314 events

Total: **665,902 real CMS collision events**.

## What We Fixed

We added exact source-file provenance. Every event row now records which ROOT file it came from, plus run/lumi/event IDs and file-level event indexes. This lets us check whether the boundary tail is stable across files.

## What Was Extracted

CMSSW extracted true MET, HT, jets, leading/subleading jet pT, muons, electrons, b-tags, max b-tag discriminator, event IDs, primary vertices, packed-candidate counts and secondary-vertex counts.

## What We Found

The strongest honest claim is that real CMS collision data show a structured high-boundary tail, defined by missing energy, visible energy, multiplicity, b-tag/reconstruction structure, secondary-vertex/candidate complexity and compression-like imbalance. This gives us a real-data boundary map for N-Frame follow-up, not a discovery claim.

Hand-defined top 5% boundary tail:

| sample_id                         |   tail_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|-------------------:|--------------:|
| cms_met_run2016g_collision        |       0.564122  |           1.65162  |         18783 |
| cms_jetht_run2016g_collision      |       0.3392    |           2.30143  |         11294 |
| cms_singlemuon_run2016g_collision |       0.0966783 |           0.189173 |          3219 |

Unsupervised top 5% boundary tail:

| sample_id                         |   tail_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|-------------------:|--------------:|
| cms_met_run2016g_collision        |        0.442095 |           1.29436  |         14720 |
| cms_jetht_run2016g_collision      |        0.359983 |           2.44244  |         11986 |
| cms_singlemuon_run2016g_collision |        0.197922 |           0.387279 |          6590 |

## Stability Across Files

The pattern is acceptable for this exploratory stage. It is not driven by one single file. MET and JetHT remain the main contributors to the high-boundary tail, and SingleMuon remains depleted. Some JetHT files are stronger than others, so the next robustness check should inspect data-quality/trigger/run conditions for the highest-boundary files.

## Is This Evidence Of SUSY?

No. This is not evidence that SUSY has been found, and it does not show that CERN missed supersymmetry particles.

The result is a real-data N-Frame boundary map: it tells us where unusual real collision events live in boundary-stress space.

## Next Step

The next step should be manual inspection of the top boundary events and adding trigger/filter information if possible. More data should only be added after we understand whether the strongest file-level enrichments are physics-like or data-quality/trigger effects.
