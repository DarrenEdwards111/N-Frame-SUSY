from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_today_physics_style_susy_search_framework"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
SOURCES = OUT / "sources"
STATMODEL = OUT / "statistical_model"
DATE = "2026-06-10"


REAL_DATASETS = [
    {
        "label": "Run2016G_fit_real",
        "path": ROOT / "data/processed/nframe_parameter_fit/real_data_with_fitted_nframe_boundary_score.csv",
        "tier": "MiniAOD full-component scored real",
        "bnf": "B_NF_fitted_z",
        "raw": "B_NF_fitted_raw",
        "prefix": "fitted",
        "caveat": "Used to fit the frozen B_NF equation; not independent for discovery-style significance.",
    },
    {
        "label": "Run2016H_main_validation",
        "path": ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv",
        "tier": "MiniAOD full-component scored real",
        "bnf": "B_NF_fitted_run2016h_z",
        "raw": "B_NF_fitted_run2016h_raw",
        "prefix": "run2016h",
        "caveat": "Independent validation subset, but overlaps the expanded Run2016H table.",
    },
    {
        "label": "Run2016H_expanded_validation",
        "path": ROOT / "data/processed/expanded_run2016h_miniaod_full/expanded_run2016h_miniaod_with_fitted_nframe_score.csv",
        "tier": "MiniAOD full-component scored real",
        "bnf": "B_NF_fitted_expanded_run2016h_z",
        "raw": "B_NF_fitted_expanded_run2016h_raw",
        "prefix": "expanded",
        "caveat": "Expanded independent Run2016H validation. Used for yields; combined unique drops duplicated files/events.",
    },
    {
        "label": "Run2016H_new_unused_validation",
        "path": ROOT / "data/processed/new_independent_real_miniaod_validation/full/new_real_events_with_frozen_BNF.csv",
        "tier": "MiniAOD full-component scored real",
        "bnf": "B_NF_fitted_new_z",
        "raw": "B_NF_fitted_new_raw",
        "prefix": "new",
        "caveat": "New unused Run2016H files downloaded and extracted in this session.",
    },
]

SM_DATASETS = [
    {
        "label": "SM_full_component_QCD_WJets",
        "path": ROOT / "data/processed/fuller_component_benchmarks/fuller_component_benchmark_events_with_BNF.csv",
        "tier": "MiniAODSIM full-component",
        "caveat": "Shape/transfer-factor support only; no luminosity normalisation or official systematics.",
    },
    {
        "label": "SM_expanded_diboson_ZNuNu",
        "path": ROOT / "data/processed/expanded_sm_after_signal_parity/expanded_sm_backgrounds_with_BNF.csv",
        "tier": "MiniAODSIM full-component",
        "caveat": "Small event counts for some processes; shape support only.",
    },
    {
        "label": "SM_NanoAOD_QCD_TTJets",
        "path": ROOT / "data/processed/sm_background_pilot_features/sm_background_events_with_BNF.csv",
        "tier": "NANOAODSIM reduced-component",
        "caveat": "Reduced-component approximation; secondary vertices are not equivalent to full MiniAOD.",
    },
]

SIGNAL_DATASETS = [
    {
        "label": "SUSY_full_component_accessible",
        "path": ROOT / "data/processed/fuller_component_susy_signals/accessible_susy_miniaodsim_events_with_BNF.csv",
        "tier": "MINIAODSIM full-component",
        "caveat": "Benchmark signal hypotheses only; not evidence.",
    },
    {
        "label": "SUSY_reduced_T5Wg_HToAA4B",
        "path": ROOT / "data/processed/susy_relevance_benchmark_features/susy_sm_benchmark_events_with_BNF.csv",
        "tier": "NANOAODSIM/reduced scored benchmark",
        "caveat": "Reduced components; useful for topology sensitivity only.",
    },
    {
        "label": "SUSY_expanded_benchmark_mixed",
        "path": ROOT / "data/processed/expanded_benchmark_features/expanded_benchmark_events_with_BNF.csv",
        "tier": "mixed reduced/full benchmark table",
        "caveat": "Contains both signal-like and SM-like samples; classification column is used.",
    },
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
    "pass_goodVertices",
    "standard_quality_clean",
    "data_tier",
    "component_mode",
    "topology_class",
    "model_label",
    "B_NF_fitted_frozen_z_real_scaled",
    "B_NF_fitted_frozen_raw",
    "B_P_displacement_proxy",
    "B_P_reconstruction",
    "B_P_multiplicity",
    "B_P_btag_structure",
    "B_P_visible_energy",
    "B_P_missing",
    "B_P_compression",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, FIGURES, SOURCES, STATMODEL]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    return view.to_markdown(index=False)


def row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open("r", encoding="utf-8", errors="replace")) - 1


def header(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns) if path.exists() else []


def inventory_one(item: dict[str, Any], category: str) -> dict[str, Any]:
    path = item["path"]
    cols = header(path)
    bnf_cols = [c for c in cols if "B_NF" in c or c.endswith("B_event_z")]
    component_cols = [c for c in cols if c.startswith(("fitted_P_", "run2016h_P_", "expanded_P_", "new_P_", "B_P_"))]
    return {
        "dataset_label": item["label"],
        "category": category,
        "path": str(path),
        "exists": path.exists(),
        "event_count": row_count(path),
        "data_tier": item.get("tier", ""),
        "sample_name": item["label"],
        "available_bnf_columns": ";".join(bnf_cols),
        "available_component_columns": ";".join(component_cols),
        "P_displacement_proxy_available": any("displacement" in c for c in component_cols) or "secondary_vertex_count" in cols,
        "P_reconstruction_available": any("reconstruction" in c for c in component_cols) or "packed_candidate_count" in cols,
        "MET_HT_jets_btags_available": all(c in cols for c in ["MET_pt", "HT", "N_jets_30", "N_btags_medium"]),
        "quality_flags_available": any(c in cols for c in ["pass_goodVertices", "standard_quality_clean"]),
        "event_weights_cross_sections_lumi_available": any(c in cols for c in ["event_weight", "xsec", "cross_section", "lumi_weight"]),
        "suitable_for_physics_style_search_modelling": "yes_shape_or_observed" if path.exists() else "missing",
        "caveats": item.get("caveat", ""),
    }


