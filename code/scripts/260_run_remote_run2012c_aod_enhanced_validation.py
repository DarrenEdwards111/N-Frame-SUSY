from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_run2012c_aod_enhanced_validation"
TABLES = OUT / "tables"
REMOTE = OUT / "remote_xrootd"
PACKAGE = ROOT / "cloud_remote_nframe_package"
CMSSW_WORK = PACKAGE / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
API = "https://opendata.cern.ch/api/records/"
EVENTS_PER_STREAM = 15_000
FILES_PER_STREAM = 3
VALIDATION_ID = "Run2012C_AOD_enhanced_cross_era"

STREAMS = [
    {"primary_dataset": "MET", "record_id": 6038},
    {"primary_dataset": "JetHT", "record_id": 6036},
    {"primary_dataset": "SingleMuon", "record_id": 6047},
    {"primary_dataset": "HTMHT", "record_id": 6034},
]


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []) or []:
        out.extend(idx.get("files", []) or [])
    out.extend(md.get("files", []) or [])
    return out


def online_urls(record_id: int) -> tuple[str, list[str], int, int]:
    payload = requests.get(f"{API}{record_id}", timeout=60)
    payload.raise_for_status()
    md = payload.json().get("metadata", {})
    all_files = files(md)
    online = [f for f in all_files if str(f.get("availability", "")).lower() == "online"]
    return str(md.get("title", "")), [str(f.get("uri", "")) for f in online[:FILES_PER_STREAM]], len(all_files), len(online)


def run_stream(row: dict[str, object]) -> dict[str, object]:
    primary = str(row["primary_dataset"])
    record_id = int(row["record_id"])
    title, urls, all_count, online_count = online_urls(record_id)
    run_id = f"remote_run2012c_aod_{primary.lower()}_enhanced"
    out_dir = CMSSW_WORK / "outputs" / run_id
    log_path = REMOTE / f"{run_id}.log"
    compact = REMOTE / f"{run_id}_event_features.csv"
    if compact.exists():
        rows = max(0, sum(1 for _ in compact.open("r", encoding="utf-8", errors="replace")) - 1)
        return {
            "primary_dataset": primary,
            "record_id": record_id,
            "title": title,
            "all_file_count": all_count,
            "online_file_count": online_count,
            "selected_file_count": len(urls),
            "planned_events": EVENTS_PER_STREAM,
            "status": "existing",
            "returncode": 0,
            "events_written": rows,
            "output_path": str(compact),
            "log_path": str(log_path),
            "validation_sample_id": VALIDATION_ID,
            "feature_scope": "enhanced_AOD_OPQ; btag fallbacks plus V0 secondary-vertex-like counts",
        }

    command_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES='{','.join(urls)}'; "
        "export NFRAME_INPUT_DIR=/data; "
        f"export NFRAME_OUTPUT_DIR=/work/outputs/{run_id}; "
        "export NFRAME_TEST_MAXEVENTS=100; "
        f"export NFRAME_MAXEVENTS_FULL={EVENTS_PER_STREAM}; "
        "bash /work/run_one_aod_sample.sh"
    )
    command = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", IMAGE, "bash", "-lc", command_inside]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(command) + "\n")
        try:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=14_400)
            code = proc.returncode
        except Exception as exc:
            log.write("\nEXCEPTION " + repr(exc) + "\n")
            code = 999
    raw = out_dir / "event_features.csv"
    rows = 0
    if code == 0 and raw.exists():
        frame = pd.read_csv(raw, low_memory=False)
        frame.insert(0, "primary_dataset", primary)
        frame.insert(1, "record_id", record_id)
        frame.insert(2, "run_era", "Run2012C")
        frame.insert(3, "sample_validation_id", VALIDATION_ID)
        frame.insert(4, "source_file_count", len(urls))
        frame.to_csv(compact, index=False)
        rows = len(frame)
    return {
        "primary_dataset": primary,
        "record_id": record_id,
        "title": title,
        "all_file_count": all_count,
        "online_file_count": online_count,
        "selected_file_count": len(urls),
        "planned_events": EVENTS_PER_STREAM,
        "status": "completed" if code == 0 and compact.exists() else "failed",
        "returncode": code,
        "events_written": rows,
        "output_path": str(compact) if compact.exists() else "",
        "log_path": str(log_path),
        "validation_sample_id": VALIDATION_ID,
        "feature_scope": "enhanced_AOD_OPQ; btag fallbacks plus V0 secondary-vertex-like counts",
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REMOTE.mkdir(parents=True, exist_ok=True)
    rows = []
    for stream in STREAMS:
        print(f"starting {stream['primary_dataset']} record {stream['record_id']}", flush=True)
        result = run_stream(stream)
        rows.append(result)
        print(f"finished {result['primary_dataset']}: {result['status']} rows={result['events_written']}", flush=True)
    ledger = pd.DataFrame(rows)
    ledger.to_csv(TABLES / "01_run2012c_aod_enhanced_extraction_ledger.csv", index=False)
    print(TABLES / "01_run2012c_aod_enhanced_extraction_ledger.csv")


if __name__ == "__main__":
    main()
