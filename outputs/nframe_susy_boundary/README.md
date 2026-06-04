# N-Frame SUSY Boundary-Selection Reanalysis

This project tests whether observed-minus-expected deviations in public ATLAS/CMS SUSY signal regions increase with an N-Frame boundary-access score.

It starts from HEPData/published signal-region tables. Raw CERN Open Data is intentionally out of scope for this first pass.

## Project Layout

- `data/raw/`: HEPData CSV/JSON files and the synthetic demo CSV.
- `data/processed/`: normalized and scored signal-region tables.
- `scripts/`: command-line pipeline scripts.
- `results/figures/`: diagnostic plots.
- `results/tables/`: regression outputs and summary tables.
- `results/nframe_boundary_results.md`: generated interpretation.

## Selected Public Sources

The source configuration is in `data/raw/selected_hepdata_sources.yml`.

Initial targets:

- CMS-SUS-21-007, HEPData `10.17182/hepdata.135454.v1`: one-lepton SUSY search with multi-bin signal-region yield tables.
- ATLAS-SUSY-2018-32, HEPData `10.17182/hepdata.89413.v4`: two-lepton electroweak SUSY search with inclusive SR background-fit tables and SR kinematic distributions.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Download HEPData Tables

```bash
python scripts/download_hepdata_tables.py
```

If HEPData returns a browser challenge for a table export, open the URL printed in `data/raw/download_manifest.json` and save the CSV/JSON into the relevant `data/raw/<analysis>/` directory. The loader also accepts a manually curated normalized CSV with these columns:

```text
analysis, experiment, sqrt_s, luminosity, signal_region, N_obs, N_exp, sigma_exp,
MET, HT_or_meff, N_jets, N_leptons, N_btags, category
```

Missing kinematic columns are allowed. Only values explicitly encoded in labels are imputed; otherwise they remain missing until scoring, where missing z-scored features contribute zero.

## Run Demo Pipeline

The included `data/raw/demo_signal_regions.csv` is synthetic and exists only to verify the workflow.

```bash
python scripts/load_signal_regions.py
python scripts/compute_boundary_score.py
python scripts/run_regression.py
python scripts/make_plots.py
python scripts/write_results_summary.py
```

For a quicker smoke test, reduce resampling:

```bash
python scripts/run_regression.py --bootstrap 1000 --permutations 1000
```

## Interpretation Rule

- `beta > 0`, bootstrap CI excludes zero, and permutation `p < .05`: preliminary support for N-Frame boundary-selection.
- CI includes zero or beta is approximately zero: no evidence for N-Frame boundary-selection.
- Significant `beta < 0`: evidence against the predicted direction.

Do not interpret this as a SUSY discovery claim. This is a meta-analysis of published signal-region deviations.
