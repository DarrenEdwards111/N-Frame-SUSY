# Final Deliverables Checklist

## 1. Scripts Created Or Modified

- `scripts/real_collision_common.py`
- `scripts/00_audit_real_collision_20gb.py`
- `scripts/01_inspect_real_collision_root_files.py`
- `scripts/02_try_uproot_real_collision_partial_extraction.py`
- `scripts/03_score_real_collision_boundary.py`
- `scripts/04_analyse_real_collision_boundary_structure.py`

## 2. Whether All 9 Real ROOT Files Were Validated

Yes. All 9 real CMS collision MiniAOD ROOT files validated against the manifest.

## 3. Whether Uproot Could Extract Anything Useful

Yes. Uproot opened all 9 files and extracted 665,902 event rows with visible jet features.

## 4. Whether CMSSW/Docker Was Available And Whether It Ran

Docker CLI is installed, but Docker Desktop's Linux engine was not running. `cmsRun` and `scram` were not available in Windows PowerShell. CMSSW extraction did not run.

## 5. Number Of Events Extracted

665,902 event rows.

## 6. Event-Level Variables Successfully Extracted

- sample ID
- source file
- event index within file
- jet multiplicity
- jets with pt > 30 GeV
- jets with pt > 50 GeV
- HT from jets > 30 GeV
- leading jet pt
- subleading jet pt
- leading jet eta/phi
- sum jet pt
- jet mass sum
- hadron-flavour proxy where readable

## 7. N-Frame Boundary Components Computed

- `R_multiplicity`
- `R_reconstruction`
- `B_boundary_equal_weight`
- `B_boundary_equal_weight_z`
- top 50%, 25%, 10%, 5%, and 1% boundary flags

## 8. Components Unavailable

- `R_missing`
- `R_compression_proxy`
- `R_lifetime_proxy`
- `R_displacement_proxy`

These were unavailable because MET and genuine lifetime/displacement variables were not extracted.

## 9. Main Real-Data Boundary Result

In the real-data Python fallback, the high-boundary tail is strongly enriched in JetHT events, which is expected for a visible jet/HT score and should be treated as boundary-stress structure in visible activity, not SUSY evidence.

## 10. Whether More Real Data Are Needed

No, not yet. Fix CMSSW extraction before downloading more.

## 11. Exact Files And Reports Created

- `results/tables/real_collision_20gb_manifest_validated.csv`
- `results/tables/root_file_inspection_summary.csv`
- `results/tables/uproot_real_collision_partial_extraction_log.csv`
- `results/tables/boundary_component_availability.csv`
- `results/tables/boundary_component_summary_by_sample.csv`
- `results/tables/real_collision_boundary_summary_by_sample.csv`
- `results/tables/real_collision_boundary_summary_by_file.csv`
- `results/tables/high_boundary_tail_enrichment_by_sample.csv`
- `results/tables/real_collision_pairwise_boundary_tests.csv`
- `results/tables/boundary_component_driver_summary.csv`
- `results/tables/top_1000_boundary_events.csv`
- `data/processed/real_collision_20gb_uproot_partial_event_features.csv`
- `data/processed/real_collision_20gb_event_features_scored.csv`
- `reports/PHASE1_DATA_AUDIT_REPORT.md`
- `reports/UPROOT_PARTIAL_EXTRACTION_REPORT.md`
- `reports/CMSSW_REAL_COLLISION_20GB_RUN_GUIDE.md`
- `reports/CMSSW_EXTRACTION_STATUS_REPORT.md`
- `reports/BOUNDARY_SCORING_REPORT.md`
- `reports/REAL_COLLISION_BOUNDARY_ANALYSIS_REPORT.md`
- `reports/OPTIONAL_SIMULATION_CALIBRATION_APPENDIX.md`
- `reports/REAL_DATA_BOUNDARY_AND_SIGNAL_REGION_SYNTHESIS.md`
- `reports/DO_WE_NEED_MORE_REAL_DATA.md`
- `reports/UPDATE_TO_DARREN_GOLD_STANDARD_NEXT_STEP.md`

## 12. Exact Command To Run Next

Open Docker Desktop first. Once it says the Linux engine is running, rerun:

```powershell
docker info
```

Then follow:

```text
reports\CMSSW_REAL_COLLISION_20GB_RUN_GUIDE.md
```

