from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
BASE_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy" / "sources" / "best_available_full_plus_reduced_weighted_sm_events.csv"
NEW_SM = ROOT / "outputs_sm_robustness_extension" / "sources" / "new_w4_znunu_smrobust_rows_with_predicted_axes.csv"
STAGE215 = ROOT / "scripts" / "215_harmonised_sm_shape_template_pyhf_fit.py"
OUT = ROOT / "outputs_control_definition_stress_test_pyhf"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

TRACE = ("MET", "0jet")
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
SCENARIOS = ["Run2016G_only", "Run2016H_only", "Run2016G_plus_Run2016H"]
MODES = ["all_weighted_sm_augmented", "full_component_only_augmented"]

CONTROL_DEFINITIONS = {
    "targeted_baseline": [("JetHT", "1to2jets"), ("SingleMuon", "0jet")],
    "all_jetht_singlemuon_bins": [(d, j) for d in ["JetHT", "SingleMuon"] for j in JET_BINS],
    "same_stage_0jet_controls": [("JetHT", "0jet"), ("SingleMuon", "0jet")],
    "adjacent_0jet_1to2jet_controls": [(d, j) for d in ["JetHT", "SingleMuon"] for j in ["0jet", "1to2jets"]],
    "jetht_all_bins_only": [("JetHT", j) for j in JET_BINS],
    "singlemuon_all_bins_only": [("SingleMuon", j) for j in JET_BINS],
}


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, JSON]:
        path.mkdir(parents=True, exist_ok=True)


