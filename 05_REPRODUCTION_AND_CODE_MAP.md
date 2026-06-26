# Reproduction and Code Map

## Environment

- Windows host with Docker Desktop.
- CMS image: `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700`.
- Python packages used: pandas, numpy, scipy, scikit-learn, pyhf, uproot, awkward, matplotlib, python-docx.
- Remote data path: CERN Open Data/XRootD endpoints documented in output manifests.

## Key code entry points

| Script | Purpose |
|---|---|
| `262_run_exact_sumweight_chunks.py` | Remote/resumable `GenFilterInfo` scans. |
| `263_build_exact_hybrid_sm_normalisation_tiers.py` | Build strict and metadata normalisation ledger. |
| `265_frozen_reference_opq_sm_shape_likelihood.py` | Corrected fixed-reference diagnostic; demonstrates control failure. |
| `266_frozen_reference_control_mixture_transfer.py` | Control-mixture transfer diagnostic; fails closure. |
| `267_stream_matched_plateau_control_transfer.py` | Trigger/offline plateau transfer diagnostic; fails closure. |
| `268_extract_run2016g_exact_trigger_calibration.py` / `269_exact_trigger_turnon_audit.py` | Exact trigger-path calibration. |
| `277_data_driven_pyhf_fit.py` | Disjoint cross-era data-driven null test; limitations documented. |
| `278_grouped_record_holdout_predictive_test.py` | Current valid grouped benchmark incrementality test. |
| `279_out_of_fold_predictive_significance.py` | Retained for provenance only; pooled significance is invalid. |
| `280_build_darren_comprehensive_handoff.py` | Rebuild this package. |

## Raw-data policy

Raw processed CSV and ROOT inputs are not copied into this package. `data_inventory.csv` gives canonical local paths, sizes and types. The output manifests under `key_outputs/outputs_remote_opq_sm_background_build/` and the cloud runbook document remote access. Do not infer that a table based on a sampled event subset is a full-record MC prediction.
