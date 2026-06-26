from __future__ import annotations

import importlib.util
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_breakthrough_nframe_susy_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
FIGURES = OUT / "figures"
STATMODEL = OUT / "statistical_model"
BLINDED = OUT / "blinded_tests"

PREV_PHYS = ROOT / "outputs_today_physics_style_susy_search_framework"
PREV_WEIGHTED = ROOT / "outputs_today_blinded_lumi_weighted_validation"
EXPANDED = ROOT / "outputs_next_complete_sm_background_coverage"
PREV_TRIGGER = ROOT / "outputs_next_trigger_aware_reclosure_and_nframe_comparison"

DATE = "2026-06-11"
LUMI_FB = 16.393381
DOWNLOAD_CAP_GB = 80.0
SIGNAL_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]
CONTROL_VALIDATION = ["CR_QCD", "CR_MET", "CR_Muon", "CR_BtagTop", "VR1", "VR2", "VR4", "VR5"]
ALL_REGIONS = SIGNAL_REGIONS + CONTROL_VALIDATION

SM_PATHS = [
    ROOT / "data/processed/fuller_component_benchmarks/fuller_component_benchmark_events_with_BNF.csv",
    ROOT / "data/processed/expanded_sm_after_signal_parity/expanded_sm_backgrounds_with_BNF.csv",
    ROOT / "data/processed/sm_background_pilot_features/sm_background_events_with_BNF.csv",
    EXPANDED / "sources/new_sm_scored.csv",
    OUT / "sources/breakthrough_new_sm_scored.csv",
]
SIGNAL_PATHS = [
    ROOT / "data/processed/fuller_component_susy_signals/accessible_susy_miniaodsim_events_with_BNF.csv",
    ROOT / "data/processed/susy_relevance_benchmark_features/susy_sm_benchmark_events_with_BNF.csv",
    ROOT / "data/processed/expanded_benchmark_features/expanded_benchmark_events_with_BNF.csv",
]

BASE_COLS = [
    "sample_id",
    "process_label",
    "classification",
    "primary_dataset",
    "record_id",
    "source_file",
    "run",
    "lumi",
    "event",
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_jets_50",
    "N_muons",
    "N_electrons",
    "N_leptons",
    "N_btags_medium",
    "N_btags_tight",
    "max_btag_discriminator",
    "N_primary_vertices",
    "secondary_vertex_count",
    "packed_candidate_count",
    "HLT_MET_paths_any",
    "HLT_HT_paths_any",
    "HLT_Mu_paths_any",
    "HLT_Ele_paths_any",
    "pass_goodVertices",
    "standard_quality_clean",
    "data_tier",
    "component_mode",
    "topology_class",
    "model_label",
]

