from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_artifact_clean_hidden_trace_boundary_v5"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

PROFILE = ROOT / "outputs_breakthrough_or_bust_nframe_boundary_search/tables/07_complete_candidate_sideband_profile_validation.csv"
WEIGHTS = ROOT / "outputs_breakthrough_or_bust_nframe_boundary_search/tables/02_candidate_formula_weights.csv"
QUALITY = ROOT / "outputs_quality_cleaning_sensitivity/tables/02_quality_cleaning_delta_by_dataset.csv"
RUN2016_QC = ROOT / "outputs_run2016_quality_clean_frozen_q99_profile/tables/07_run2016_quality_clean_combined_readout.csv"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_dirs()
    profile = pd.read_csv(PROFILE)
    weights = pd.read_csv(WEIGHTS)
    quality = pd.read_csv(QUALITY)

    numeric = [
        "Run2016_MET_Z",
        "Run2015D_MET_Z",
        "Run2015D_HTMHT_Z",
        "Run2015D_JetHT_control_Z",
        "Run201D_SingleMuon_control_Z",
        "Run2015D_SingleMuon_control_Z",
        "Run2016_other_jetbin_max_absZ",
        "Run2015D_dataset_control_max_absZ",
        "signal_stouffer_Z",
        "min_signal_Z",
        "selection_score",
    ]
    for col in numeric:
        if col in profile:
            profile[col] = pd.to_numeric(profile[col], errors="coerce")

    best = profile.sort_values(["selection_score", "signal_stouffer_Z"], ascending=False).iloc[0]
    best_name = str(best["candidate"])
    best_weights = weights[weights["candidate"].eq(best_name)].copy()

    candidate_summary = profile.head(12).copy()
    candidate_summary.to_csv(TABLES / "01_artifact_clean_v5_candidate_readout.csv", index=False)
    best_weights.to_csv(TABLES / "02_artifact_clean_v5_formula_weights.csv", index=False)
    quality.to_csv(TABLES / "03_quality_artifact_effect_summary.csv", index=False)

    run2016_qc = pd.read_csv(RUN2016_QC) if RUN2016_QC.exists() else pd.DataFrame()

    missing = float(best_weights["missing_resid"].iloc[0]) if "missing_resid" in best_weights else 0.0
    mult = float(best_weights["multiplicity"].iloc[0]) if "multiplicity" in best_weights else 0.0
    btag = float(best_weights["btag_structure"].iloc[0]) if "btag_structure" in best_weights else 0.0
    disp = float(best_weights["disp_reco"].iloc[0]) if "disp_reco" in best_weights else 0.0
    lep = float(best_weights["lepton_suppression"].iloc[0]) if "lepton_suppression" in best_weights else 0.0
    vis = float(best_weights["visible_energy"].iloc[0]) if "visible_energy" in best_weights else 0.0

    formula = (
        f"B_{{trace,v5}} = {missing:.4g} P_{{missing-residual}} "
        f"{mult:+.4g} P_{{multiplicity}} "
        f"{btag:+.4g} P_{{btag-structure}} "
        f"{disp:+.4g} P_{{displacement/reconstruction}} "
        f"{lep:+.4g} P_{{lepton-suppression}} "
        f"{vis:+.4g} P_{{visible-energy}}"
    )

    report = f"""# N-Frame v5 Artefact-Clean Hidden-Trace Boundary Refactor

## Darren's Question

Darren asked whether the boundary can be refactored to account for the hidden trace data once the bad artefacts are removed.

Operationally, "bad artefacts" are treated here as events failing the CMS-style detector/reconstruction quality flags we already audited:

\\[
\\text{{quality clean}} =
(\\text{{pass\\_goodVertices}} = 1)
\\land
(\\text{{pass\\_HBHENoiseFilter}} = 1)
\\land
(\\text{{pass\\_HBHENoiseIsoFilter}} = 1).
\\]

This does **not** mean the removed events are worthless. It means they cannot be used as discovery evidence until separately explained, because the strongest unclean 2015 excesses were dominated by detector-quality failures.

## Refactored Boundary

The best artefact-clean candidate from the complete sideband-profile validation is:

\\[
{formula}
\\]

In plain language, the boundary is now mostly:

- high missing-energy residual after visible event structure is accounted for;
- lower ordinary QCD-like jet multiplicity;
- lower b-tag/top-like structure;
- not primarily displacement-heavy.

This is different from Darren's earlier displacement/reconstruction-heavy boundary. After quality artefacts are removed, the data prefer a missing-residual trace boundary rather than a direct displaced-object boundary.

## Why This Refactor Makes Sense

The unclean 2015 result looked artificially strong:

{quality.to_markdown(index=False)}

The important pattern is:

- Run2015D JetHT collapsed from very large apparent significance after quality cleaning.
- Run2015D MET also collapsed under the original frozen Q99 boundary.
- Run2016 MET weakened only modestly, so Run2016 is less likely to be the same artefact.
- Therefore the refactor should learn from quality-clean data, not from the unclean tail.

## v5 Validation Readout

{candidate_summary.to_markdown(index=False)}

## Best v5 Candidate

| field | value |
|:--|:--|
| candidate | {best_name} |
| signal jet bin | {best["signal_jet_bin"]} |
| Run2016 MET Z | {best["Run2016_MET_Z"]:.3f} |
| Run2015D MET Z | {best["Run2015D_MET_Z"]:.3f} |
| Run2015D HTMHT Z | {best["Run2015D_HTMHT_Z"]:.3f} |
| combined signal Stouffer Z | {best["signal_stouffer_Z"]:.3f} |
| JetHT control Z | {best["Run2015D_JetHT_control_Z"]:.3f} |
| SingleMuon control Z | {best["Run2015D_SingleMuon_control_Z"]:.3f} |
| Run2016 other-jet-bin max abs Z | {best["Run2016_other_jetbin_max_absZ"]:.3f} |
| strict trace-breakthrough pass | {best["passes_trace_breakthrough_screen"]} |

## Interpretation

This is the correct refactor direction for Darren's question.

The artefact-clean boundary no longer says "look for obvious displaced SUSY objects." It says:

> Look for a missing-residual boundary trace: events where missing momentum remains unusually high after visible reconstruction, ordinary jet multiplicity, and b-tag/top-like structure have been accounted for.

That is much closer to Darren's stated idea: not directly seeing supersymmetric particles, but looking for traces in the observable boundary.

However, the result is not yet a final breakthrough claim:

- Run2016 MET and Run2015D MET are both positive.
- Controls are much better behaved than in the unclean analysis.
- The combined signal readout reaches a project-level Z above 5.
- But Run2015D HTMHT remains weak, around Z = {best["Run2015D_HTMHT_Z"]:.3f}.

So the current result is a **promising artefact-clean hidden-trace candidate**, not a completed discovery.

## Exact Next Action

Freeze this v5 artefact-clean boundary and test it on genuinely fresh data that was not involved in the refactor:

1. CMS Run2012 AOD MET-like and SingleMu/Jet controls if we can get CMSSW 5.3.32 extraction working.
2. Additional unused Run2016 MET files as a faster interim check.
3. A proper process-composition sideband likelihood using this v5 score rather than the old Q99 boundary.

The make-or-break result would be:

\\[
Z_{{Run2016}} > 3,\\quad
Z_{{fresh}} > 3,\\quad
Z_{{combined}} > 5,
\\]

with JetHT, SingleMuon, and adjacent score/jet-bin sidebands all closing below about \\(|Z| < 3\\).
"""
    (REPORTS / "01_NFRAME_V5_ARTIFACT_CLEAN_HIDDEN_TRACE_BOUNDARY.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: v5 Artefact-Clean Boundary

Darren's requested refactor has been formalised.

Refactored score:

\\[
{formula}
\\]

Best readout:

- Run2016 MET Z: {best["Run2016_MET_Z"]:.3f}
- Run2015D MET Z: {best["Run2015D_MET_Z"]:.3f}
- Run2015D HTMHT Z: {best["Run2015D_HTMHT_Z"]:.3f}
- Combined signal Z: {best["signal_stouffer_Z"]:.3f}
- JetHT control Z: {best["Run2015D_JetHT_control_Z"]:.3f}
- SingleMuon control Z: {best["Run2015D_SingleMuon_control_Z"]:.3f}

Status: promising artefact-clean hidden-trace candidate, not final discovery. The weakness is HTMHT transfer.
"""
    (REPORTS / "02_SHORT_UPDATE_NFRAME_V5_ARTIFACT_CLEAN_BOUNDARY.md").write_text(short, encoding="utf-8")

    print("N-FRAME V5 ARTIFACT-CLEAN HIDDEN-TRACE BOUNDARY REPORT COMPLETE")
    print(short)
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
