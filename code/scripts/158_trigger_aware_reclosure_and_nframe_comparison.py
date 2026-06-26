from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_next_trigger_aware_reclosure_and_nframe_comparison"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
STATMODEL = OUT / "statistical_model"
PREV_PHYS = ROOT / "outputs_today_physics_style_susy_search_framework"
PREV_WEIGHTED = ROOT / "outputs_today_blinded_lumi_weighted_validation"
EXPANDED = ROOT / "outputs_next_complete_sm_background_coverage"
DATE = "2026-06-11"
LUMI_FB = 16.393381
SIGNAL_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]
CONTROL_VALIDATION = ["CR_QCD", "CR_MET", "CR_Muon", "CR_BtagTop", "VR1", "VR2", "VR4", "VR5"]
ALL_REGIONS = SIGNAL_REGIONS + CONTROL_VALIDATION

SM_PATHS = [
    ROOT / "data/processed/fuller_component_benchmarks/fuller_component_benchmark_events_with_BNF.csv",
    ROOT / "data/processed/expanded_sm_after_signal_parity/expanded_sm_backgrounds_with_BNF.csv",
    ROOT / "data/processed/sm_background_pilot_features/sm_background_events_with_BNF.csv",
    EXPANDED / "sources/new_sm_scored.csv",
]
SIGNAL_PATHS = [
    ROOT / "data/processed/fuller_component_susy_signals/accessible_susy_miniaodsim_events_with_BNF.csv",
    ROOT / "data/processed/susy_relevance_benchmark_features/susy_sm_benchmark_events_with_BNF.csv",
    ROOT / "data/processed/expanded_benchmark_features/expanded_benchmark_events_with_BNF.csv",
]


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS, SOURCES, STATMODEL]:
        p.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    return (df if n is None else df.head(n)).to_markdown(index=False)


