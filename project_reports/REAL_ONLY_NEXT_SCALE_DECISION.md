# Real-Only Next Scale Decision

Date: 2026-06-08

## Did 50k/100k Run Successfully?

The 50,000-event intermediate target ran successfully for all three real CMS primary datasets. We did not run 100,000 per sample yet because the instruction was to validate the intermediate run first.

## Events Analysed

Total real events analysed: 150,000

| sample_id                         | primary_dataset   |   record_id |   events |
|:----------------------------------|:------------------|------------:|---------:|
| cms_met_run2016g_collision        | MET               |       30509 |    50000 |
| cms_jetht_run2016g_collision      | JetHT             |       30508 |    50000 |
| cms_singlemuon_run2016g_collision | SingleMuon        |       30513 |    50000 |

## Are High-Boundary Tails Stable?

The tails are structured and repeatable enough to justify scaling, but source-file stability cannot be fully assessed because exact per-event source file provenance is not yet written by the analyzer. Dataset-level stability is clear: MET and JetHT are enriched in hand-defined high-boundary tails; SingleMuon is lower.

## Is More Data Needed?

Yes, if Darren wants a stronger real-data-only case. More real data would test whether the high-boundary tail remains stable across more files and luminosity sections.

## Should We Process The Full 20.789 GiB?

Recommendation: yes, but only after adding exact per-event source file provenance to the analyzer or at least splitting extraction file-by-file. The current 50k run is stable and output size is manageable, so full processing is technically feasible.

## Should We Add More Real CMS Records?

Not yet. First finish the downloaded 20.789 GiB real subset. Then add more records only if the same high-boundary structure persists.

## Should We Add NanoAOD Validation?

Yes as a parallel validation later. NanoAOD is easier to process and could check whether the same boundary axes appear in a flatter real-data format, but MiniAOD remains the stronger current route because it exposes richer CMS objects.

## Exact Next Command

Run full extraction sample-by-sample after deciding whether to add file-level provenance first. The current safe next technical step is:

```powershell
# First update the analyzer/run route to preserve exact source file per event or run one ROOT file at a time.
# Then run full real-only extraction with NFRAME_MAXEVENTS_FULL=-1 for MET, JetHT and SingleMuon only.
```

Do not process simulated files for the main result.
