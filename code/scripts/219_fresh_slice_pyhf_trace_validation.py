from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
IN_READOUT = ROOT / "outputs_sm_robustness_extension" / "tables" / "04_augmented_sm_template_target_readout.csv"
OUT = ROOT / "outputs_fresh_slice_pyhf_trace_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

TRACE = ("MET", "0jet")
SUPPORT = ("HTMHT", "1to2jets")
CONTROLS = [("JetHT", "1to2jets"), ("SingleMuon", "0jet")]
SCENARIOS = ["Run2016G_only", "Run2016H_only", "Run2016G_plus_Run2016H"]
MODES = ["all_weighted_sm_augmented", "full_component_only_augmented"]
CONTROL_CLOSE_TOL = 1e-9


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, JSON]:
        path.mkdir(parents=True, exist_ok=True)


def z_from_p(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def gaussian_z(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def load_rows(mode: str, scenario: str, include_support: bool) -> pd.DataFrame:
    readout = pd.read_csv(IN_READOUT)
    sub = readout[(readout["sm_template_mode"].eq(mode)) & (readout["scenario"].eq(scenario))].copy()
    wanted = [TRACE, *CONTROLS]
    if include_support:
        wanted.insert(1, SUPPORT)
    rows = []
    for dataset, jet_bin in wanted:
        hit = sub[(sub["primary_dataset"].eq(dataset)) & (sub["jet_bin"].eq(jet_bin))]
        if hit.empty:
            raise RuntimeError(f"Missing {mode} {scenario} {dataset} {jet_bin}")
        rows.append(hit.iloc[0].to_dict())
    out = pd.DataFrame(rows)
    for col in ["q99_observed", "q99_expected_sm_shape", "relative_shape_uncertainty_needed_for_controls"]:
        out[col] = pd.to_numeric(out[col], errors="raise")
    return out


def build_model(rows: pd.DataFrame, rel_unc: float) -> tuple[pyhf.Model, list[float]]:
    channels = []
    observations_by_channel = {}
    for r in rows.itertuples(index=False):
        dataset = str(r.primary_dataset)
        jet_bin = str(r.jet_bin)
        channel = f"{dataset}_{jet_bin}"
        obs = float(r.q99_observed)
        bkg = max(float(r.q99_expected_sm_shape), 1e-9)
        is_trace = (dataset, jet_bin) == TRACE
        observations_by_channel[channel] = obs
        channels.append(
            {
                "name": channel,
                "samples": [
                    {
                        "name": "nframe_trace_excess",
                        "data": [bkg if is_trace else 0.0],
                        "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}],
                    },
                    {
                        "name": "sm_background",
                        "data": [bkg],
                        "modifiers": [
                            {
                                "name": "correlated_sm_shape",
                                "type": "normsys",
                                "data": {"hi": 1.0 + rel_unc, "lo": max(1.0 - rel_unc, 1e-6)},
                            },
                            {
                                "name": f"mcstat_{dataset}_{jet_bin}",
                                "type": "staterror",
                                "data": [float(max(np.sqrt(bkg), 1.0))],
                            },
                        ],
                    },
                ],
            }
        )
    spec = {
        "channels": channels,
        "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}],
    }
    model = pyhf.Model(spec, poi_name="mu_trace")
    observations = []
    for channel in model.config.channels:
        observations.append(observations_by_channel[channel])
    data = observations + model.config.auxdata
    return model, data


def run_one(mode: str, scenario: str, include_support: bool) -> tuple[dict, list[dict]]:
    rows = load_rows(mode, scenario, include_support)
    rel_unc = float(rows["relative_shape_uncertainty_needed_for_controls"].iloc[0])
    model, data = build_model(rows, rel_unc)
    p = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
    fit = pyhf.infer.mle.fit(data, model)
    par = {name: float(fit[i]) for i, name in enumerate(model.config.par_order)}
    channel_rows = []
    for r in rows.itertuples(index=False):
        z = gaussian_z(float(r.q99_observed), float(r.q99_expected_sm_shape), rel_unc)
        channel_rows.append(
            {
                "sm_template_mode": mode,
                "scenario": scenario,
                "likelihood_variant": "MET_HTMHT_plus_controls" if include_support else "MET_plus_controls",
                "primary_dataset": r.primary_dataset,
                "jet_bin": r.jet_bin,
                "role": r.role,
                "observed": float(r.q99_observed),
                "expected_sm": float(r.q99_expected_sm_shape),
                "obs_exp": float(r.obs_exp),
                "gaussian_Z": z,
            }
        )
    trace_row = next(r for r in channel_rows if (r["primary_dataset"], r["jet_bin"]) == TRACE)
    control_z = [
        abs(r["gaussian_Z"])
        for r in channel_rows
        if (r["primary_dataset"], r["jet_bin"]) in CONTROLS
    ]
    controls_close = bool(max(control_z) <= 3.0 + CONTROL_CLOSE_TOL) if control_z else False
    summary = {
        "sm_template_mode": mode,
        "scenario": scenario,
        "likelihood_variant": "MET_HTMHT_plus_controls" if include_support else "MET_plus_controls",
        "relative_shape_uncertainty": rel_unc,
        "MET_0jet_observed": trace_row["observed"],
        "MET_0jet_expected": trace_row["expected_sm"],
        "MET_0jet_gaussian_Z": trace_row["gaussian_Z"],
        "max_control_abs_gaussian_Z": max(control_z) if control_z else np.nan,
        "controls_close": controls_close,
        "pyhf_background_only_p": p,
        "pyhf_background_only_Z": z_from_p(p),
        "fit_mu_trace": par.get("mu_trace", np.nan),
        "fit_correlated_sm_shape": par.get("correlated_sm_shape", np.nan),
        "passes_trace_screen": bool(trace_row["gaussian_Z"] > 5.0 and controls_close),
    }
    spec_name = f"pyhf_{mode}_{scenario}_{summary['likelihood_variant']}.json"
    (JSON / spec_name).write_text(json.dumps(model.spec, indent=2), encoding="utf-8")
    return summary, channel_rows


def main() -> None:
    ensure_dirs()
    summaries = []
    channels = []
    for mode in MODES:
        for scenario in SCENARIOS:
            for include_support in [False, True]:
                summary, rows = run_one(mode, scenario, include_support)
                summaries.append(summary)
                channels.extend(rows)
    summary_df = pd.DataFrame(summaries)
    channel_df = pd.DataFrame(channels)
    summary_df.to_csv(TABLES / "01_fresh_slice_pyhf_summary.csv", index=False)
    channel_df.to_csv(TABLES / "02_fresh_slice_pyhf_channels.csv", index=False)

    core = summary_df[
        summary_df["likelihood_variant"].eq("MET_plus_controls")
        & summary_df["sm_template_mode"].eq("all_weighted_sm_augmented")
    ].copy()

    report = f"""# Fresh-Slice pyhf Validation of the N-Frame Boundary Trace

## Purpose

This stage reruns the same augmented-SM pyhf likelihood separately on validation slices rather than only on the combined Run2016G plus Run2016H result. No score weights are refit and no new data are downloaded.

The tested claim remains narrow: N-Frame identifies an observable MET-region boundary trace in real CMS data. This is not a direct SUSY-particle discovery claim.

## Frozen Test

- Trace candidate: MET, 0-jet, Q99 frozen N-Frame boundary tail.
- Controls: JetHT 1-2 jets and SingleMuon 0-jet.
- Optional support channel: HTMHT 1-2 jets.
- SM model: W/Z+jets plus hard-QCD augmented weighted template.
- Likelihood: pyhf background-only discovery test with a correlated SM-shape nuisance and per-channel finite-template staterrors.

## Core Fresh-Slice Result

{core.to_markdown(index=False, floatfmt=".6g")}

## Full Summary

{summary_df.to_markdown(index=False, floatfmt=".6g")}

## Channel Readout

{channel_df.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The Run2016H-only slice is the most important fresh validation slice because it is independent of the earlier Run2016G development direction. A high MET 0-jet pyhf Z with controls closed means the boundary trace is not just a Run2016G-only effect.

The combined result should be interpreted only after checking the individual slices. A robust boundary-trace claim requires the fresh slice to preserve the MET excess while JetHT and SingleMuon remain controlled.
"""
    (REPORTS / "01_FRESH_SLICE_PYHF_TRACE_VALIDATION.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_FRESH_SLICE_PYHF_TRACE_VALIDATION.md")
    print(core.to_string(index=False))


if __name__ == "__main__":
    main()
