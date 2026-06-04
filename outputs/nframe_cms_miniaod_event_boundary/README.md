# N-Frame Event-Level Boundary-Access Analysis using CMS 2016G MiniAOD

Input data:

`D:/cern_open_data/cms_met_run2016g_miniaod_10gb`

This project is a feasibility/prototype analysis. It does not claim SUSY discovery and does not attempt a full CMS SUSY reinterpretation.

## Run Order

```bash
python scripts/01_make_filelist.py
python scripts/02_inspect_root_files.py
python scripts/03_extract_event_features_uproot.py
```

If `03_extract_event_features_uproot.py` reports that MiniAOD requires CMSSW/FWLite, use the CMSSW route below.

If a flat feature file exists:

```bash
python scripts/04_compute_nframe_event_scores.py
python scripts/05_event_level_descriptives.py
python scripts/06_make_event_plots.py
python scripts/07_build_pseudo_signal_regions.py
python scripts/08_boundary_outlier_analysis.py
python scripts/09_write_event_level_summary.py
```

## CMSSW Route

CMS MiniAOD is usually EDM ROOT, not flat NanoAOD. If uproot cannot expose the event-object branches, run a CMSSW analyzer inside a compatible CMS Open Data Docker/CMSSW environment.

Files provided:

- `cmssw/NFrameMiniAODAnalyzer.cc`
- `cmssw/run_nframe_miniAOD_cfg.py`

Inside CMSSW, place `NFrameMiniAODAnalyzer.cc` in a plugin package, build with `scram b`, then run:

```bash
cmsRun cmssw/run_nframe_miniAOD_cfg.py
```

Copy the produced `event_features.csv` to:

`data/processed/event_features.csv`

Then continue:

```bash
python scripts/04_compute_nframe_event_scores.py --input data/processed/event_features.csv --output data/processed/event_features_nframe_scored.csv
python scripts/05_event_level_descriptives.py --input data/processed/event_features_nframe_scored.csv
python scripts/06_make_event_plots.py --input data/processed/event_features_nframe_scored.csv
python scripts/07_build_pseudo_signal_regions.py --input data/processed/event_features_nframe_scored.csv
python scripts/09_write_event_level_summary.py --features data/processed/event_features_nframe_scored.csv
```

## Scientific Integrity

- Do not claim SUSY discovery.
- Do not call high-boundary events SUSY candidates.
- Do not compare to Standard Model expectations without simulation/background estimates.
- Report MiniAOD/CMSSW limitations honestly.
