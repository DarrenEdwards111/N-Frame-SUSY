from __future__ import annotations

"""Remote CMSSW extraction of exact trigger-family flags for calibration."""

import subprocess
import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cloud_remote_nframe_package" / "manifests" / "01_real_cms_miniaod_remote_cloud_manifest.csv"
CMSSW = ROOT / "cloud_remote_nframe_package" / "cmssw_full_extraction"
OUT = ROOT / "outputs_exact_trigger_calibration_run2016g"
TABLES = OUT / "tables"
REMOTE = OUT / "remote_xrootd"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
DATASETS = ["MET", "JetHT", "SingleMuon"]
EVENTS_PER_STREAM = 5_000


def run_one(dataset: str, row: pd.Series) -> dict[str, object]:
    run_id = f"exact_trigger_calibration_run2016g_{dataset.lower()}"
    output_dir = CMSSW / "outputs" / run_id
    log = REMOTE / f"{run_id}.log"
    inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES='{row.xrootd_url}'; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=100; "
        f"export NFRAME_MAXEVENTS_FULL={EVENTS_PER_STREAM}; "
        "bash /work/run_one_sample.sh"
    )
    command = ["docker", "run", "--rm", "-v", f"{CMSSW}:/work", IMAGE, "bash", "-lc", inside]
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        handle.write(" ".join(command) + "\n")
        try:
            completed = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, text=True, timeout=14_400)
            rc = completed.returncode
        except Exception as exc:
            handle.write(f"\nEXCEPTION {exc!r}\n")
            rc = 999
    output = output_dir / "event_features.csv"
    compact = REMOTE / f"{run_id}_event_features.csv"
    rows = 0
    if rc == 0 and output.exists():
        data = pd.read_csv(output, low_memory=False)
        data.insert(0, "primary_dataset", dataset)
        data.to_csv(compact, index=False)
        rows = len(data)
    return {"primary_dataset": dataset, "record_id": int(row.record_id), "file_index": int(row.file_index), "xrootd_url": row.xrootd_url, "status": "completed" if compact.exists() else "failed", "returncode": rc, "events_written": rows, "output_path": str(compact) if compact.exists() else "", "log_path": str(log)}


def main() -> None:
    for path in [TABLES, REMOTE]:
        path.mkdir(parents=True, exist_ok=True)
    requested = [x.strip() for x in os.environ.get("NFRAME_TRIGGER_CALIBRATION_DATASETS", ",".join(DATASETS)).split(",") if x.strip()]
    unknown = sorted(set(requested) - set(DATASETS))
    if unknown:
        raise ValueError(f"Unknown datasets: {unknown}")
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[(manifest["run_era"].eq("Run2016G")) & manifest["primary_dataset"].isin(requested)].copy()
    plan = manifest.sort_values("selection_order").groupby("primary_dataset", as_index=False).head(1)
    plan.to_csv(TABLES / "01_exact_trigger_calibration_plan.csv", index=False)
    results = [run_one(dataset, plan[plan["primary_dataset"].eq(dataset)].iloc[0]) for dataset in requested]
    current = pd.DataFrame(results)
    ledger_path = TABLES / "02_exact_trigger_calibration_ledger.csv"
    previous = pd.read_csv(ledger_path) if ledger_path.exists() else pd.DataFrame()
    if not previous.empty:
        previous = previous[~previous["primary_dataset"].isin(requested)].copy()
    ledger = pd.concat([previous, current], ignore_index=True, sort=False)
    ledger.to_csv(ledger_path, index=False)
    frames = [pd.read_csv(row.output_path, low_memory=False) for row in ledger.itertuples(index=False) if row.status == "completed"]
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(TABLES / "03_exact_trigger_calibration_events.csv", index=False)
    print(ledger.to_string(index=False))
    print(TABLES / "03_exact_trigger_calibration_events.csv")


if __name__ == "__main__":
    main()
