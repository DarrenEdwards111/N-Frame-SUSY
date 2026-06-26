from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "cloud_remote_nframe_package"
MANIFEST = PACKAGE / "manifests" / "01_real_cms_miniaod_remote_cloud_manifest.csv"
OUT = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation"
REMOTE = OUT / "remote_xrootd"
LEDGER = REMOTE / "remote_processing_ledger.csv"
CMSSW_WORK = PACKAGE / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def completed_keys() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame(columns=["record_id", "primary_dataset", "file_index"])
    ledger = pd.read_csv(LEDGER)
    return ledger[ledger["status"].eq("completed")][["record_id", "primary_dataset", "file_index"]].drop_duplicates()


def run_group(dataset: str, group: pd.DataFrame) -> dict[str, object]:
    run_id = f"remote_group_run2015d_{dataset.lower()}_holdout"
    out_dir = CMSSW_WORK / "outputs" / run_id
    log_path = REMOTE / f"{run_id}.log"
    urls = ",".join(group["xrootd_url"].astype(str))
    max_events = 5000 * len(group)
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES='{urls}'; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=100; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", IMAGE, "bash", "-lc", cmd_inside]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        try:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=7200)
            returncode = result.returncode
        except Exception as exc:
            log.write("\nEXCEPTION " + repr(exc) + "\n")
            returncode = 999
    output_path = out_dir / "event_features.csv"
    return {
        "dataset_label": f"Run2015D_{dataset}_remote_holdout_group",
        "record_id": int(group["record_id"].iloc[0]),
        "process_family": "real_collision_data",
        "primary_dataset": dataset,
        "run_era": "Run2015D",
        "data_tier": "MINIAOD",
        "xrootd_url": ";".join(group["xrootd_url"].astype(str)),
        "file_index": -1,
        "planned_max_events": max_events,
        "status": "completed" if returncode == 0 and output_path.exists() else "failed",
        "output_path": str(output_path) if output_path.exists() else "",
        "log_path": str(log_path),
        "returncode": returncode,
        "source_file_count": len(group),
        "validation_sample_id": "Run2015D_remote_mht_aware_holdout",
        "notes": "disjoint remaining Run2015D files; frozen OPQ held-out validation; grouped remote MHT-aware CMSSW extraction",
    }


def main() -> None:
    REMOTE.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[manifest["run_era"].eq("Run2015D")].copy()
    complete = completed_keys()
    remaining = manifest.merge(complete.assign(already_completed=True), on=["record_id", "primary_dataset", "file_index"], how="left")
    remaining = remaining[remaining["already_completed"].isna()].copy()
    plan = (
        remaining.groupby("primary_dataset", as_index=False)
        .agg(files=("xrootd_url", "count"), total_size_gb=("size_gb", "sum"))
    )
    plan["planned_max_events"] = plan["files"] * 5000
    plan.to_csv(OUT / "tables" / "12_run2015d_holdout_grouped_remote_plan.csv", index=False)
    print(plan.to_string(index=False), flush=True)

    results = []
    for dataset in ["HTMHT", "MET", "JetHT", "SingleMuon"]:
        group = remaining[remaining["primary_dataset"].eq(dataset)]
        if group.empty:
            continue
        print(f"starting {dataset}: {len(group)} files", flush=True)
        result = run_group(dataset, group)
        results.append(result)
        print(f"finished {dataset}: {result['status']} rc={result['returncode']}", flush=True)

    previous = pd.read_csv(LEDGER) if LEDGER.exists() else pd.DataFrame()
    all_rows = pd.concat([previous, pd.DataFrame(results)], ignore_index=True, sort=False)
    all_rows.to_csv(LEDGER, index=False)
    pd.DataFrame(results).to_csv(OUT / "tables" / "13_run2015d_holdout_grouped_remote_ledger.csv", index=False)
    print(OUT / "tables" / "13_run2015d_holdout_grouped_remote_ledger.csv")


if __name__ == "__main__":
    main()
