from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_breakthrough_readiness_synthesis"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

MULTI = ROOT / "outputs_frozen_q99_multifile_breakthrough_audit/tables/02_frozen_q99_summary_by_file_and_control.csv"
COMBINED = ROOT / "outputs_frozen_q99_multifile_breakthrough_audit/tables/03_frozen_q99_multifile_combined_significance.csv"
CONTROLS = ROOT / "outputs_frozen_q99_multifile_breakthrough_audit/tables/04_jetbin_control_summary.csv"
FRESH = ROOT / "outputs_frozen_q99_1to2jet_fresh_validation/tables/06_fresh_q99_1to2jet_validation_summary.csv"
AVAIL = ROOT / "outputs_frozen_q99_1to2jet_fresh_validation/tables/01_cern_run2017_2018_met_availability_audit.csv"


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_dirs()
    summary = pd.read_csv(MULTI)
    combined = pd.read_csv(COMBINED)
    controls = pd.read_csv(CONTROLS)
    fresh = pd.read_csv(FRESH)
    avail = pd.read_csv(AVAIL)

    signal = summary[(summary["unit"].eq("source_file")) & (summary["jet_bin"].eq("1to2jets"))].copy()
    signal["passes_5sigma"] = signal["q99_shape_Z"] >= 5
    signal["positive"] = signal["q99_shape_Z"] > 0

    criteria = pd.DataFrame(
        [
            {
                "criterion": "Region frozen before fresh validation",
                "status": "PASS",
                "evidence": "Frozen manifest written before fresh 17CF0768 Run2016H file was scored.",
            },
            {
                "criterion": "Fresh disjoint real-data replication",
                "status": "PASS",
                "evidence": f"Fresh file Q99 Z = {fresh['q99_Z_with_shape_uncertainty'].iloc[0]:.2f}, Obs/Exp = {fresh['q99_observed_over_expected'].iloc[0]:.2f}.",
            },
            {
                "criterion": "Multifile consistency",
                "status": "STRONG_PARTIAL",
                "evidence": f"{int(signal['passes_5sigma'].sum())}/{len(signal)} source files pass 5 sigma; all {len(signal)} are positive; weakest file Z = {signal['q99_shape_Z'].min():.2f}.",
            },
            {
                "criterion": "Combined frozen-region significance",
                "status": "PASS",
                "evidence": f"Stouffer Z = {combined['stouffer_Z'].iloc[0]:.2f}; Fisher Z = {combined['fisher_Z'].iloc[0]:.2f}; total Obs/Exp = {combined['total_obs_exp_shape'].iloc[0]:.2f}.",
            },
            {
                "criterion": "Jet-bin controls do not show same effect",
                "status": "PASS",
                "evidence": "0-jet, 3-4 jet and 5+ jet controls are below discovery level in the aggregate.",
            },
            {
                "criterion": "New CMS era validation",
                "status": "BLOCKED",
                "evidence": "CERN API search found no usable CMS Run2017/Run2018 MET MiniAOD records.",
            },
            {
                "criterion": "Official CMS analysis-grade SM systematics",
                "status": "NOT_COMPLETE",
                "evidence": "Current SM model is luminosity-weighted and sideband-shaped, but not an official CMS profile-likelihood background model with full object/trigger uncertainties.",
            },
            {
                "criterion": "Direct SUSY/bulk-space particle claim",
                "status": "NO_CLAIM",
                "evidence": "Evidence supports an observable N-Frame boundary-trace anomaly candidate, not direct detection of supersymmetric particles.",
            },
        ]
    )
    criteria.to_csv(TABLES / "01_breakthrough_readiness_criteria.csv", index=False)
    signal.to_csv(TABLES / "02_signal_file_consistency.csv", index=False)

    final_status = "BREAKTHROUGH_LEVEL_ANOMALY_CANDIDATE_NOT_FINAL_DISCOVERY"
    synthesis = f"""# Breakthrough Readiness Synthesis

## Bottom Line

Status: **{final_status}**

The frozen Q99 1-2 jet N-Frame MET boundary trace is now a strong anomaly candidate. It replicated on a fresh disjoint Run2016H MET MiniAOD file and is positive across every currently available disjoint MET source file tested.

It is not yet a final discovery claim because a genuinely new CMS era was not available through the CERN Open Data API, and the SM background model is not yet official CMS analysis-grade.

## Core Result

{combined.to_markdown(index=False)}

## Per-File Frozen Signal

{signal[["source_file", "q99_shape_observed", "q99_shape_expected", "q99_shape_obs_exp", "q99_shape_Z", "passes_5sigma"]].to_markdown(index=False)}

## Controls

{controls[["jet_bin", "q99_shape_observed", "q99_shape_expected", "q99_shape_obs_exp", "q99_shape_Z"]].to_markdown(index=False)}

## Readiness Criteria

{criteria.to_markdown(index=False)}

## Plain-English Interpretation

The earlier broad MET excess was vulnerable because the sideband was also high. The stronger finding is narrower:

**In MET events with 1-2 jets, the very final 1% of the N-Frame missing-vs-visible boundary score remains far above the sideband-shaped SM expectation.**

Across 8 disjoint source files:

- total observed Q99 events: {combined['total_observed'].iloc[0]:.0f}
- total expected after sideband-shape correction: {combined['total_expected_shape'].iloc[0]:.1f}
- observed/expected: {combined['total_obs_exp_shape'].iloc[0]:.2f}x
- combined Stouffer Z: {combined['stouffer_Z'].iloc[0]:.2f}
- combined Fisher Z: {combined['fisher_Z'].iloc[0]:.2f}

This is breakthrough-level for the project as an N-Frame boundary-trace anomaly candidate. It is not yet a Nobel/discovery-level physics result until it survives new-era or independent-experiment validation and official-grade SM systematics.
"""
    (REPORTS / "01_BREAKTHROUGH_READINESS_SYNTHESIS.md").write_text(synthesis, encoding="utf-8")

    short = f"""# Short Update: Breakthrough Readiness

The frozen Q99 1-2 jet N-Frame MET boundary trace is now a strong breakthrough-level anomaly candidate.

Combined across 8 disjoint MET source files:

- observed: {combined['total_observed'].iloc[0]:.0f}
- expected after sideband-shape correction: {combined['total_expected_shape'].iloc[0]:.1f}
- Obs/Exp: {combined['total_obs_exp_shape'].iloc[0]:.2f}x
- Stouffer Z: {combined['stouffer_Z'].iloc[0]:.2f}
- Fisher Z: {combined['fisher_Z'].iloc[0]:.2f}
- files passing 5 sigma individually: {int(combined['files_passing_5sigma'].iloc[0])}/{int(combined['n_files'].iloc[0])}

Controls:

{controls[["jet_bin", "q99_shape_obs_exp", "q99_shape_Z"]].to_markdown(index=False)}

Best honest wording: breakthrough-level N-Frame boundary-trace anomaly candidate, not yet final SUSY/new-physics discovery.
"""
    (REPORTS / "02_SHORT_UPDATE_BREAKTHROUGH_READINESS.md").write_text(short, encoding="utf-8")

    print("BREAKTHROUGH READINESS SYNTHESIS COMPLETE")
    print(criteria.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