def load_stage215():
    spec = importlib.util.spec_from_file_location("stage215", STAGE215)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {STAGE215}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def z_value(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def z_from_p(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def min_uncertainty_for_controls(df: pd.DataFrame, controls: list[tuple[str, str]]) -> float:
    rows = []
    for dataset, jet_bin in controls:
        hit = df[(df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet_bin))]
        if not hit.empty:
            rows.append(hit.iloc[0])
    if not rows:
        return np.nan
    lo, hi = 0.0, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        vals = [
            abs(z_value(float(r.q99_observed), float(r.q99_expected_sm_shape), mid))
            for r in rows
            if float(r.q99_expected_sm_shape) > 0
        ]
        if vals and max(vals) <= 3.0:
            hi = mid
        else:
            lo = mid
    return float(hi)


def build_augmented_region_predictions(stage215) -> pd.DataFrame:
    real_cells = pd.concat([stage215.load_real_g_cells(), stage215.load_real_h_cells()], ignore_index=True)
    base = pd.read_csv(BASE_SM, low_memory=False)
    new = pd.read_csv(NEW_SM, low_memory=False)
    sm = pd.concat([base, new], ignore_index=True, sort=False)
    sm["event_weight"] = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(0.0).clip(lower=0.0)
    sm["process_family_base"] = sm["process_family_norm"].astype(str).str.replace("_reduced", "", regex=False)
    sm["component_mode"] = sm.get("component_mode", "").astype(str)
    for col in ["N_muons", "N_electrons", "N_jets_30"]:
        if col not in sm:
            sm[col] = 0.0
        sm[col] = pd.to_numeric(sm[col], errors="coerce").fillna(0.0)
    leptons = sm["N_muons"] + sm["N_electrons"]
    weights = sm["event_weight"].to_numpy(float)
    mean = np.average(leptons, weights=weights) if weights.sum() > 0 else 0.0
    sd = np.sqrt(np.average((leptons - mean) ** 2, weights=weights)) if weights.sum() > 0 else 1.0
    sm["leptonic_control_axis"] = -(leptons - mean) / max(float(sd), 1e-9)
    sm["sm_frozen_proxy_score"] = sum(
        stage215.FROZEN_WEIGHTS[col] * pd.to_numeric(sm[col], errors="coerce").fillna(0.0).to_numpy(float)
        for col in stage215.FROZEN_WEIGHTS
    )
    sm["jet_bin"] = pd.cut(
        sm["N_jets_30"],
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)

    templates = []
    original = stage215.sm_mode_mask
    for mode in MODES:
        if mode == "all_weighted_sm_augmented":
            sub = sm
        else:
            sub = sm[sm["component_mode"].str.contains("full", case=False, na=False)]
        stage215.sm_mode_mask = lambda _sm, _mode: pd.Series(True, index=_sm.index)
        templates.append(stage215.build_sm_template(sub, mode))
    stage215.sm_mode_mask = original
    template = pd.concat(templates, ignore_index=True)
    pred = stage215.predict_from_template(real_cells, template)
    return stage215.aggregate_predictions(pred)


def scenario_df(agg: pd.DataFrame, mode: str, scenario: str) -> pd.DataFrame:
    mode_df = agg[agg["sm_template_mode"].eq(mode)].copy()
    if scenario == "Run2016G_only":
        return mode_df[mode_df["validation_sample"].eq("Run2016G")].copy()
    if scenario == "Run2016H_only":
        return mode_df[mode_df["validation_sample"].eq("Run2016H")].copy()
    if scenario == "Run2016G_plus_Run2016H":
        return mode_df.groupby(["sm_template_mode", "primary_dataset", "jet_bin"], as_index=False)[
            ["q99_observed", "q99_expected_sm_shape", "real_sideband_observed", "sm_side_weight", "sm_tail_weight"]
        ].sum()
    raise ValueError(scenario)


def build_pyhf(df: pd.DataFrame, rel_unc: float, controls: list[tuple[str, str]]) -> tuple[pyhf.Model, list[float], list[dict]]:
    wanted = [TRACE] + controls
    channels = []
    observations = {}
    channel_rows = []
    for dataset, jet_bin in wanted:
        hit = df[(df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet_bin))]
        if hit.empty:
            continue
        row = hit.iloc[0]
        channel = f"{dataset}_{jet_bin}"
        obs = float(row["q99_observed"])
        exp = max(float(row["q99_expected_sm_shape"]), 1e-9)
        is_trace = (dataset, jet_bin) == TRACE
        observations[channel] = obs
        channels.append(
            {
                "name": channel,
                "samples": [
                    {
                        "name": "nframe_trace_excess",
                        "data": [exp if is_trace else 0.0],
                        "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}],
                    },
                    {
                        "name": "sm_background",
                        "data": [exp],
                        "modifiers": [
                            {
                                "name": "correlated_sm_shape",
                                "type": "normsys",
                                "data": {"hi": 1.0 + rel_unc, "lo": max(1.0 - rel_unc, 1e-6)},
                            },
                            {
                                "name": f"mcstat_{dataset}_{jet_bin}",
                                "type": "staterror",
                                "data": [float(max(np.sqrt(exp), 1.0))],
                            },
                        ],
                    },
                ],
            }
        )
        channel_rows.append(
            {
                "primary_dataset": dataset,
                "jet_bin": jet_bin,
                "role": "trace_candidate" if is_trace else "control",
                "observed": obs,
                "expected_sm": exp,
                "obs_exp": obs / exp if exp > 0 else np.nan,
                "gaussian_Z": z_value(obs, exp, rel_unc),
            }
        )
    spec = {
        "channels": channels,
        "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}],
    }
    model = pyhf.Model(spec, poi_name="mu_trace")
    data = [observations[name] for name in model.config.channels] + model.config.auxdata
    return model, data, channel_rows


