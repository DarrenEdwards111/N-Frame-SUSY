from __future__ import annotations

"""Grouped remote Run2016G validation extraction for frozen OPQ replication."""

import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "cloud_remote_nframe_package"
MANIFEST = PACKAGE / "manifests" / "01_real_cms_miniaod_remote_cloud_manifest.csv"
OUT = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation"
TABLES = OUT / "tables"
REMOTE = OUT / "remote_xrootd"
LEDGER = REMOTE / "remote_processing_ledger.csv"
CMSSW_WORK = PACKAGE / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
VALIDATION_ID = "Run2016G_remote_mht_aware_fresh"
FILES_PER_DATASET = 3
EVENTS_PER_FILE = 5_000


def run_group(dataset: str, group: pd.DataFrame) -> dict[str, object]:
    run_id = f"remote_group_run2016g_{dataset.lower()}_fresh"
    out_dir = CMSSW_WORK / "outputs" / run_id
    log_path = REMOTE / f"{run_id}.log"
    urls = ",".join(group["xrootd_url"].astype(str))
    max_events = EVENTS_PER_FILE * len(group)
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
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=14_400)
            returncode = result.returncode
        except Exception as exc:
            log.write("\nEXCEPTION " + repr(exc) + "\n")
            returncode = 999
    output_path = out_dir / "event_features.csv"
    status = "completed" if returncode == 0 and output_path.exists() else "failed"
    events_written = 0
    if output_path.exists():
        try:
            events_written = max(0, sum(1 for _ in output_path.open("r", encoding="utf-8", errors="replace")) - 1)
        except Exception:
            events_written = 0
    return {
        "dataset_label": f"Run2016G_{dataset}_remote_fresh_group",
        "record_id": int(group["record_id"].iloc[0]),
        "process_family": "real_collision_data",
        "primary_dataset": dataset,
        "run_era": "Run2016G",
        "data_tier": "MINIAOD",
        "xrootd_url": ";".join(group["xrootd_url"].astype(str)),
        "file_index": -100 - ["HTMHT", "MET", "JetHT", "SingleMuon"].index(dataset),
        "planned_max_events": max_events,
        "status": status,
        "output_path": str(output_path) if output_path.exists() else "",
        "log_path": str(log_path),
        "returncode": returncode,
        "source_file_count": len(group),
        "events_written": events_written,
        "validation_sample_id": VALIDATION_ID,
        "notes": "fresh grouped Run2016G remote MHT-aware CMSSW extraction; fixed OPQ validation; compact features only",
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REMOTE.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[manifest["run_era"].eq("Run2016G")].copy()
    selected = []
    for dataset in ["HTMHT", "MET", "JetHT", "SingleMuon"]:
        group = manifest[manifest["primary_dataset"].eq(dataset)].sort_values("selection_order").head(FILES_PER_DATASET)
        selected.append(group)
    plan = pd.concat(selected, ignore_index=True)
    plan.to_csv(TABLES / "14_run2016g_fresh_grouped_remote_plan.csv", index=False)
    print(
        plan.groupby("primary_dataset", as_index=False)
        .agg(files=("xrootd_url", "count"), total_size_gb=("size_gb", "sum"))
        .to_string(index=False),
        flush=True,
    )

    results = []
    for dataset in ["HTMHT", "MET", "JetHT", "SingleMuon"]:
        group = plan[plan["primary_dataset"].eq(dataset)]
        print(f"starting {dataset}: {len(group)} files", flush=True)
        result = run_group(dataset, group)
        results.append(result)
        print(f"finished {dataset}: {result['status']} rows={result['events_written']} rc={result['returncode']}", flush=True)

    previous = pd.read_csv(LEDGER) if LEDGER.exists() else pd.DataFrame()
    current = pd.DataFrame(results)
    if not previous.empty:
        previous = previous[previous.get("validation_sample_id", "").astype(str).ne(VALIDATION_ID)].copy()
    all_rows = pd.concat([previous, current], ignore_index=True, sort=False)
    all_rows.to_csv(LEDGER, index=False)
    current.to_csv(TABLES / "15_run2016g_fresh_grouped_remote_ledger.csv", index=False)
    print(TABLES / "15_run2016g_fresh_grouped_remote_ledger.csv")


if __name__ == "__main__":
    main()