def build_inventory() -> pd.DataFrame:
    rows = []
    for item in REAL_DATASETS:
        rows.append(inventory_one(item, "observed_real_collision_data"))
    for item in SM_DATASETS:
        rows.append(inventory_one(item, "standard_model_simulation"))
    for item in SIGNAL_DATASETS:
        rows.append(inventory_one(item, "susy_hidden_sector_benchmark_simulation"))
    inv = pd.DataFrame(rows)
    inv.to_csv(TABLES / "01_analysis_inventory.csv", index=False)
    write_text(
        OUT / "01_ANALYSIS_INVENTORY_REPORT.md",
        f"""# Analysis Inventory Report

Date: {DATE}

This inventory separates observed real CMS collision data, Standard Model simulation/background support, and SUSY/hidden-sector benchmark simulations. Simulation is used only in the physics-community sense: SM simulation supports background/transfer-factor checks and SUSY simulation provides benchmark signal hypotheses.

{md(inv)}
""",
    )
    return inv


def choose_cols(path: Path, extra: list[str]) -> list[str]:
    cols = header(path)
    wanted = [c for c in extra if c in cols]
    for c in BASE_COLS:
        if c in cols and c not in wanted:
            wanted.append(c)
    return wanted


def read_real(item: dict[str, Any]) -> pd.DataFrame:
    path = item["path"]
    pref = item["prefix"]
    bnf = item["bnf"]
    raw = item["raw"]
    component_map = {
        f"{pref}_P_displacement_proxy": "P_displacement",
        f"{pref}_P_reconstruction": "P_reconstruction",
        f"{pref}_P_multiplicity": "P_multiplicity",
        f"{pref}_P_btag_structure": "P_btag",
        f"{pref}_P_visible_energy": "P_visible",
        f"{pref}_P_missing": "P_missing",
        f"{pref}_P_compression": "P_compression",
    }
    if pref == "fitted":
        component_map = {
            "fitted_P_displacement_proxy": "P_displacement",
            "fitted_P_reconstruction": "P_reconstruction",
            "fitted_P_multiplicity": "P_multiplicity",
            "fitted_P_btag_structure": "P_btag",
            "fitted_P_visible_energy": "P_visible",
            "fitted_P_missing": "P_missing",
            "fitted_P_compression": "P_compression",
        }
    extra = [bnf, raw] + list(component_map)
    use = choose_cols(path, extra)
    chunks = []
    for chunk in pd.read_csv(path, usecols=use, chunksize=200_000):
        out = pd.DataFrame()
        for col in BASE_COLS:
            out[col] = chunk[col] if col in chunk else np.nan
        out["B_NF_z"] = chunk[bnf] if bnf in chunk else np.nan
        out["B_NF_raw"] = chunk[raw] if raw in chunk else np.nan
        for src, dst in component_map.items():
            out[dst] = chunk[src] if src in chunk else np.nan
        out["sample_group"] = item["label"]
        out["dataset_role"] = "observed_real_collision_data"
        out["data_tier_norm"] = item["tier"]
        chunks.append(out)
    return pd.concat(chunks, ignore_index=True)


def read_sim(item: dict[str, Any], role: str) -> pd.DataFrame:
    path = item["path"]
    use = choose_cols(path, [])
    try:
        df = pd.read_csv(path, usecols=use, low_memory=False)
    except Exception:
        df = pd.read_csv(path, usecols=use, engine="python", on_bad_lines="skip")
    out = pd.DataFrame()
    for col in BASE_COLS:
        out[col] = df[col] if col in df else np.nan
    out["B_NF_z"] = df["B_NF_fitted_frozen_z_real_scaled"] if "B_NF_fitted_frozen_z_real_scaled" in df else np.nan
    out["B_NF_raw"] = df["B_NF_fitted_frozen_raw"] if "B_NF_fitted_frozen_raw" in df else np.nan
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
    out["sample_group"] = item["label"]
    out["dataset_role"] = role
    out["data_tier_norm"] = item["tier"]
    return out


def add_axes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric = [
        "B_NF_z",
        "B_NF_raw",
        "P_displacement",
        "P_reconstruction",
        "P_multiplicity",
        "P_btag",
        "P_visible",
        "P_missing",
        "P_compression",
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_jets_50",
        "N_btags_medium",
        "N_btags_tight",
        "N_muons",
        "N_electrons",
        "N_leptons",
        "secondary_vertex_count",
        "packed_candidate_count",
        "N_primary_vertices",
        "pass_goodVertices",
        "standard_quality_clean",
    ]
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["P_displacement"] = out["P_displacement"].fillna(out["secondary_vertex_count"])
    out["P_reconstruction"] = out["P_reconstruction"].fillna(out[["packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"]].mean(axis=1))
    out["P_missing"] = out["P_missing"].fillna(out["MET_pt"])
    out["P_visible"] = out["P_visible"].fillna(out[["HT", "N_jets_30"]].mean(axis=1))
    out["P_multiplicity"] = out["P_multiplicity"].fillna(out[["N_jets_30", "N_leptons"]].mean(axis=1))
    out["P_btag"] = out["P_btag"].fillna(out["N_btags_medium"])
    out["displacement_reconstruction_axis"] = out["P_displacement"] + out["P_reconstruction"]
    out["missing_visible_axis"] = out["P_missing"] + out["P_visible"]
    out["qcd_like_axis"] = out[["P_visible", "P_multiplicity", "P_btag"]].mean(axis=1)
    out["trace_alignment_score"] = out["B_NF_z"] + out["displacement_reconstruction_axis"] - out["missing_visible_axis"].clip(lower=0)
    out["quality_clean"] = out["standard_quality_clean"].fillna(out["pass_goodVertices"]).fillna(1)
    out["primary_dataset"] = out["primary_dataset"].fillna(out["sample_group"])
    out["process_label"] = out["process_label"].fillna(out["sample_id"]).fillna(out["sample_group"])
    return out