def main() -> None:
    ensure_dirs()
    stage215 = load_stage215()
    agg = build_augmented_region_predictions(stage215)
    agg.to_csv(TABLES / "00_augmented_region_predictions_all_jet_bins.csv", index=False)

    summaries = []
    channels = []
    for mode in MODES:
        for scenario in SCENARIOS:
            df = scenario_df(agg, mode, scenario)
            for control_name, controls in CONTROL_DEFINITIONS.items():
                rel = min_uncertainty_for_controls(df, controls)
                if not np.isfinite(rel):
                    continue
                model, data, channel_rows = build_pyhf(df, rel, controls)
                p = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
                fit = pyhf.infer.mle.fit(data, model)
                par = {name: float(fit[i]) for i, name in enumerate(model.config.par_order)}
                trace = next(r for r in channel_rows if r["role"] == "trace_candidate")
                control_z = [abs(r["gaussian_Z"]) for r in channel_rows if r["role"] == "control"]
                summary = {
                    "sm_template_mode": mode,
                    "scenario": scenario,
                    "control_definition": control_name,
                    "n_control_channels": len(control_z),
                    "relative_shape_uncertainty_needed_for_controls": rel,
                    "MET_0jet_observed": trace["observed"],
                    "MET_0jet_expected": trace["expected_sm"],
                    "MET_0jet_gaussian_Z": trace["gaussian_Z"],
                    "max_control_absZ": max(control_z) if control_z else np.nan,
                    "controls_close": bool(control_z and max(control_z) <= 3.0 + 1e-9),
                    "pyhf_background_only_p": p,
                    "pyhf_background_only_Z": z_from_p(p),
                    "fit_mu_trace": par.get("mu_trace", np.nan),
                    "fit_correlated_sm_shape": par.get("correlated_sm_shape", np.nan),
                    "passes_robust_trace_screen": bool(trace["gaussian_Z"] > 5.0 and control_z and max(control_z) <= 3.0 + 1e-9),
                }
                summaries.append(summary)
                for row in channel_rows:
                    channels.append({**summary, **row})
                (JSON / f"pyhf_{mode}_{scenario}_{control_name}.json").write_text(json.dumps(model.spec, indent=2), encoding="utf-8")

    summary_df = pd.DataFrame(summaries)
    channel_df = pd.DataFrame(channels)
    summary_df.to_csv(TABLES / "01_control_definition_stress_summary.csv", index=False)
    channel_df.to_csv(TABLES / "02_control_definition_stress_channels.csv", index=False)

    core = summary_df[
        summary_df["sm_template_mode"].eq("all_weighted_sm_augmented")
        & summary_df["scenario"].eq("Run2016H_only")
    ].sort_values("relative_shape_uncertainty_needed_for_controls")
    combined = summary_df[
        summary_df["sm_template_mode"].eq("all_weighted_sm_augmented")
        & summary_df["scenario"].eq("Run2016G_plus_Run2016H")
    ].sort_values("relative_shape_uncertainty_needed_for_controls")

    report = f"""# Control-Definition Stress Test for the pyhf N-Frame Trace

## Purpose

This stage checks whether the fresh Run2016H MET 0-jet N-Frame boundary trace survives reasonable changes to the control definition. No score weights are refit and no new data are downloaded.

## Control Definitions Tested

{pd.DataFrame([{"control_definition": k, "channels": ", ".join([f"{d}:{j}" for d, j in v])} for k, v in CONTROL_DEFINITIONS.items()]).to_markdown(index=False)}

## Core Run2016H Result

{core.to_markdown(index=False, floatfmt=".6g")}

## Combined Run2016G plus Run2016H Result

{combined.to_markdown(index=False, floatfmt=".6g")}

## Full Summary

{summary_df.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The key question is whether `Run2016H_only` keeps MET 0-jet above 5 sigma while controls close under broader control definitions. If it does, the trace is less likely to be an artefact of one chosen control pair. If it fails only under very broad all-bin controls, the next technical issue is not the MET trace itself, but mismodelling in one or more control jet bins.
"""
    (REPORTS / "01_CONTROL_DEFINITION_STRESS_TEST.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_CONTROL_DEFINITION_STRESS_TEST.md")
    print(core.to_string(index=False))


if __name__ == "__main__":
    main()
