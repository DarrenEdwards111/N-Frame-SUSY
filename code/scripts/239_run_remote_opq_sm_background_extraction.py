from __future__ import annotations

"""Run the distributed remote SM plan and retain compact feature tables only."""

import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REMOTE = OUT / "remote_xrootd"
MANIFEST = TABLES / "02_remote_sm_distributed_file_manifest.csv"
PACKAGE = ROOT / "cloud_remote_nframe_package"
CMSSW_WORK = PACKAGE / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def run_record(record_id: int, group: pd.DataFrame) -> dict[str, object]:
    family = str(group["process_family"].iloc[0])
    run_id = f"remote_opq_sm_{record_id}_{family.lower()}"
    out_dir = CMSSW_WORK / "outputs" / run_id
    log_path = REMOTE / f"{run_id}.log"
    urls = ",".join(group["xrootd_url"].astype(str))
    max_events = int(group["planned_events_from_file"].sum())
    command_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES='{urls}'; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=100; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
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
    compact = REMOTE / f"{run_id}_event_features.csv"
    rows = 0
    gen_valid_fraction = float("nan")
    if code == 0 and raw.exists():
        frame = pd.read_csv(raw, low_memory=False)
        frame.insert(0, "record_id", record_id)
        frame.insert(1, "process_family", family)
        frame.insert(2, "source_file_count", len(group))
        frame.to_csv(compact, index=False)
        rows = len(frame)
        if "generator_weight_status" in frame:
            gen_valid_fraction = float(pd.to_numeric(frame["generator_weight_status"], errors="coerce").fillna(0).mean())
    return {
        "record_id": record_id,
        "process_family": family,
        "source_file_count": len(group),
        "planned_events": max_events,
        "status": "completed" if code == 0 and compact.exists() else "failed",
        "returncode": code,
        "feature_rows": rows,
        "generator_weight_valid_fraction": gen_valid_fraction,
        "output_path": str(compact) if compact.exists() else "",
        "log_path": str(log_path),
        "remote_only_raw_root": True,
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REMOTE.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    requested = {int(value) for value in sys.argv[1:]} if len(sys.argv) > 1 else set()
    if requested:
        manifest = manifest[manifest["record_id"].isin(requested)].copy()
        missing = requested - set(manifest["record_id"].astype(int))
        if missing:
            raise SystemExit(f"Requested record IDs absent from manifest: {sorted(missing)}")
    results = []
    for record_id, group in manifest.groupby("record_id", sort=False):
        print(f"starting record {record_id} ({group['process_family'].iloc[0]})", flush=True)
        result = run_record(int(record_id), group)
        results.append(result)
        print(f"finished record {record_id}: {result['status']} rows={result['feature_rows']}", flush=True)
    ledger_path = TABLES / "03_remote_sm_extraction_ledger.csv"
    previous = pd.read_csv(ledger_path) if ledger_path.exists() else pd.DataFrame()
    current = pd.DataFrame(results)
    if not previous.empty and not current.empty:
        previous = previous[~previous["record_id"].isin(current["record_id"])].copy()
    pd.concat([previous, current], ignore_index=True, sort=False).to_csv(ledger_path, index=False)
    print(TABLES / "03_remote_sm_extraction_ledger.csv")


if __name__ == "__main__":
    main()