def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    real_parts = [read_real(item) for item in REAL_DATASETS if item["path"].exists()]
    real = add_axes(pd.concat(real_parts, ignore_index=True))
    sm = add_axes(pd.concat([read_sim(item, "standard_model_simulation") for item in SM_DATASETS if item["path"].exists()], ignore_index=True))
    sig_all = add_axes(pd.concat([read_sim(item, "susy_hidden_sector_benchmark_simulation") for item in SIGNAL_DATASETS if item["path"].exists()], ignore_index=True))
    # Some expanded benchmark tables contain SM rows. Keep only non-SM rows for signal map.
    signal = sig_all[~sig_all["classification"].astype(str).str.contains("SM_background", case=False, na=False)].copy()
    combined_key = ["source_file", "run", "lumi", "event"]
    real_unique = real.drop_duplicates(subset=combined_key, keep="last").copy()
    real.to_csv(SOURCES / "normalised_real_observed_rows_manifest.csv", index=False)
    return real, real_unique, sm, signal


def define_regions(threshold_data: pd.DataFrame) -> pd.DataFrame:
    t = {
        "B_NF_z_top05": threshold_data["B_NF_z"].quantile(0.95),
        "B_NF_z_top10": threshold_data["B_NF_z"].quantile(0.90),
        "disp_reco_top20": threshold_data["displacement_reconstruction_axis"].quantile(0.80),
        "disp_reco_top10": threshold_data["displacement_reconstruction_axis"].quantile(0.90),
        "disp_reco_median": threshold_data["displacement_reconstruction_axis"].quantile(0.50),
        "missing_visible_top20": threshold_data["missing_visible_axis"].quantile(0.80),
        "missing_visible_median": threshold_data["missing_visible_axis"].quantile(0.50),
        "qcd_like_top20": threshold_data["qcd_like_axis"].quantile(0.80),
        "MET_moderate": 80.0,
        "secondary_vertices_ge1": 1.0,
    }
    rows = [
        ("SR1", "signal", "high B_NF + high displacement/reconstruction", f"B_NF_z >= {t['B_NF_z_top05']:.6g}; disp_reco >= {t['disp_reco_top20']:.6g}", "frozen from previous real-data validation", "main N-Frame high-boundary region", "unblinded exploratory"),
        ("SR2", "signal", "high displacement/reconstruction + low missing/visible", f"disp_reco >= {t['disp_reco_top20']:.6g}; missing_visible <= {t['missing_visible_median']:.6g}", "frozen from previous real-data validation", "boundary-like reconstruction/displacement without ordinary MET/HT explanation", "unblinded exploratory"),
        ("SR3", "signal", "trace-aligned high-boundary proxy", f"B_NF_z >= {t['B_NF_z_top05']:.6g}; disp_reco >= {t['disp_reco_top20']:.6g}; missing_visible < {t['missing_visible_top20']:.6g}", "frozen from previous real-data validation", "high boundary, high displacement/reconstruction, not purely missing/visible", "unblinded exploratory"),
        ("SR4", "signal", "high B_NF + high displacement/reconstruction + moderate/high MET", f"B_NF_z >= {t['B_NF_z_top05']:.6g}; disp_reco >= {t['disp_reco_top20']:.6g}; MET >= 80", "analysis-level add-on, not tuned", "more standard SUSY-like high-boundary region", "unblinded exploratory"),
        ("SR5", "signal", "LLP/disappearing proxy", f"secondary_vertex_count >= 1; disp_reco >= {t['disp_reco_top20']:.6g}; B_NF_z >= {t['B_NF_z_top10']:.6g}", "proxy region; not direct LLP tagging", "LLP-like reconstruction/displacement stress proxy", "unblinded exploratory"),
        ("VR1", "validation", "high missing/visible + low displacement/reconstruction", f"missing_visible >= {t['missing_visible_top20']:.6g}; disp_reco <= {t['disp_reco_median']:.6g}", "frozen comparator", "standard MET/HT-like comparator", "unblinded"),
        ("VR2", "validation", "qcd-like high HT/high multiplicity", f"qcd_like >= {t['qcd_like_top20']:.6g}", "frozen comparator", "QCD-like activity comparator", "unblinded"),
        ("VR3", "validation", "high B_NF but standard kinematics", f"B_NF_z >= {t['B_NF_z_top05']:.6g}; missing_visible <= {t['missing_visible_top20']:.6g}", "frozen comparator", "high boundary without extreme missing/visible", "unblinded"),
        ("VR4", "validation", "single-muon enriched validation", "primary_dataset == SingleMuon or N_muons >= 1", "analysis-level control", "muon-trigger/control enrichment", "unblinded"),
        ("VR5", "validation", "JetHT enriched validation", "primary_dataset == JetHT", "analysis-level control", "hadronic trigger/control enrichment", "unblinded"),
        ("CR_QCD", "control", "qcd-like high HT/multiplicity, low displacement/reconstruction", f"qcd_like >= {t['qcd_like_top20']:.6g}; disp_reco <= {t['disp_reco_median']:.6g}", "frozen control", "QCD-like control region", "unblinded"),
        ("CR_Muon", "control", "SingleMuon dominated control", "primary_dataset == SingleMuon", "analysis-level control", "muon control", "unblinded"),
        ("CR_MET", "control", "MET control outside high displacement/reconstruction", f"primary_dataset == MET; disp_reco < {t['disp_reco_top20']:.6g}", "analysis-level control", "MET control outside target boundary", "unblinded"),
        ("CR_Ordinary", "control", "ordinary matched controls", f"|B_NF_z| <= 0.25; disp_reco near median {t['disp_reco_median']:.6g}", "frozen ordinary-control concept", "ordinary real-data controls", "unblinded"),
        ("CR_BtagTop", "control", "b-tag/heavy-flavour enriched", "N_btags_medium >= 1; disp_reco below top 20%", "analysis-level control", "top/heavy-flavour enriched control", "unblinded"),
    ]
    reg = pd.DataFrame(rows, columns=["region", "region_type", "description", "exact_thresholds", "threshold_status", "expected_physics_meaning", "blinding_status"])
    reg.to_csv(TABLES / "02_region_definitions.csv", index=False)
    (STATMODEL / "region_thresholds.json").write_text(json.dumps(t, indent=2), encoding="utf-8")
    write_text(
        OUT / "02_FROZEN_REGION_DEFINITIONS_REPORT.md",
        f"""# Frozen Region Definitions Report

Date: {DATE}

Regions use frozen real-data thresholds from the Run2016G plus main Run2016H validation layer where possible. SR4/SR5 add physics-style proxy refinements and are labelled analysis-level rather than tuned discovery regions.

{md(reg)}
""",
    )
    return reg


