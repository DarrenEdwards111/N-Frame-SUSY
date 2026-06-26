# Real-Only Full Next Step Decision

Date: 2026-06-08

## Did Full Extraction Finish?

Yes. Full extraction completed for all 9 downloaded real MiniAOD ROOT files.

## Total Events Analysed

665,902 real CMS collision events.

| sample_id                         | primary_dataset   |   events |   files |
|:----------------------------------|:------------------|---------:|--------:|
| cms_jetht_run2016g_collision      | JetHT             |    98145 |       4 |
| cms_met_run2016g_collision        | MET               |   227443 |       3 |
| cms_singlemuon_run2016g_collision | SingleMuon        |   340314 |       2 |

## Disk And Output Size

Approximate CSV output size in `cmssw_real_only_full_file_by_file`: **2527.9 MB**. D: drive remained healthy after processing.

## Runtime

The full file-by-file extraction took roughly 45 minutes in the logged run. Analysis/scoring took a few additional minutes.

## Was The Boundary Pattern Stable By File?

Acceptable for exploratory use, but not perfectly uniform. The effect is not one-file-only: MET and JetHT high-boundary enrichment persists across multiple files. Some JetHT files have higher boundary fractions, so file-level follow-up is needed.

## Is More Real Data Needed?

Not immediately. The better next step is to inspect the current top boundary events and add trigger/filter variables. More data should be added only after clarifying whether file-level enrichments reflect physics-like structure, trigger selection or data-quality conditions.

## Should We Add More Run2016G Files Or Primary Datasets?

Later, yes, if the current file-level pattern remains interpretable after trigger/data-quality follow-up. For now, do not add more data.

## Should We Add NanoAOD As A Cross-Check?

Yes, but after inspecting the MiniAOD top events. NanoAOD would be a useful faster parallel validation.

## Should We Inspect Top Boundary Events Manually?

Yes. This is the recommended next action.

## Exact Recommended Next Command

```powershell
D:\Anaconda\python.exe "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\scripts\28_analyse_real_only_full_high_boundary_tail.py"
```

Then inspect:

`results/tables/real_only_full_top_1000_hand_boundary_events.csv`

and cross-check top events against file/run/lumi patterns and available CMS trigger/filter information.
