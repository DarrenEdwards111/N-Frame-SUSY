from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import urllib3


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_fresh_run2016h_tri_dynamic_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
LOGS = OUT / "logs"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_fresh_run2016h_tri_dynamic_validation")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest"

SPEC = importlib.util.spec_from_file_location("tri", ROOT / "scripts/192_tri_aspect_dynamic_boundary_model.py")
tri = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tri)
v4 = tri.v4

RECORDS = {
    "HTMHT": 30540,
    "MET": 30542,
    "JetHT": 30541,
    "SingleMuon": 30546,
}
FILES_PER_DATASET = 3
MIN_FILE_SIZE_GB = {
    "HTMHT": 0.50,
    "MET": 0.50,
    "JetHT": 0.50,
    "SingleMuon": 0.50,
}
QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]
BEST_DYNAMIC_MODEL = {
    "candidate": "tri_dynamic_02_frozen",
    "MET": {"observer_projection": 0.80, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.20, "physical_projection": 0.0, "leptonic_control_axis": 0.0},
    "HTMHT": {"observer_projection": 0.45, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.10, "physical_projection": 0.35, "leptonic_control_axis": 0.0},
    "JetHT": {"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.35, "physical_projection": 0.0, "leptonic_control_axis": 0.0},
    "SingleMuon": {"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.20, "physical_projection": 0.0, "leptonic_control_axis": -0.15},
}


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, LOGS, DOWNLOAD_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


def safe(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def local_root_path(dataset: str, record_id: int, filename: str) -> Path:
    return DOWNLOAD_ROOT / dataset / str(record_id) / filename


def fetch_record_files(record_id: int) -> tuple[str, list[dict]]:
    urllib3.disable_warnings()
    rec = requests.get(f"https://opendata.cern.ch/api/records/{record_id}", timeout=60, verify=False).json()
    files = []
    for index in rec["metadata"].get("_file_indices", []):
        files.extend(index.get("files", []))
    return rec["metadata"].get("title", ""), sorted(files, key=lambda f: int(f["size"]))


def build_manifest() -> pd.DataFrame:
    existing_names = {p.name for p in Path(r"D:\cern_open_data").rglob("*.root") if DOWNLOAD_ROOT not in p.parents}
    rows = []
    for dataset, record_id in RECORDS.items():
        title, files = fetch_record_files(record_id)
        min_size = MIN_FILE_SIZE_GB[dataset] * 1e9
        fresh = [f for f in files if f["filename"] not in existing_names and int(f["size"]) >= min_size]
        selected = fresh[:FILES_PER_DATASET]
        for rank, f in enumerate(selected, start=1):
            rows.append(
                {
                    "primary_dataset": dataset,
                    "record_id": record_id,
                    "record_title": title,
                    "rank_by_size_after_filters": rank,
                    "filename": f["filename"],
                    "size_bytes": int(f["size"]),
                    "size_gb": int(f["size"]) / 1e9,
                    "uri": f["uri"],
                    "https_url": uri_to_https(f["uri"]),
                    "local_path": str(local_root_path(dataset, record_id, f["filename"])),
                    "selection_rule": f"first {FILES_PER_DATASET} unused files >= {MIN_FILE_SIZE_GB[dataset]} GB by ascending CERN metadata size",
                    "frozen_model": "tri_dynamic_02_frozen",
                }
            )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "01_selected_fresh_run2016h_files.csv", index=False)
    return manifest


def download_file(row: pd.Series) -> dict:
    target = Path(row["local_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = int(row["size_bytes"])
    if target.exists() and target.stat().st_size == expected:
        print(f"[download] already present {target.name} ({expected / 1e9:.3f} GB)", flush=True)
        return {"status": "already_present", "bytes": expected}
    tmp = target.with_suffix(target.suffix + ".part")
    resume_bytes = tmp.stat().st_size if tmp.exists() else 0
    print(f"[download] starting {target.name} ({expected / 1e9:.3f} GB)", flush=True)
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        cmd = [
            curl,
            "-L",
            "-k",
            "--fail",
            "--retry",
            "5",
            "--retry-delay",
            "5",
            "--connect-timeout",
            "30",
            "--speed-time",
            "120",
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
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        last_report = -1
        started = time.time()
        if resume_bytes:
            print(f"[download] resuming {target.name} from {resume_bytes / 1e9:.3f} GB", flush=True)
        while True:
            code = proc.poll()
            current = tmp.stat().st_size if tmp.exists() else 0
            if current != last_report:
                pct = 100 * current / expected if expected else 0
                print(f"[download] {target.name}: {current / 1e9:.3f}/{expected / 1e9:.3f} GB ({pct:.1f}%)", flush=True)
                last_report = current
            if code is not None:
                err = proc.stderr.read() if proc.stderr else ""
                if code != 0:
                    raise RuntimeError(f"curl failed for {target.name} with code {code}: {err[-1000:]}")
                break
            if time.time() - started > 60 and current == 0:
                print(f"[download] {target.name}: still waiting for first bytes", flush=True)
            time.sleep(15)
    else:
        urllib3.disable_warnings()
        written = 0
        last_report = 0
        with requests.get(row["https_url"], stream=True, timeout=(30, 180), verify=False) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as fh:
                for chunk in resp.iter_content(8 * 1024 * 1024):
                    if chunk:
                        fh.write(chunk)
                        written += len(chunk)
                        if written - last_report >= 128 * 1024 * 1024 or written == expected:
                            pct = 100 * written / expected if expected else 0
                            print(f"[download] {target.name}: {written / 1e9:.3f}/{expected / 1e9:.3f} GB ({pct:.1f}%)", flush=True)
                            last_report = written
    actual = tmp.stat().st_size
    if actual != expected:
        raise RuntimeError(f"size mismatch for {target.name}: expected {expected}, got {actual}")
    tmp.replace(target)
    print(f"[download] finished {target.name}", flush=True)
    return {"status": "downloaded", "bytes": actual}


def download_manifest(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in manifest.iterrows():
        print(f"[download] dataset={row['primary_dataset']} file={row['rank_by_size_after_filters']}/{FILES_PER_DATASET}", flush=True)
        started = time.time()
        result = download_file(row)
        rows.append({**row.to_dict(), "download_status": result["status"], "download_seconds": time.time() - started})
        pd.DataFrame(rows).to_csv(TABLES / "02_download_audit.csv", index=False)
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "02_download_audit.csv", index=False)
    return audit


def run_with_heartbeat(cmd: list[str], log_path: Path, label: str) -> int:
    env = os.environ.copy()
    started = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, env=env)
        last_size = 0
        while True:
            code = proc.poll()
            size = log_path.stat().st_size if log_path.exists() else 0
            elapsed = time.time() - started
            if code is not None:
                print(f"[extract] {label}: finished returncode={code} elapsed={elapsed / 60:.1f} min log={size / 1e6:.2f} MB", flush=True)
                return int(code)
            if size != last_size:
                print(f"[extract] {label}: running elapsed={elapsed / 60:.1f} min log={size / 1e6:.2f} MB", flush=True)
                last_size = size
            else:
                print(f"[extract] {label}: still running elapsed={elapsed / 60:.1f} min log unchanged={size / 1e6:.2f} MB", flush=True)
            time.sleep(30)


def run_cmssw_batch(dataset: str, group: pd.DataFrame) -> dict:
    run_id = f"fresh_run2016h_tri_dynamic_{safe(dataset)}_batch{len(group)}"
    out_csv = SOURCES / f"{run_id}_event_features.csv"
    if out_csv.exists():
        events = sum(1 for _ in out_csv.open("r", encoding="utf-8", errors="replace")) - 1
        print(f"[extract] already present {dataset}: {events} events", flush=True)
        return {"primary_dataset": dataset, "run_id": run_id, "status": "existing", "events_written": events, "output_csv": str(out_csv), "log_path": ""}

    container_paths = [f"/data/{dataset}/{int(r.record_id)}/{r.filename}" for r in group.itertuples(index=False)]
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={','.join(container_paths)}; "
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
    log_path = LOGS / f"{run_id}.log"
    print(f"[extract] starting {dataset}: {len(group)} files, log={log_path}", flush=True)
    returncode = run_with_heartbeat(cmd, log_path, dataset)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    if returncode != 0 or not raw.exists():
        return {"primary_dataset": dataset, "run_id": run_id, "status": "failed", "events_written": 0, "output_csv": "", "log_path": str(log_path), "returncode": returncode}
    df = pd.read_csv(raw)
    df.insert(0, "sample_id", run_id)
    df.insert(1, "primary_dataset", dataset)
    df.insert(2, "record_id", ";".join(group["record_id"].astype(str)))
    df.insert(3, "run_era", "Run2016H_fresh")
    df.insert(4, "source_file", ";".join(group["filename"].astype(str)))
    df.insert(5, "source_file_count", len(group))
    df.insert(6, "local_input_path_or_container_path", " | ".join(group["local_path"].astype(str)) + " | " + ",".join(container_paths))
    df.insert(7, "event_index_within_batch", range(len(df)))
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df.to_csv(out_csv, index=False)
    print(f"[extract] completed {dataset}: {len(df)} events", flush=True)
    return {"primary_dataset": dataset, "run_id": run_id, "status": "extracted", "events_written": len(df), "output_csv": str(out_csv), "log_path": str(log_path), "returncode": returncode}


def extract_batches(audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset, group in audit.groupby("primary_dataset", sort=False):
        print(f"[extract] queue dataset={dataset}", flush=True)
        result = run_cmssw_batch(dataset, group)
        rows.append(result)
        pd.DataFrame(rows).to_csv(TABLES / "03_extraction_audit.csv", index=False)
        if result["status"] == "failed":
            raise RuntimeError(f"CMSSW extraction failed for {dataset}; see {result['log_path']}")
    extraction = pd.DataFrame(rows)
    extraction.to_csv(TABLES / "03_extraction_audit.csv", index=False)
    frames = [pd.read_csv(p, low_memory=False) for p in extraction["output_csv"]]
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(SOURCES / "fresh_run2016h_combined_event_features.csv", index=False)
    return extraction


def strict_quality(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    for col in QUALITY_FILTERS:
        if col not in out:
            out[col] = -999
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(-999)
    out["strict_quality_clean"] = (out[QUALITY_FILTERS] == 1).all(axis=1)
    audit = (
        out.groupby("primary_dataset", as_index=False)
        .agg(events_before=("event", "count"), events_after_strict_quality=("strict_quality_clean", "sum"))
    )
    audit["retention_fraction"] = audit["events_after_strict_quality"] / audit["events_before"]
    clean = out[out["strict_quality_clean"]].copy()
    return clean, audit


def score_and_validate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("[analysis] scoring fresh combined features with frozen tri_dynamic_02", flush=True)
    real_raw = pd.read_csv(SOURCES / "fresh_run2016h_combined_event_features.csv", low_memory=False)
    clean, quality_audit = strict_quality(real_raw)
    for col in ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "packed_candidate_count", "secondary_vertex_count"]:
        if col not in clean:
            clean[col] = 0.0
        clean[col] = pd.to_numeric(clean[col], errors="coerce").fillna(0.0)
    clean["era"] = "Run2016H_fresh"
    clean["event_weight"] = 1.0
    clean["split"] = "validation"
    sm_raw = v4.add_base_transforms(v4.read_sm())
    ref = v4.fit_reference(sm_raw)
    sm = v4.apply_reference(sm_raw, ref)
    real = v4.apply_reference(clean, ref)
    sm, real = tri.add_tri_aspect_components(sm, real)
    real_b, sm_by_dataset = tri.assign_dynamic_bands(real, sm, BEST_DYNAMIC_MODEL)
    counts = tri.counts_for_dynamic(real_b, sm_by_dataset, "validation", "tri_dynamic_02_frozen")
    counts.to_csv(TABLES / "04_fresh_dynamic_score_band_counts.csv", index=False)
    summary = v4.summarize_counts(counts)
    summary.to_csv(TABLES / "05_fresh_dynamic_sideband_profile_summary.csv", index=False)

    def get(dataset: str, jet_bin: str = "1to2jets") -> pd.Series | None:
        rows = summary[(summary["primary_dataset"].eq(dataset)) & (summary["jet_bin"].eq(jet_bin))]
        return rows.iloc[0] if not rows.empty else None

    met = get("MET")
    htmht = get("HTMHT")
    jetht = get("JetHT")
    smuon = get("SingleMuon")
    signal_z = [float(x["q99_profile_Z"]) for x in [met, htmht] if x is not None and pd.notna(x["q99_profile_Z"])]
    combined_z = float(np.sum(signal_z) / np.sqrt(len(signal_z))) if signal_z else np.nan
    readout = pd.DataFrame(
        [
            {
                "test": "fresh_run2016h_tri_dynamic_02_frozen",
                "MET_1to2jets_Z": float(met["q99_profile_Z"]) if met is not None else np.nan,
                "MET_1to2jets_obs_exp": float(met["q99_obs_exp_profile"]) if met is not None else np.nan,
                "HTMHT_1to2jets_Z": float(htmht["q99_profile_Z"]) if htmht is not None else np.nan,
                "HTMHT_1to2jets_obs_exp": float(htmht["q99_obs_exp_profile"]) if htmht is not None else np.nan,
                "combined_MET_HTMHT_stouffer_Z": combined_z,
                "JetHT_1to2jets_control_Z": float(jetht["q99_profile_Z"]) if jetht is not None else np.nan,
                "SingleMuon_1to2jets_control_Z": float(smuon["q99_profile_Z"]) if smuon is not None else np.nan,
                "controls_close_absZ_lt3": bool(
                    (abs(float(jetht["q99_profile_Z"])) < 3 if jetht is not None else False)
                    and (abs(float(smuon["q99_profile_Z"])) < 3 if smuon is not None else False)
                ),
                "fresh_validation_supports_dynamic_trace": bool(
                    len(signal_z) == 2
                    and combined_z > 5
                    and (met is not None and float(met["q99_profile_Z"]) > 3)
                    and (htmht is not None and float(htmht["q99_profile_Z"]) > 3)
                    and (jetht is not None and abs(float(jetht["q99_profile_Z"])) < 3)
                    and (smuon is not None and abs(float(smuon["q99_profile_Z"])) < 3)
                ),
            }
        ]
    )
    quality_audit.to_csv(TABLES / "06_quality_audit.csv", index=False)
    readout.to_csv(TABLES / "07_fresh_validation_readout.csv", index=False)
    return summary, quality_audit, readout


def write_reports(manifest: pd.DataFrame, download: pd.DataFrame, extraction: pd.DataFrame, summary: pd.DataFrame, quality: pd.DataFrame, readout: pd.DataFrame) -> None:
    weights = pd.DataFrame(
        [{"dataset_context": ds, **{k: v for k, v in BEST_DYNAMIC_MODEL[ds].items()}} for ds in ["MET", "HTMHT", "JetHT", "SingleMuon"]]
    )
    weights.to_csv(TABLES / "08_frozen_tri_dynamic_context_weights.csv", index=False)
    report = f"""# Fresh Run2016H Tri-Aspect Dynamic Boundary Validation

## Purpose

This is a fresh validation of the frozen dynamic N-Frame boundary `tri_dynamic_02`. No boundary weights are refit in this run.

The selected batch uses unused CMS Run2016H MiniAOD files from:

- MET
- HTMHT
- JetHT
- SingleMuon

MET and HTMHT are the missing-boundary streams. JetHT and SingleMuon are analysed as controls, not ignored.

## Frozen Dynamic Boundary

{weights.to_markdown(index=False)}

## Selected Files

{manifest.to_markdown(index=False)}

Total selected ROOT input size: {manifest["size_gb"].sum():.3f} GB.

## Download Audit

{download[["primary_dataset", "filename", "size_gb", "download_status", "download_seconds"]].to_markdown(index=False)}

## Extraction Audit

{extraction.to_markdown(index=False)}

## Quality-Clean Audit

{quality.to_markdown(index=False)}

## Fresh Validation Readout

{readout.to_markdown(index=False)}

## Full Sideband-Profile Summary

{summary.to_markdown(index=False)}

## Interpretation

This is the first larger fresh Run2016H validation batch for the tri-aspect dynamic boundary. The key question is whether MET and HTMHT both remain positive while JetHT and SingleMuon controls remain below about |Z| < 3.
"""
    (REPORTS / "01_FRESH_RUN2016H_TRI_DYNAMIC_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Fresh Run2016H Tri-Dynamic Validation

{readout.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_FRESH_RUN2016H_TRI_DYNAMIC.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    print("[start] fresh Run2016H tri-dynamic validation", flush=True)
    manifest = build_manifest()
    print(f"[manifest] selected {len(manifest)} files, total {manifest['size_gb'].sum():.3f} GB", flush=True)
    download = download_manifest(manifest)
    print("[download] complete", flush=True)
    extraction = extract_batches(download)
    print("[extract] all dataset batches complete", flush=True)
    summary, quality, readout = score_and_validate()
    print("[analysis] validation complete", flush=True)
    write_reports(manifest, download, extraction, summary, quality, readout)
    print("FRESH RUN2016H TRI-DYNAMIC VALIDATION COMPLETE")
    print(readout.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
