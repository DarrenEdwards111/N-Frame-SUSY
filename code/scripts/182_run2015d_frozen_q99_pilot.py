from __future__ import annotations

import json
import subprocess
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import urllib3
from scipy.stats import chi2, norm


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_run2015d_frozen_q99_pilot"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_run2015d_frozen_q99_pilot")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
# CMS Open Data recommends CMSSW_7_6_7 for these 2015 MiniAOD records.
# On this Windows/Docker setup the old slc6 image cannot launch bash/sh, while
# the already validated 10_6_30 image can read the 2015 MiniAOD files. This is
# therefore an extraction compatibility workaround, not a change to the frozen
# N-Frame region.
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest"
RUNNER = "run_one_sample_python_compat.sh"

FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
FREEZE_MANIFEST = ROOT / "outputs_frozen_q99_1to2jet_fresh_validation/FROZEN_Q99_1TO2JET_REGION_MANIFEST.json"

RECORDS = {
    "MET": 24123,
    "HTMHT": 24125,
    "JetHT": 24124,
    "SingleMuon": 24119,
}
FILES_PER_DATASET = 3
MIN_SELECTION_MB = 80.0
MAX_SELECTION_MB = 180.0
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
MIDPOINTS = {
    "q000_050": 0.25,
    "q050_080": 0.65,
    "q080_090": 0.85,
    "q090_095": 0.925,
    "q095_0975": 0.9625,
    "q0975_099": 0.9825,
    "q099_100": 0.995,
}
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
SIDE_REPORT_BANDS = ["q080_090", "q090_095"]
SIGNAL_BAND = "q099_100"
REL_UNC = 0.127


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, DOWNLOAD_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


def safe(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


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
    return mean, float(np.sqrt(max(var, 1e-12)))


def fetch_record_files(record_id: int) -> list[dict]:
    rec = requests.get(f"https://opendata.cern.ch/api/records/{record_id}", timeout=60).json()
    files: list[dict] = []
    for index in rec["metadata"].get("_file_indices", []):
        files.extend(index.get("files", []))
    return sorted(files, key=lambda f: int(f["size"]))


def build_file_manifest() -> pd.DataFrame:
    rows = []
    for dataset, record_id in RECORDS.items():
        all_files = fetch_record_files(record_id)
        sized = [f for f in all_files if MIN_SELECTION_MB <= int(f["size"]) / 1e6 <= MAX_SELECTION_MB]
        selected_files = sized[:FILES_PER_DATASET] if len(sized) >= FILES_PER_DATASET else all_files[:FILES_PER_DATASET]
        for rank, f in enumerate(selected_files, start=1):
            local = DOWNLOAD_ROOT / dataset / str(record_id) / f["filename"]
            rows.append(
                {
                    "primary_dataset": dataset,
                    "record_id": record_id,
                    "rank_by_size": rank,
                    "filename": f["filename"],
                    "size_bytes": int(f["size"]),
                    "size_mb": int(f["size"]) / 1e6,
                    "url": uri_to_https(f["uri"]),
                    "local_path": str(local),
                    "selected_before_results": True,
                    "selection_rule": f"first {FILES_PER_DATASET} files by size within {MIN_SELECTION_MB}-{MAX_SELECTION_MB} MB, fallback to smallest files",
                }
            )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "01_run2015d_selected_file_manifest.csv", index=False)
    return manifest


