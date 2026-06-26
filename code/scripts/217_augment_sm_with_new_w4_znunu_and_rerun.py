from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import urllib3
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score


ROOT = Path(__file__).resolve().parents[1]
BASE_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy" / "sources" / "best_available_full_plus_reduced_weighted_sm_events.csv"
OUT = ROOT / "outputs_sm_robustness_extension"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
STAGE215 = ROOT / "scripts" / "215_harmonised_sm_shape_template_pyhf_fit.py"

NEW_SAMPLES = [
    {
        "sample_id": "smrobust_w4jets_69550_small",
        "record_id": 69550,
        "process_family_norm": "WJets",
        "process_label": "W4JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8",
        "path": ROOT.parent / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction" / "outputs" / "smrobust_w4jets_69550_small" / "event_features.csv",
    },
    {
        "sample_id": "smrobust_znunu_74909_small",
        "record_id": 74909,
        "process_family_norm": "ZNuNu",
        "process_label": "ZJetsToNuNu_Zpt-200toInf_BPSFilter_TuneCP5_13TeV-madgraphMLM-pythia8",
        "path": ROOT.parent / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction" / "outputs" / "smrobust_znunu_74909_small" / "event_features.csv",
    },
    {
        "sample_id": "smrobust_qcd_ht700to1000_63139_small",
        "record_id": 63139,
        "process_family_norm": "QCD",
        "process_label": "QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8",
        "path": ROOT.parent / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction" / "outputs" / "smrobust_qcd_ht700to1000_63139_small" / "event_features.csv",
    },
    {
        "sample_id": "smrobust_qcd_ht1000to1500_63078_small",
        "record_id": 63078,
        "process_family_norm": "QCD",
        "process_label": "QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8",
        "path": ROOT.parent / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction" / "outputs" / "smrobust_qcd_ht1000to1500_63078_small" / "event_features.csv",
    },
    {
        "sample_id": "smrobust_qcd_ht1500to2000_63094_small",
        "record_id": 63094,
        "process_family_norm": "QCD",
        "process_label": "QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8",
        "path": ROOT.parent / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction" / "outputs" / "smrobust_qcd_ht1500to2000_63094_small" / "event_features.csv",
    },
]

FEATURES = [
    "MET_pt",
    "MHT_pt",
    "MHT_over_HT",
    "MET_minus_MHT",
    "HT",
    "N_jets_30",
    "N_jets_50",
    "N_muons",
    "N_electrons",
    "N_leptons",
    "N_btags_medium",
    "N_primary_vertices",
    "packed_candidate_count",
    "secondary_vertex_count",
    "max_btag_discriminator",
]
AXES = ["missing_visible_axis", "displacement_reconstruction_axis", "qcd_like_axis"]
LUMI_PB = 16_380.0


def load_stage215():
    spec = importlib.util.spec_from_file_location("stage215", STAGE215)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {STAGE215}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def metadata_weight(record_id: int, extracted_events: int) -> tuple[float, dict]:
    urllib3.disable_warnings()
    rec = requests.get(f"https://opendata.cern.ch/api/records/{record_id}", timeout=60, verify=False)
    rec.raise_for_status()
    md = rec.json()["metadata"]
    xsec = md.get("cross_section", {}) or {}
    dist = md.get("distribution", {}) or {}
    xs = float(xsec.get("total_value", np.nan))
    generated = float(dist.get("number_events", np.nan))
    filt = float(xsec.get("filter_efficiency", 1.0) or 1.0)
    match = float(xsec.get("matching_efficiency", 1.0) or 1.0)
    weight = xs * LUMI_PB * filt * match / generated if generated > 0 and np.isfinite(xs) else 1.0
    return weight, {
        "record_id": record_id,
        "title": md.get("title", ""),
        "cross_section_pb": xs,
        "generated_events": generated,
        "filter_efficiency": filt,
        "matching_efficiency": match,
        "lumi_pb": LUMI_PB,
        "nominal_event_weight": weight,
        "extracted_events": extracted_events,
    }


