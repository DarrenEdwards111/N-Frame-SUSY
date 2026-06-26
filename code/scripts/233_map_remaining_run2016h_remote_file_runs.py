from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "cloud_remote_nframe_package"
MANIFEST = PACKAGE / "manifests" / "01_real_cms_miniaod_remote_cloud_manifest.csv"
LEDGER = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation" / "remote_xrootd" / "remote_processing_ledger.csv"
LOCAL = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv"
OUT = ROOT / "outputs_run2016h_remote_local_composition_diagnostic"
TABLES = OUT / "tables"

IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
RUN_PATTERN = re.compile(r"(\d+)\s+0\s+0\s+0\s+\(Run\)")


def actual_run(url: str) -> tuple[int | None, str]:
    cmd = [
        "docker",
        "run",
        "--rm",
        IMAGE,
        "bash",
        "-lc",
        f"edmFileUtil -e '{url}' 2>/dev/null | head -12",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        text = result.stdout + "\n" + result.stderr
    except Exception as exc:
        return None, repr(exc)
    match = RUN_PATTERN.search(text)
    if match:
        return int(match.group(1)), "ok"
    return None, text[-500:].replace("\n", " ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-existing", action="store_true", help="Repair the saved mapping using captured metadata without remote calls.")
    args = parser.parse_args()
    TABLES.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[manifest["run_era"].eq("Run2016H")].copy()
    ledger = pd.read_csv(LEDGER)
    completed = ledger[ledger["status"].eq("completed")][["record_id", "primary_dataset", "file_index"]].drop_duplicates()
    manifest = manifest.merge(completed.assign(already_remote_completed=True), on=["record_id", "primary_dataset", "file_index"], how="left")
    remaining = manifest[manifest["already_remote_completed"].isna()].copy()

    local = pd.read_csv(LOCAL, usecols=["primary_dataset", "run"], low_memory=False)
    local_runs = local.groupby("primary_dataset")["run"].apply(lambda s: sorted(set(int(v) for v in s))).to_dict()
    mapping_path = TABLES / "05_remaining_run2016h_remote_file_run_mapping.csv"
    if args.from_existing and mapping_path.exists():
        out = pd.read_csv(mapping_path)
        repaired_runs = []
        for text in out["metadata_status"].fillna("").astype(str):
            match = RUN_PATTERN.search(text)
            repaired_runs.append(int(match.group(1)) if match else None)
        out["actual_run"] = repaired_runs
        out["matches_local_run_for_stream"] = [
            bool(run in set(local_runs.get(dataset, []))) if pd.notna(run) else False
            for run, dataset in zip(out["actual_run"], out["primary_dataset"])
        ]
        out["local_runs_for_stream"] = out["primary_dataset"].map(lambda d: ";".join(str(x) for x in local_runs.get(d, [])))
    else:
        rows = []
        for i, row in remaining.sort_values(["primary_dataset", "file_index"]).iterrows():
            run, status = actual_run(str(row["xrootd_url"]))
            rows.append(
                {
                    **row.to_dict(),
                    "actual_run": run,
                    "metadata_status": status,
                    "matches_local_run_for_stream": bool(run in set(local_runs.get(row["primary_dataset"], []))) if run is not None else False,
                    "local_runs_for_stream": ";".join(str(x) for x in local_runs.get(row["primary_dataset"], [])),
                }
            )
            print(f"mapped {len(rows)}/{len(remaining)} {row['primary_dataset']} file={row['file_index']} run={run} {status}", flush=True)
        out = pd.DataFrame(rows)
    out.to_csv(TABLES / "05_remaining_run2016h_remote_file_run_mapping.csv", index=False)
    matched = out[out["matches_local_run_for_stream"]].copy()
    matched.to_csv(TABLES / "06_run2016h_matched_run_remote_candidates.csv", index=False)
    summary = (
        out.groupby("primary_dataset", as_index=False)
        .agg(files_mapped=("xrootd_url", "count"), known_runs=("actual_run", lambda s: ";".join(str(x) for x in sorted(set(s.dropna().astype(int))))), matched_local_runs=("matches_local_run_for_stream", "sum"))
    )
    summary.to_csv(TABLES / "07_remaining_run2016h_mapping_summary.csv", index=False)
    print(TABLES / "05_remaining_run2016h_remote_file_run_mapping.csv")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
