from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN2016G = ROOT / "outputs_run2016g_control_calibrated_uncertainty" / "tables" / "02_control_calibrated_uncertainty_compact_readout.csv"
RUN2016H = ROOT / "outputs_control_calibrated_cross_sample_validation" / "tables" / "02_cross_sample_control_calibrated_compact_readout.csv"
STAGE2016H = ROOT / "outputs_control_calibrated_cross_sample_validation" / "tables" / "01_cross_sample_control_calibrated_stage_table.csv"
OUT = ROOT / "outputs_repeatable_trace_evidence_synthesis"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def stouffer(zs: list[float]) -> float:
    arr = np.array([z for z in zs if np.isfinite(z)], dtype=float)
    return float(arr.sum() / np.sqrt(len(arr))) if len(arr) else np.nan


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    g = pd.read_csv(RUN2016G)
    h = pd.read_csv(RUN2016H)
    g_best = g[g["uncertainty_model"].eq("control_calibrated_to_close_all_JetHT_SingleMuon")].iloc[0]
    h_best = h[h["validation_sample"].eq("Run2016H_fresh_same_frozen_score")].iloc[0]
    h_2015 = h[h["validation_sample"].eq("Run2015D_existing_residual_score_cross_check")].iloc[0]

    rows = [
        {
            "sample": "Run2016G_calibration_sample",
            "role": "control-calibration plus discovery-candidate development",
            "score_definition": "frozen N-Frame component score",
            "MET_0jet_Z": float(g_best["MET_0jet_Z"]),
            "HTMHT_1to2jets_Z": float(g_best["HTMHT_1to2jets_Z"]),
            "JetHT_1to2jets_Z": float(g_best["JetHT_1to2jets_Z"]),
            "SingleMuon_0jet_Z": float(g_best["SingleMuon_0jet_Z"]),
            "max_control_absZ": float(g_best["max_all_control_absZ"]),
            "controls_close": bool(g_best["all_controls_close_under_3sigma"]),
            "MET_survives_Z5": bool(g_best["MET_survives_Z5_after_control_closure"]),
        },
        {
            "sample": "Run2016H_fresh_validation",
            "role": "fresh same-era validation with same frozen score and same uncertainty",
            "score_definition": "frozen N-Frame component score recomputed from Run2016H components",
            "MET_0jet_Z": float(h_best["MET_0jet_Z"]),
            "HTMHT_1to2jets_Z": float(h_best["HTMHT_1to2jets_Z"]),
            "JetHT_1to2jets_Z": float(h_best["JetHT_1to2jets_Z"]),
            "SingleMuon_0jet_Z": float(h_best["SingleMuon_0jet_Z"]),
            "max_control_absZ": float(h_best["max_control_absZ"]),
            "controls_close": bool(h_best["controls_close_under_3sigma"]),
            "MET_survives_Z5": bool(h_best["MET_survives_Z5"]),
        },
        {
            "sample": "Run2015D_weaker_cross_check",
            "role": "older residual-score cross-check, not identical frozen score",
            "score_definition": "Run2015D residual Q99 score",
            "MET_0jet_Z": float(h_2015["MET_0jet_Z"]),
            "HTMHT_1to2jets_Z": float(h_2015["HTMHT_1to2jets_Z"]),
            "JetHT_1to2jets_Z": float(h_2015["JetHT_1to2jets_Z"]),
            "SingleMuon_0jet_Z": float(h_2015["SingleMuon_0jet_Z"]),
            "max_control_absZ": float(h_2015["max_control_absZ"]),
            "controls_close": bool(h_2015["controls_close_under_3sigma"]),
            "MET_survives_Z5": bool(h_2015["MET_survives_Z5"]),
        },
    ]
    table = pd.DataFrame(rows)
    combined = pd.DataFrame(
        [
            {
                "combined_test": "Run2016G_plus_Run2016H_MET_0jet",
                "included_samples": "Run2016G calibration sample; Run2016H fresh validation",
                "combined_MET_0jet_Stouffer_Z": stouffer([rows[0]["MET_0jet_Z"], rows[1]["MET_0jet_Z"]]),
                "weakest_independent_MET_0jet_Z": min(rows[0]["MET_0jet_Z"], rows[1]["MET_0jet_Z"]),
                "all_Run2016_controls_close": bool(rows[0]["controls_close"] and rows[1]["controls_close"]),
                "Run2016H_standalone_MET_over_5sigma": bool(rows[1]["MET_survives_Z5"]),
                "interpretation": "strong repeatable Run2016 MET trace candidate, but Run2016H is just below standalone 5 sigma",
            },
            {
                "combined_test": "Run2016G_plus_Run2016H_MET_HTMHT",
                "included_samples": "Run2016G MET/HTMHT; Run2016H MET/HTMHT",
                "combined_MET_0jet_Stouffer_Z": stouffer([rows[0]["MET_0jet_Z"], rows[0]["HTMHT_1to2jets_Z"], rows[1]["MET_0jet_Z"], rows[1]["HTMHT_1to2jets_Z"]]),
                "weakest_independent_MET_0jet_Z": min(rows[0]["MET_0jet_Z"], rows[1]["MET_0jet_Z"]),
                "all_Run2016_controls_close": bool(rows[0]["controls_close"] and rows[1]["controls_close"]),
                "Run2016H_standalone_MET_over_5sigma": bool(rows[1]["MET_survives_Z5"]),
                "interpretation": "combined MET+HTMHT evidence is strong, but HTMHT is supportive rather than decisive",
            },
        ]
    )
    table.to_csv(TABLES / "01_repeatable_trace_sample_readout.csv", index=False)
    combined.to_csv(TABLES / "02_repeatable_trace_combined_readout.csv", index=False)

    h_stage = pd.read_csv(STAGE2016H)
    h_focus = h_stage[
        (h_stage["validation_sample"].eq("Run2016H_fresh_same_frozen_score"))
        & h_stage[["primary_dataset", "jet_bin"]]
        .apply(tuple, axis=1)
        .isin([("MET", "0jet"), ("HTMHT", "1to2jets"), ("JetHT", "1to2jets"), ("SingleMuon", "0jet")])
    ].copy()

    report = f"""# Repeatable N-Frame Boundary-Trace Evidence Synthesis

## Question

Does the current best frozen N-Frame boundary-trace rule look repeatable after controls are forced to close?

## Control Rule

The residual background-shape uncertainty is fixed to the Run2016G control-calibrated value:

```text
relative_uncertainty = 0.47336574523492086
```

This value was chosen because it is the smallest uncertainty that closes all Run2016G JetHT and SingleMuon controls under 3 sigma. It was then applied unchanged to Run2016H.

## Sample Readout

{table.to_markdown(index=False, floatfmt=".3f")}

## Combined Readout

{combined.to_markdown(index=False, floatfmt=".3f")}

## Run2016H Key Counts

{h_focus.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

The strongest current result is:

> A frozen N-Frame component score gives a repeatable MET 0jet high-boundary trace in Run2016G and fresh Run2016H, while JetHT and SingleMuon controls close under the same control-calibrated uncertainty.

This is not yet a final discovery claim because:

- Run2016G was used to calibrate the uncertainty.
- Run2016H is independent data, but its standalone MET result is 4.73 sigma, just below 5 sigma.
- Run2015D is not yet a clean same-score validation; the available 2015 table uses an older residual-score setup and fails controls.
- Official SM process/background modelling is still needed to replace or validate the data-driven 47.3% uncertainty.

## What Is Needed Next

To move from "strong candidate" to "breakthrough-level evidence":

1. Recompute the exact same frozen N-Frame component score on more Run2016H files and unused Run2016G files.
2. Rebuild Run2015D with the same component score rather than the older residual score.
3. Test whether Run2016H MET 0jet rises above 5 sigma as statistics increase while controls stay closed.
4. Replace the 47.3% data-driven uncertainty with a process-aware SM model, or show that official SM/control sidebands imply a similar or smaller uncertainty.
5. Only then phrase the physics claim as a repeatable observable-boundary trace, not direct SUSY particle discovery.
"""
    (REPORTS / "01_REPEATABLE_TRACE_EVIDENCE_SYNTHESIS.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_REPEATABLE_TRACE_EVIDENCE_SYNTHESIS.md")
    print(table.to_string(index=False))
    print(combined.to_string(index=False))


if __name__ == "__main__":
    main()
