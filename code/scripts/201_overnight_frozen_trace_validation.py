from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import urllib3
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_overnight_frozen_trace_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
LOGS = OUT / "logs"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_overnight_frozen_trace_validation")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest"
RUNNER = "run_one_sample_python_compat.sh"

RECORDS = [
    {"era": "Run2016G", "primary_dataset": "HTMHT", "record_id": 30507},
    {"era": "Run2016G", "primary_dataset": "MET", "record_id": 30509},
    {"era": "Run2016G", "primary_dataset": "JetHT", "record_id": 30508},
    {"era": "Run2016G", "primary_dataset": "SingleMuon", "record_id": 30513},
    {"era": "Run2016H", "primary_dataset": "HTMHT", "record_id": 30540},
    {"era": "Run2016H", "primary_dataset": "MET", "record_id": 30542},
    {"era": "Run2016H", "primary_dataset": "JetHT", "record_id": 30541},
    {"era": "Run2016H", "primary_dataset": "SingleMuon", "record_id": 30546},
    {"era": "Run2015D", "primary_dataset": "HTMHT", "record_id": 24125},
    {"era": "Run2015D", "primary_dataset": "MET", "record_id": 24123},
    {"era": "Run2015D", "primary_dataset": "JetHT", "record_id": 24124},
    {"era": "Run2015D", "primary_dataset": "SingleMuon", "record_id": 24119},
]

QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]
COMPONENTS = [
    "observer_projection",
    "physical_projection",
    "algebraic_projection",
    "ordinary_qcd_axis",
    "leptonic_control_axis",
]
FROZEN_WEIGHTS = {
    "observer_projection": 0.3137254901960784,
    "physical_projection": 0.3137254901960784,
    "algebraic_projection": 0.0,
    "ordinary_qcd_axis": -0.27450980392156865,
    "leptonic_control_axis": -0.09803921568627451,
}
SIGNAL_STAGES = {"MET": "0jet", "HTMHT": "1to2jets"}
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
REL_UNC = 0.30
TARGET_GB = 145.0
CHUNK_MAX_GB = 8.0
CHUNK_MAX_FILES = 4
MIN_FILE_GB = 0.05
MAX_FILE_GB = 2.25

# Deliberate validation budget, not a blind bulk download.
# Signals get the most data; controls get enough to reject trigger artefacts;
# Run2015D is kept smaller because it is useful cross-era stress, but many files
# are tiny and expensive to process one by one.
RECORD_TARGET_GB = {
    ("Run2016G", "MET"): 16.0,
    ("Run2016G", "HTMHT"): 16.0,
    ("Run2016G", "JetHT"): 10.0,
    ("Run2016G", "SingleMuon"): 10.0,
    ("Run2016H", "MET"): 16.0,
    ("Run2016H", "HTMHT"): 16.0,
    ("Run2016H", "JetHT"): 10.0,
    ("Run2016H", "SingleMuon"): 10.0,
    ("Run2015D", "MET"): 8.0,
    ("Run2015D", "HTMHT"): 8.0,
    ("Run2015D", "JetHT"): 5.0,
    ("Run2015D", "SingleMuon"): 5.0,
}


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, LOGS, DOWNLOAD_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


