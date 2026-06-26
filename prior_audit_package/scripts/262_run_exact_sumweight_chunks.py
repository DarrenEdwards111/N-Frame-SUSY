from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CMSSW_WORK = ROOT / "cloud_remote_nframe_package" / "cmssw_full_extraction"
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
CHUNKS = CMSSW_WORK / "exact_sumweight_chunks"
PLAN = TABLES / "14_exact_genfilter_sumweight_file_plan.csv"
SUMMARY = TABLES / "15_exact_genfilter_sumweight_file_plan_summary.csv"
MASTER = TABLES / "16_exact_genfilter_sumweights_resumable.csv"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def read_done() -> pd.DataFrame:
    frames = []
    if MASTER.exists():
        frames.append(pd.read_csv(MASTER))
    old = CMSSW_WORK / "exact_genfilter_sumweight_output.csv"
    if old.exists():
        frames.append(pd.read_csv(old))
    if not frames:
        return pd.DataFrame(columns=["record_id", "file_index", "status"])
    df = pd.concat(frames, ignore_index=True)
    df["record_id"] = pd.to_numeric(df["record_id"], errors="coerce").astype("Int64")
    df["file_index"] = pd.to_numeric(df["file_index"], errors="coerce").astype("Int64")
    return df.drop_duplicates(["record_id", "file_index"], keep="last")


def main() -> None:
    if not PLAN.exists():
        raise FileNotFoundError(PLAN)
    CHUNKS.mkdir(parents=True, exist_ok=True)
    chunk_size = int(os.environ.get("NFRAME_SUMWEIGHT_CHUNK_SIZE", "20"))
    max_chunks = int(os.environ.get("NFRAME_SUMWEIGHT_MAX_CHUNKS", "1"))
    records = os.environ.get("NFRAME_SUMWEIGHT_RECORDS", "69548,68072,68082")
    wanted_records = {int(x.strip()) for x in records.split(",") if x.strip()}

    plan = pd.read_csv(PLAN)
    if SUMMARY.exists():
        summary = pd.read_csv(SUMMARY)
        full_online = set(
            pd.to_numeric(
                summary.loc[
                    summary["mode"].eq("full_online_exact_target") & summary["record_id"].isin(wanted_records),
                    "record_id",
                ],
                errors="coerce",
            )
            .dropna()
            .astype(int)
            .tolist()
        )
    else:
        full_online = wanted_records
    todo = plan[plan["record_id"].isin(full_online)].copy()
    done = read_done()
    done_ok = set(
        zip(
            done.loc[pd.to_numeric(done.get("status", 999), errors="coerce").eq(0), "record_id"].astype(int),
            done.loc[pd.to_numeric(done.get("status", 999), errors="coerce").eq(0), "file_index"].astype(int),
        )
    )
    todo = todo[
        ~todo.apply(lambda r: (int(r["record_id"]), int(r["file_index"])) in done_ok, axis=1)
    ].copy()
    todo = todo.sort_values(["record_id", "file_index"]).head(chunk_size * max_chunks)
    if todo.empty:
        print("No pending exact-sumweight files for selected records.")
        return

    all_outputs = []
    for chunk_id in range(max_chunks):
        chunk = todo.iloc[chunk_id * chunk_size : (chunk_id + 1) * chunk_size].copy()
        if chunk.empty:
            continue
        input_path = CHUNKS / f"sumweight_chunk_{chunk_id:03d}.csv"
        output_path = CHUNKS / f"sumweight_chunk_{chunk_id:03d}_output.csv"
        log_path = CHUNKS / f"sumweight_chunk_{chunk_id:03d}.log"
        chunk[["record_id", "process_family", "file_index", "xrootd_url"]].to_csv(input_path, index=False, header=False, lineterminator="\n")
        inside = (
            f"export NFRAME_SUMWEIGHT_LIST=/work/{input_path.relative_to(CMSSW_WORK).as_posix()}; "
            f"export NFRAME_SUMWEIGHT_OUTPUT=/work/{output_path.relative_to(CMSSW_WORK).as_posix()}; "
            "cd /work; "
            "root -l -b -q read_genfilter_lumi_summary_list.C"
        )
        cmd = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", IMAGE, "bash", "-lc", inside]
        print(f"running chunk {chunk_id}: {len(chunk)} files -> {output_path}", flush=True)
        with log_path.open("w", encoding="utf-8", errors="replace") as log:
            log.write(" ".join(cmd) + "\n")
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=21_600)
        if proc.returncode != 0:
            print(f"chunk {chunk_id} failed rc={proc.returncode}; see {log_path}", flush=True)
            break
        if output_path.exists():
            all_outputs.append(pd.read_csv(output_path))

    if all_outputs:
        new = pd.concat(all_outputs, ignore_index=True)
        old_master = pd.read_csv(MASTER) if MASTER.exists() else pd.DataFrame()
        old_cmssw = pd.read_csv(CMSSW_WORK / "exact_genfilter_sumweight_output.csv") if (CMSSW_WORK / "exact_genfilter_sumweight_output.csv").exists() else pd.DataFrame()
        combined = pd.concat([old_cmssw, old_master, new], ignore_index=True)
        combined = combined.drop_duplicates(["record_id", "file_index"], keep="last")
        combined.to_csv(MASTER, index=False)
        shutil.copy2(MASTER, CMSSW_WORK / "exact_genfilter_sumweight_output_resumable.csv")
        shutil.copy2(MASTER, OUT / "sumweight_chunks_latest.csv")
        print(combined.groupby(["record_id", "process_family", "status"]).size().reset_index(name="n").to_string(index=False))
        print(MASTER)


if __name__ == "__main__":
    main()
