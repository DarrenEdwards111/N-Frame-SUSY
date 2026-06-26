import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
REAL_ROOT = Path(r"D:\cern_open_data\nframe_stage2_real_collision_20gb")
TABLES = ROOT / "results" / "tables"
LOGS = ROOT / "results" / "logs"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def safe_name(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text)


def inject_metadata(raw_csv: Path, out_csv: Path, row: pd.Series, start_index: int) -> int:
    df = pd.read_csv(raw_csv)
    df.insert(0, "sample_id", row.sample_id)
    df.insert(1, "primary_dataset", row.primary_dataset)
    df.insert(2, "record_id", int(row.record_id))
    df.insert(3, "source_file", row.source_file)
    df.insert(4, "source_file_stem", row.source_file_stem)
    df.insert(5, "source_file_index", int(row.source_file_index))
    df.insert(6, "local_input_path_or_container_path", f"{row.local_input_path} | {row.container_input_path}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(start_index, start_index + len(df)))
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df["include_in_real_only_analysis"] = True
    if "N_jets" not in df.columns and "N_jets_all" in df.columns:
        df["N_jets"] = df["N_jets_all"]
    df["extraction_limitations"] = "exact source-file provenance injected after one-file CMSSW extraction"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return len(df)


def run_one(row: pd.Series, out_dir: Path, max_events: int, mode: str, start_index: int) -> dict:
    run_id = f"{mode}_{row.sample_id}_{row.source_file_stem}"
    log_path = LOGS / f"real_only_{mode}_cmssw_{row.sample_id}_{row.source_file_stem}.log"
    LOGS.mkdir(parents=True, exist_ok=True)
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={row.container_input_path}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
    )
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{CMSSW_WORK}:/work",
        "-v", f"{REAL_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(docker_cmd) + "\n")
        proc = subprocess.run(docker_cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    out_csv = out_dir / f"{row.sample_id}_{row.source_file_stem}_event_features.csv"
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    n_events = 0
    if status == "success":
        n_events = inject_metadata(raw, out_csv, row, start_index)
    return {
        "mode": mode,
        "sample_id": row.sample_id,
        "primary_dataset": row.primary_dataset,
        "record_id": int(row.record_id),
        "source_file": row.source_file,
        "source_file_stem": row.source_file_stem,
        "source_file_index": int(row.source_file_index),
        "max_events": max_events,
        "status": status,
        "events_written": n_events,
        "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path),
        "returncode": proc.returncode,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["file_by_file_test", "full_file_by_file", "trigger_filter_5k_by_file", "trigger_filter_full"], required=True)
    parser.add_argument("--max-events", type=int, required=True)
    parser.add_argument("--limit-one-per-sample", action="store_true")
    args = parser.parse_args()

    manifest_path = TABLES / "real_only_file_by_file_manifest.csv"
    if not manifest_path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "21_prepare_real_only_file_by_file_extraction.py")], check=True)
    manifest = pd.read_csv(manifest_path)
    if args.limit_one_per_sample:
        manifest = manifest.sort_values(["sample_id", "source_file_index"]).groupby("sample_id", as_index=False).head(1)

    out_dir_map = {
        "file_by_file_test": "cmssw_real_only_file_by_file_test",
        "full_file_by_file": "cmssw_real_only_full_file_by_file",
        "trigger_filter_5k_by_file": "cmssw_real_only_trigger_filter_5k_by_file",
        "trigger_filter_full": "cmssw_real_only_trigger_filter_full",
    }
    out_dir_name = out_dir_map[args.mode]
    out_dir = ROOT / "data" / "processed" / out_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)
    starts = {sample: 0 for sample in manifest.sample_id.unique()}
    rows = []
    for _, row in manifest.sort_values(["sample_id", "source_file_index"]).iterrows():
        result = run_one(row, out_dir, args.max_events, args.mode, starts[row.sample_id])
        starts[row.sample_id] += result["events_written"]
        rows.append(result)
        pd.DataFrame(rows).to_csv(TABLES / f"real_only_{args.mode}_extraction_status.csv", index=False)
        if result["status"] != "success":
            print(pd.DataFrame(rows).to_string(index=False))
            raise SystemExit(2)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