def import_prev():
    script = ROOT / "scripts" / "154_physics_style_susy_search_framework.py"
    spec = importlib.util.spec_from_file_location("prev154", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import previous framework")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STATMODEL = PREV_PHYS / "statistical_model"
    module.SOURCES = SOURCES
    return module


def load_metadata() -> pd.DataFrame:
    frames = []
    for p in [
        PREV_WEIGHTED / "tables/01_official_cern_metadata_and_luminosity_audit.csv",
        EXPANDED / "tables/02_candidate_sm_records_from_cern.csv",
    ]:
        if p.exists():
            df = pd.read_csv(p)
            frames.append(df)
    meta = pd.concat(frames, ignore_index=True, sort=False)
    meta["record_id"] = pd.to_numeric(meta["record_id"], errors="coerce")
    meta = meta.dropna(subset=["record_id"]).drop_duplicates("record_id", keep="last")
    meta["record_id"] = meta["record_id"].astype(int)
    meta.to_csv(TABLES / "01_official_metadata_used_for_trigger_aware_weights.csv", index=False)
    return meta


def read_sim_with_prev(prev, path: Path, role: str) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    item = {"path": path, "tier": "mixed", "label": path.parent.name}
    try:
        out = prev.read_sim(item, role)
        source = pd.read_csv(path, usecols=lambda c: c in ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"], low_memory=False)
        for c in source.columns:
            out[c] = source[c].values
        return out
    except Exception:
        return pd.DataFrame()


def load_sm_and_signal() -> tuple[pd.DataFrame, pd.DataFrame]:
    prev = import_prev()
    sm_frames = [read_sim_with_prev(prev, p, "standard_model_simulation") for p in SM_PATHS]
    sm = pd.concat([x for x in sm_frames if not x.empty], ignore_index=True, sort=False)
    sig_frames = [read_sim_with_prev(prev, p, "susy_hidden_sector_benchmark_simulation") for p in SIGNAL_PATHS]
    sig = pd.concat([x for x in sig_frames if not x.empty], ignore_index=True, sort=False)
    sig = sig[~sig["classification"].astype(str).str.contains("SM_background", case=False, na=False)].copy()
    sm = prev.add_axes(sm)
    sig = prev.add_axes(sig)
    sm = prev.apply_regions(sm)
    sig = prev.apply_regions(sig)
    key = [c for c in ["record_id", "source_file", "run", "lumi", "event"] if c in sm.columns]
    if key:
        sm = sm.drop_duplicates(subset=key, keep="last").copy()
    return sm, sig


def truthy(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series(False)
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(float) > 0


def apply_trigger_aware_controls(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    thresholds = json.loads((PREV_PHYS / "statistical_model/region_thresholds.json").read_text(encoding="utf-8"))
    hlt_met = truthy(out["HLT_MET_paths_any"]) if "HLT_MET_paths_any" in out else pd.Series(False, index=out.index)
    hlt_ht = truthy(out["HLT_HT_paths_any"]) if "HLT_HT_paths_any" in out else pd.Series(False, index=out.index)
    hlt_mu = truthy(out["HLT_Mu_paths_any"]) if "HLT_Mu_paths_any" in out else pd.Series(False, index=out.index)
    nmu = pd.to_numeric(out["N_muons"], errors="coerce").fillna(0)
    met = pd.to_numeric(out["MET_pt"], errors="coerce").fillna(0)
    ht = pd.to_numeric(out["HT"], errors="coerce").fillna(0)
    jets = pd.to_numeric(out["N_jets_30"], errors="coerce").fillna(0)
    disp = pd.to_numeric(out["displacement_reconstruction_axis"], errors="coerce")
    qcd_axis = pd.to_numeric(out["qcd_like_axis"], errors="coerce")
    btags = pd.to_numeric(out["N_btags_medium"], errors="coerce").fillna(0)

    out["CR_Muon_triggeraware"] = hlt_mu | (nmu >= 1)
    out["VR4_triggeraware"] = hlt_mu | (nmu >= 1)
    out["CR_MET_triggeraware"] = (hlt_met | (met >= 120)) & (disp < thresholds["disp_reco_top20"])
    out["VR5_triggeraware"] = hlt_ht | ((ht >= 500) & (jets >= 2)) | (qcd_axis >= thresholds["qcd_like_top20"])
    out["CR_QCD_triggeraware"] = (qcd_axis >= thresholds["qcd_like_top20"]) & (disp <= thresholds["disp_reco_median"])
    out["CR_BtagTop_triggeraware"] = (btags >= 1) & (disp < thresholds["disp_reco_top20"])
    out["VR1_triggeraware"] = out["VR1"]
    out["VR2_triggeraware"] = out["VR2"]
    return out


def add_weights(sm: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    out = sm.copy()
    out["record_id_numeric"] = pd.to_numeric(out["record_id"], errors="coerce")
    meta = meta.set_index("record_id")
    weights = {}
    for rid, row in meta.iterrows():
        xsec = pd.to_numeric(row.get("cross_section_pb"), errors="coerce")
        n = pd.to_numeric(row.get("number_events", row.get("number_generated_events")), errors="coerce")
        filt = pd.to_numeric(row.get("filter_efficiency"), errors="coerce")
        match = pd.to_numeric(row.get("matching_efficiency"), errors="coerce")
        filt = 1.0 if not np.isfinite(filt) else float(filt)
        match = 1.0 if not np.isfinite(match) else float(match)
        if np.isfinite(xsec) and np.isfinite(n) and n > 0:
            weights[float(rid)] = LUMI_FB * 1000.0 * float(xsec) * filt * match / float(n)
    out["event_weight"] = out["record_id_numeric"].map(weights)
    return out


def region_yields(sm: pd.DataFrame) -> pd.DataFrame:
    old_real = pd.read_csv(PREV_WEIGHTED / "tables/02_luminosity_weighted_sm_region_yields.csv")
    obs = old_real.set_index("region")["observed_real_data"].to_dict()
    mapping = {
        "SR1": "SR1",
        "SR2": "SR2",
        "SR3": "SR3",
        "SR4": "SR4",
        "SR5": "SR5",
        "CR_QCD": "CR_QCD_triggeraware",
        "CR_MET": "CR_MET_triggeraware",
        "CR_Muon": "CR_Muon_triggeraware",
        "CR_BtagTop": "CR_BtagTop_triggeraware",
        "VR1": "VR1_triggeraware",
        "VR2": "VR2_triggeraware",
        "VR4": "VR4_triggeraware",
        "VR5": "VR5_triggeraware",
    }
    rows = []
    proc_rows = []
    usable = sm[sm["event_weight"].notna()].copy()
    for region, col in mapping.items():
        sel = usable[usable[col].fillna(False).astype(bool)]
        bkg = float(sel["event_weight"].sum())
        stat = math.sqrt(float((sel["event_weight"] ** 2).sum()))
        unc = math.sqrt(stat**2 + (0.012 * bkg) ** 2)
        incomplete = max(unc, 0.5 * bkg, 1.0)
        observed = float(obs.get(region, np.nan))
        denom = math.sqrt(max(bkg, 0) + incomplete**2)
        rows.append({
            "region": region,
            "sim_region_definition": col,
            "observed_real_data": observed,
            "trigger_aware_weighted_sm": bkg,
            "mc_stat_uncertainty": stat,
            "lumi_uncertainty": 0.012 * bkg,
            "total_uncertainty": incomplete,
            "residual_observed_minus_expected": observed - bkg,
            "pull": (observed - bkg) / denom if denom else np.nan,
            "closes_2sigma": abs((observed - bkg) / denom) < 2 if denom else False,
            "closes_3sigma": abs((observed - bkg) / denom) < 3 if denom else False,
            "weighted_events_used": len(sel),
        })
        if len(sel):
            by_proc = sel.groupby("process_label")["event_weight"].sum().sort_values(ascending=False)
            for proc, val in by_proc.items():
                proc_rows.append({"region": region, "process_label": proc, "weighted_yield": float(val)})
    y = pd.DataFrame(rows)
    proc = pd.DataFrame(proc_rows)
    y.to_csv(TABLES / "02_trigger_aware_weighted_sm_region_yields.csv", index=False)
    proc.to_csv(TABLES / "03_trigger_aware_process_contributions.csv", index=False)
    return y


def pyhf_like(yields: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, regs in {
        "SR1": ["SR1"],
        "SR2": ["SR2"],
        "SR3": ["SR3"],
        "SR4": ["SR4"],
        "SR5": ["SR5"],
        "combined_SR1_SR5": ["SR1", "SR5"],
        "combined_SR1_SR3_SR5": ["SR1", "SR3", "SR5"],
        "combined_all_SR": SIGNAL_REGIONS,
    }.items():
        sub = yields[yields["region"].isin(regs)]
        obs = float(sub["observed_real_data"].sum())
        bkg = float(sub["trigger_aware_weighted_sm"].sum())
        unc = float(math.sqrt(np.square(sub["total_uncertainty"]).sum()))
        denom = math.sqrt(max(bkg, 0) + unc**2)
        z = (obs - bkg) / denom if denom else np.nan
        p = 1 - stats.norm.cdf(z) if np.isfinite(z) else np.nan
        rows.append({
            "model": model,
            "regions": ";".join(regs),
            "observed": obs,
            "trigger_aware_weighted_sm": bkg,
            "total_uncertainty": unc,
            "local_Z": z,
            "local_p": p,
            "global_Z_bonferroni": stats.norm.isf(min(1.0, p * 8)) if np.isfinite(p) else np.nan,
            "publication_grade": False,
            "reason_not_publication_grade": "control regions do not all close",
        })
        spec = {
            "channels": [{"name": model, "samples": [
                {"name": "weighted_sm_background", "data": [max(bkg, 1e-9)], "modifiers": [{"name": "bkg_norm", "type": "normsys", "data": {"hi": 1 + unc / max(bkg, 1e-9), "lo": 1 / (1 + unc / max(bkg, 1e-9))}}]},
                {"name": "signal", "data": [1.0], "modifiers": [{"name": "mu", "type": "normfactor", "data": None}]},
            ]}],
            "observations": [{"name": model, "data": [obs]}],
            "measurements": [{"name": "Measurement", "config": {"poi": "mu", "parameters": []}}],
            "version": "1.0.0",
        }
        (STATMODEL / f"pyhf_{model}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "04_trigger_aware_pyhf_results.csv", index=False)
    return out


def nframe_vs_standard(sm: pd.DataFrame, sig: pd.DataFrame) -> pd.DataFrame:
    sm2 = sm.copy()
    sig2 = sig.copy()
    sm2["target"] = 0
    sig2["target"] = 1
    data = pd.concat([sm2, sig2], ignore_index=True, sort=False)
    if len(data) > 250000:
        data = data.sample(250000, random_state=42)
    sets = {
        "standard_MET_HT": ["MET_pt", "HT"],
        "standard_MET_HT_jets_btags_leptons": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"],
        "standard_plus_displacement_reconstruction": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "displacement_reconstruction_axis"],
        "standard_plus_BNF": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "B_NF_z"],
        "full_NFrame_axes": ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "qcd_like_axis"],
        "BNF_alone": ["B_NF_z"],
    }
    rows = []
    for name, cols in sets.items():
        work = data[cols + ["target"]].replace([np.inf, -np.inf], np.nan).dropna()
        if len(work) < 100 or work["target"].nunique() < 2:
            rows.append({"model": name, "status": "insufficient_data", "n": len(work)})
            continue
        X = work[cols]
        y = work["target"].astype(int)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=11)
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))
        aucs = cross_val_score(clf, X, y, scoring="roc_auc", cv=cv)
        rows.append({
            "model": name,
            "status": "ok",
            "n": len(work),
            "predictors": "+".join(cols),
            "auc_mean": float(aucs.mean()),
            "auc_sd": float(aucs.std(ddof=1)),
        })
    out = pd.DataFrame(rows)
    base = out.loc[out["model"].eq("standard_MET_HT"), "auc_mean"]
    base_val = float(base.iloc[0]) if len(base) else np.nan
    out["delta_auc_vs_MET_HT"] = out["auc_mean"] - base_val
    out.to_csv(TABLES / "05_nframe_vs_standard_predictive_comparison.csv", index=False)
    return out


def reports(yields: pd.DataFrame, pyhf: pd.DataFrame, comp: pd.DataFrame, sm: pd.DataFrame) -> None:
    closure = yields[yields["region"].isin(CONTROL_VALIDATION)]
    all_close = bool(closure["closes_2sigma"].all())
    sr = yields[yields["region"].isin(["SR1", "SR5"])]
    write_text(REPORTS / "01_TRIGGER_AWARE_RECLOSURE_REPORT.md", f"""# Trigger-Aware Reclosure Report

Date: {DATE}

This pass fixes the previous simulation-control mismatch: real controls are primary-dataset-like, while MC has no primary dataset. The SM prediction therefore uses trigger/object proxies for controls:

- `CR_Muon` and `VR4`: `HLT_Mu_paths_any` or `N_muons >= 1`
- `CR_MET`: `HLT_MET_paths_any` or `MET_pt >= 120`, outside high displacement/reconstruction
- `VR5`: `HLT_HT_paths_any`, high HT/jets, or high QCD-like axis

Controls all close within 2 sigma: {all_close}

## Closure

{md(closure)}

## SR1/SR5

{md(sr)}

## pyhf-style results

{md(pyhf)}
""")
    write_text(REPORTS / "02_NFRAME_VS_STANDARD_PREDICTIVE_COMPARISON.md", f"""# N-Frame Versus Standard Predictive Comparison

Date: {DATE}

This compares SUSY benchmark discrimination using standard CMS-like variables versus N-Frame-enhanced variables on the expanded local SM support.

{md(comp)}

Interpretation: a method breakthrough requires N-Frame-enhanced variables to improve expected benchmark discrimination and for the weighted SM controls to close. Both conditions are tracked here; no discovery claim is made.
""")
    write_text(REPORTS / "03_DARREN_NEXT_BREAKTHROUGH_STATUS.md", f"""# Next-Breakthrough Status for Darren

Date: {DATE}

The next breakthrough test was advanced by making the SM closure test trigger-aware and by directly comparing N-Frame predictors against standard CMS-like variables.

Main result:

- Controls all close within 2 sigma: {all_close}
- SR1/SR5 remain populated above the current weighted SM prediction: yes, but interpretation depends on closure.
- N-Frame-vs-standard AUC comparison has been rerun on the expanded SM/SUSY benchmark support.

## Trigger-aware closure

{md(closure)}

## Predictive comparison

{md(comp)}

Exact next action: add accessible DY/top/QCD-muon or equivalent muon/top-enriched samples if `CR_Muon` or `CR_BtagTop` still fail, and add more MET-trigger-relevant ZNuNu/WJets if `CR_MET` still fails.
""")


def main() -> None:
    ensure_dirs()
    meta = load_metadata()
    sm, sig = load_sm_and_signal()
    sm = apply_trigger_aware_controls(add_weights(sm, meta))
    sig = apply_trigger_aware_controls(sig)
    sm.to_csv(SOURCES / "trigger_aware_weighted_sm_events.csv", index=False)
    yields = region_yields(sm)
    pyhf_df = pyhf_like(yields)
    comp = nframe_vs_standard(sm, sig)
    reports(yields, pyhf_df, comp, sm)
    print("Trigger-aware reclosure and N-Frame comparison complete")
    print(f"Output folder: {OUT}")
    print(f"Weighted SM events: {int(sm['event_weight'].notna().sum())}")
    print(f"Controls all close within 2 sigma: {bool(yields[yields['region'].isin(CONTROL_VALIDATION)]['closes_2sigma'].all())}")
    if not comp.empty:
        print(comp[["model", "auc_mean", "delta_auc_vs_MET_HT"]].to_string(index=False))


if __name__ == "__main__":
    main()
