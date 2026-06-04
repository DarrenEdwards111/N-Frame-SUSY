# N-Frame SUSY Exploratory Analyses

This repository contains generated data tables, scripts, reports, and packaged outputs for exploratory N-Frame SUSY/public-signal-region and CMS MiniAOD event-level analyses.

Scientific scope:

- No SUSY discovery is claimed.
- No hidden-symmetry confirmation is claimed.
- Signal-region analyses are public-data meta-analyses.
- CMS MiniAOD event-level outputs are feature-extraction and boundary-score prototypes.

Large external CERN Open Data ROOT files are not committed because they are 10.96 GB total and exceed normal GitHub storage/file limits. Their local filenames, sizes, and source metadata are recorded under `external_data_manifests/`.

Key folders:

- `outputs/nframe_susy_boundary/`: signal-region metadata, verified/imputed datasets, model results, plots, and summaries.
- `outputs/nframe_cms_miniaod_event_boundary/`: MiniAOD uproot-derived event-level tables and CMSSW run packages.
- `outputs/nframe_cms_miniaod_full/`: CMSSW project scaffold for full MiniAOD extraction.
- `external_data_manifests/`: manifest for local CMS Open Data ROOT files.
