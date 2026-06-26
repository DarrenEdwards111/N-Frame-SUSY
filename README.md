# N-Frame / CERN Comprehensive Handoff

**Prepared:** 24 June 2026  
**Project root:** `nframe_cms_stage2_event_boundary`  
**Purpose:** allow Darren to reconstruct the full project history, inspect every important method/result, and continue from the current evidence without relying on undocumented AI summaries.

## Start here

1. Read `01_EXECUTIVE_STATUS.md`.
2. Read `02_PROJECT_CHRONOLOGY_AND_FINDINGS.md`.
3. Read `03_VERIFIED_RESULTS_VS_INVALIDATED_CLAIMS.md`.
4. Read `04_CURRENT_ROADBLOCKS_AND_REQUIRED_DECISIONS.md`.
5. Use `05_REPRODUCTION_AND_CODE_MAP.md` with `code/` and `key_outputs/` to reproduce or extend individual stages.

## Current conclusion

No direct SUSY discovery, hidden-sector discovery, or credible collider anomaly has been established. Earlier high-significance values were invalidated by self-referential score bands, incomplete backgrounds, overlapping calibration/test events, or event-level pseudo-replication.

The strongest surviving statements are:

- independent MiniAOD/AOD/NanoAOD extraction and feature-mapping work is operational;
- N-Frame-inspired scores can expose reconstruction/topology structure, but no unambiguous real-data residual survives the corrected disjoint test;
- the fully disjoint Run2016G-to-Run2016H data-driven MET-shape comparison is null (`local Z about 0.77` under its stated model);
- a record-level benchmark test has the full N-Frame feature set improve AUC in all five held-out signal records, but independent-record evidence is weak (`one-sided p = 0.061`, Z = 1.55), not breakthrough-level.

## Package scope

This package contains code, reports, result tables, source theory PDFs, manuscripts, reproducibility instructions, remote-data manifests, and a manifest of excluded raw data. Raw event CSV/ROOT files are intentionally excluded because they are too large and can be regenerated from the documented CERN Open Data/XRootD manifests.

## Non-negotiable interpretation rules

- Do not quote `7.76 sigma`, `5.75 sigma`, `10.8 sigma`, or `36.9 sigma` as valid physics/model evidence.
- Do not alter score coefficients, quantile edges, regions or systematics after inspecting a final holdout in order to recover a high Z.
- Do not combine MiniAOD, NanoAOD, AOD and ATLAS statistics into one significance.
- A future anomaly claim requires a fixed protocol, disjoint holdout, complete signed-weight process model, and closed control/validation regions.
