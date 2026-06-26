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
OUT = ROOT / "outputs_sideband_definition_stress_test_pyhf"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

TRACE = ("MET", "0jet")
BASELINE_CONTROLS = [("JetHT", "1to2jets"), ("SingleMuon", "0jet")]
ALL_CONTROLS = [(d, j) for d in ["JetHT", "SingleMuon"] for j in ["0jet", "1to2jets", "3to4jets", "5plusjets"]]
SCENARIOS = ["Run2016G_only", "Run2016H_only", "Run2016G_plus_Run2016H"]
MODES = ["all_weighted_sm_augmented", "full_component_only_augmented"]

SIDEBAND_DEFINITIONS = {
    "broad_q50_q99": ["q050_080", "q080_090", "q090_095", "q095_099"],
    "upper_q80_q99": ["q080_090", "q090_095", "q095_099"],
    "near_q90_q99": ["q090_095", "q095_099"],
    "adjacent_q95_q99": ["q095_099"],
    "lower_q50_q95": ["q050_080", "q080_090", "q090_095"],
}
CONTROL_DEFINITIONS = {
    "targeted_baseline": BASELINE_CONTROLS,
    "all_jetht_singlemuon_bins": ALL_CONTROLS,
}
TAIL = "q099_100"


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


def prepare_augmented_sm(stage215) -> pd.DataFrame:
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
    return sm


def build_templates(stage215, sm: pd.DataFrame) -> pd.DataFrame:
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
    return pd.concat(templates, ignore_index=True)


def predict_for_sideband(real_cells: pd.DataFrame, template: pd.DataFrame, sidebands: list[str]) -> pd.DataFrame:
    real_side = (
        real_cells[real_cells["score_band"].isin(sidebands)]
        .groupby(["validation_sample", "primary_dataset", "jet_bin", "missing_bin"], as_index=False)["observed"]
        .sum()
        .rename(columns={"observed": "real_sideband_observed"})
    )
    real_tail = (
        real_cells[real_cells["score_band"].eq(TAIL)]
        .groupby(["validation_sample", "primary_dataset", "jet_bin", "missing_bin"], as_index=False)["observed"]
        .sum()
        .rename(columns={"observed": "real_tail_observed"})
    )
    side = (
        template[template["score_band"].isin(sidebands)]
        .groupby(["sm_template_mode", "jet_bin", "missing_bin"], as_index=False)["sm_weight"]
        .sum()
        .rename(columns={"sm_weight": "sm_side_weight_selected"})
    )
    tail = (
        template[template["score_band"].eq(TAIL)]
        .groupby(["sm_template_mode", "jet_bin", "missing_bin"], as_index=False)["sm_weight"]
        .sum()
        .rename(columns={"sm_weight": "sm_tail_weight"})
    )
    ratio = side.merge(tail, on=["sm_template_mode", "jet_bin", "missing_bin"], how="outer").fillna(0.0)
    ratio["sm_tail_to_side_ratio"] = ratio["sm_tail_weight"] / ratio["sm_side_weight_selected"].replace(0, np.nan)
    pred = real_side.merge(real_tail, on=["validation_sample", "primary_dataset", "jet_bin", "missing_bin"], how="left")
    pred["real_tail_observed"] = pred["real_tail_observed"].fillna(0.0)
    pred = pred.merge(ratio, on=["jet_bin", "missing_bin"], how="left")
    pred["sm_shape_expected_tail"] = pred["real_sideband_observed"] * pred["sm_tail_to_side_ratio"]
    return pred


def aggregate(pred: pd.DataFrame) -> pd.DataFrame:
    out = pred.groupby(["sm_template_mode", "validation_sample", "primary_dataset", "jet_bin"], as_index=False).agg(
        q99_observed=("real_tail_observed", "sum"),
        q99_expected_sm_shape=("sm_shape_expected_tail", "sum"),
        real_sideband_observed=("real_sideband_observed", "sum"),
        sm_side_weight=("sm_side_weight_selected", "sum"),
        sm_tail_weight=("sm_tail_weight", "sum"),
    )
    out["obs_exp"] = out["q99_observed"] / out["q99_expected_sm_shape"].replace(0, np.nan)
    return out


def scenario_df(agg: pd.DataFrame, mode: str, scenario: str) -> pd.DataFrame:
    mode_df = agg[agg["sm_template_mode"].eq(mode)].copy()
    if scenario == "Run2016G_only":
        return mode_df[mode_df["validation_sample"].eq("Run2016G")].copy()
    if scenario == "Run2016H_only":
        return mode_df[mode_df["validation_sample"].eq("Run2016H")].copy()
    return mode_df.groupby(["sm_template_mode", "primary_dataset", "jet_bin"], as_index=False)[
        ["q99_observed", "q99_expected_sm_shape", "real_sideband_observed", "sm_side_weight", "sm_tail_weight"]
    ].sum()


def min_uncertainty(df: pd.DataFrame, controls: list[tuple[str, str]]) -> float:
    rows = []
    for dataset, jet_bin in controls:
        hit = df[(df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet_bin))]
        if not hit.empty and float(hit["q99_expected_sm_shape"].iloc[0]) > 0:
            rows.append(hit.iloc[0])
    if not rows:
        return np.nan
    lo, hi = 0.0, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        vals = [abs(z_value(float(r.q99_observed), float(r.q99_expected_sm_shape), mid)) for r in rows]
        if max(vals) <= 3.0:
            hi = mid
        else:
            lo = mid
    return float(hi)