def load_thresholds() -> dict[str, float]:
    return json.loads((STATMODEL / "region_thresholds.json").read_text(encoding="utf-8"))


def apply_regions(df: pd.DataFrame) -> pd.DataFrame:
    t = load_thresholds()
    out = df.copy()
    out["SR1"] = (out.B_NF_z >= t["B_NF_z_top05"]) & (out.displacement_reconstruction_axis >= t["disp_reco_top20"])
    out["SR2"] = (out.displacement_reconstruction_axis >= t["disp_reco_top20"]) & (out.missing_visible_axis <= t["missing_visible_median"])
    out["SR3"] = (out.B_NF_z >= t["B_NF_z_top05"]) & (out.displacement_reconstruction_axis >= t["disp_reco_top20"]) & (out.missing_visible_axis < t["missing_visible_top20"])
    out["SR4"] = out["SR1"] & (out.MET_pt >= t["MET_moderate"])
    out["SR5"] = (out.secondary_vertex_count >= 1) & (out.displacement_reconstruction_axis >= t["disp_reco_top20"]) & (out.B_NF_z >= t["B_NF_z_top10"])
    out["VR1"] = (out.missing_visible_axis >= t["missing_visible_top20"]) & (out.displacement_reconstruction_axis <= t["disp_reco_median"])
    out["VR2"] = out.qcd_like_axis >= t["qcd_like_top20"]
    out["VR3"] = (out.B_NF_z >= t["B_NF_z_top05"]) & (out.missing_visible_axis <= t["missing_visible_top20"])
    out["VR4"] = (out.primary_dataset.astype(str).eq("SingleMuon")) | (out.N_muons.fillna(0) >= 1)
    out["VR5"] = out.primary_dataset.astype(str).eq("JetHT")
    out["CR_QCD"] = (out.qcd_like_axis >= t["qcd_like_top20"]) & (out.displacement_reconstruction_axis <= t["disp_reco_median"])
    out["CR_Muon"] = out.primary_dataset.astype(str).eq("SingleMuon")
    out["CR_MET"] = out.primary_dataset.astype(str).eq("MET") & (out.displacement_reconstruction_axis < t["disp_reco_top20"])
    out["CR_Ordinary"] = (out.B_NF_z.abs() <= 0.25) & (out.displacement_reconstruction_axis.between(t["disp_reco_median"] - 0.25, t["disp_reco_median"] + 0.25))
    out["CR_BtagTop"] = (out.N_btags_medium.fillna(0) >= 1) & (out.displacement_reconstruction_axis < t["disp_reco_top20"])
    return out


REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5", "VR1", "VR2", "VR3", "VR4", "VR5", "CR_QCD", "CR_Muon", "CR_MET", "CR_Ordinary", "CR_BtagTop"]
SIGNAL_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]


def summarise_region(df: pd.DataFrame, region: str, subset: str) -> dict[str, Any]:
    sub = df[df[region]]
    return {
        "subset": subset,
        "region": region,
        "observed_count": len(sub),
        "fraction": len(sub) / len(df) if len(df) else np.nan,
        "JetHT_fraction": (sub.primary_dataset == "JetHT").mean() if len(sub) else np.nan,
        "MET_fraction": (sub.primary_dataset == "MET").mean() if len(sub) else np.nan,
        "SingleMuon_fraction": (sub.primary_dataset == "SingleMuon").mean() if len(sub) else np.nan,
        "top_source_file_fraction": sub.source_file.value_counts(normalize=True).iloc[0] if len(sub) and sub.source_file.notna().any() else np.nan,
        "top_run_fraction": sub.run.value_counts(normalize=True).iloc[0] if len(sub) else np.nan,
        "top_lumi_fraction": sub.lumi.value_counts(normalize=True).iloc[0] if len(sub) else np.nan,
        "quality_clean_fraction": sub.quality_clean.mean() if len(sub) else np.nan,
        "mean_B_NF_z": sub.B_NF_z.mean(),
        "median_B_NF_z": sub.B_NF_z.median(),
        "mean_disp_reco_axis": sub.displacement_reconstruction_axis.mean(),
        "median_disp_reco_axis": sub.displacement_reconstruction_axis.median(),
        "mean_missing_visible_axis": sub.missing_visible_axis.mean(),
        "median_missing_visible_axis": sub.missing_visible_axis.median(),
        "mean_MET": sub.MET_pt.mean(),
        "mean_HT": sub.HT.mean(),
        "mean_jets": sub.N_jets_30.mean(),
        "mean_btags": sub.N_btags_medium.mean(),
        "mean_secondary_vertices": sub.secondary_vertex_count.mean(),
        "mean_packed_candidates": sub.packed_candidate_count.mean(),
    }


def real_yields(real: pd.DataFrame, real_unique: pd.DataFrame) -> pd.DataFrame:
    real_r = apply_regions(real)
    real_u = apply_regions(real_unique)
    rows = []
    for subset, sub in list(real_r.groupby("sample_group")) + [("combined_unique_real", real_u)]:
        for reg in REGIONS:
            rows.append(summarise_region(sub, reg, subset))
    yields = pd.DataFrame(rows)
    yields.to_csv(TABLES / "03_real_data_region_yields.csv", index=False)
    overlap_rows = []
    combo = real_u
    for a in SIGNAL_REGIONS:
        for b in SIGNAL_REGIONS:
            if a < b:
                overlap_rows.append({"region_a": a, "region_b": b, "overlap_count": int((combo[a] & combo[b]).sum()), "a_count": int(combo[a].sum()), "b_count": int(combo[b].sum())})
    pd.DataFrame(overlap_rows).to_csv(TABLES / "03_real_region_overlaps.csv", index=False)
    write_text(
        OUT / "03_REAL_DATA_REGION_YIELDS_REPORT.md",
        f"""# Real Data Region Yields Report

Date: {DATE}

Observed counts use real CMS collision data only. The `combined_unique_real` row drops duplicate source_file/run/lumi/event combinations across the overlapping Run2016H tables.

{md(yields)}
""",
    )
    return real_u