def prepare_features(df: pd.DataFrame, medians: pd.Series | None = None) -> tuple[pd.DataFrame, pd.Series]:
    out = df.copy()
    for col in FEATURES:
        if col not in out:
            out[col] = 0.0
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_MHT_pt"] = np.log1p(out["MHT_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["met_ht_ratio"] = out["MET_pt"] / np.maximum(out["HT"], 1.0)
    use = FEATURES + ["log1p_MET_pt", "log1p_MHT_pt", "log1p_HT", "met_ht_ratio"]
    x = out[use].replace([np.inf, -np.inf], np.nan)
    if medians is None:
        medians = x.median(numeric_only=True).fillna(0.0)
    x = x.fillna(medians)
    return x, medians


def fit_axis_models(base: pd.DataFrame) -> tuple[dict, pd.Series, pd.DataFrame]:
    train = base.copy()
    x, med = prepare_features(train)
    rows = []
    models = {}
    weights = pd.to_numeric(train.get("event_weight", 1.0), errors="coerce").fillna(1.0).clip(lower=0.0)
    for axis in AXES:
        y = pd.to_numeric(train[axis], errors="coerce")
        mask = y.notna()
        # Keep training bounded and deterministic.
        idx = np.flatnonzero(mask.to_numpy())
        if len(idx) > 80_000:
            rng = np.random.default_rng(20260617)
            idx = rng.choice(idx, size=80_000, replace=False)
        split = int(0.8 * len(idx))
        tr_idx, te_idx = idx[:split], idx[split:]
        model = HistGradientBoostingRegressor(max_iter=220, learning_rate=0.06, max_leaf_nodes=31, random_state=20260617)
        model.fit(x.iloc[tr_idx], y.iloc[tr_idx], sample_weight=weights.iloc[tr_idx])
        pred = model.predict(x.iloc[te_idx])
        rows.append({"axis": axis, "train_rows": len(tr_idx), "test_rows": len(te_idx), "test_r2": r2_score(y.iloc[te_idx], pred)})
        models[axis] = model
    return models, med, pd.DataFrame(rows)


