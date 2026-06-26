from __future__ import annotations

import json
import math
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import urllib3
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
PYDEPS = ROOT / ".atlas_pydeps"
OUT = ROOT / "outputs_atlas_open_data_q99_analogue"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\atlas_nframe_q99_analogue")

ATLAS_RECORD = 15001
LUMI_FB = 10.0
LUMI_PB = LUMI_FB * 1000.0

DATA_FILES = [
    "data_A.1lep.root",
]

# Compact SM set: high-pT W/Z+jets plus top/diboson components. This is an analogue template,
# not the full ATLAS 1-lepton SM prediction.
SM_FILE_KEYS = [
    "mc_410025.single_top_schan.1lep.root",
    "mc_410013.single_top_wtchan.1lep.root",
    "mc_410011.single_top_tchan.1lep.root",
    "mc_364181.Wenu_PTV280_500_BFilter.1lep.root",
    "mc_364180.Wenu_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364179.Wenu_PTV280_500_CVetoBVeto.1lep.root",
    "mc_364183.Wenu_PTV1000_E_CMS.1lep.root",
    "mc_364182.Wenu_PTV500_1000.1lep.root",
    "mc_364167.Wmunu_PTV280_500_BFilter.1lep.root",
    "mc_364166.Wmunu_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364165.Wmunu_PTV280_500_CVetoBVeto.1lep.root",
    "mc_364169.Wmunu_PTV1000_E_CMS.1lep.root",
    "mc_364168.Wmunu_PTV500_1000.1lep.root",
    "mc_364195.Wtaunu_PTV280_500_BFilter.1lep.root",
    "mc_364194.Wtaunu_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364193.Wtaunu_PTV280_500_CVetoBVeto.1lep.root",
    "mc_364197.Wtaunu_PTV1000_E_CMS.1lep.root",
    "mc_364196.Wtaunu_PTV500_1000.1lep.root",
    "mc_364124.Zee_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364127.Zee_PTV1000_E_CMS.1lep.root",
    "mc_364126.Zee_PTV500_1000.1lep.root",
    "mc_364110.Zmumu_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364113.Zmumu_PTV1000_E_CMS.1lep.root",
    "mc_364112.Zmumu_PTV500_1000.1lep.root",
    "mc_364138.Ztautau_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364141.Ztautau_PTV1000_E_CMS.1lep.root",
    "mc_364140.Ztautau_PTV500_1000.1lep.root",
    "mc_363358.WqqZll.1lep.root",
    "mc_363356.ZqqZll.1lep.root",
    "mc_363490.llll.1lep.root",
    "mc_363491.lllv.1lep.root",
    "mc_363492.llvv.1lep.root",
]

MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = ["q000_050", "q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099", "q099_100"]
MIDPOINTS = {"q000_050": 0.25, "q050_080": 0.65, "q080_090": 0.85, "q090_095": 0.925, "q095_0975": 0.9625, "q0975_099": 0.9825, "q099_100": 0.995}
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
SIDE_REPORT_BANDS = ["q080_090", "q090_095"]
SIGNAL_BAND = "q099_100"
REL_UNC = 0.30


def add_pydeps() -> None:
    import sys

    if str(PYDEPS) not in sys.path:
        sys.path.insert(0, str(PYDEPS))


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS, SOURCES, DOWNLOAD_ROOT]:
        p.mkdir(parents=True, exist_ok=True)


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


def family_from_key(key: str) -> str:
    if "Wenu" in key or "Wmunu" in key or "Wtaunu" in key:
        return "Wjets"
    if "Zee" in key or "Zmumu" in key or "Ztautau" in key:
        return "Zjets"
    if "single_top" in key or "ttbar" in key:
        return "top"
    if any(x in key for x in ["Wqq", "Zqq", "llll", "lllv", "llvv"]):
        return "diboson"
    return "other"