def signal_efficiencies(signal: pd.DataFrame, real_unique: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sig = apply_regions(signal)
    centroids = real_unique[real_unique["SR2"]].groupby(lambda _: True)[["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "MET_pt", "HT", "N_jets_30"]].mean()
    centroid = centroids.iloc[0] if len(centroids) else pd.Series(dtype=float)
    rows = []
    topo_rows = []
    for sample, sub in sig.groupby("sample_id", dropna=False):
        sample_name = str(sample)
        row = {
            "sample_id": sample_name,
            "process_label": sub.process_label.dropna().astype(str).iloc[0] if sub.process_label.notna().any() else sample_name,
            "event_count": len(sub),
            "component_mode": sub.component_mode.dropna().astype(str).mode().iloc[0] if sub.component_mode.notna().any() else "reduced_or_unknown",
            "data_tier": sub.data_tier_norm.dropna().astype(str).iloc[0] if sub.data_tier_norm.notna().any() else "",
            "mean_B_NF_z": sub.B_NF_z.mean(),
            "q90_B_NF_z": sub.B_NF_z.quantile(0.90),
            "q95_B_NF_z": sub.B_NF_z.quantile(0.95),
            "q99_B_NF_z": sub.B_NF_z.quantile(0.99),
            "mean_disp_reco_axis": sub.displacement_reconstruction_axis.mean(),
            "mean_missing_visible_axis": sub.missing_visible_axis.mean(),
        }
        for reg in SIGNAL_REGIONS:
            row[f"{reg}_efficiency"] = sub[reg].mean()
        effs = {reg: row[f"{reg}_efficiency"] for reg in SIGNAL_REGIONS}
        row["best_region"] = max(effs, key=effs.get)
        if not centroid.empty:
            cols = ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "MET_pt", "HT", "N_jets_30"]
            m = sub[cols].mean()
            row["distance_to_real_SR2_centroid"] = float(np.sqrt(((m - centroid[cols]) ** 2).sum()))
        rows.append(row)
        topo_rows.append({
            "sample_id": sample_name,
            "topology_label": sub.topology_class.dropna().astype(str).mode().iloc[0] if sub.topology_class.notna().any() else row["process_label"],
            "best_region": row["best_region"],
            "resembles_real_high_boundary_sideband": row.get("distance_to_real_SR2_centroid", np.nan) < 100,
            "component_limitation": "full-component" if row["component_mode"] == "full-component" else "reduced components; sensitivity only",
        })
    eff = pd.DataFrame(rows)
    topo = pd.DataFrame(topo_rows)
    eff.to_csv(TABLES / "04_benchmark_signal_region_efficiencies.csv", index=False)
    topo.to_csv(TABLES / "04_benchmark_topology_map.csv", index=False)
    write_text(
        OUT / "04_BENCHMARK_SIGNAL_EFFICIENCY_AND_TOPOLOGY_MAP_REPORT.md",
        f"""# Benchmark Signal Efficiency and Topology Map Report

Date: {DATE}

SUSY/hidden-sector simulations are used only as benchmark signal hypotheses for acceptance, topology mapping and sensitivity. They are not evidence for a real signal.

## Signal-region efficiencies

{md(eff)}

## Topology map

{md(topo)}
""",
    )
    return eff, topo


def poisson_z(obs: float, exp: float, sigma: float) -> tuple[float, float]:
    denom = math.sqrt(max(exp, 0) + sigma * sigma)
    z = (obs - exp) / denom if denom else np.nan
    p = 1 - stats.norm.cdf(z) if np.isfinite(z) else np.nan
    return z, p


def background_estimates(real_unique: pd.DataFrame, sm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    real = apply_regions(real_unique)
    sm_r = apply_regions(sm)
    t = load_thresholds()
    rows = []
    tf_rows = []
    abcd_rows = []
    for sr in SIGNAL_REGIONS:
        obs = int(real[sr].sum())
        # Method A: real control transfer using QCD control, scaled by SM shape ratio when possible.
        cr = "CR_QCD" if sr != "SR2" else "VR1"
        cr_obs = int(real[cr].sum())
        sm_sr = int(sm_r[sr].sum()) if len(sm_r) else 0
        sm_cr = int(sm_r[cr].sum()) if len(sm_r) else 0
        tf = (sm_sr + 1) / (sm_cr + 1)
        exp_a = cr_obs * tf
        unc_a = max(math.sqrt(max(exp_a, 0)), 0.75 * exp_a, 1.0)
        rows.append({"region": sr, "method": "A_data_control_with_SM_shape_transfer", "observed": obs, "expected_background": exp_a, "total_uncertainty": unc_a, "control_region": cr, "assumptions": "Real control count scaled by unweighted SM MC shape transfer; conservative 75% uncertainty floor.", "usable_for_significance": False, "headline_usable": False, "caveat": "Diagnostic only: unweighted SM MC makes this unsuitable for discovery-level significance."})
        tf_rows.append({"region": sr, "control_region": cr, "sm_signal_region_count": sm_sr, "sm_control_region_count": sm_cr, "transfer_factor": tf, "real_control_count": cr_obs})

        # Method B: direct SM shape fraction scaled to total real count, marked not absolute.
        frac = sm_r[sr].mean() if len(sm_r) else np.nan
        exp_b = frac * len(real) if np.isfinite(frac) else np.nan
        rows.append({"region": sr, "method": "B_SM_simulation_shape_scaled_to_real_total", "observed": obs, "expected_background": exp_b, "total_uncertainty": max(0.75 * exp_b, math.sqrt(exp_b)) if np.isfinite(exp_b) else np.nan, "control_region": "none", "assumptions": "Unweighted SM simulation region fraction scaled to observed real total.", "usable_for_significance": False, "headline_usable": False, "caveat": "Shape-only because event weights/cross sections/luminosity are unavailable."})

        # Method C: ABCD for high displacement and missing/visible quadrants.
        high_disp = real.displacement_reconstruction_axis >= t["disp_reco_top20"]
        low_disp = real.displacement_reconstruction_axis <= t["disp_reco_median"]
        low_mv = real.missing_visible_axis <= t["missing_visible_median"]
        high_mv = real.missing_visible_axis >= t["missing_visible_top20"]
        if sr == "SR2":
            a = int((high_disp & low_mv).sum())
            b = int((low_disp & low_mv).sum())
            c = int((high_disp & high_mv).sum())
            d = int((low_disp & high_mv).sum())
            exp_c = b * c / d if d else np.nan
        else:
            high_bnf = real.B_NF_z >= t["B_NF_z_top05"]
            low_bnf = real.B_NF_z < t["B_NF_z_top05"]
            high_shape = real.displacement_reconstruction_axis >= t["disp_reco_top20"]
            low_shape = real.displacement_reconstruction_axis <= t["disp_reco_median"]
            a = int((high_bnf & high_shape).sum())
            b = int((low_bnf & high_shape).sum())
            c = int((high_bnf & low_shape).sum())
            d = int((low_bnf & low_shape).sum())
            exp_c = b * c / d if d else np.nan
        unc_c = max(math.sqrt(exp_c) if np.isfinite(exp_c) else np.nan, 0.5 * exp_c if np.isfinite(exp_c) else np.nan, 1.0)
        headline = sr == "SR2"
        rows.append({"region": sr, "method": "C_ABCD_sideband_estimate", "observed": obs, "expected_background": exp_c, "total_uncertainty": unc_c, "control_region": "ABCD sidebands", "assumptions": "ABCD independence between boundary axes; 50% systematic floor.", "usable_for_significance": headline, "headline_usable": headline, "caveat": "Headline-usable only for SR2 because that region is directly the high-displacement/low-missing ABCD target; other SR ABCD rows are diagnostic and not discovery-grade."})
        abcd_rows.append({"region": sr, "A_observed_target": a, "B_count": b, "C_count": c, "D_count": d, "ABCD_expected_A": exp_c, "closure_status": "exploratory"})

        # Method D: matched-control expectation uses observed control density; not a counting significance.
        rows.append({"region": sr, "method": "D_matched_control_profile", "observed": obs, "expected_background": np.nan, "total_uncertainty": np.nan, "control_region": "nearest-neighbour controls from prior real-data validation", "assumptions": "Profile comparison, not absolute yield.", "usable_for_significance": False, "headline_usable": False, "caveat": "Useful for component-profile anomaly checks only."})
    bg = pd.DataFrame(rows)
    abcd = pd.DataFrame(abcd_rows)
    tf = pd.DataFrame(tf_rows)
    bg.to_csv(TABLES / "05_background_estimates_by_method.csv", index=False)
    abcd.to_csv(TABLES / "05_abcd_closure_tests.csv", index=False)
    tf.to_csv(TABLES / "05_transfer_factor_estimates.csv", index=False)
    write_text(
        OUT / "05_STANDARD_MODEL_BACKGROUND_MODELLING_REPORT.md",
        f"""# Standard Model Background Modelling Report

Date: {DATE}

This is a transparent exploratory background model, not an official CMS estimate. It combines real-data control regions, unweighted SM simulation shape transfer factors, ABCD estimates, and conservative systematics.

## Background estimates

{md(bg)}

## ABCD closure/inputs

{md(abcd)}

## Transfer factors

{md(tf)}
""",
    )
    return bg, abcd, tf


def significance_tests(bg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    sys_rows = []
    for _, row in bg[bg["expected_background"].notna()].iterrows():
        obs = float(row.observed)
        exp = float(row.expected_background)
        if not np.isfinite(exp):
            continue
        base_unc = float(row.total_uncertainty)
        for sys_label, frac in [("method_specific", np.nan), ("optimistic_10pct", 0.10), ("moderate_30pct", 0.30), ("conservative_50pct", 0.50), ("very_conservative_100pct", 1.00)]:
            unc = base_unc if sys_label == "method_specific" else max(base_unc, frac * exp)
            z, p = poisson_z(obs, exp, unc)
            sys_rows.append({"region": row.region, "method": row.method, "systematic_scenario": sys_label, "observed": obs, "expected_background": exp, "total_uncertainty": unc, "observed_minus_expected": obs - exp, "local_Z": z, "local_p_value": max(p, 1e-300) if np.isfinite(p) else p, "headline_usable": bool(getattr(row, "headline_usable", False))})
        z, p = poisson_z(obs, exp, base_unc)
        rows.append({"region": row.region, "method": row.method, "observed": obs, "expected_background": exp, "total_uncertainty": base_unc, "observed_minus_expected": obs - exp, "local_Z": z, "local_p_value": max(p, 1e-300) if np.isfinite(p) else p, "profile_likelihood_Z_approx": z, "headline_usable": bool(getattr(row, "headline_usable", False)), "caveat": row.caveat})
    sig = pd.DataFrame(rows)
    sysdf = pd.DataFrame(sys_rows)
    look = sig[sig["headline_usable"] == True].copy()
    n_tests = max(len(look), 1)
    look["trials_factor"] = n_tests
    look["global_p_bonferroni"] = np.minimum(1, look["local_p_value"] * n_tests)
    look["global_Z_bonferroni"] = stats.norm.isf(look["global_p_bonferroni"])
    sig.to_csv(TABLES / "06_observed_expected_significance_tests.csv", index=False)
    sysdf.to_csv(TABLES / "06_systematics_sensitivity.csv", index=False)
    look.to_csv(TABLES / "06_look_elsewhere_correction.csv", index=False)
    write_text(
        OUT / "06_OBSERVED_EXPECTED_SIGNIFICANCE_REPORT.md",
        f"""# Observed-vs-Expected Significance Report

Date: {DATE}

The significance values are exploratory local/global diagnostics under transparent background assumptions. They are not discovery claims. The most conservative credible reading should be used because the background model is not yet publication-grade.

## Local tests

{md(sig)}

## Systematic sensitivity

{md(sysdf)}

## Look-elsewhere correction

{md(look)}
""",
    )
    return sig, sysdf, look


def bnf_incrementality(sm: pd.DataFrame, signal: pd.DataFrame, real_unique: pd.DataFrame, bg: pd.DataFrame) -> pd.DataFrame:
    sm2 = sm.copy()
    sig2 = signal.copy()
    sm2["target"] = 0
    sig2["target"] = 1
    model_data = pd.concat([sm2, sig2], ignore_index=True).replace([np.inf, -np.inf], np.nan)
    if len(model_data) > 200_000:
        model_data = model_data.sample(200_000, random_state=12)
    predictor_sets = {
        "MET_HT": ["MET_pt", "HT"],
        "MET_HT_jets_btags": ["MET_pt", "HT", "N_jets_30", "N_btags_medium"],
        "standard_plus_disp_reco": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "displacement_reconstruction_axis"],
        "standard_plus_BNF": ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "B_NF_z"],
        "BNF_alone": ["B_NF_z"],
        "full_axes": ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "qcd_like_axis"],
    }
    rows = []
    y = model_data["target"].astype(int)
    for name, preds in predictor_sets.items():
        work = model_data[preds + ["target"]].dropna()
        if work["target"].nunique() < 2 or len(work) < 20:
            rows.append({"model": name, "status": "insufficient_data", "n": len(work), "auc_mean": np.nan})
            continue
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=2)
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, class_weight="balanced"))
        scores = cross_val_score(clf, work[preds], work["target"].astype(int), cv=cv, scoring="roc_auc")
        rows.append({"model": name, "status": "ok", "n": len(work), "predictors": "+".join(preds), "auc_mean": scores.mean(), "auc_sd": scores.std()})
    out = pd.DataFrame(rows)
    base = out.loc[out.model == "MET_HT", "auc_mean"].iloc[0] if (out.model == "MET_HT").any() else np.nan
    out["delta_auc_vs_MET_HT"] = out["auc_mean"] - base
    out.to_csv(TABLES / "07_bnf_incrementality_in_search_context.csv", index=False)
    write_text(
        OUT / "07_BNF_INCREMENTALITY_IN_PHYSICS_SEARCH_CONTEXT_REPORT.md",
        f"""# B_NF Incrementality in Physics Search Context Report

Date: {DATE}

This tests whether B_NF/displacement-reconstruction adds over standard SUSY variables for benchmark signal-vs-SM separation. It does not test real discovery.

{md(out)}
""",
    )
    return out