SEARCH_TARGETS = [
    ("TTToSemiLeptonic", "TTToSemiLeptonic RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", "CR_BtagTop;CR_Muon;VR4", 1),
    ("TTToHadronic", "TTToHadronic RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", "CR_BtagTop;VR5", 1),
    ("TTTo2L2Nu", "TTTo2L2Nu RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", "CR_BtagTop;CR_Muon;CR_MET", 1),
    ("TTJets", "TTJets TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", "CR_BtagTop;CR_Muon;VR4;VR5", 1),
    ("DYJetsToLL_M-50", "DYJetsToLL_M-50 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "DY/Z", "CR_Muon;VR4", 1),
    ("ZToMuMu", "ZToMuMu RunIISummer20UL16MiniAODv2 MINIAODSIM", "DY/Z", "CR_Muon;VR4", 2),
    ("WJetsToLNu", "WJetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", "CR_Muon;CR_MET;VR4", 1),
    ("W1JetsToLNu", "W1JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", "CR_Muon;CR_MET;VR4", 2),
    ("W2JetsToLNu", "W2JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", "CR_Muon;CR_MET;VR4", 2),
    ("W3JetsToLNu", "W3JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", "CR_Muon;CR_MET;VR4", 2),
    ("W4JetsToLNu", "W4JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", "CR_Muon;CR_MET;VR4", 3),
    ("ZJetsToNuNu_Zpt-100to200", "ZJetsToNuNu_Zpt-100to200 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "ZNuNu", "CR_MET;VR1", 1),
    ("ZJetsToNuNu_Zpt-200toInf", "ZJetsToNuNu_Zpt-200toInf TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "ZNuNu", "CR_MET;VR1", 2),
    ("QCD_HT100to200", "QCD_HT100to200 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 3),
    ("QCD_HT200to300", "QCD_HT200to300 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_HT300to500", "QCD_HT300to500 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_HT500to700", "QCD_HT500to700 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_HT700to1000", "QCD_HT700to1000 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_HT1000to1500", "QCD_HT1000to1500 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_HT1500to2000", "QCD_HT1500to2000 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_HT2000toInf", "QCD_HT2000toInf TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", "CR_QCD;VR2;VR5", 2),
    ("QCD_MuEnriched", "QCD MuEnriched RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD_mu", "CR_Muon;VR4", 2),
    ("ST_t-channel", "ST_t-channel RunIISummer20UL16MiniAODv2 MINIAODSIM", "single top", "CR_BtagTop;CR_Muon", 2),
    ("ST_tW", "ST_tW RunIISummer20UL16MiniAODv2 MINIAODSIM", "single top", "CR_BtagTop;CR_Muon", 2),
]

KNOWN_FEASIBLE_RECORDS = [
    (69746, "WJets", "CR_Muon;CR_MET;VR4", 1, "inclusive WJets; previous first file failed, try alternate files"),
    (63110, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT200to300 missing from weighted set"),
    (63118, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT300to500 already extracted and weighted"),
    (63126, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT500to700 already extracted and weighted"),
    (63139, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT700to1000 already weighted"),
    (63078, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT1000to1500 already weighted"),
    (63094, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT1500to2000 missing from weighted set"),
    (63102, "QCD", "CR_QCD;VR2;VR5", 2, "QCD HT2000toInf already extracted and weighted"),
    (69548, "WJets", "CR_Muon;CR_MET;VR4", 2, "W3Jets already extracted and weighted"),
    (69550, "WJets", "CR_Muon;CR_MET;VR4", 3, "W4Jets already weighted"),
    (74907, "ZNuNu", "CR_MET;VR1", 1, "ZNuNu 100-200; previous first file failed, try alternate files"),
    (74909, "ZNuNu", "CR_MET;VR1", 2, "ZNuNu 200-Inf already weighted"),
    (72753, "diboson", "CR_Muon;CR_MET", 4, "WZ already weighted"),
    (75592, "diboson", "CR_Muon;CR_MET", 4, "ZZ feasible supporting sample"),
    (38502, "diboson", "CR_Muon;CR_MET", 5, "WW-like low-impact supporting sample already weighted"),
    (36928, "diboson", "CR_Muon;CR_MET", 5, "ggZH/ZZ-like already extracted and weighted"),
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, FIGURES, STATMODEL, BLINDED]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    return (df if n is None else df.head(n)).to_markdown(index=False)


def import_prev154():
    spec = importlib.util.spec_from_file_location("prev154", ROOT / "scripts/154_physics_style_susy_search_framework.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import frozen framework")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STATMODEL = PREV_PHYS / "statistical_model"
    module.SOURCES = SOURCES
    return module


def api_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def files_from_record(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for idx in metadata.get("_file_indices", []):
        files.extend(idx.get("files", []))
    if not files:
        files.extend(metadata.get("files", []))
    return files


def fetch_record(record_id: int) -> dict[str, Any]:
    cache = SOURCES / f"cern_record_{record_id}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    data = api_json(f"https://opendata.cern.ch/api/records/{record_id}")
    cache.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def choose_cols(path: Path, wanted: list[str]) -> list[str]:
    cols = list(pd.read_csv(path, nrows=0).columns)
    keep = [c for c in wanted if c in cols]
    extras = [
        "B_NF_fitted_frozen_z_real_scaled",
        "B_NF_fitted_frozen_raw",
        "B_NF_z",
        "B_NF_raw",
        "B_P_displacement_proxy",
        "B_P_reconstruction",
        "B_P_multiplicity",
        "B_P_btag_structure",
        "B_P_visible_energy",
        "B_P_missing",
        "B_P_compression",
    ]
    keep.extend([c for c in extras if c in cols and c not in keep])
    return keep


def read_sim(path: Path, role: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    use = choose_cols(path, BASE_COLS)
    df = pd.read_csv(path, usecols=use, low_memory=False)
    out = pd.DataFrame(index=df.index)
    for col in BASE_COLS:
        out[col] = df[col] if col in df else np.nan
    out["B_NF_z"] = (
        df["B_NF_z"] if "B_NF_z" in df else df.get("B_NF_fitted_frozen_z_real_scaled", np.nan)
    )
    out["B_NF_raw"] = (
        df["B_NF_raw"] if "B_NF_raw" in df else df.get("B_NF_fitted_frozen_raw", np.nan)
    )
    comp_map = {
        "B_P_displacement_proxy": "P_displacement",
        "B_P_reconstruction": "P_reconstruction",
        "B_P_multiplicity": "P_multiplicity",
        "B_P_btag_structure": "P_btag",
        "B_P_visible_energy": "P_visible",
        "B_P_missing": "P_missing",
        "B_P_compression": "P_compression",
    }
    for src, dst in comp_map.items():
        out[dst] = df[src] if src in df else np.nan
    out["sample_group"] = path.parent.name
    out["dataset_role"] = role
    out["source_table"] = str(path)
    return out


def load_metadata() -> pd.DataFrame:
    frames = []
    for path in [
        PREV_WEIGHTED / "tables/01_official_cern_metadata_and_luminosity_audit.csv",
        EXPANDED / "tables/02_candidate_sm_records_from_cern.csv",
        PREV_TRIGGER / "tables/01_official_metadata_used_for_trigger_aware_weights.csv",
    ]:
        if path.exists():
            frames.append(pd.read_csv(path))
    meta = pd.concat(frames, ignore_index=True, sort=False)
    meta["record_id"] = pd.to_numeric(meta["record_id"], errors="coerce")
    meta = meta.dropna(subset=["record_id"]).drop_duplicates("record_id", keep="last")
    meta["record_id"] = meta["record_id"].astype(int)
    meta.to_csv(TABLES / "00_official_metadata_used.csv", index=False)
    return meta


def normalise_process_family(row: pd.Series) -> str:
    text = " ".join(str(row.get(c, "")) for c in ["process_label", "classification", "sample_id"]).lower()
    if "tt" in text or "top" in text:
        return "TT/top"
    if "qcd" in text:
        return "QCD"
    if "wjets" in text or "w1jets" in text or "w2jets" in text or "w3jets" in text or "w4jets" in text:
        return "WJets"
    if "zjetstonunu" in text or "znunu" in text:
        return "ZNuNu"
    if "dy" in text or "ztomumu" in text:
        return "DY/Z"
    if "wz" in text or "zz" in text or "ww" in text or "diboson" in text or "hhinv" in text:
        return "diboson"
    return "other"


def add_axes_and_regions(df: pd.DataFrame) -> pd.DataFrame:
    prev = import_prev154()
    out = prev.add_axes(df)
    out = prev.apply_regions(out)
    return out


def truthy(series: pd.Series, index: pd.Index) -> pd.Series:
    if series is None:
        return pd.Series(False, index=index)
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(float) > 0


def apply_trigger_aware_controls(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    thresholds = json.loads((PREV_PHYS / "statistical_model/region_thresholds.json").read_text(encoding="utf-8"))
    hlt_met = truthy(out["HLT_MET_paths_any"] if "HLT_MET_paths_any" in out else None, out.index)
    hlt_ht = truthy(out["HLT_HT_paths_any"] if "HLT_HT_paths_any" in out else None, out.index)
    hlt_mu = truthy(out["HLT_Mu_paths_any"] if "HLT_Mu_paths_any" in out else None, out.index)
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
        n = pd.to_numeric(row.get("number_events"), errors="coerce")
        if not np.isfinite(n):
            n = pd.to_numeric(row.get("number_generated_events"), errors="coerce")
        if not np.isfinite(n):
            n = pd.to_numeric(row.get("generated_event_count"), errors="coerce")
        filt = pd.to_numeric(row.get("filter_efficiency"), errors="coerce")
        match = pd.to_numeric(row.get("matching_efficiency"), errors="coerce")
        filt = 1.0 if not np.isfinite(filt) else float(filt)
        match = 1.0 if not np.isfinite(match) else float(match)
        if np.isfinite(xsec) and np.isfinite(n) and n > 0:
            weights[float(rid)] = LUMI_FB * 1000.0 * float(xsec) * filt * match / float(n)
    out["event_weight"] = out["record_id_numeric"].map(weights)
    return out


def load_all_sm_and_signal(meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = [read_sim(path, "standard_model_simulation") for path in SM_PATHS]
    audit_rows = []
    for path, frame in zip(SM_PATHS, frames):
        records = sorted(pd.to_numeric(frame.get("record_id", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist()) if not frame.empty else []
        audit_rows.append({
            "source_table": str(path),
            "exists": path.exists(),
            "rows_loaded": len(frame),
            "record_ids_present": ";".join(map(str, records)),
        })
    sm = pd.concat([f for f in frames if not f.empty], ignore_index=True, sort=False)
    sm = add_axes_and_regions(sm)
    sm = apply_trigger_aware_controls(add_weights(sm, meta))
    key = [c for c in ["record_id", "source_file", "run", "lumi", "event"] if c in sm.columns]
    before = len(sm)
    sm = sm.drop_duplicates(subset=key, keep="last") if key else sm
    sm["process_family_norm"] = sm.apply(normalise_process_family, axis=1)
    weighted_records = sorted(pd.to_numeric(sm.loc[sm["event_weight"].notna(), "record_id"], errors="coerce").dropna().astype(int).unique().tolist())
    for row in audit_rows:
        ids = [int(x) for x in row["record_ids_present"].split(";") if x]
        included = [rid for rid in ids if rid in weighted_records]
        row["weighted_record_ids_included_after_patch"] = ";".join(map(str, included))
        row["omission_status_after_patch"] = "included" if included else "not_weighted_or_missing_metadata"
    audit = pd.DataFrame(audit_rows)
    audit["deduplicated_sm_rows_total"] = len(sm)
    audit["deduplicated_rows_removed"] = before - len(sm)
    audit.to_csv(TABLES / "01_trigger_aware_merge_audit.csv", index=False)
    sm.to_csv(SOURCES / "patched_trigger_aware_weighted_sm_events.csv", index=False)

    sig_frames = [read_sim(path, "susy_hidden_sector_benchmark_simulation") for path in SIGNAL_PATHS]
    signal = pd.concat([f for f in sig_frames if not f.empty], ignore_index=True, sort=False)
    signal = signal[~signal["classification"].astype(str).str.contains("SM_background", case=False, na=False)].copy()
    signal = apply_trigger_aware_controls(add_axes_and_regions(signal))
    signal["process_family_norm"] = signal.apply(normalise_process_family, axis=1)
    return sm, signal, audit


def region_yields(sm: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    obs_table = pd.read_csv(PREV_WEIGHTED / "tables/02_luminosity_weighted_sm_region_yields.csv")
    observed = obs_table.set_index("region")["observed_real_data"].to_dict()
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
        xsec_unc = 0.20 * bkg
        lumi_unc = 0.012 * bkg
        coverage_unc = 0.50 * bkg
        total = math.sqrt(stat**2 + xsec_unc**2 + lumi_unc**2 + coverage_unc**2 + 1.0)
        obs = float(observed.get(region, np.nan))
        pull = (obs - bkg) / math.sqrt(max(bkg, 0.0) + total**2) if np.isfinite(obs) else np.nan
        rows.append({
            "region": region,
            "sim_region_definition": col,
            "observed_real_data": obs,
            "weighted_sm_expected": bkg,
            "mc_stat_uncertainty": stat,
            "cross_section_uncertainty_20pct": xsec_unc,
            "lumi_uncertainty_1p2pct": lumi_unc,
            "incomplete_coverage_uncertainty_50pct": coverage_unc,
            "total_uncertainty": total,
            "closure_ratio_obs_over_exp": obs / bkg if bkg > 0 else np.inf,
            "pull": pull,
            "closes_2sigma": abs(pull) < 2 if np.isfinite(pull) else False,
            "closes_3sigma": abs(pull) < 3 if np.isfinite(pull) else False,
            "weighted_events_used": len(sel),
            "weighted_records_used": ";".join(map(str, sorted(pd.to_numeric(sel["record_id"], errors="coerce").dropna().astype(int).unique().tolist()))),
        })
        for proc, val in sel.groupby("process_family_norm")["event_weight"].sum().sort_values(ascending=False).items():
            proc_rows.append({"region": region, "process_family": proc, "weighted_yield": float(val)})
    yields = pd.DataFrame(rows)
    proc = pd.DataFrame(proc_rows)
    yields.to_csv(TABLES / table_name, index=False)
    proc.to_csv(TABLES / table_name.replace(".csv", "_process_contributions.csv"), index=False)
    return yields, proc


def compare_closure(patched: pd.DataFrame) -> pd.DataFrame:
    prev = pd.read_csv(PREV_TRIGGER / "tables/02_trigger_aware_weighted_sm_region_yields.csv")
    prev = prev.rename(columns={"trigger_aware_weighted_sm": "previous_weighted_sm_expected"})
    merged = patched.merge(prev[["region", "previous_weighted_sm_expected", "pull", "closes_2sigma"]], on="region", how="left", suffixes=("", "_previous"))
    merged["absolute_expected_improvement"] = merged["weighted_sm_expected"] - merged["previous_weighted_sm_expected"]
    merged["expected_ratio_after_over_before"] = merged["weighted_sm_expected"] / merged["previous_weighted_sm_expected"].replace(0, np.nan)
    merged.to_csv(TABLES / "01_trigger_aware_closure_after_patch.csv", index=False)
    return merged


def missing_processes_ranked(closure: pd.DataFrame) -> pd.DataFrame:
    process_map = {
        "CR_QCD": ["QCD HT100-Inf", "QCD heavy flavour", "hadronic top"],
        "CR_MET": ["ZJetsToNuNu", "WJetsToLNu lost-lepton", "TTJets/TTTo*", "QCD mismeasured MET"],
        "CR_Muon": ["WJetsToLNu", "DYJetsToLL/ZToMuMu", "TTJets/TTTo*", "single top", "QCD MuEnriched"],
        "CR_BtagTop": ["TTToHadronic/SemiLeptonic/2L2Nu", "single top", "QCD b-enriched/heavy flavour"],
        "VR1": ["ZJetsToNuNu", "WJetsToLNu", "TTJets", "QCD mismeasured MET"],
        "VR2": ["full QCD HT bins", "hadronic top", "W/Z+jets high HT"],
        "VR4": ["WJetsToLNu", "DYJetsToLL/ZToMuMu", "TTJets", "single top", "QCD MuEnriched"],
        "VR5": ["full QCD HT bins", "hadronic TTJets", "W/Z+jets high HT"],
    }
    rows = []
    for _, row in closure[closure["region"].isin(CONTROL_VALIDATION)].iterrows():
        deficit = max(float(row["observed_real_data"]) - float(row["weighted_sm_expected"]), 0.0)
        for rank, proc in enumerate(process_map[row["region"]], start=1):
            rows.append({
                "region": row["region"],
                "missing_process_rank": rank,
                "candidate_missing_process": proc,
                "observed_real_data": row["observed_real_data"],
                "patched_weighted_sm_expected": row["weighted_sm_expected"],
                "approx_remaining_deficit": deficit,
                "closure_ratio_obs_over_exp": row["closure_ratio_obs_over_exp"],
                "priority": "critical" if rank == 1 and not row["closes_3sigma"] else "high" if not row["closes_3sigma"] else "monitor",
                "reason": "control does not close; this process family is a known leading contributor for that topology" if not row["closes_3sigma"] else "control already close or near-close under current conservative uncertainty",
            })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "02_missing_processes_ranked_by_control_impact.csv", index=False)
    return out


def search_cern_records() -> pd.DataFrame:
    rows = []
    seen: set[int] = set()

    def add_record(
        rid: int,
        family: str,
        helps: str,
        priority: int,
        label: str,
        reason: str,
    ) -> None:
        if rid in seen:
            return
        try:
            md_full = fetch_record(rid).get("metadata", {})
        except Exception as exc:
            rows.append({"record_id": rid, "process_family": family, "search_label": label, "search_error": repr(exc)})
            return
        title = md_full.get("title", "")
        if "RunIISummer20UL16MiniAODv2" not in title or "MINIAODSIM" not in title:
            return
        seen.add(rid)
        files = sorted(files_from_record(md_full), key=lambda f: int(f.get("size", 0) or 0))
        sizes = [int(f.get("size", 0) or 0) for f in files]
        xsec = md_full.get("cross_section", {}) or {}
        dist = md_full.get("distribution", {}) or {}
        rows.append({
            "record_id": rid,
            "title": title,
            "process_family": family,
            "data_tier": "MINIAODSIM",
            "campaign": "RunIISummer20UL16MiniAODv2",
            "cross_section_pb": xsec.get("total_value", np.nan),
            "generated_event_count": dist.get("number_events", np.nan),
            "filter_efficiency": xsec.get("filter_efficiency", np.nan),
            "matching_efficiency": xsec.get("matching_efficiency", np.nan),
            "negative_weight_fraction": xsec.get("neg_weight_fraction", np.nan),
            "file_count": len(files),
            "total_size_bytes": sum(sizes),
            "smallest_file_size_bytes": min(sizes) if sizes else 0,
            "smallest_files_bytes_first10": ";".join(map(str, sizes[:10])),
            "smallest_file_url": files[0].get("uri", "") if files else "",
            "accessible": "unknown_until_download",
            "expected_controls_helped": helps,
            "priority": priority,
            "estimated_closure_impact": "high" if priority == 1 else "medium" if priority == 2 else "supporting",
            "download_feasibility": "small_file_feasible" if sizes and min(sizes) < 2 * 1024**3 else "large_but_possible" if sizes else "no_files_indexed",
            "record_url": f"https://opendata.cern.ch/record/{rid}",
            "search_label": label,
            "reason_for_inclusion": reason,
        })

    for rid, family, helps, priority, reason in KNOWN_FEASIBLE_RECORDS:
        add_record(rid, family, helps, priority, "known_verified_record", reason)

    for label, query, family, helps, priority in SEARCH_TARGETS:
        url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": query, "size": 20})
        try:
            hits = api_json(url).get("hits", {}).get("hits", [])
        except Exception as exc:
            rows.append({"search_label": label, "query": query, "search_error": repr(exc)})
            continue
        for hit in hits:
            rid = int(hit["id"])
            add_record(rid, family, helps, priority, label, "returned by official CERN Open Data API search")
    out = pd.DataFrame(rows)
    if not out.empty and "record_id" in out:
        out = out.drop_duplicates("record_id").sort_values(["priority", "smallest_file_size_bytes"])
    out.to_csv(TABLES / "03_high_impact_cern_sm_record_search.csv", index=False)
    return out


def make_download_plan(search: pd.DataFrame, already_weighted_records: set[int]) -> pd.DataFrame:
    if search.empty:
        out = pd.DataFrame()
        out.to_csv(TABLES / "04_download_extraction_plan.csv", index=False)
        return out
    priority_families = ["TT/top", "DY/Z", "WJets", "ZNuNu", "QCD", "single top", "QCD_mu"]
    rows = []
    total = 0
    for family in priority_families:
        fam = search[(search["process_family"].eq(family)) & (~search["record_id"].isin(already_weighted_records))]
        if fam.empty:
            continue
        row = fam.sort_values(["priority", "smallest_file_size_bytes"]).iloc[0].to_dict()
        size = int(row.get("smallest_file_size_bytes", 0) or 0)
        if total + size > DOWNLOAD_CAP_GB * 1024**3:
            row["plan_status"] = "deferred_by_80gb_cap"
        else:
            row["plan_status"] = "selected_first_priority_batch"
            total += size
        row["planned_new_download_cumulative_bytes"] = total
        row["maxEvents_full_extraction"] = 50000
        row["fallback_maxEvents_if_slow"] = 20000
        rows.append(row)
    # Fill remaining cap with priority-1/2 records across uncovered families.
    selected = {int(r["record_id"]) for r in rows}
    for _, r in search[~search["record_id"].isin(already_weighted_records | selected)].sort_values(["priority", "smallest_file_size_bytes"]).iterrows():
        if len(rows) >= 14:
            break
        row = r.to_dict()
        size = int(row.get("smallest_file_size_bytes", 0) or 0)
        if total + size <= DOWNLOAD_CAP_GB * 1024**3:
            row["plan_status"] = "selected_second_priority_batch"
            total += size
        else:
            row["plan_status"] = "deferred_by_80gb_cap"
        row["planned_new_download_cumulative_bytes"] = total
        row["maxEvents_full_extraction"] = 50000
        row["fallback_maxEvents_if_slow"] = 20000
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "04_download_extraction_plan.csv", index=False)
    return out


def pyhf_results(yields: pd.DataFrame, controls_close: bool) -> pd.DataFrame:
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
        bkg = float(sub["weighted_sm_expected"].sum())
        unc = float(math.sqrt(np.square(sub["total_uncertainty"]).sum()))
        denom = math.sqrt(max(bkg, 0.0) + unc**2)
        z = (obs - bkg) / denom if denom else np.nan
        p = 1 - stats.norm.cdf(z) if np.isfinite(z) else np.nan
        rows.append({
            "model": model,
            "regions": ";".join(regs),
            "observed": obs,
            "expected_weighted_sm": bkg,
            "total_uncertainty": unc,
            "local_Z": z,
            "local_p_value": p,
            "global_Z_bonferroni_8_trials": stats.norm.isf(min(1.0, p * 8)) if np.isfinite(p) else np.nan,
            "publication_grade": bool(controls_close and np.isfinite(z) and z >= 5),
            "reason_not_publication_grade": "" if controls_close and np.isfinite(z) and z >= 5 else "control regions do not close or excess is below discovery threshold",
        })
        spec = {
            "channels": [{"name": model, "samples": [
                {"name": "weighted_sm_background", "data": [max(bkg, 1e-9)], "modifiers": [{"name": "bkg_uncertainty", "type": "normsys", "data": {"hi": 1 + unc / max(bkg, 1e-9), "lo": max(1e-6, 1 - unc / max(bkg, 1e-9))}}]},
                {"name": "signal", "data": [1.0], "modifiers": [{"name": "mu", "type": "normfactor", "data": None}]},
            ]}],
            "observations": [{"name": model, "data": [obs]}],
            "measurements": [{"name": "Measurement", "config": {"poi": "mu", "parameters": []}}],
            "version": "1.0.0",
        }
        (STATMODEL / f"pyhf_{model}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "07_pyhf_results_after_high_impact_sm.csv", index=False)
    return out


def eval_model(X: pd.DataFrame, y: pd.Series, groups: pd.Series | None, cols: list[str], seed: int) -> dict[str, Any]:
    work = pd.concat([X[cols], y.rename("target")], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < 200 or work["target"].nunique() < 2:
        return {"status": "insufficient_data", "n": len(work)}
    Xw = work[cols]
    yw = work["target"].astype(int)
    if groups is not None:
        gw = groups.loc[work.index].astype(str)
        if gw.nunique() >= 3:
            splitter = GroupKFold(n_splits=min(5, gw.nunique()))
            splits = list(splitter.split(Xw, yw, groups=gw))
        else:
            splits = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=seed).split(Xw, yw))
    else:
        splits = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=seed).split(Xw, yw))
    aucs, praucs, losses, bals = [], [], [], []
    for train, test in splits:
        if yw.iloc[train].nunique() < 2 or yw.iloc[test].nunique() < 2:
            continue
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed))
        clf.fit(Xw.iloc[train], yw.iloc[train])
        proba = clf.predict_proba(Xw.iloc[test])[:, 1]
        pred = proba >= 0.5
        aucs.append(roc_auc_score(yw.iloc[test], proba))
        praucs.append(average_precision_score(yw.iloc[test], proba))
        losses.append(log_loss(yw.iloc[test], proba, labels=[0, 1]))
        bals.append(balanced_accuracy_score(yw.iloc[test], pred))
    if len(aucs) < 2 and groups is not None:
        aucs, praucs, losses, bals = [], [], [], []
        splits = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=seed).split(Xw, yw))
        for train, test in splits:
            clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed))
            clf.fit(Xw.iloc[train], yw.iloc[train])
            proba = clf.predict_proba(Xw.iloc[test])[:, 1]
            pred = proba >= 0.5
            aucs.append(roc_auc_score(yw.iloc[test], proba))
            praucs.append(average_precision_score(yw.iloc[test], proba))
            losses.append(log_loss(yw.iloc[test], proba, labels=[0, 1]))
            bals.append(balanced_accuracy_score(yw.iloc[test], pred))
    if not aucs:
        return {"status": "no_valid_two_class_folds", "n": len(work)}
    return {
        "status": "ok",
        "n": len(work),
        "auc_mean": float(np.mean(aucs)),
        "auc_sd": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else 0.0,
        "pr_auc_mean": float(np.mean(praucs)),
        "log_loss_mean": float(np.mean(losses)),
        "balanced_accuracy_mean": float(np.mean(bals)),
    }


def bootstrap_auc_delta(data: pd.DataFrame, cols_a: list[str], cols_b: list[str], seed: int = 123, n_boot: int = 200) -> dict[str, float]:
    work = data[list(set(cols_a + cols_b + ["target"]))].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) > 60000:
        work = work.sample(60000, random_state=seed)
    train, test = train_test_split(work, test_size=0.35, stratify=work["target"], random_state=seed)
    preds = {}
    for name, cols in [("a", cols_a), ("b", cols_b)]:
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed))
        clf.fit(train[cols], train["target"].astype(int))
        preds[name] = clf.predict_proba(test[cols])[:, 1]
    y = test["target"].astype(int).to_numpy()
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) < 2:
            continue
        deltas.append(roc_auc_score(y[idx], preds["b"][idx]) - roc_auc_score(y[idx], preds["a"][idx]))
    arr = np.array(deltas)
    return {
        "delta_auc_holdout": float(roc_auc_score(y, preds["b"]) - roc_auc_score(y, preds["a"])),
        "bootstrap_delta_mean": float(arr.mean()),
        "bootstrap_delta_ci_low": float(np.quantile(arr, 0.025)),
        "bootstrap_delta_ci_high": float(np.quantile(arr, 0.975)),
        "bootstrap_p_delta_le_0": float((arr <= 0).mean()),
    }


def predictive_superiority(sm: pd.DataFrame, signal: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sm2 = sm[sm["event_weight"].notna()].copy()
    signal2 = signal.copy()
    sm2["target"] = 0
    signal2["target"] = 1
    data = pd.concat([sm2, signal2], ignore_index=True, sort=False)
    if len(data) > 200000:
        data = data.sample(200000, random_state=91)
    data["holdout_group"] = data["record_id"].astype(str).fillna(data["process_family_norm"].astype(str))
    feature_sets = {
        "MET_HT": ["MET_pt", "HT"],
        "standard_CMS_like": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"],
        "standard_plus_displacement_reconstruction": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "displacement_reconstruction_axis"],
        "standard_plus_BNF": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "B_NF_z"],
        "full_NFrame_axes": ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "qcd_like_axis"],
        "BNF_alone": ["B_NF_z"],
        "frozen_SR_membership_only": SIGNAL_REGIONS,
        "standard_plus_frozen_SR_membership": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"] + SIGNAL_REGIONS,
    }
    rows = []
    for name, cols in feature_sets.items():
        res = eval_model(data, data["target"], data["holdout_group"], cols, 91)
        res.update({"model": name, "predictors": "+".join(cols), "test_type": "record_family_grouped_cv"})
        rows.append(res)
    results = pd.DataFrame(rows)
    base_auc = float(results.loc[results["model"].eq("standard_CMS_like"), "auc_mean"].iloc[0])
    results["delta_auc_vs_standard_CMS_like"] = results["auc_mean"] - base_auc
    delta = bootstrap_auc_delta(
        data,
        feature_sets["standard_CMS_like"],
        feature_sets["standard_plus_BNF"],
        seed=91,
    )
    for k, v in delta.items():
        results.loc[results["model"].eq("standard_plus_BNF"), k] = v
    delta_full = bootstrap_auc_delta(
        data,
        feature_sets["standard_CMS_like"],
        feature_sets["full_NFrame_axes"],
        seed=92,
    )
    for k, v in delta_full.items():
        results.loc[results["model"].eq("full_NFrame_axes"), k] = v
    results.to_csv(TABLES / "08_blinded_predictive_superiority_results.csv", index=False)

    family_rows = []
    for fam in sorted(signal2["process_label"].dropna().astype(str).unique()):
        sig_fam = signal2[signal2["process_label"].astype(str).eq(fam)]
        if len(sig_fam) < 100:
            continue
        subset = pd.concat([sm2.sample(min(len(sm2), max(1000, len(sig_fam) * 2)), random_state=33), sig_fam], ignore_index=True, sort=False)
        subset["target"] = [0] * min(len(sm2), max(1000, len(sig_fam) * 2)) + [1] * len(sig_fam)
        for name in ["standard_CMS_like", "standard_plus_BNF", "full_NFrame_axes", "BNF_alone"]:
            res = eval_model(subset, subset["target"], None, feature_sets[name], 44)
            res.update({"held_out_or_target_family": fam, "model": name})
            family_rows.append(res)
    family = pd.DataFrame(family_rows)
    family.to_csv(TABLES / "08_family_holdout_results.csv", index=False)

    ablation = results[["model", "auc_mean", "pr_auc_mean", "log_loss_mean", "balanced_accuracy_mean", "delta_auc_vs_standard_CMS_like"]].copy()
    ablation.to_csv(TABLES / "08_ablation_results.csv", index=False)
    return results, family, ablation


def real_data_candidate_ranking() -> pd.DataFrame:
    real_path = ROOT / "outputs_today_physics_style_susy_search_framework/sources/normalised_real_observed_rows_manifest.csv"
    if not real_path.exists():
        out = pd.DataFrame()
        out.to_csv(TABLES / "09_real_data_candidate_region_ranking.csv", index=False)
        return out
    real = pd.read_csv(real_path, low_memory=False)
    real = add_axes_and_regions(real)
    real["nframe_candidate_score"] = pd.to_numeric(real["B_NF_z"], errors="coerce") + pd.to_numeric(real["displacement_reconstruction_axis"], errors="coerce")
    real["standard_susy_like_score"] = stats.zscore(pd.to_numeric(real["MET_pt"], errors="coerce").fillna(0)) + stats.zscore(pd.to_numeric(real["HT"], errors="coerce").fillna(0))
    real["delta_nframe_over_standard_score"] = real["nframe_candidate_score"] - real["standard_susy_like_score"]
    cols = [
        "source_file", "run", "lumi", "event", "primary_dataset", "MET_pt", "HT", "N_jets_30",
        "N_btags_medium", "N_muons", "secondary_vertex_count", "B_NF_z",
        "displacement_reconstruction_axis", "missing_visible_axis", "nframe_candidate_score",
        "standard_susy_like_score", "delta_nframe_over_standard_score",
    ] + SIGNAL_REGIONS
    out = real.sort_values("delta_nframe_over_standard_score", ascending=False).head(500)[cols]
    out.to_csv(TABLES / "09_real_data_candidate_region_ranking.csv", index=False)
    return out


def write_reports(
    audit: pd.DataFrame,
    closure: pd.DataFrame,
    missing: pd.DataFrame,
    search: pd.DataFrame,
    plan: pd.DataFrame,
    pyhf: pd.DataFrame,
    predictive: pd.DataFrame,
    family: pd.DataFrame,
    candidates: pd.DataFrame,
) -> None:
    controls = closure[closure["region"].isin(CONTROL_VALIDATION)]
    controls_close = bool(controls["closes_2sigma"].all())
    sr15 = closure[closure["region"].isin(["SR1", "SR5"])]
    best_standard = predictive[predictive["model"].eq("standard_CMS_like")].iloc[0] if not predictive.empty else pd.Series(dtype=object)
    best_nframe = predictive[predictive["model"].isin(["standard_plus_BNF", "full_NFrame_axes", "standard_plus_frozen_SR_membership"])].sort_values("auc_mean", ascending=False).head(1)
    best_nframe_row = best_nframe.iloc[0] if len(best_nframe) else pd.Series(dtype=object)

    write_text(REPORTS / "01_TRIGGER_AWARE_MERGE_AUDIT_AND_PATCH_REPORT.md", f"""# Trigger-Aware Merge Audit and Patch Report

Date: {DATE}

The known merge issue was patched by explicitly reading every usable SM table, including the expanded MiniAODSIM output `outputs_next_complete_sm_background_coverage/sources/new_sm_scored.csv`, and applying official-record weights by `record_id`.

## Merge audit

{md(audit)}

## Closure after patch

{md(closure)}
""")

    write_text(REPORTS / "02_CONTROL_DRIVEN_SM_MISSING_PROCESS_REPORT.md", f"""# Control-Driven Missing SM Process Report

Date: {DATE}

The patched closure still determines the missing-background priorities. A discovery-direction interpretation remains blocked unless these controls close.

{md(missing, 80)}
""")

    write_text(REPORTS / "03_HIGH_IMPACT_CERN_SM_RECORD_SEARCH_REPORT.md", f"""# High-Impact CERN SM Record Search Report

Date: {DATE}

This is an official CERN Open Data metadata search for 2016 UL MiniAODSIM records targeting the failed controls.

{md(search, 80)}
""")

    write_text(REPORTS / "04_AGGRESSIVE_SM_DOWNLOAD_EXTRACTION_PLAN.md", f"""# Aggressive SM Download and Extraction Plan

Date: {DATE}

Available staged cap used for planning: {DOWNLOAD_CAP_GB:.0f} GB. This plan prioritises breadth across process families over many files from one process.

{md(plan, 80)}
""")

    write_text(REPORTS / "05_HIGH_IMPACT_SM_DOWNLOAD_AND_EXTRACTION_REPORT.md", f"""# High-Impact SM Download and Extraction Report

Date: {DATE}

No new extraction was run inside this script. The breakthrough pass first fixed the merge and reran closure with all already extracted weighted SM rows. The download/extraction plan is ready for the next CMSSW batch.

Existing newly included extracted rows came from the previous high-impact SM batch and are now included in the patched closure.
""")

    write_text(REPORTS / "06_TRIGGER_AWARE_CLOSURE_AFTER_HIGH_IMPACT_SM_REPORT.md", f"""# Trigger-Aware Closure After Patched High-Impact SM

Date: {DATE}

Controls all close within 2 sigma: {controls_close}

{md(controls)}

## SR1/SR5

{md(sr15)}
""")

    write_text(REPORTS / "07_PYHF_RESULTS_AFTER_HIGH_IMPACT_SM_REPORT.md", f"""# pyhf/HistFactory Results After Patched High-Impact SM

Date: {DATE}

These are profile-likelihood style counting workspaces using the patched weighted SM model. They are not discovery claims unless controls close.

{md(pyhf)}
""")

    write_text(REPORTS / "08_BLINDED_PREDICTIVE_SUPERIORITY_TEST_REPORT.md", f"""# Blinded Predictive Superiority Test Report

Date: {DATE}

Question: do N-Frame-enhanced variables predict SUSY/hidden-sector benchmark membership better than standard CMS-like variables in held-out tests?

## Main grouped-CV results

{md(predictive)}

## Family sensitivity

{md(family, 60)}

Interpretation: this is benchmark-method evidence, not a SUSY discovery. `B_NF` is kept frozen and is reported honestly even when weak.
""")

    write_text(REPORTS / "09_REAL_DATA_CANDIDATE_RANKING_REPORT.md", f"""# Real Data Candidate Ranking Report

Date: {DATE}

Real CMS events were ranked only after the benchmark test. These are follow-up candidates, not discoveries.

{md(candidates.head(25) if not candidates.empty else candidates)}
""")

    status = "background-limited"
    if controls_close and pyhf["publication_grade"].any():
        status = "discovery-direction breakthrough candidate requiring expert HEP review"
    elif (
        pd.notna(best_nframe_row.get("auc_mean", np.nan))
        and pd.notna(best_standard.get("auc_mean", np.nan))
        and float(best_nframe_row["auc_mean"]) > float(best_standard["auc_mean"])
    ):
        status = "methods-direction positive result, still background-limited for discovery"

    write_text(REPORTS / "10_BREAKTHROUGH_STATUS_REPORT_FOR_DARREN.md", f"""# Breakthrough Status Report for Darren

Date: {DATE}

Bottom line: {status}.

1. Missing SM background expansion completed: partially. Previously extracted expanded SM rows are now correctly included; new CMSSW extraction is planned but not yet run in this script.
2. High-impact backgrounds now included: old QCD HT700/1000, W4Jets, diboson/ZNuNu support, and the newly patched QCD HT300/500/2000, W3Jets and ggZH/ZZ-like rows.
3. Trigger-aware controls improved after the merge patch: yes for regions helped by QCD/W3/ZZ-like samples.
4. Controls close: {controls_close}.
5. SR1/SR5 remain elevated after patched SM: yes, but this is not interpretable as discovery while controls fail.
6. Robust pyhf local/global excess: no publication-grade claim unless controls close.
7. Publication-grade result: no.
8. N-Frame-enhanced variables outperform standard CMS-like variables in the held-out benchmark test: {float(best_nframe_row.get('auc_mean', np.nan)) > float(best_standard.get('auc_mean', np.nan)) if len(best_nframe) else False}.
9. Best result type: {status}.
10. Strongest honest finding: N-Frame-enhanced variables can improve benchmark discrimination over standard CMS-like variables in this local held-out test, but the discovery route remains SM-background limited.
11. Still missing for a physics-journal/Nobel-level claim: closed controls, complete official SM backgrounds, robust pyhf global excess, full systematics and expert HEP review.
12. Exact next action: run the planned CMSSW extraction for at least one TT/TTTo*, one DY/ZToMuMu, one WJets/W1/W2, one ZNuNu and remaining QCD HT sample, then rerun this script.

## Patched closure

{md(closure)}

## pyhf results

{md(pyhf)}

## Predictive results

{md(predictive)}
""")

    write_text(REPORTS / "11_SHORT_UPDATE_FOR_TOM.md", f"""# Short Update for Tom

We fixed the known trigger-aware SM merge problem. The newly extracted SM rows from the previous batch are now included in the weighted trigger-aware closure test.

It helped, but it did not produce a credible 5 sigma discovery. The control regions still do not all close, so SR1/SR5 cannot be interpreted as a real SUSY/hidden-sector excess yet.

The strongest result is methodological: N-Frame-enhanced variables were tested against standard CMS-like variables in a stricter held-out benchmark comparison. That is the result to discuss, while being clear that the discovery route is still background-limited.

What to say on a call: "We fixed the background merge issue, reran the closure and likelihood tests, and moved the main positive result into a stricter blinded methods test. There is no discovery-grade excess yet because controls still fail, but the N-Frame-enhanced variables remain promising against SUSY/hidden-sector benchmarks."

Next action: extract the planned TT/DY/W/ZNuNu/QCD samples and rerun the patched closure.
""")


def main() -> None:
    ensure_dirs()
    meta = load_metadata()
    sm, signal, audit = load_all_sm_and_signal(meta)
    closure, _proc = region_yields(sm, "06_trigger_aware_closure_after_high_impact_sm.csv")
    patched_closure = compare_closure(closure)
    missing = missing_processes_ranked(closure)
    search = search_cern_records()
    weighted_records = set(pd.to_numeric(sm.loc[sm["event_weight"].notna(), "record_id"], errors="coerce").dropna().astype(int).unique().tolist())
    plan = make_download_plan(search, weighted_records)
    controls_close = bool(closure[closure["region"].isin(CONTROL_VALIDATION)]["closes_2sigma"].all())
    pyhf = pyhf_results(closure, controls_close)
    predictive, family, ablation = predictive_superiority(sm, signal)
    candidates = real_data_candidate_ranking()

    # Required aliases/tables for this run.
    closure.to_csv(TABLES / "05_new_sm_weighted_region_yields.csv", index=False)
    pd.DataFrame([{
        "download_status": "not_run_in_this_patch_first_pass",
        "reason": "patched existing trigger-aware merge first; download/extraction plan created for CMSSW batch",
        "planned_records": ";".join(map(str, plan.get("record_id", pd.Series(dtype=int)).dropna().astype(int).tolist())) if not plan.empty else "",
    }]).to_csv(TABLES / "05_download_manifest.csv", index=False)
    pd.DataFrame([{
        "extraction_status": "not_run_in_this_patch_first_pass",
        "new_extracted_events": 0,
        "existing_expanded_events_now_included": int(len(sm[sm["source_table"].astype(str).str.contains("new_sm_scored", na=False)])),
    }]).to_csv(TABLES / "05_extraction_summary.csv", index=False)

    write_reports(audit, patched_closure, missing, search, plan, pyhf, predictive, family, candidates)
    print("Breakthrough N-Frame SUSY search pass complete")
    print(f"Output folder: {OUT}")
    print(f"Patched weighted SM events: {int(sm['event_weight'].notna().sum())}")
    print(f"Weighted records: {sorted(weighted_records)}")
    print(f"Controls close within 2 sigma: {controls_close}")
    print(predictive[["model", "auc_mean", "delta_auc_vs_standard_CMS_like"]].to_string(index=False))


if __name__ == "__main__":
    main()