def download_file(row: pd.Series) -> Path:
    target = Path(row["local_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == int(row["size_bytes"]):
        return target
    urllib3.disable_warnings()
    tmp = target.with_suffix(target.suffix + ".part")
    with requests.get(row["url"], stream=True, timeout=90, verify=False) as r:
        r.raise_for_status()
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(1024 * 1024 * 8):
                if chunk:
                    fh.write(chunk)
    tmp.replace(target)
    return target


def run_cmssw(row: pd.Series, local_path: Path) -> Path:
    dataset = str(row["primary_dataset"])
    stem = Path(row["filename"]).stem
    run_id = f"run2015d_{safe(dataset)}_{stem}"
    log_path = OUT / f"{run_id}_cmssw.log"
    container_path = f"/data/{dataset}/{int(row['record_id'])}/{row['filename']}"
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={container_path}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=100; "
        "export NFRAME_MAXEVENTS_FULL=-1; "
        f"bash /work/{RUNNER}"
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
        raise RuntimeError(f"CMSSW extraction failed for {run_id}; see {log_path}")
    df = pd.read_csv(raw)
    out_csv = SOURCES / f"{run_id}_event_features.csv"
    df.insert(0, "sample_id", run_id)
    df.insert(1, "primary_dataset", dataset)
    df.insert(2, "record_id", int(row["record_id"]))
    df.insert(3, "source_file", row["filename"])
    df.insert(4, "source_file_stem", stem)
    df.insert(5, "local_input_path_or_container_path", f"{local_path} | {container_path}")
    df.insert(6, "event_index_within_file", range(len(df)))
    df["run_era"] = "Run2015D"
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df.to_csv(out_csv, index=False)
    return out_csv


def extract_all(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in manifest.iterrows():
        local = download_file(row)
        out_csv = SOURCES / f"run2015d_{safe(str(row['primary_dataset']))}_{Path(row['filename']).stem}_event_features.csv"
        status = "existing"
        error = ""
        if not out_csv.exists():
            try:
                out_csv = run_cmssw(row, local)
                status = "extracted"
            except Exception as exc:
                status = "failed"
                error = str(exc)
        events = 0
        if out_csv.exists():
            events = sum(1 for _ in out_csv.open("r", encoding="utf-8", errors="replace")) - 1
        rows.append(
            {
                **row.to_dict(),
                "local_size_bytes": local.stat().st_size,
                "output_csv": str(out_csv) if out_csv.exists() else "",
                "events_extracted": max(events, 0),
                "status": status,
                "error": error,
            }
        )
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "02_run2015d_extraction_audit.csv", index=False)
    return audit


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
    x_df = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = x_df.median().to_numpy(float)
    x = x_df.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
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
    score = sm["common_missing_resid_visible_only"].to_numpy(float)
    score_edges = {}
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


def z_unc(obs: float, exp: float, rel: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel * exp) ** 2, 1e-12)))


def summarize_counts(counts: pd.DataFrame, sideband_rms: float) -> dict:
    rel = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
    side = counts[counts["score_band"].isin(SIDE_REPORT_BANDS)]
    sig = counts[counts["score_band"].eq(SIGNAL_BAND)]
    out = {
        "sideband_log_rms": sideband_rms,
        "relative_uncertainty_used": rel,
    }
    for prefix, df, exp_col in [
        ("sideband_80_95_official", side, "expected_official"),
        ("q99_official", sig, "expected_official"),
        ("q99_shape", sig, "expected_shape"),
    ]:
        obs = float(df["observed"].sum())
        exp = float(df[exp_col].sum())
        out[f"{prefix}_observed"] = obs
        out[f"{prefix}_expected"] = exp
        out[f"{prefix}_obs_exp"] = obs / exp if exp > 0 else np.inf
        out[f"{prefix}_Z"] = z_unc(obs, exp, rel)
    return out