def build_pyhf(df: pd.DataFrame, rel_unc: float, controls: list[tuple[str, str]]) -> tuple[pyhf.Model, list[float], list[dict]]:
    wanted = [TRACE] + controls
    channels = []
    observations = {}
    rows = []
    for dataset, jet_bin in wanted:
        hit = df[(df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet_bin))]
        if hit.empty:
            continue
        r = hit.iloc[0]
        channel = f"{dataset}_{jet_bin}"
        obs = float(r["q99_observed"])
        exp = max(float(r["q99_expected_sm_shape"]), 1e-9)
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
                            {"name": "correlated_sm_shape", "type": "normsys", "data": {"hi": 1 + rel_unc, "lo": max(1 - rel_unc, 1e-6)}},
                            {"name": f"mcstat_{dataset}_{jet_bin}", "type": "staterror", "data": [float(max(np.sqrt(exp), 1.0))]},
                        ],
                    },
                ],
            }
        )
        rows.append(
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
    model = pyhf.Model({"channels": channels, "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}]}, poi_name="mu_trace")
    data = [observations[name] for name in model.config.channels] + model.config.auxdata
    return model, data, rows


def main() -> None:
    ensure_dirs()
    stage215 = load_stage215()
    real_cells = pd.concat([stage215.load_real_g_cells(), stage215.load_real_h_cells()], ignore_index=True)
    template = build_templates(stage215, prepare_augmented_sm(stage215))

    summaries = []
    channels = []
    for sideband_name, sidebands in SIDEBAND_DEFINITIONS.items():
        agg = aggregate(predict_for_sideband(real_cells, template, sidebands))
        agg["sideband_definition"] = sideband_name
        agg.to_csv(TABLES / f"00_region_predictions_{sideband_name}.csv", index=False)
        for mode in MODES:
            for scenario in SCENARIOS:
                df = scenario_df(agg, mode, scenario)
                for control_name, controls in CONTROL_DEFINITIONS.items():
                    rel = min_uncertainty(df, controls)
                    if not np.isfinite(rel):
                        continue
                    model, data, rowset = build_pyhf(df, rel, controls)
                    p = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
                    fit = pyhf.infer.mle.fit(data, model)
                    par = {name: float(fit[i]) for i, name in enumerate(model.config.par_order)}
                    trace = next(r for r in rowset if r["role"] == "trace_candidate")
                    control_z = [abs(r["gaussian_Z"]) for r in rowset if r["role"] == "control"]
                    summary = {
                        "sideband_definition": sideband_name,
                        "sideband_bands": ",".join(sidebands),
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
                    for row in rowset:
                        channels.append({**summary, **row})
                    (JSON / f"pyhf_{sideband_name}_{mode}_{scenario}_{control_name}.json").write_text(json.dumps(model.spec, indent=2), encoding="utf-8")

    summary_df = pd.DataFrame(summaries)
    channel_df = pd.DataFrame(channels)
    summary_df.to_csv(TABLES / "01_sideband_definition_stress_summary.csv", index=False)
    channel_df.to_csv(TABLES / "02_sideband_definition_stress_channels.csv", index=False)

    core = summary_df[
        summary_df["sm_template_mode"].eq("all_weighted_sm_augmented")
        & summary_df["scenario"].eq("Run2016H_only")
        & summary_df["control_definition"].eq("targeted_baseline")
    ].sort_values("sideband_definition")
    broad_controls = summary_df[
        summary_df["sm_template_mode"].eq("all_weighted_sm_augmented")
        & summary_df["scenario"].eq("Run2016H_only")
        & summary_df["control_definition"].eq("all_jetht_singlemuon_bins")
    ].sort_values("sideband_definition")
    combined = summary_df[
        summary_df["sm_template_mode"].eq("all_weighted_sm_augmented")
        & summary_df["scenario"].eq("Run2016G_plus_Run2016H")
        & summary_df["control_definition"].eq("all_jetht_singlemuon_bins")
    ].sort_values("sideband_definition")

    report = f"""# Sideband-Definition Stress Test for the N-Frame Trace

## Purpose

This stage checks whether the MET 0-jet N-Frame boundary trace depends on the sideband window used to transfer the augmented SM shape into the Q99 tail. No N-Frame score weights are refit and no new data are downloaded.

## Sideband Definitions

{pd.DataFrame([{"sideband_definition": k, "bands": ", ".join(v)} for k, v in SIDEBAND_DEFINITIONS.items()]).to_markdown(index=False)}

## Core Run2016H Targeted-Control Result

{core.to_markdown(index=False, floatfmt=".6g")}

## Run2016H Broad-Control Result

{broad_controls.to_markdown(index=False, floatfmt=".6g")}

## Combined Run2016G plus Run2016H Broad-Control Result

{combined.to_markdown(index=False, floatfmt=".6g")}

## Full Summary

{summary_df.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The decisive check is the adjacent sideband `q095_099`, because it uses the closest observed region below the Q99 tail. If Run2016H-only remains above 5 sigma with controls closed under `adjacent_q95_q99`, the trace is not just a broad-sideband extrapolation artefact. If it fails there but passes broad sidebands, the current blocker is local tail-shape extrapolation.
"""
    (REPORTS / "01_SIDEBAND_DEFINITION_STRESS_TEST.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_SIDEBAND_DEFINITION_STRESS_TEST.md")
    print(core.to_string(index=False))


if __name__ == "__main__":
    main()