def safe(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


def existing_root_names() -> set[str]:
    names = set()
    root = Path(r"D:\cern_open_data")
    if root.exists():
        for path in root.rglob("*.root"):
            if DOWNLOAD_ROOT in path.parents:
                continue
            names.add(path.name)
    return names


def fetch_record_files(record_id: int) -> tuple[str, list[dict]]:
    urllib3.disable_warnings()
    rec = requests.get(f"https://opendata.cern.ch/api/records/{record_id}", timeout=60, verify=False)
    rec.raise_for_status()
    meta = rec.json()["metadata"]
    files = []
    for index in meta.get("_file_indices", []):
        files.extend(index.get("files", []))
    return meta.get("title", ""), sorted(files, key=lambda f: int(f["size"]))


def build_manifest(target_gb: float = TARGET_GB) -> pd.DataFrame:
    seen = existing_root_names()
    selected: list[dict[str, object]] = []
    total = 0.0
    for rec in RECORDS:
        title, files = fetch_record_files(int(rec["record_id"]))
        candidates = []
        era = str(rec["era"])
        dataset = str(rec["primary_dataset"])
        record_target = float(RECORD_TARGET_GB.get((era, dataset), 8.0))
        for f in files:
            size_gb = int(f["size"]) / 1e9
            if f["filename"] in seen:
                continue
            if size_gb < MIN_FILE_GB or size_gb > MAX_FILE_GB:
                continue
            candidates.append(
                {
                    **rec,
                    "record_title": title,
                    "filename": f["filename"],
                    "size_bytes": int(f["size"]),
                    "size_gb": size_gb,
                    "uri": f["uri"],
                    "https_url": uri_to_https(f["uri"]),
                    "local_path": str(DOWNLOAD_ROOT / rec["era"] / rec["primary_dataset"] / str(rec["record_id"]) / f["filename"]),
                }
            )
        # Prefer medium files so each validation stream has enough events without
        # relying on the largest EOS files, which are more prone to long stalls.
        candidates = sorted(candidates, key=lambda r: (abs(float(r["size_gb"]) - 1.25), str(r["filename"])))
        record_total = 0.0
        for row in candidates:
            if total + float(row["size_gb"]) > target_gb:
                break
            if record_total >= record_target:
                break
            if record_total > 0 and record_total + float(row["size_gb"]) > record_target + 1.5:
                continue
            row = dict(row)
            row["selection_order"] = len(selected) + 1
            row["selected_before_results"] = True
            row["record_target_gb"] = record_target
            row["selection_rule"] = (
                "smart validation manifest: processable CMS MiniAOD only; skip files already used elsewhere under D:/cern_open_data; "
                "prefer fewer medium/large unused files; allocate larger budgets to MET/HTMHT signals, smaller budgets to controls and Run2015D"
            )
            selected.append(row)
            total += float(row["size_gb"])
            record_total += float(row["size_gb"])

    manifest = pd.DataFrame(selected)
    manifest.to_csv(TABLES / "00_selected_overnight_root_manifest.csv", index=False)
    return manifest


def download_one(row: pd.Series) -> dict[str, object]:
    target = Path(row["local_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = int(row["size_bytes"])
    if target.exists() and target.stat().st_size == expected:
        return {"download_status": "already_present", "downloaded_bytes": expected, "error": ""}
    tmp = target.with_suffix(target.suffix + ".part")
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is required for resumable overnight downloads")
    cmd = [
        curl,
        "-L",
        "-k",
        "--fail",
        "--retry",
        "8",
        "--retry-delay",
        "10",
        "--connect-timeout",
        "30",
        "--speed-time",
        "240",
        "--speed-limit",
        "1024",
        "--silent",
        "--show-error",
        "-C",
        "-",
        "-o",
        str(tmp),
        str(row["https_url"]),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    last_size = -1
    started = time.time()
    stagnant_reports = 0
    while True:
        code = proc.poll()
        current = tmp.stat().st_size if tmp.exists() else 0
        if current != last_size:
            pct = 100.0 * current / expected if expected else 0.0
            print(f"[download] {target.name}: {current / 1e9:.3f}/{expected / 1e9:.3f} GB ({pct:.1f}%)", flush=True)
            last_size = current
            stagnant_reports = 0
        else:
            stagnant_reports += 1
            print(f"[download] {target.name}: still waiting/progress unchanged at {current / 1e9:.3f} GB", flush=True)
        if code is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            if code != 0:
                return {"download_status": "failed", "downloaded_bytes": current, "error": stderr[-1000:]}
            break
        if stagnant_reports >= 20 and current == 0:
            proc.kill()
            stderr = proc.stderr.read() if proc.stderr else ""
            return {"download_status": "failed_no_initial_progress", "downloaded_bytes": current, "error": stderr[-1000:] or "no initial progress after 10 minutes"}
        time.sleep(30)
    actual = tmp.stat().st_size if tmp.exists() else 0
    if actual != expected:
        return {"download_status": "size_mismatch", "downloaded_bytes": actual, "error": f"expected {expected}, got {actual}"}
    tmp.replace(target)
    return {"download_status": "downloaded", "downloaded_bytes": actual, "error": ""}


def download_manifest(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, row in manifest.iterrows():
        label = f"{row['era']} {row['primary_dataset']} {i + 1}/{len(manifest)} {row['size_gb']:.3f} GB"
        print(f"[download] {label}", flush=True)
        started = time.time()
        result = download_one(row)
        rows.append({**row.to_dict(), **result, "download_seconds": time.time() - started})
        pd.DataFrame(rows).to_csv(TABLES / "01_download_audit.csv", index=False)
        if result["download_status"] not in {"downloaded", "already_present"}:
            print(f"[download] failed {label}: {result['error']}", flush=True)
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_download_audit.csv", index=False)
    return audit


def make_chunks(downloaded: pd.DataFrame) -> pd.DataFrame:
    ok = downloaded[downloaded["download_status"].isin(["downloaded", "already_present"])].copy()
    rows = []
    for (era, dataset, record_id), group in ok.groupby(["era", "primary_dataset", "record_id"], sort=False):
        chunk_files = []
        chunk_gb = 0.0
        chunk_idx = 0
        for _, row in group.sort_values("selection_order").iterrows():
            size = float(row["size_gb"])
            if chunk_files and (chunk_gb + size > CHUNK_MAX_GB or len(chunk_files) >= CHUNK_MAX_FILES):
                chunk_idx += 1
                for r in chunk_files:
                    rows.append({**r, "chunk_index": chunk_idx})
                chunk_files = []
                chunk_gb = 0.0
            chunk_files.append(row.to_dict())
            chunk_gb += size
        if chunk_files:
            chunk_idx += 1
            for r in chunk_files:
                rows.append({**r, "chunk_index": chunk_idx})
    chunks = pd.DataFrame(rows)
    chunks.to_csv(TABLES / "02_extraction_chunk_manifest.csv", index=False)
    return chunks


def run_with_heartbeat(cmd: list[str], log_path: Path, label: str) -> int:
    started = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
        last_size = -1
        while True:
            code = proc.poll()
            size = log_path.stat().st_size if log_path.exists() else 0
            elapsed = (time.time() - started) / 60.0
            if code is not None:
                print(f"[extract] {label}: finished rc={code} elapsed={elapsed:.1f} min log={size / 1e6:.2f} MB", flush=True)
                return int(code)
            if size != last_size:
                print(f"[extract] {label}: running elapsed={elapsed:.1f} min log={size / 1e6:.2f} MB", flush=True)
                last_size = size
            time.sleep(60)


def extract_chunk(group: pd.DataFrame) -> dict[str, object]:
    era = str(group["era"].iloc[0])
    dataset = str(group["primary_dataset"].iloc[0])
    record_id = int(group["record_id"].iloc[0])
    chunk_index = int(group["chunk_index"].iloc[0])
    run_id = f"overnight_{safe(era)}_{safe(dataset)}_{record_id}_chunk{chunk_index:03d}"
    out_csv = SOURCES / f"{run_id}_event_features.csv"
    if out_csv.exists():
        header = pd.read_csv(out_csv, nrows=0).columns
        if {"MHT_pt", "MHT_phi", "MHT_over_HT", "MET_minus_MHT"}.issubset(header):
            events = sum(1 for _ in out_csv.open("r", encoding="utf-8", errors="replace")) - 1
            return {"run_id": run_id, "era": era, "primary_dataset": dataset, "record_id": record_id, "chunk_index": chunk_index, "status": "existing", "events_written": events, "output_csv": str(out_csv), "returncode": 0, "error": ""}

    container_paths = [f"/data/{era}/{dataset}/{record_id}/{name}" for name in group["filename"]]
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={','.join(container_paths)}; "
        "export NFRAME_INPUT_DIR=/data; "
        f"export NFRAME_OUTPUT_DIR=/work/outputs/{run_id}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
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
    log_path = LOGS / f"{run_id}.log"
    label = f"{era} {dataset} chunk {chunk_index}"
    print(f"[extract] starting {label}: {len(group)} files {group['size_gb'].sum():.3f} GB", flush=True)
    rc = run_with_heartbeat(cmd, log_path, label)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    if rc != 0 or not raw.exists():
        return {"run_id": run_id, "era": era, "primary_dataset": dataset, "record_id": record_id, "chunk_index": chunk_index, "status": "failed", "events_written": 0, "output_csv": "", "returncode": rc, "error": f"see {log_path}"}
    try:
        df = pd.read_csv(raw, low_memory=False)
        required = {"MHT_pt", "MHT_phi", "MHT_over_HT", "MET_minus_MHT"}
        missing = required.difference(df.columns)
        if missing:
            raise RuntimeError(f"missing columns {sorted(missing)}")
        df.insert(0, "sample_id", run_id)
        df.insert(1, "era", era)
        df.insert(2, "primary_dataset", dataset)
        df.insert(3, "record_id", record_id)
        df.insert(4, "chunk_index", chunk_index)
        df.insert(5, "source_file", ";".join(group["filename"].astype(str)))
        df.insert(6, "source_file_count", len(group))
        df.insert(7, "event_index_within_chunk", range(len(df)))
        df["is_real_collision"] = True
        df["is_simulated"] = False
        df.to_csv(out_csv, index=False)
        return {"run_id": run_id, "era": era, "primary_dataset": dataset, "record_id": record_id, "chunk_index": chunk_index, "status": "extracted", "events_written": len(df), "output_csv": str(out_csv), "returncode": rc, "error": ""}
    except Exception as exc:
        return {"run_id": run_id, "era": era, "primary_dataset": dataset, "record_id": record_id, "chunk_index": chunk_index, "status": "postprocess_failed", "events_written": 0, "output_csv": "", "returncode": rc, "error": str(exc)}


def extract_chunks(chunks: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in chunks.groupby(["era", "primary_dataset", "record_id", "chunk_index"], sort=False):
        result = extract_chunk(group)
        rows.append(result)
        pd.DataFrame(rows).to_csv(TABLES / "03_extraction_audit.csv", index=False)
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "03_extraction_audit.csv", index=False)
    return audit


def numeric(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in df:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def jet_bin(n_jets: pd.Series) -> pd.Series:
    n = pd.to_numeric(n_jets, errors="coerce").fillna(0).astype(float)
    bins = np.select(
        [n <= 0, (n >= 1) & (n <= 2), (n >= 3) & (n <= 4), n >= 5],
        ["0jet", "1to2jets", "3to4jets", "5plusjets"],
        default="unknown",
    )
    return pd.Series(pd.Categorical(bins, categories=JET_BINS), index=n.index)


def zscore(values: pd.Series, ref_mask: pd.Series | np.ndarray | None = None) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    ref = x if ref_mask is None else x.loc[ref_mask]
    mean = float(ref.mean()) if len(ref) else 0.0
    sd = float(ref.std(ddof=0)) if len(ref) else 1.0
    if not np.isfinite(sd) or sd <= 1e-9:
        sd = 1.0
    return (x - mean) / sd


def strict_quality(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    for col in QUALITY_FILTERS:
        out[col] = numeric(out, col, -999)
    out["strict_quality_clean"] = (out[QUALITY_FILTERS] == 1).all(axis=1)
    audit = (
        out.groupby(["era", "primary_dataset"], as_index=False)
        .agg(events_before=("event", "count"), events_after_strict_quality=("strict_quality_clean", "sum"))
    )
    audit["retention_fraction"] = audit["events_after_strict_quality"] / audit["events_before"].replace(0, np.nan)
    return out[out["strict_quality_clean"]].copy(), audit


def add_dataset_components(group: pd.DataFrame) -> pd.DataFrame:
    dataset = str(group["primary_dataset"].iloc[0])
    g = group.copy()
    g["missing_proxy_kind"] = "MHT_pt" if dataset == "HTMHT" else "MET_pt"
    g["missing_proxy_pt"] = numeric(g, "MHT_pt" if dataset == "HTMHT" else "MET_pt")
    g["log1p_missing_proxy"] = np.log1p(np.clip(g["missing_proxy_pt"], 0, None))
    g["log1p_HT"] = np.log1p(np.clip(numeric(g, "HT"), 0, None))
    g["N_jets_30"] = numeric(g, "N_jets_30")
    g["N_btags_medium"] = numeric(g, "N_btags_medium")
    g["N_muons"] = numeric(g, "N_muons")
    g["N_electrons"] = numeric(g, "N_electrons")
    g["secondary_vertex_count"] = numeric(g, "secondary_vertex_count")
    g["packed_candidate_count"] = numeric(g, "packed_candidate_count")
    g["mht_over_ht_clean"] = numeric(g, "MHT_over_HT").replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-10, 10)
    g["met_minus_mht"] = numeric(g, "MET_minus_MHT")
    g["jet_bin"] = jet_bin(g["N_jets_30"])

    lower_mask = g["log1p_missing_proxy"] <= g["log1p_missing_proxy"].quantile(0.95)
    x_cols = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
    x = g.loc[lower_mask, x_cols].to_numpy(float)
    y = g.loc[lower_mask, "log1p_missing_proxy"].to_numpy(float)
    if len(g.loc[lower_mask]) >= len(x_cols) + 5:
        design = np.column_stack([np.ones(len(x)), x])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        pred = np.column_stack([np.ones(len(g)), g[x_cols].to_numpy(float)]) @ beta
    else:
        pred = np.full(len(g), float(g.loc[lower_mask, "log1p_missing_proxy"].mean()))
    g["observer_projection"] = zscore(pd.Series(g["log1p_missing_proxy"].to_numpy(float) - pred, index=g.index), lower_mask)

    disp_raw = np.log1p(np.clip(g["secondary_vertex_count"], 0, None)) + 0.05 * zscore(np.log1p(np.clip(g["packed_candidate_count"], 0, None)))
    g["physical_projection"] = (
        0.65 * zscore(g["log1p_missing_proxy"], lower_mask)
        + 0.20 * zscore(g["log1p_HT"], lower_mask)
        + 0.15 * zscore(disp_raw, lower_mask)
    )

    pca_cols = ["log1p_missing_proxy", "log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "mht_over_ht_clean", "met_minus_mht"]
    ref = g.loc[lower_mask, pca_cols].to_numpy(float)
    all_x = g[pca_cols].to_numpy(float)
    mean = ref.mean(axis=0)
    sd = ref.std(axis=0)
    sd = np.where(sd <= 1e-9, 1.0, sd)
    z_ref = (ref - mean) / sd
    z_all = (all_x - mean) / sd
    if len(ref) >= len(pca_cols) + 5:
        _, _, vt = np.linalg.svd(z_ref, full_matrices=False)
        basis = vt[: min(3, vt.shape[0])].T
        recon = (z_all @ basis) @ basis.T
        resid = np.sqrt(np.mean((z_all - recon) ** 2, axis=1))
    else:
        resid = np.zeros(len(g), dtype=float)
    g["algebraic_projection"] = zscore(pd.Series(resid, index=g.index), lower_mask)
    g["ordinary_qcd_axis"] = 0.70 * zscore(g["N_jets_30"], lower_mask) + 0.30 * zscore(g["N_btags_medium"], lower_mask)
    g["leptonic_control_axis"] = -zscore(g["N_muons"] + g["N_electrons"], lower_mask)
    g["frozen_boundary_score"] = sum(FROZEN_WEIGHTS[col] * g[col].to_numpy(float) for col in COMPONENTS)
    return g


def score_and_validate(extraction: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = [p for p in extraction["output_csv"].dropna().astype(str) if p]
    frames = []
    usecols_needed = {
        "era",
        "primary_dataset",
        "run",
        "lumi",
        "event",
        "MET_pt",
        "MHT_pt",
        "MHT_phi",
        "MHT_over_HT",
        "MET_minus_MHT",
        "HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "secondary_vertex_count",
        "packed_candidate_count",
        *QUALITY_FILTERS,
    }
    for p in files:
        header = pd.read_csv(p, nrows=0).columns
        usecols = [c for c in header if c in usecols_needed]
        frames.append(pd.read_csv(p, usecols=usecols, low_memory=False))
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    clean, quality = strict_quality(raw)
    quality.to_csv(TABLES / "04_quality_audit.csv", index=False)
    if clean.empty:
        return pd.DataFrame(), quality, pd.DataFrame()

    scored_frames = []
    for _, group in clean.groupby(["era", "primary_dataset"], sort=False):
        scored_frames.append(add_dataset_components(group))
    scored = pd.concat(scored_frames, ignore_index=True)
    slim_cols = ["era", "primary_dataset", "run", "lumi", "event", "missing_proxy_kind", "missing_proxy_pt", "jet_bin", "frozen_boundary_score", *COMPONENTS]
    scored[slim_cols].to_csv(SOURCES / "overnight_frozen_trace_scored_events_slim.csv", index=False)

    rows = []
    for (era, dataset), group in scored.groupby(["era", "primary_dataset"], sort=False):
        g = group.copy()
        edges = np.unique(g["missing_proxy_pt"].quantile(np.linspace(0, 1, 11)).to_numpy(float))
        if len(edges) < 3:
            edges = np.array([-np.inf, np.inf])
        else:
            edges[0], edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=edges, labels=False, include_lowest=True)
        thresholds = g.groupby("missing_bin", observed=False)["frozen_boundary_score"].quantile(0.99)
        g["q99_tail"] = g["frozen_boundary_score"] >= g["missing_bin"].map(thresholds).astype(float)
        expected_frac = g.groupby("missing_bin", observed=False)["q99_tail"].mean().rename("expected_tail_fraction")
        for jet, sub in g.groupby("jet_bin", observed=False):
            if str(jet) not in JET_BINS:
                continue
            expected = float(sub["missing_bin"].map(expected_frac).astype(float).sum())
            observed = int(sub["q99_tail"].sum())
            z = (observed - expected) / np.sqrt(expected + (REL_UNC * expected) ** 2) if expected > 0 else np.nan
            rows.append(
                {
                    "era": era,
                    "primary_dataset": dataset,
                    "jet_bin": str(jet),
                    "events": len(sub),
                    "q99_observed": observed,
                    "q99_expected_internal": expected,
                    "q99_obs_exp_internal": observed / expected if expected > 0 else np.nan,
                    "q99_internal_Z_relunc30": z,
                    "tail_definition": "frozen local_refine_00287 top 1% within same-era/stream missing-proxy deciles",
                }
            )
    stage_table = pd.DataFrame(rows)
    stage_table.to_csv(TABLES / "05_frozen_stage_tail_table.csv", index=False)
    readout_rows = []
    for era, sub in stage_table.groupby("era", sort=False):
        def get(dataset: str, jet: str, col: str = "q99_internal_Z_relunc30") -> float:
            row = sub[(sub["primary_dataset"].eq(dataset)) & (sub["jet_bin"].eq(jet))]
            return float(row[col].iloc[0]) if not row.empty else np.nan

        met_z = get("MET", SIGNAL_STAGES["MET"])
        htmht_z = get("HTMHT", SIGNAL_STAGES["HTMHT"])
        signals = np.array([met_z, htmht_z], dtype=float)
        finite = signals[np.isfinite(signals)]
        combined = float(finite.sum() / np.sqrt(len(finite))) if len(finite) else np.nan
        controls = []
        for dataset in CONTROL_DATASETS:
            for jet in JET_BINS:
                val = get(dataset, jet)
                if np.isfinite(val):
                    controls.append(val)
        max_ctrl = float(np.max(np.abs(controls))) if controls else np.nan
        readout_rows.append(
            {
                "era": era,
                "MET_stage": SIGNAL_STAGES["MET"],
                "HTMHT_stage": SIGNAL_STAGES["HTMHT"],
                "MET_stage_Z": met_z,
                "HTMHT_stage_Z": htmht_z,
                "signal_stouffer_Z": combined,
                "max_control_absZ_all_stages": max_ctrl,
                "passes_frozen_trace_screen": bool(
                    np.isfinite(met_z)
                    and np.isfinite(htmht_z)
                    and met_z >= 3
                    and htmht_z >= 3
                    and combined >= 5
                    and np.isfinite(max_ctrl)
                    and max_ctrl < 3
                ),
            }
        )
    readout = pd.DataFrame(readout_rows)
    if not readout.empty:
        z_vals = readout["signal_stouffer_Z"].dropna().to_numpy(float)
        combined_z = float(z_vals.sum() / np.sqrt(len(z_vals))) if len(z_vals) else np.nan
        post_z = float(norm.isf(min(1.0, norm.sf(combined_z) * max(len(z_vals), 1)))) if np.isfinite(combined_z) else np.nan
        readout["all_era_stouffer_Z"] = combined_z
        readout["all_era_simple_era_trial_Z"] = post_z
    readout.to_csv(TABLES / "06_frozen_trace_validation_readout.csv", index=False)
    return stage_table, quality, readout


def write_reports(manifest: pd.DataFrame, download: pd.DataFrame, extraction: pd.DataFrame, quality: pd.DataFrame, readout: pd.DataFrame) -> None:
    selected_gb = manifest["size_gb"].sum() if not manifest.empty else 0.0
    downloaded_gb = download.loc[download["download_status"].isin(["downloaded", "already_present"]), "size_gb"].sum() if not download.empty else 0.0
    extracted_events = extraction.loc[extraction["status"].isin(["extracted", "existing"]), "events_written"].sum() if not extraction.empty else 0
    report = f"""# Overnight Frozen N-Frame Trace Validation

## Purpose

This is an overnight large-data validation of the frozen `local_refine_00287` boundary:

```latex
B = 0.313725O + 0.313725P - 0.274510Q - 0.098039L
```

The stage rule is frozen:

- MET: `0jet`
- HTMHT: `1to2jets`
- controls: JetHT and SingleMuon must remain below `|Z| < 3` across all jet stages.

## Data Selection

Selected ROOT input size: {selected_gb:.3f} GB.

Downloaded/available ROOT input size: {downloaded_gb:.3f} GB.

Extracted events: {int(extracted_events)}.

The records are CMS MiniAOD records from Run2016G, Run2016H, and Run2015D. 2012 AOD was intentionally not used in this overnight run because the current CMSSW MiniAOD extractor is not the correct reader for 2012 AOD.

## Quality Audit

{quality.to_markdown(index=False) if not quality.empty else "Quality audit not available yet."}

## Frozen Validation Readout

{readout.to_markdown(index=False) if not readout.empty else "Readout not available yet."}

## Interpretation

This run does not refit the N-Frame weights. It tests whether the current strongest boundary-trace candidate survives on much larger, unused CMS MiniAOD data.
"""
    (REPORTS / "01_OVERNIGHT_FROZEN_TRACE_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Overnight Frozen Trace Validation

Selected ROOT input size: {selected_gb:.3f} GB.

Downloaded/available ROOT input size: {downloaded_gb:.3f} GB.

Extracted events: {int(extracted_events)}.

{readout.to_markdown(index=False) if not readout.empty else "Readout not available yet."}
"""
    (REPORTS / "02_SHORT_UPDATE_OVERNIGHT_FROZEN_TRACE.md").write_text(short, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-gb", type=float, default=float(os.environ.get("NFRAME_OVERNIGHT_TARGET_GB", TARGET_GB)))
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    print("[start] overnight frozen trace validation", flush=True)
    manifest = build_manifest(args.target_gb)
    print(f"[manifest] selected {len(manifest)} files, {manifest['size_gb'].sum():.3f} GB", flush=True)
    if args.plan_only:
        print("[plan-only] stopping after manifest", flush=True)
        return
    download = download_manifest(manifest)
    print("[download] complete", flush=True)
    chunks = make_chunks(download)
    print(f"[extract] prepared {chunks.groupby(['era','primary_dataset','record_id','chunk_index']).ngroups if not chunks.empty else 0} chunks", flush=True)
    extraction = extract_chunks(chunks)
    print("[extract] complete", flush=True)
    stage_table, quality, readout = score_and_validate(extraction[extraction["status"].isin(["extracted", "existing"])])
    print("[analysis] complete", flush=True)
    write_reports(manifest, download, extraction, quality, readout)
    print("OVERNIGHT FROZEN TRACE VALIDATION COMPLETE", flush=True)
    if not readout.empty:
        print(readout.to_string(index=False), flush=True)
    print("Outputs:", OUT, flush=True)


if __name__ == "__main__":
    main()