def fetch_record_files() -> pd.DataFrame:
    r = requests.get(f"https://opendata.cern.ch/api/records/{ATLAS_RECORD}", timeout=30)
    r.raise_for_status()
    files = r.json()["metadata"]["_files"]
    rows = []
    wanted = set(DATA_FILES + SM_FILE_KEYS)
    for f in files:
        key = f["key"]
        if key not in wanted:
            continue
        rows.append(
            {
                "key": key,
                "size_bytes": int(f["size"]),
                "size_gb": f["size"] / 1e9,
                "uri": f["uri"],
                "url": uri_to_https(f["uri"]),
                "role": "real_data" if key.startswith("data_") else "sm_mc",
                "family": "real_data" if key.startswith("data_") else family_from_key(key),
                "local_path": str(DOWNLOAD_ROOT / key),
            }
        )
    manifest = pd.DataFrame(rows).sort_values(["role", "family", "key"])
    missing = wanted - set(manifest["key"])
    if missing:
        raise SystemExit(f"Missing ATLAS keys in record {ATLAS_RECORD}: {sorted(missing)}")
    manifest.to_csv(TABLES / "00_atlas_download_manifest.csv", index=False)
    return manifest


def download_files(manifest: pd.DataFrame) -> pd.DataFrame:
    urllib3.disable_warnings()
    rows = []
    for row in manifest.itertuples(index=False):
        target = Path(row.local_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.stat().st_size != int(row.size_bytes):
            with requests.get(row.url, stream=True, verify=False, timeout=60) as r:
                r.raise_for_status()
                tmp = target.with_suffix(target.suffix + ".part")
                with tmp.open("wb") as fh:
                    for chunk in r.iter_content(1024 * 1024 * 16):
                        if chunk:
                            fh.write(chunk)
                tmp.replace(target)
        rows.append({**row._asdict(), "downloaded": target.exists(), "actual_size_bytes": target.stat().st_size})
        pd.DataFrame(rows).to_csv(TABLES / "01_atlas_download_status.csv", index=False)
        print(f"downloaded/verified {target.name} {target.stat().st_size / 1e9:.3f} GB")
    return pd.DataFrame(rows)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    mean = float(np.average(values[mask], weights=weights[mask]))
    var = float(np.average((values[mask] - mean) ** 2, weights=weights[mask]))
    return mean, math.sqrt(max(var, 1e-12))


def scalar_first(arr, default=0.0):
    import awkward as ak

    filled = ak.fill_none(ak.firsts(arr), default)
    return ak.to_numpy(filled)


def extract_file(path: Path, role: str, family: str, key: str) -> pd.DataFrame:
    add_pydeps()
    import awkward as ak
    import uproot

    branches = [
        "runNumber",
        "eventNumber",
        "mcWeight",
        "scaleFactor_PILEUP",
        "scaleFactor_ELE",
        "scaleFactor_MUON",
        "scaleFactor_BTAG",
        "scaleFactor_LepTRIGGER",
        "trigE",
        "trigM",
        "lep_n",
        "lep_pt",
        "met_et",
        "jet_n",
        "jet_pt",
        "jet_MV2c10",
        "XSection",
        "SumWeights",
    ]
    tree = uproot.open(path)["mini"]
    arrays = tree.arrays([b for b in branches if b in tree.keys()], library="ak")
    n = len(arrays["eventNumber"])
    jet_pt = arrays["jet_pt"]
    jet_n_30 = ak.sum(jet_pt > 30_000, axis=1)
    jet_n_50 = ak.sum(jet_pt > 50_000, axis=1)
    ht = ak.sum(jet_pt[jet_pt > 30_000], axis=1) / 1000.0
    leading_jet_pt = scalar_first(jet_pt / 1000.0, 0.0)
    btags = ak.sum(arrays["jet_MV2c10"] > 0.8244273, axis=1) if "jet_MV2c10" in arrays.fields else np.zeros(n)
    lep_pt = scalar_first(arrays["lep_pt"] / 1000.0, 0.0)
    df = pd.DataFrame(
        {
            "source_file": key,
            "role": role,
            "family": family,
            "run": np.asarray(arrays["runNumber"]),
            "event": np.asarray(arrays["eventNumber"]),
            "MET_pt": np.asarray(arrays["met_et"]) / 1000.0,
            "N_jets_30": np.asarray(jet_n_30, dtype=float),
            "N_jets_50": np.asarray(jet_n_50, dtype=float),
            "HT": np.asarray(ht, dtype=float),
            "leading_jet_pt": leading_jet_pt,
            "N_btags_medium": np.asarray(btags, dtype=float),
            "N_leptons": np.asarray(arrays["lep_n"], dtype=float),
            "leading_lepton_pt": lep_pt,
            "trigE": np.asarray(arrays["trigE"], dtype=float),
            "trigM": np.asarray(arrays["trigM"], dtype=float),
        }
    )
    if role == "sm_mc":
        weight = np.asarray(arrays["mcWeight"], dtype=float)
        for sf in ["scaleFactor_PILEUP", "scaleFactor_ELE", "scaleFactor_MUON", "scaleFactor_BTAG", "scaleFactor_LepTRIGGER"]:
            if sf in arrays.fields:
                weight = weight * np.asarray(arrays[sf], dtype=float)
        xsec = np.asarray(arrays["XSection"], dtype=float) if "XSection" in arrays.fields else np.ones(n)
        sumw = np.asarray(arrays["SumWeights"], dtype=float) if "SumWeights" in arrays.fields else np.ones(n)
        df["event_weight"] = weight * xsec * LUMI_PB / np.clip(sumw, 1e-12, np.inf)
    else:
        df["event_weight"] = 1.0
    return df


def extract_features(downloaded: pd.DataFrame) -> pd.DataFrame:
    frames = []
    audit = []
    for row in downloaded.itertuples(index=False):
        path = Path(row.local_path)
        df = extract_file(path, row.role, row.family, row.key)
        out = SOURCES / f"{Path(row.key).stem}_features.csv"
        df.to_csv(out, index=False)
        frames.append(df)
        audit.append({"key": row.key, "role": row.role, "family": row.family, "events": len(df), "feature_csv": str(out)})
        pd.DataFrame(audit).to_csv(TABLES / "02_atlas_feature_extraction_audit.csv", index=False)
        print(f"extracted {row.key}: {len(df)} events")
    all_df = pd.concat(frames, ignore_index=True)
    all_df.to_csv(SOURCES / "atlas_1lep_real_and_sm_features.csv", index=False)
    return all_df


def fit_score(sm: pd.DataFrame, real: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sm = sm.copy()
    real = real.copy()
    for frame in [sm, real]:
        frame["log1p_MET_pt"] = np.log1p(frame["MET_pt"].clip(lower=0))
        frame["log1p_HT"] = np.log1p(frame["HT"].clip(lower=0))
    visible = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_leptons", "leading_lepton_pt"]
    weights = sm["event_weight"].abs().clip(lower=1e-12).to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), weights)
    
    # Calculate medians from sm
    x_sm = sm[visible].copy()
    for v in visible:
        x_sm[v] = pd.to_numeric(x_sm[v], errors="coerce")
    med = x_sm.median()
    x_sm = x_sm.fillna(med).to_numpy(float)
    
    y = ((sm["log1p_MET_pt"] - mean_met) / sd_met).to_numpy(float)
    sw = np.sqrt(weights)
    design = np.column_stack([np.ones(len(x_sm)), x_sm])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    
    for frame in [sm, real]:
        frame["atlas_missing_z"] = (frame["log1p_MET_pt"] - mean_met) / sd_met
        # convert and fill iteratively to save memory
        xx = np.zeros((len(frame), len(visible)), dtype=float)
        for i, v in enumerate(visible):
            xx[:, i] = pd.to_numeric(frame[v], errors="coerce").fillna(med[v]).to_numpy(float)
        frame["atlas_missing_resid_visible_only"] = frame["atlas_missing_z"].to_numpy(float) - np.column_stack([np.ones(len(xx)), xx]) @ coef
    return sm, real


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    w = sm["event_weight"].abs().clip(lower=1e-12).to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, w, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score = sm["atlas_missing_resid_visible_only"].to_numpy(float)
    score_edges = {}
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        mask = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[mask], w[mask], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_bands(df: pd.DataFrame, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    met_bin = pd.cut(df["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(df), None, dtype=object)
    score = df["atlas_missing_resid_visible_only"].to_numpy(float)
    met_bin_arr = met_bin.to_numpy()
    for i in range(MET_BINS):
        mask = met_bin_arr == i
        edges = score_edges[i]
        for name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = name
    df["met_bin"] = met_bin
    df["score_band"] = band
    # only return subset of columns to save memory, or just return the filtered frame
    return df[df["score_band"].notna()]


def z_unc(obs: float, exp: float, rel: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel * exp) ** 2, 1e-12)))


