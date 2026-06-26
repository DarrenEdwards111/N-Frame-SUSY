from __future__ import annotations

import json
import subprocess
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import urllib3
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_frozen_q99_1to2jet_fresh_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_frozen_q99_1to2jet_fresh_validation")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"

FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
KNOWN_REAL_FILES = [
    ROOT / "data/processed/nframe_parameter_fit/real_data_with_fitted_nframe_boundary_score.csv",
    ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv",
    ROOT / "data/processed/expanded_run2016h_miniaod_full/expanded_run2016h_miniaod_with_fitted_nframe_score.csv",
    ROOT / "data/processed/new_independent_real_miniaod_validation/full/new_real_events_with_frozen_BNF.csv",
]

FEATURES = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_btags_medium",
    "N_muons",
    "N_electrons",
    "secondary_vertex_count",
    "packed_candidate_count",
]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = ["q000_050", "q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099", "q099_100"]
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
FINAL_BAND = "q099_100"
REL_UNC = 0.127
CMS_OPEN_RECORD_MET_RUN2016H_MINIAOD = 30542


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, DOWNLOAD_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


def safe(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


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
    return mean, np.sqrt(max(var, 1e-12))


def write_freeze_manifest() -> dict:
    manifest = {
        "freeze_name": "NFRAME_Q99_1TO2JET_MET_BOUNDARY_TRACE_V1",
        "freeze_date": "2026-06-11",
        "status": "frozen_before_fresh_validation",
        "region_definition": {
            "primary_dataset": "MET",
            "score": "common_missing_resid_visible_only",
            "condition_variable": "MET_pt",
            "met_bins": 10,
            "topology": "N_jets_30 in [1, 2]",
            "signal_band": "q099_100",
            "signal_band_plain_english": "top 1% N-Frame missing-vs-visible boundary score inside each MET bin",
            "sideband_shape_fit_bands": ["q050_080", "q080_090", "q090_095"],
            "sideband_control_band_for_reporting": "q080_095",
        },
        "frozen_interpretation_rules": [
            "Use real CMS collision data only.",
            "Do not use simulated samples as observed data.",
            "Do not call this a SUSY classifier.",
            "Do not claim direct SUSY particle discovery.",
            "Report the q99 1-2 jet trace as an observable boundary anomaly candidate only.",
        ],
        "development_evidence_source": str(
            ROOT
            / "outputs_q99_1to2jet_tail_candidate_replication/reports/01_Q99_1TO2JET_FINAL_TAIL_CANDIDATE_REPLICATION_REPORT.md"
        ),
        "fresh_validation_priority": [
            "CMS Run2017/Run2018 MET MiniAOD open data if available",
            "otherwise a disjoint unused CMS Run2016H MET MiniAOD file",
        ],
    }
    (OUT / "FROZEN_Q99_1TO2JET_REGION_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (REPORTS / "00_FROZEN_Q99_1TO2JET_REGION.md").write_text(
        "# Frozen Q99 1-2 Jet N-Frame Region\n\n"
        "This file freezes the candidate before any fresh validation run.\n\n"
        f"```json\n{json.dumps(manifest, indent=2)}\n```\n",
        encoding="utf-8",
    )
    return manifest


def cern_api_search_audit() -> pd.DataFrame:
    rows = []
    for query in [
        "CMS MET Run2017 MINIAOD",
        "CMS MET Run2018 MINIAOD",
        "MET Run2017 MINIAOD",
        "MET Run2018 MINIAOD",
        "Run2017 MET",
        "Run2018 MET",
    ]:
        r = requests.get("https://opendata.cern.ch/api/records/", params={"q": query, "size": 10}, timeout=30)
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        rows.append(
            {
                "query": query,
                "hits_returned": len(hits),
                "total_hits": data.get("hits", {}).get("total", 0),
                "usable_for_fresh_validation": len(hits) > 0,
                "note": "No record found by API search" if not hits else "Inspect records manually before use",
            }
        )
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_cern_run2017_2018_met_availability_audit.csv", index=False)
    return audit


def known_used_filenames() -> set[str]:
    used: set[str] = set()
    for path in KNOWN_REAL_FILES:
        if not path.exists():
            continue
        try:
            header = pd.read_csv(path, nrows=0).columns
            if "source_file" in header:
                used.update(pd.read_csv(path, usecols=["source_file"])["source_file"].dropna().astype(str).unique())
        except Exception:
            continue
    return used


def fetch_met_run2016h_files() -> list[dict]:
    rec = requests.get(f"https://opendata.cern.ch/api/records/{CMS_OPEN_RECORD_MET_RUN2016H_MINIAOD}", timeout=30).json()
    files: list[dict] = []
    for index in rec["metadata"].get("_file_indices", []):
        files.extend(index.get("files", []))
    return sorted(files, key=lambda f: f["size"])


def select_fresh_file() -> pd.Series:
    used = known_used_filenames()
    rows = []
    for f in fetch_met_run2016h_files():
        filename = f["filename"]
        local = DOWNLOAD_ROOT / "met" / str(CMS_OPEN_RECORD_MET_RUN2016H_MINIAOD) / filename
        row = {
            "record_id": CMS_OPEN_RECORD_MET_RUN2016H_MINIAOD,
            "primary_dataset": "MET",
            "run_era": "Run2016H",
            "data_tier": "MINIAOD",
            "filename": filename,
            "size_bytes": int(f["size"]),
            "size_gb": f["size"] / 1e9,
            "url": uri_to_https(f["uri"]),
            "already_used_in_q99_development_or_validation": filename in used,
            "local_path": str(local),
            "selected": False,
        }
        rows.append(row)
    candidates = pd.DataFrame(rows)
    unused = candidates[~candidates["already_used_in_q99_development_or_validation"]].copy()
    if unused.empty:
        raise SystemExit("No unused Run2016H MET MiniAOD files found.")
    selected = unused.sort_values("size_bytes").iloc[0].copy()
    candidates.loc[candidates["filename"].eq(selected["filename"]), "selected"] = True
    candidates.to_csv(TABLES / "02_fresh_run2016h_met_candidate_files.csv", index=False)
    pd.DataFrame([selected]).to_csv(TABLES / "03_selected_fresh_run2016h_met_file.csv", index=False)
    return selected


def download_selected(row: pd.Series) -> Path:
    target = Path(row["local_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == int(row["size_bytes"]):
        return target
    urllib3.disable_warnings()
    with requests.get(row["url"], stream=True, timeout=60, verify=False) as r:
        r.raise_for_status()
        tmp = target.with_suffix(target.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(1024 * 1024 * 8):
                if chunk:
                    fh.write(chunk)
        tmp.replace(target)
    return target


def run_cmssw_extraction(row: pd.Series, local_path: Path) -> Path:
    stem = Path(row["filename"]).stem
    run_id = f"frozen_q99_fresh_run2016h_met_{stem}"
    log_path = OUT / f"{run_id}_cmssw.log"
    container_path = f"/data/met/{int(row['record_id'])}/{row['filename']}"
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={container_path}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
        "export NFRAME_MAXEVENTS_FULL=-1; "
        "bash /work/run_one_sample.sh"
    )
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{CMSSW_WORK}:/work",
        "-v",
        f"{DOWNLOAD_ROOT}:/data",
        IMAGE,
        "bash",
        "-lc",
        cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    if proc.returncode != 0 or not raw.exists():
        raise SystemExit(f"CMSSW extraction failed; see {log_path}")
    df = pd.read_csv(raw)
    out_csv = SOURCES / f"{run_id}_event_features.csv"
    df.insert(0, "sample_id", run_id)
    df.insert(1, "primary_dataset", "MET")
    df.insert(2, "record_id", int(row["record_id"]))
    df.insert(3, "source_file", row["filename"])
    df.insert(4, "source_file_stem", stem)
    df.insert(5, "local_input_path_or_container_path", f"{local_path} | {container_path}")
    df.insert(6, "event_index_within_file", range(len(df)))
    df["run_era"] = "Run2016H"
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df.to_csv(out_csv, index=False)
    pd.DataFrame(
        [
            {
                "record_id": int(row["record_id"]),
                "filename": row["filename"],
                "local_path": str(local_path),
                "expected_size_bytes": int(row["size_bytes"]),
                "actual_size_bytes": local_path.stat().st_size,
                "events_extracted": len(df),
                "output_csv": str(out_csv),
                "cmssw_log": str(log_path),
            }
        ]
    ).to_csv(TABLES / "04_fresh_run2016h_met_extraction_manifest.csv", index=False)
    return out_csv


def read_sm() -> pd.DataFrame:
    header = pd.read_csv(FULL_WEIGHTED_SM, nrows=0).columns
    use = [c for c in FEATURES + ["event_weight"] if c in header]
    sm = pd.read_csv(FULL_WEIGHTED_SM, usecols=use, low_memory=False)
    for col in FEATURES + ["event_weight"]:
        if col not in sm:
            sm[col] = 1.0 if col == "event_weight" else 0.0
        sm[col] = pd.to_numeric(sm[col], errors="coerce")
    sm["event_weight"] = sm["event_weight"].fillna(1.0)
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    return sm


def fit_visible_residual(sm: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    weights = sm["event_weight"].to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), weights)
    sm = sm.copy()
    sm["common_missing_z"] = (sm["log1p_MET_pt"] - mean_met) / sd_met
    x = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = x.median().to_numpy(float)
    x = x.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
    y = sm["common_missing_z"].to_numpy(float)
    sw = np.sqrt(np.clip(weights, 1e-12, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    sm["common_missing_resid_visible_only"] = y - design @ coef
    return {"mean_logmet": mean_met, "sd_logmet": sd_met, "visible_median": med, "coef": coef}, sm


def apply_visible_residual(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    for col in FEATURES:
        if col not in out:
            out[col] = 0.0
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["common_missing_z"] = (out["log1p_MET_pt"] - params["mean_logmet"]) / params["sd_logmet"]
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["visible_median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["common_missing_resid_visible_only"] = out["common_missing_z"].to_numpy(float) - design @ params["coef"]
    return out


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    weights = sm["event_weight"].to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, weights, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score_edges = {}
    score = sm["common_missing_resid_visible_only"].to_numpy(float)
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        mask = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[mask], weights[mask], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_bands(df: pd.DataFrame, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["met_bin"] = pd.cut(out["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(out), None, dtype=object)
    score = out["common_missing_resid_visible_only"].to_numpy(float)
    met_bins = out["met_bin"].to_numpy()
    for i in range(MET_BINS):
        mask = met_bins == i
        edges = score_edges[i]
        for band_name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = band_name
    out["score_band"] = band
    return out[out["score_band"].notna()].copy()


def shape_corrected_fresh_test(fresh_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sm = read_sm()
    params, sm = fit_visible_residual(sm)
    met_edges, score_edges = define_bins(sm)
    sm = assign_bands(sm, met_edges, score_edges)
    fresh = assign_bands(apply_visible_residual(pd.read_csv(fresh_csv), params), met_edges, score_edges)
    sm_topo = sm[(sm["N_jets_30"].fillna(0) >= 1) & (sm["N_jets_30"].fillna(0) <= 2)].copy()
    fresh_topo = fresh[(fresh["N_jets_30"].fillna(0) >= 1) & (fresh["N_jets_30"].fillna(0) <= 2)].copy()
    rows = []
    for met_bin, band in product(range(MET_BINS), SCORE_BANDS):
        r_bin = fresh_topo[fresh_topo["met_bin"].eq(met_bin)]
        s_bin = sm_topo[sm_topo["met_bin"].eq(met_bin)]
        if len(r_bin) < 5 or s_bin["event_weight"].sum() <= 0:
            continue
        frac = float(s_bin.loc[s_bin["score_band"].eq(band), "event_weight"].sum() / s_bin["event_weight"].sum())
        rows.append(
            {
                "met_bin": met_bin,
                "score_band": band,
                "real_met_topology_bin_n": len(r_bin),
                "observed": int((r_bin["score_band"].eq(band)).sum()),
                "sm_fraction": frac,
                "expected_official_shape": len(r_bin) * frac,
            }
        )
    counts = pd.DataFrame(rows)
    fit = counts[counts["score_band"].isin(SIDEBAND_FIT_BANDS)].copy()
    midpoint = {"q050_080": 0.65, "q080_090": 0.85, "q090_095": 0.925, "q099_100": 0.995}
    fit["midpoint"] = fit["score_band"].map(midpoint)
    oe = (fit["observed"].to_numpy(float) + 0.5) / (fit["expected_official_shape"].to_numpy(float) + 0.5)
    x = fit["midpoint"].to_numpy(float) - 0.90
    y = np.log(np.clip(oe, 1e-6, np.inf))
    weights = np.sqrt(np.clip(fit["observed"].to_numpy(float), 1.0, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * weights[:, None], y * weights, rcond=None)
    sideband_rms = float(np.sqrt(np.average((y - design @ coef) ** 2, weights=weights)))
    counts["midpoint"] = counts["score_band"].map({**midpoint, "q000_050": 0.25, "q095_0975": 0.9625, "q0975_099": 0.9825})
    counts["sideband_shape_correction"] = np.exp(coef[0] + (counts["midpoint"] - 0.90) * coef[1])
    counts["expected_shape_extrapolated"] = counts["expected_official_shape"] * counts["sideband_shape_correction"]
    tail = counts[counts["score_band"].eq(FINAL_BAND)]
    sideband = counts[counts["score_band"].isin(["q080_090", "q090_095"])]
    obs = float(tail["observed"].sum())
    exp = float(tail["expected_shape_extrapolated"].sum())
    rel = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
    z = float((obs - exp) / np.sqrt(max(exp + (rel * exp) ** 2, 1e-12)))
    summary = pd.DataFrame(
        [
            {
                "fresh_sample": Path(fresh_csv).name,
                "fresh_events_total": len(fresh),
                "fresh_events_1to2jets": len(fresh_topo),
                "sideband_80_95_observed": int(sideband["observed"].sum()),
                "sideband_80_95_expected_official": float(sideband["expected_official_shape"].sum()),
                "sideband_80_95_observed_over_expected": float(sideband["observed"].sum() / sideband["expected_official_shape"].sum()),
                "q99_observed": obs,
                "q99_expected_shape_extrapolated": exp,
                "q99_observed_over_expected": float(obs / exp) if exp > 0 else np.inf,
                "sideband_log_rms": sideband_rms,
                "relative_uncertainty_used": rel,
                "q99_Z_with_shape_uncertainty": z,
                "passes_5sigma": z >= 5.0,
            }
        ]
    )
    fresh_topo.to_csv(SOURCES / "fresh_scored_1to2jet_met_events.csv", index=False)
    counts.to_csv(TABLES / "05_fresh_q99_1to2jet_score_band_counts.csv", index=False)
    summary.to_csv(TABLES / "06_fresh_q99_1to2jet_validation_summary.csv", index=False)
    return counts, summary


def write_report(api_audit: pd.DataFrame, selected: pd.Series, summary: pd.DataFrame) -> None:
    report = f"""# Frozen Q99 1-2 Jet Fresh Validation

## What Was Frozen

The region was frozen before this fresh validation:

- MET primary dataset
- 1-2 reconstructed jets with `N_jets_30`
- `common_missing_resid_visible_only` N-Frame score
- top 1% score band inside each raw MET bin
- broad sideband trend fitted only below the signal band

## Run2017/Run2018 Open-Data Availability

{api_audit.to_markdown(index=False)}

No CMS Run2017/Run2018 MET MiniAOD record was found by the CERN Open Data API search used here, so the fallback was a disjoint unused Run2016H MET MiniAOD file.

## Fresh Fallback File

{pd.DataFrame([selected]).to_markdown(index=False)}

## Fresh Validation Result

{summary.to_markdown(index=False)}

## Interpretation

This is a frozen-region test on a newly selected disjoint Run2016H MET MiniAOD file. It is not a new-era validation because Run2017/Run2018 MET MiniAOD open data was not found by the API search.

If the fresh q99 Z is above 5 sigma, the Q99 1-2 jet candidate strengthens. If it is below 5 sigma, the candidate remains interesting but is not yet robust enough for a discovery-style claim.
"""
    (REPORTS / "01_FROZEN_Q99_1TO2JET_FRESH_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Frozen Q99 1-2 Jet Fresh Validation

Frozen region: MET stream, 1-2 jets, top 1% N-Frame missing-vs-visible boundary score inside raw MET bins.

Run2017/Run2018 MET MiniAOD API search found no usable records, so we used a disjoint unused Run2016H MET MiniAOD file.

Fresh validation result:

{summary.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_FROZEN_Q99_1TO2JET_FRESH_VALIDATION.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    write_freeze_manifest()
    api_audit = cern_api_search_audit()
    selected = select_fresh_file()
    local_path = download_selected(selected)
    fresh_csv = run_cmssw_extraction(selected, local_path)
    _, summary = shape_corrected_fresh_test(fresh_csv)
    write_report(api_audit, selected, summary)
    print("FROZEN Q99 1-2 JET FRESH VALIDATION COMPLETE")
    print(summary.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