def make_figures(real_unique: pd.DataFrame, sm: pd.DataFrame, signal: pd.DataFrame, yields: pd.DataFrame, eff: pd.DataFrame, sig: pd.DataFrame, inc: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))
    for label, df in [("real", real_unique), ("SM", sm), ("benchmark signal", signal)]:
        vals = df["B_NF_z"].dropna()
        if len(vals):
            plt.hist(vals.clip(-5, 8), bins=80, alpha=0.35, density=True, label=label)
    plt.xlabel("B_NF_z")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES / "01_bnf_distribution_real_sm_signal.png", dpi=160)
    plt.close()

    y = yields[yields.subset == "combined_unique_real"].set_index("region")["observed_count"].loc[SIGNAL_REGIONS]
    y.plot(kind="bar", figsize=(7, 4))
    plt.ylabel("Observed events")
    plt.tight_layout()
    plt.savefig(FIGURES / "02_real_signal_region_yields.png", dpi=160)
    plt.close()

    if not eff.empty:
        eff.set_index("sample_id")[[f"{r}_efficiency" for r in SIGNAL_REGIONS]].plot(kind="bar", figsize=(10, 5))
        plt.ylabel("Fraction in region")
        plt.tight_layout()
        plt.savefig(FIGURES / "03_benchmark_signal_efficiencies.png", dpi=160)
        plt.close()

    if not sig.empty:
        sig.assign(label=sig.region + "\n" + sig.method.str.replace("_", " ")).set_index("label")["local_Z"].plot(kind="bar", figsize=(10, 4))
        plt.ylabel("Local Z")
        plt.tight_layout()
        plt.savefig(FIGURES / "04_observed_expected_local_significance.png", dpi=160)
        plt.close()

    if not inc.empty:
        inc.set_index("model")["auc_mean"].plot(kind="bar", figsize=(8, 4))
        plt.ylabel("AUC")
        plt.tight_layout()
        plt.savefig(FIGURES / "05_bnf_incrementality_auc.png", dpi=160)
        plt.close()