def load_new_rows(models: dict, medians: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    meta_rows = []
    for sample in NEW_SAMPLES:
        path = Path(sample["path"])
        if not path.exists():
            continue
        df = pd.read_csv(path, low_memory=False)
        weight, meta = metadata_weight(int(sample["record_id"]), len(df))
        meta_rows.append({**sample, **meta, "path": str(path)})
        x, _ = prepare_features(df, medians)
        out = df.copy()
        for axis, model in models.items():
            out[axis] = model.predict(x)
        out["process_family_norm"] = sample["process_family_norm"]
        out["process_label"] = sample["process_label"]
        out["component_mode"] = "full-component-smrobust-extension"
        out["event_weight"] = weight
        out["record_id"] = sample["record_id"]
        out["record_id_numeric"] = sample["record_id"]
        out["sample_id"] = sample["sample_id"]
        out["source_table"] = str(path)
        out["primary_dataset"] = "SM_extension"
        frames.append(out)
    if not frames:
        return pd.DataFrame(), pd.DataFrame(meta_rows)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(meta_rows)


def rerun_template(stage215, augmented: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Reuse stage215 machinery by writing an augmented temp and monkeypatching load_sm.
    real_cells = pd.concat([stage215.load_real_g_cells(), stage215.load_real_h_cells()], ignore_index=True)
    sm = augmented.copy()
    sm["event_weight"] = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(0.0)
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
        stage215.FROZEN_WEIGHTS[col] * sm[col].fillna(0.0).to_numpy(float) for col in stage215.FROZEN_WEIGHTS
    )
    sm["jet_bin"] = pd.cut(sm["N_jets_30"], bins=[-np.inf, 0, 2, 4, np.inf], labels=["0jet", "1to2jets", "3to4jets", "5plusjets"]).astype(str)
    templates = []
    for mode in ["all_weighted_sm_augmented", "full_component_only_augmented", "smrobust_extension_only"]:
        if mode == "all_weighted_sm_augmented":
            sub = sm
        elif mode == "full_component_only_augmented":
            sub = sm[sm["component_mode"].str.contains("full", case=False, na=False)]
        else:
            sub = sm[sm["component_mode"].eq("full-component-smrobust-extension")]
        tmp = sub.copy()
        tmp["event_weight"] = tmp["event_weight"].clip(lower=0.0)
        # Build directly with a small wrapper: stage215.build_sm_template expects stage215.load_sm output.
        original = stage215.sm_mode_mask
        stage215.sm_mode_mask = lambda _sm, _mode, _target=mode: pd.Series(True, index=_sm.index)
        t = stage215.build_sm_template(tmp, mode)
        stage215.sm_mode_mask = original
        templates.append(t)
    template = pd.concat(templates, ignore_index=True)
    pred = stage215.predict_from_template(real_cells, template)
    agg = stage215.aggregate_predictions(pred)
    scenarios, target = stage215.build_readouts(agg)
    return scenarios, target


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    stage215 = load_stage215()
    base = pd.read_csv(BASE_SM, low_memory=False)
    models, medians, model_quality = fit_axis_models(base)
    new_rows, meta = load_new_rows(models, medians)
    if new_rows.empty:
        raise SystemExit("No new extracted rows found.")
    augmented = pd.concat([base, new_rows], ignore_index=True, sort=False)
    scenarios, target = rerun_template(stage215, augmented)

    model_quality.to_csv(TABLES / "01_axis_model_quality.csv", index=False)
    meta.drop(columns=["path"], errors="ignore").to_csv(TABLES / "02_new_sm_extension_metadata.csv", index=False)
    new_rows.to_csv(SOURCES / "new_w4_znunu_smrobust_rows_with_predicted_axes.csv", index=False)
    scenarios.to_csv(TABLES / "03_augmented_sm_template_scenario_summary.csv", index=False)
    target.to_csv(TABLES / "04_augmented_sm_template_target_readout.csv", index=False)

    combined = scenarios[scenarios["scenario"].eq("Run2016G_plus_Run2016H")].copy()
    report = f"""# Augmented SM Template with New W4Jets and ZNuNu MiniAOD

## Purpose

This run adds newly extracted full-component MiniAOD samples to the SM template stress test:

- W4JetsToLNu, record 69550
- ZJetsToNuNu Zpt-200toInf, record 74909
- QCD HT700to1000, record 63139
- QCD HT1000to1500, record 63078
- QCD HT1500to2000, record 63094

The files were selected because they were HTTP-accessible and directly stress the W/Z+jets and hard-QCD SM tail hypotheses. The extracted rows were mapped onto the existing frozen-score axes using regressors trained on the current weighted SM table.

## Axis Model Quality

{model_quality.to_markdown(index=False, floatfmt=".3f")}

## New Sample Metadata

{meta.drop(columns=["path"], errors="ignore").to_markdown(index=False, floatfmt=".6g")}

## Combined Run2016G+Run2016H Result

{combined.to_markdown(index=False, floatfmt=".3f")}

## Full Scenario Summary

{scenarios.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

This is a robustness extension, not a replacement for an official CMS SM model. A pass after augmentation means the result survives adding more full-component WJets/ZNuNu shape support. A failure means the trace is sensitive to the newly added SM tail shape.
"""
    (REPORTS / "01_AUGMENTED_SM_TEMPLATE_W4_ZNUNU_REPORT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_AUGMENTED_SM_TEMPLATE_W4_ZNUNU_REPORT.md")
    print(combined.to_string(index=False))


if __name__ == "__main__":
    main()