def run_region(real: pd.DataFrame, sm: pd.DataFrame, jet_bin: str) -> tuple[pd.DataFrame, dict]:
    if jet_bin == "1to2jets":
        r = real[(real["N_jets_30"] >= 1) & (real["N_jets_30"] <= 2)]
        s = sm[(sm["N_jets_30"] >= 1) & (sm["N_jets_30"] <= 2)]
    elif jet_bin == "0jet":
        r = real[real["N_jets_30"] == 0]
        s = sm[sm["N_jets_30"] == 0]
    elif jet_bin == "3to4jets":
        r = real[(real["N_jets_30"] >= 3) & (real["N_jets_30"] <= 4)]
        s = sm[(sm["N_jets_30"] >= 3) & (sm["N_jets_30"] <= 4)]
    else:
        r = real[real["N_jets_30"] >= 5]
        s = sm[sm["N_jets_30"] >= 5]
    rows = []
    for met_bin, band in product(range(MET_BINS), SCORE_BANDS):
        rb = r[r["met_bin"].eq(met_bin)]
        sb = s[s["met_bin"].eq(met_bin)]
        if len(rb) < 5 or sb["event_weight"].abs().sum() <= 0:
            continue
        sw = sb["event_weight"].abs()
        frac = float(sw[sb["score_band"].eq(band)].sum() / sw.sum())
        rows.append({"jet_bin": jet_bin, "met_bin": met_bin, "score_band": band, "observed": int((rb["score_band"].eq(band)).sum()), "met_bin_n": len(rb), "sm_fraction": frac, "expected_official_shape": len(rb) * frac, "midpoint": MIDPOINTS[band]})
    counts = pd.DataFrame(rows)
    fit = counts[counts["score_band"].isin(SIDEBAND_FIT_BANDS)].copy()
    if len(fit) < 4:
        return counts, {"jet_bin": jet_bin, "usable": False}
    oe = (fit["observed"].to_numpy(float) + 0.5) / (fit["expected_official_shape"].to_numpy(float) + 0.5)
    x = fit["midpoint"].to_numpy(float) - 0.90
    y = np.log(np.clip(oe, 1e-6, np.inf))
    ww = np.sqrt(np.clip(fit["observed"].to_numpy(float), 1.0, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * ww[:, None], y * ww, rcond=None)
    sideband_rms = float(np.sqrt(np.average((y - design @ coef) ** 2, weights=ww)))
    counts["shape_correction"] = np.exp(coef[0] + (counts["midpoint"] - 0.90) * coef[1])
    counts["expected_shape"] = counts["expected_official_shape"] * counts["shape_correction"]
    rel = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
    signal = counts[counts["score_band"].eq(SIGNAL_BAND)]
    side = counts[counts["score_band"].isin(SIDE_REPORT_BANDS)]
    obs = float(signal["observed"].sum())
    exp = float(signal["expected_shape"].sum())
    side_obs = float(side["observed"].sum())
    side_exp = float(side["expected_official_shape"].sum())
    summary = {
        "jet_bin": jet_bin,
        "usable": True,
        "real_events": int(len(r)),
        "sideband_80_95_observed": side_obs,
        "sideband_80_95_expected_official": side_exp,
        "sideband_80_95_obs_exp": side_obs / side_exp if side_exp > 0 else np.inf,
        "q99_observed": obs,
        "q99_expected_shape": exp,
        "q99_obs_exp": obs / exp if exp > 0 else np.inf,
        "sideband_log_rms": sideband_rms,
        "relative_uncertainty_used": rel,
        "q99_Z": z_unc(obs, exp, rel),
    }
    return counts, summary


def main() -> None:
    ensure_dirs()
    manifest = fetch_record_files()
    downloaded = download_files(manifest)
    feature_audit = TABLES / "02_atlas_feature_extraction_audit.csv"
    all_features_path = SOURCES / "atlas_1lep_real_and_sm_features.csv"
    if all_features_path.exists() and feature_audit.exists():
        df = pd.read_csv(all_features_path, low_memory=False)
    else:
        df = extract_features(downloaded)
    real = df[df["role"].eq("real_data")].copy()
    sm = df[df["role"].eq("sm_mc")].copy()
    sm_scored, real_scored = fit_score(sm, real)
    met_edges, score_edges = define_bins(sm_scored)
    real_scored = assign_bands(real_scored, met_edges, score_edges)
    sm_scored = assign_bands(sm_scored, met_edges, score_edges)
    real_scored.to_csv(SOURCES / "atlas_real_data_A_scored.csv", index=False)
    sm_scored.to_csv(SOURCES / "atlas_compact_sm_scored.csv", index=False)

    counts_frames = []
    summaries = []
    for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
        counts, summary = run_region(real_scored, sm_scored, jet_bin)
        if not counts.empty:
            counts_frames.append(counts)
        summaries.append(summary)
    counts_df = pd.concat(counts_frames, ignore_index=True)
    summary_df = pd.DataFrame(summaries)
    counts_df.to_csv(TABLES / "03_atlas_q99_score_band_counts.csv", index=False)
    summary_df.to_csv(TABLES / "04_atlas_q99_analogue_summary.csv", index=False)

    source_summary = downloaded.groupby(["role", "family"], as_index=False).agg(files=("key", "count"), gb=("size_gb", "sum"), events=("actual_size_bytes", "count"))
    report = f"""# ATLAS Open Data Q99 1-2 Jet N-Frame Analogue

## Purpose

Test whether the CMS frozen Q99 1-2 jet missing-vs-visible boundary trace has an independent-detector analogue in public ATLAS 13 TeV Open Data.

## Important Difference From CMS

This is not an exact CMS MiniAOD replication. ATLAS Open Data 2020 is provided as preselected flat ROOT ntuples. This run uses the public exactly-one-lepton ATLAS collection because it has real data, MET, jets, leptons, b-tag information and matching SM MC.

## Inputs

Record: CERN Open Data ATLAS record {ATLAS_RECORD}

{source_summary.to_markdown(index=False)}

## Frozen Analogue Rule

- ATLAS real data, `data_A.1lep.root`
- 1-2 jets with pT > 30 GeV
- missing-vs-visible residual score: residual of log(MET) after HT, jet count, b-tags, lepton count and leading lepton pT
- raw-MET-binned score bands
- signal band: top 1%, q99-100
- sideband-shape correction fitted from 50-95%
- jet-bin controls: 0 jet, 3-4 jets, 5+ jets

## Result

{summary_df.to_markdown(index=False)}

## Interpretation

This is an ATLAS analogue check, not a final discovery test. A positive q99 result in the 1-2 jet bin with non-discovery controls would support detector-independent behaviour. A null or control-dominated result would mean the CMS trace does not simply transfer to this ATLAS preselected channel.
"""
    (REPORTS / "01_ATLAS_OPEN_DATA_Q99_ANALOGUE_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: ATLAS Q99 Analogue

We tested an ATLAS Open Data analogue of the frozen CMS Q99 1-2 jet N-Frame boundary trace.

Result:

{summary_df.to_markdown(index=False)}

This is not exact CMS replication because ATLAS Open Data uses preselected flat ntuples, here the exactly-one-lepton channel.
"""
    (REPORTS / "02_SHORT_UPDATE_ATLAS_Q99_ANALOGUE.md").write_text(short, encoding="utf-8")
    print("ATLAS Q99 ANALOGUE COMPLETE")
    print(summary_df.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