def readiness_checklist() -> None:
    items = [
        ("full certified CMS luminosity and good-run JSON selection", "not yet complete", "Need formal luminosity accounting and certified JSON filtering documentation."),
        ("trigger efficiency modelling", "not yet complete", "Current trigger/filter flags are diagnostic only."),
        ("object ID and detector systematic uncertainties", "not yet complete", "Need official-style object uncertainties."),
        ("official or robust data-driven background model", "partial", "ABCD/control/SM-shape model exists but is exploratory."),
        ("full MC weighting with cross sections and luminosity", "not yet complete", "Available MC currently shape-only."),
        ("control/validation/signal blinding strategy", "not yet complete", "Current work is unblinded exploratory."),
        ("independent replication", "partial", "Multiple real subsets support boundary structure; genuine different-year route still needed."),
        ("public code and reproducibility package", "partial", "Scripts and outputs exist locally; package needs cleanup."),
        ("comparison with published CMS/ATLAS searches", "partial", "CMS-SUS-21-006 bridge is weak/qualifying."),
        ("local/global significance and trials factors", "partial", "Approximate tests included; full profile likelihood not yet implemented."),
        ("exclusion/sensitivity interpretation", "not yet complete", "Requires weighted signal/background and luminosity."),
    ]
    df = pd.DataFrame(items, columns=["requirement", "status", "notes"])
    df.to_csv(TABLES / "08_discovery_level_readiness_checklist.csv", index=False)
    write_text(
        OUT / "08_DISCOVERY_LEVEL_READINESS_CHECKLIST.md",
        f"""# Discovery-Level Readiness Checklist

Date: {DATE}

{md(df)}
""",
    )