def counts_for(real_sub: pd.DataFrame, sm_sub: pd.DataFrame, labels: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    for met_bin, band in product(range(MET_BINS), SCORE_BANDS):
        r_bin = real_sub[real_sub["met_bin"].eq(met_bin)]
        s_bin = sm_sub[sm_sub["met_bin"].eq(met_bin)]
        if len(r_bin) < 5 or s_bin["event_weight"].sum() <= 0:
            continue
        frac = float(s_bin.loc[s_bin["score_band"].eq(band), "event_weight"].sum() / s_bin["event_weight"].sum())
        rows.append(
            {
                **labels,
                "met_bin": met_bin,
                "score_band": band,
                "met_bin_n": len(r_bin),
                "observed": int((r_bin["score_band"].eq(band)).sum()),
                "sm_fraction": frac,
                "expected_official": len(r_bin) * frac,
                "midpoint": MIDPOINTS[band],
            }
        )
    counts = pd.DataFrame(rows)
    if counts.empty:
        return counts, {**labels, "status": "no_counts"}
    fit = counts[counts["score_band"].isin(SIDEBAND_FIT_BANDS)]
    oe = (fit["observed"].to_numpy(float) + 0.5) / (fit["expected_official"].to_numpy(float) + 0.5)
    x = fit["midpoint"].to_numpy(float) - 0.90
    y = np.log(np.clip(oe, 1e-6, np.inf))
    weights = np.sqrt(np.clip(fit["observed"].to_numpy(float), 1.0, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * weights[:, None], y * weights, rcond=None)
    sideband_rms = float(np.sqrt(np.average((y - design @ coef) ** 2, weights=weights)))
    counts["shape_correction"] = np.exp(coef[0] + (counts["midpoint"] - 0.90) * coef[1])
    counts["expected_shape"] = counts["expected_official"] * counts["shape_correction"]
    return counts, {**labels, **summarize_counts(counts, sideband_rms), "status": "ok"}


def stouffer(zs: pd.Series) -> float:
    vals = zs.replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
    if len(vals) == 0:
        return np.nan
    return float(vals.sum() / np.sqrt(len(vals)))


def fisher(zs: pd.Series) -> float:
    vals = zs.replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
    if len(vals) == 0:
        return np.nan
    ps = np.clip(norm.sf(vals), 1e-300, 1.0)
    p = chi2.sf(-2 * np.log(ps).sum(), 2 * len(ps))
    return float(norm.isf(p))


def run_validation(audit: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sm = read_sm()
    params, sm = fit_visible_residual(sm)
    met_edges, score_edges = define_bins(sm)
    sm = assign_bands(sm, met_edges, score_edges)
    sm["jet_bin_frozen"] = pd.cut(
        sm["N_jets_30"].fillna(0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)

    frames = []
    for _, row in audit[audit["status"].isin(["existing", "extracted"])].iterrows():
        path = Path(row["output_csv"])
        if not path.exists():
            continue
        df = pd.read_csv(path, low_memory=False)
        frames.append(df)
    if not frames:
        raise RuntimeError("No extracted Run2015D feature files available.")
    real = pd.concat(frames, ignore_index=True)
    real = assign_bands(apply_visible_residual(real, params), met_edges, score_edges)
    real["jet_bin_frozen"] = pd.cut(
        real["N_jets_30"].fillna(0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    real.to_csv(SOURCES / "run2015d_all_selected_real_events_scored.csv", index=False)

    counts_frames = []
    summaries = []
    for dataset in sorted(real["primary_dataset"].dropna().unique()):
        for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
            real_sub = real[(real["primary_dataset"].eq(dataset)) & (real["jet_bin_frozen"].eq(jet_bin))]
            sm_sub = sm[sm["jet_bin_frozen"].eq(jet_bin)]
            counts, summary = counts_for(real_sub, sm_sub, {"primary_dataset": dataset, "unit": "dataset_total", "source_file": "ALL", "jet_bin": jet_bin})
            if not counts.empty:
                counts_frames.append(counts)
            summaries.append(summary)
        for source_file, real_file in real[real["primary_dataset"].eq(dataset)].groupby("source_file"):
            real_sub = real_file[real_file["jet_bin_frozen"].eq("1to2jets")]
            sm_sub = sm[sm["jet_bin_frozen"].eq("1to2jets")]
            counts, summary = counts_for(real_sub, sm_sub, {"primary_dataset": dataset, "unit": "source_file", "source_file": source_file, "jet_bin": "1to2jets"})
            if not counts.empty:
                counts_frames.append(counts)
            summaries.append(summary)

    counts_all = pd.concat(counts_frames, ignore_index=True) if counts_frames else pd.DataFrame()
    summary_df = pd.DataFrame(summaries)
    counts_all.to_csv(TABLES / "03_run2015d_frozen_q99_score_band_counts.csv", index=False)
    summary_df.to_csv(TABLES / "04_run2015d_frozen_q99_summary.csv", index=False)

    sig = summary_df[
        (summary_df["unit"].eq("dataset_total"))
        & (summary_df["jet_bin"].eq("1to2jets"))
        & (summary_df["primary_dataset"].isin(["MET", "HTMHT"]))
        & (summary_df["status"].eq("ok"))
    ].copy()
    controls = summary_df[
        (summary_df["unit"].eq("dataset_total"))
        & (summary_df["jet_bin"].eq("1to2jets"))
        & (summary_df["primary_dataset"].isin(["JetHT", "SingleMuon"]))
        & (summary_df["status"].eq("ok"))
    ].copy()
    combo = pd.DataFrame(
        [
            {
                "combined_unit": "Run2015D_MET_plus_HTMHT_pilot",
                "datasets": ",".join(sig["primary_dataset"].astype(str)),
                "n_dataset_summaries": len(sig),
                "stouffer_Z_q99_shape": stouffer(sig["q99_shape_Z"]) if not sig.empty else np.nan,
                "fisher_Z_q99_shape": fisher(sig["q99_shape_Z"]) if not sig.empty else np.nan,
                "min_signal_dataset_Z": float(sig["q99_shape_Z"].min()) if not sig.empty else np.nan,
                "max_control_dataset_Z": float(controls["q99_shape_Z"].max()) if not controls.empty else np.nan,
                "interpretation": "pilot_only_uses_2016_derived_weighted_sm_reference_and_cmssw_10630_extraction_workaround_not_final_2015_sm_model",
            }
        ]
    )
    combo.to_csv(TABLES / "05_run2015d_signal_control_combined_summary.csv", index=False)
    return real, summary_df, combo


def write_report(manifest: pd.DataFrame, audit: pd.DataFrame, summary: pd.DataFrame, combo: pd.DataFrame) -> None:
    freeze = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8")) if FREEZE_MANIFEST.exists() else {}
    signal = summary[(summary["unit"].eq("dataset_total")) & (summary["jet_bin"].eq("1to2jets")) & (summary["primary_dataset"].isin(["MET", "HTMHT"]))]
    controls = summary[(summary["unit"].eq("dataset_total")) & (summary["jet_bin"].eq("1to2jets")) & (summary["primary_dataset"].isin(["JetHT", "SingleMuon"]))]
    min_signal_z = float(signal["q99_shape_Z"].min()) if len(signal) else np.nan
    max_control_z = float(controls["q99_shape_Z"].max()) if len(controls) else np.nan
    if np.isfinite(min_signal_z) and min_signal_z >= 5 and np.isfinite(max_control_z) and max_control_z < 3:
        conclusion = "Pilot-positive with controls approximately closed."
    elif np.isfinite(min_signal_z) and min_signal_z >= 5:
        conclusion = "Signal-like streams are pilot-positive, but controls do not close cleanly. This is not discovery-grade."
    elif np.isfinite(max_control_z) and max_control_z >= 3:
        conclusion = "Mixed/control-limited: HTMHT/MET show positive tail structure, but the minimum signal-stream Z is below 5 and JetHT control fails badly. This is not discovery-grade."
    else:
        conclusion = "The frozen region did not produce a robust positive Run2015D pilot."
    report = f"""# Run2015D Frozen Q99 1-2 Jet Pilot Validation

## Purpose

This is the first cross-era CMS pilot test after the Run2016 frozen-region result. It applies the frozen Q99 one-to-two-jet N-Frame missing-vs-visible boundary definition to a small, preselected sample of CMS Run2015D MiniAOD files.

## Frozen Definition Used

```json
{json.dumps(freeze.get("region_definition", {}), indent=2)}
```

## Important Caveat

This is not yet a discovery-grade 2015 result. The event extraction uses real 2015 CMS collision data, but the tail thresholds and weighted SM reference are still the project-level Run-2 SM reference built before this 2015 pilot. A final 2015 claim needs 2015-matched luminosity-weighted SM backgrounds and certified luminosity/systematics.

The CMS Open Data records recommend CMSSW_7_6_7 for 2015 MiniAOD. In this local Windows/Docker environment the old slc6 7.6.7 image failed to launch bash/sh, so extraction used the already validated CMSSW_10_6_30 image as a compatibility workaround. A spot test confirmed that CMSSW_10_6_30 could open and read the Run2015D MiniAOD file. This must be repeated in official CMSSW_7_6_7 or a CMS Open Data VM before any final claim.

## Preselected Files

{manifest.to_markdown(index=False)}

## Extraction Audit

{audit[["primary_dataset","filename","size_mb","events_extracted","status","error"]].to_markdown(index=False)}

## Frozen Q99 1-2 Jet Dataset-Level Results

Practical conclusion: **{conclusion}**

Signal-like missing-energy streams:

{signal[["primary_dataset","jet_bin","q99_shape_observed","q99_shape_expected","q99_shape_obs_exp","q99_shape_Z","sideband_80_95_official_obs_exp","relative_uncertainty_used","status"]].to_markdown(index=False)}

Controls:

{controls[["primary_dataset","jet_bin","q99_shape_observed","q99_shape_expected","q99_shape_obs_exp","q99_shape_Z","sideband_80_95_official_obs_exp","relative_uncertainty_used","status"]].to_markdown(index=False)}

Combined pilot summary:

{combo.to_markdown(index=False)}

## Interpretation

Current outcome: {conclusion}

If MET and HTMHT are positive while JetHT and SingleMuon are not, this supports the frozen CMS boundary-trace candidate in an independent year. If controls, especially JetHT, also show a large q99 excess, this points to shared stream/background/shape-modelling problems rather than a closed signal-region discovery. If MET/HTMHT do not replicate, the Run2016 candidate weakens.

This pilot deliberately uses a small selected file set, so it should be treated as a go/no-go screen for a larger Run2015D extraction, not as the final breakthrough result.
"""
    (REPORTS / "01_RUN2015D_FROZEN_Q99_PILOT_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Run2015D Frozen Q99 Pilot

Applied the frozen Q99 1-2 jet N-Frame missing-vs-visible boundary region to a small preselected Run2015D MiniAOD sample.

Combined signal-like pilot:

{combo.to_markdown(index=False)}

Dataset-level 1-2 jet q99 shape results:

{summary[(summary["unit"].eq("dataset_total")) & (summary["jet_bin"].eq("1to2jets"))][["primary_dataset","q99_shape_observed","q99_shape_expected","q99_shape_obs_exp","q99_shape_Z","status"]].to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_RUN2015D_FROZEN_Q99_PILOT.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    manifest = build_file_manifest()
    audit = extract_all(manifest)
    failed = audit[audit["status"].eq("failed")]
    if len(failed) == len(audit):
        raise SystemExit("All Run2015D extractions failed; see *_cmssw.log in output directory.")
    _, summary, combo = run_validation(audit)
    write_report(manifest, audit, summary, combo)
    print("RUN2015D FROZEN Q99 PILOT COMPLETE")
    print(combo.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
