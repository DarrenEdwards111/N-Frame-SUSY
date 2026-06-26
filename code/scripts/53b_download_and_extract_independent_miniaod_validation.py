import subprocess
from pathlib import Path

import pandas as pd
import requests
import urllib3


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_validation_real_independent")
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
LOGS = ROOT / "results" / "logs"
OUT_DIR = ROOT / "data" / "processed" / "independent_validation_miniaod"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def download_file(row) -> Path:
    target = DOWNLOAD_ROOT / row.target_subdir / row.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == int(row.size_bytes):
        return target
    urllib3.disable_warnings()
    with requests.get(row.https_url, stream=True, timeout=60, verify=False) as r:
        r.raise_for_status()
        tmp = target.with_suffix(target.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=1024 * 1024 * 8):
                if chunk:
                    fh.write(chunk)
        tmp.replace(target)
    return target


def inject_metadata(raw_csv: Path, out_csv: Path, row, local_path: Path) -> int:
    df = pd.read_csv(raw_csv)
    df.insert(0, "sample_id", f"validation_{row.primary_dataset.lower()}_run2016h_collision")
    df.insert(1, "primary_dataset", row.primary_dataset)
    df.insert(2, "record_id", int(row.record_id))
    df.insert(3, "source_file", row.filename)
    df.insert(4, "source_file_stem", Path(row.filename).stem)
    df.insert(5, "source_file_index", 0)
    df.insert(6, "local_input_path_or_container_path", f"{local_path} | /data/{row.target_subdir}/{row.filename}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(len(df)))
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df["include_in_real_only_analysis"] = True
    if "N_jets" not in df and "N_jets_all" in df:
        df["N_jets"] = df["N_jets_all"]
    df["validation_route"] = "independent_run2016h_miniaod"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return len(df)


def run_cmssw(row, local_path: Path) -> dict:
    run_id = f"independent_validation_miniaod_{row.primary_dataset.lower()}_{Path(row.filename).stem}"
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{run_id}.log"
    container_path = f"/data/{row.target_subdir}/{row.filename}".replace("\\", "/")
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={container_path}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
        "export NFRAME_MAXEVENTS_FULL=-1; "
        "bash /work/run_one_sample.sh"
    )
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{CMSSW_WORK}:/work",
        "-v", f"{DOWNLOAD_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(docker_cmd) + "\n")
        proc = subprocess.run(docker_cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    out_csv = OUT_DIR / f"validation_{row.primary_dataset.lower()}_{Path(row.filename).stem}_event_features.csv"
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    n = inject_metadata(raw, out_csv, row, local_path) if status == "success" else 0
    return {
        "record_id": int(row.record_id), "primary_dataset": row.primary_dataset, "filename": row.filename,
        "downloaded_path": str(local_path), "expected_size_bytes": int(row.size_bytes),
        "actual_size_bytes": local_path.stat().st_size if local_path.exists() else 0,
        "extraction_status": status, "events_written": n, "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path), "returncode": proc.returncode,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    plan = pd.read_csv(TABLES / "independent_real_validation_selected_download_plan.csv")
    if plan["size_gb"].sum() > 20:
        raise SystemExit("Planned download is above 20 GB; user approval required.")
    rows = []
    for row in plan.itertuples(index=False):
        local = download_file(row)
        rows.append(run_cmssw(row, local))
        pd.DataFrame(rows).to_csv(TABLES / "independent_validation_download_manifest.csv", index=False)
    manifest = pd.DataFrame(rows)
    frames = [pd.read_csv(p) for p in manifest.loc[manifest.extraction_status == "success", "output_csv"]]
    combined = pd.concat(frames, ignore_index=True)
    combined_path = OUT_DIR / "validation_miniaod_event_features.csv"
    combined.to_csv(combined_path, index=False)
    summary = combined.groupby(["sample_id", "primary_dataset", "source_file"], as_index=False).agg(events=("event", "count"), runs=("run", "nunique"))
    summary.to_csv(TABLES / "independent_miniaod_validation_summary.csv", index=False)
    report = [
        "# Independent MiniAOD Validation Extraction Report",
        "",
        "Date: 2026-06-09",
        "",
        "Independent Run2016H MiniAOD real collision files were downloaded and processed with the existing CMSSW extractor. No simulated samples were used.",
        "",
        "## Manifest",
        "",
        manifest.to_markdown(index=False),
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False),
        "",
        f"Combined output: `{combined_path}`",
    ]
    (REPORTS / "INDEPENDENT_VALIDATION_DOWNLOAD_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    (REPORTS / "INDEPENDENT_MINIAOD_VALIDATION_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(manifest.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