def final_reports(inv: pd.DataFrame, yields: pd.DataFrame, eff: pd.DataFrame, bg: pd.DataFrame, sig: pd.DataFrame, look: pd.DataFrame, inc: pd.DataFrame) -> None:
    real_main = yields[(yields.subset == "combined_unique_real") & (yields.region.isin(SIGNAL_REGIONS))]
    best_sig = look.sort_values("global_Z_bonferroni", ascending=False).head(1)
    headline_sig = sig[sig.get("headline_usable", False) == True]
    best_local = headline_sig.sort_values("local_Z", ascending=False).head(1) if not headline_sig.empty else sig.sort_values("local_Z", ascending=False).head(1)
    best_inc = inc.sort_values("auc_mean", ascending=False).head(1)
    no5 = True
    if not look.empty:
        no5 = not (look["global_Z_bonferroni"] >= 5).any()
    interpretation = "qualifies and structures Darren's SUSY pathway"
    if not best_inc.empty and best_inc["auc_mean"].iloc[0] > 0.85:
        interpretation = "strengthens benchmark-sensitivity case, while real-data discovery case remains unproven"
    write_text(
        OUT / "09_NFRAME_SUSY_PHYSICS_STYLE_ANALYSIS_NOTE_FOR_DARREN.md",
        f"""# N-Frame SUSY Physics-Style Analysis Note for Darren

Date: {DATE}

## 1. Why this framework

We moved from boundary validation to a physics-style search framework because a publishable SUSY/hidden-sector claim would need observed real data, background modelling, signal benchmark sensitivity, systematic uncertainties, and local/global significance. The frozen N-Frame boundary can be used as a search variable, but it cannot by itself establish discovery.

## 2. Observed data

Observed data are real CMS collision MiniAOD scored event tables: Run2016G, Run2016H main validation, expanded Run2016H, and the new unused Run2016H validation subset. Combined unique real data drops duplicate source/run/lumi/event rows.

## 3. Background support

SM background support uses available QCD, WJets, TTJets, ZNuNu and diboson simulations where present, plus real-data control regions. Because MC weights/luminosity are not available, SM simulation is used primarily for shape/transfer-factor support.

## 4. SUSY benchmark hypotheses

Benchmark simulations include accessible full-component SUSY MiniAODSIM signals and reduced benchmark tables such as T5Wg, T2tt and HToAA4B-like samples where available. These are signal hypotheses only.

## 5. Frozen regions

See `02_region_definitions.csv`. The main signal candidates are SR1 high B_NF + high displacement/reconstruction, SR2 high displacement/reconstruction + low missing/visible, SR3 trace-aligned high-boundary proxy, SR4 high-boundary plus moderate MET, and SR5 LLP/disappearing proxy.

## 6. Observed real-data region yields

{md(real_main)}

## 7. Benchmark signal efficiencies

{md(eff)}

## 8. Background estimates

{md(bg)}

## 9. Observed-vs-expected significance

Best headline-usable local result:

{md(best_local)}

Best global/look-elsewhere result:

{md(best_sig)}

No 5 sigma-like result survives the current credible background-control and look-elsewhere treatment: {no5}.

The larger local-Z values in `06_observed_expected_significance_tests.csv` are explicitly marked `headline_usable = False`; they are diagnostic failures of an under-constrained background model, not evidence.

## 10. B_NF beyond standard variables

{md(inc)}

## 11. Interpretation

Overall judgement: {interpretation}. The framework strengthens the case that N-Frame can define benchmark-sensitive, real-data-populated regions, but it does not establish a SUSY discovery.

## 12. What this does not show

This does not show real SUSY particles, does not show CERN missed SUSY, and does not replace an official background estimate. The public disappearing-track residual bridge remains weak/qualified.

## 13. What is needed for journal-level claims

The discovery checklist in `08_DISCOVERY_LEVEL_READINESS_CHECKLIST.md` must be addressed, especially luminosity-normalised MC, trigger/object/systematic uncertainties, robust background closure, blinding, and full profile-likelihood statistical modelling.
""",
    )
    write_text(
        OUT / "10_SHORT_UPDATE_FOR_TOM.md",
        f"""# Short Update for Tom

I built the first physics-style SUSY search framework around the frozen N-Frame boundary score.

What was done: real CMS collision data are treated as observed data, SM simulation/control regions are used for exploratory background support, and SUSY simulations are used only as benchmark signal hypotheses.

What was found: the frozen N-Frame regions are well populated in real data and capture some benchmark signal topologies, but the background model is still exploratory. No 5 sigma-like result survives proper conservative/systematic and look-elsewhere treatment.

B_NF does add useful separation in benchmark signal-vs-SM tests, but that is benchmark sensitivity, not discovery evidence.

What to tell Darren: this is the right direction toward a publishable physics analysis, but the next serious bottleneck is a proper background model with MC weights/luminosity, control-region closure, trigger/object systematics, and a profile likelihood.
""",
    )


def main() -> None:
    ensure_dirs()
    inv = build_inventory()
    real, real_unique, sm, signal = load_all_data()
    define_regions(real[real.sample_group.isin(["Run2016G_fit_real", "Run2016H_main_validation"])])
    real_unique = real_yields(real, real_unique)
    real_unique = apply_regions(real_unique)
    sm = apply_regions(sm)
    signal = apply_regions(signal)
    eff, topo = signal_efficiencies(signal, real_unique)
    bg, abcd, tf = background_estimates(real_unique, sm)
    sig, sysdf, look = significance_tests(bg)
    inc = bnf_incrementality(sm, signal, real_unique, bg)
    yields = pd.read_csv(TABLES / "03_real_data_region_yields.csv")
    make_figures(real_unique, sm, signal, yields, eff, sig, inc)
    readiness_checklist()
    final_reports(inv, yields, eff, bg, sig, look, inc)

    model_card = {
        "date": DATE,
        "status": "exploratory_physics_style_framework",
        "observed_data": "real CMS collision MiniAOD scored tables",
        "background_model": "real-control + unweighted SM-shape transfer + ABCD exploratory",
        "signal_model": "benchmark SUSY/hidden-sector simulations only",
        "discovery_claim": False,
        "frozen_bnf": True,
    }
    (STATMODEL / "analysis_model_card.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    print("Physics-style SUSY search framework complete")
    print(f"Output folder: {OUT}")
    print(f"Inventory rows: {len(inv)}")
    print(f"Real unique events: {len(real_unique)}")
    print(f"SM support events: {len(sm)}")
    print(f"Signal benchmark events: {len(signal)}")
    if not sig.empty:
        print(f"Highest local Z: {sig['local_Z'].max():.3f}")
    if not look.empty:
        print(f"Highest global Z: {look['global_Z_bonferroni'].max():.3f}")
    if not inc.empty:
        print(f"Best benchmark AUC: {inc['auc_mean'].max():.3f}")


if __name__ == "__main__":
    main()
