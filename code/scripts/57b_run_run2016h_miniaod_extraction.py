import argparse
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
DATA_ROOT = Path(r"D:\cern_open_data\nframe_validation_real_independent")
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
LOGS = ROOT / "results" / "logs"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"

FILES = [
    {
        "sample_id": "validation_jetht_run2016h_miniaod_collision",
        "primary_dataset": "JetHT",
        "record_id": 30541,
        "filename": "FC0EE8E8-8640-8649-B22A-F0C750DD5DE0.root",
        "relpath": "jetht_run2016h_validation/30541/FC0EE8E8-8640-8649-B22A-F0C750DD5DE0.root",
        "short": "jetht",
    },
    {
        "sample_id": "validation_met_run2016h_miniaod_collision",
        "primary_dataset": "MET",
        "record_id": 30542,
        "filename": "6D1DA38B-AEFA-3849-B346-3B2653B46C9E.root",
        "relpath": "met_run2016h_validation/30542/6D1DA38B-AEFA-3849-B346-3B2653B46C9E.root",
        "short": "met",
    },
    {
        "sample_id": "validation_singlemuon_run2016h_miniaod_collision",
        "primary_dataset": "SingleMuon",
        "record_id": 30546,
        "filename": "E5768FBE-A1B2-F047-999D-0B5C0B051827.root",
        "relpath": "singlemuon_run2016h_validation/30546/E5768FBE-A1B2-F047-999D-0B5C0B051827.root",
        "short": "singlemuon",
    },
]


def inject(raw_csv: Path, out_csv: Path, item: dict) -> int:
    df = pd.read_csv(raw_csv)
    stem = Path(item["filename"]).stem
    df.insert(0, "sample_id", item["sample_id"])
    df.insert(1, "primary_dataset", item["primary_dataset"])
    df.insert(2, "record_id", item["record_id"])
    df.insert(3, "source_file", item["filename"])
    df.insert(4, "source_file_stem", stem)
    df.insert(5, "source_file_index", 0)
    df.insert(6, "local_input_path_or_container_path", f"{DATA_ROOT / item['relpath']} | /data/{item['relpath']}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(len(df)))
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df["include_in_real_only_analysis"] = True
    if "N_jets" not in df.columns and "N_jets_all" in df.columns:
        df["N_jets"] = df["N_jets_all"]
    df["validation_route"] = "independent_run2016h_miniaod"
    df["extraction_limitations"] = "Run2016H independent MiniAOD extraction with exact source-file provenance"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return len(df)


def run_one(item: dict, mode: str, max_events: int, out_dir: Path) -> dict:
    LOGS.mkdir(parents=True, exist_ok=True)
    run_id = f"run2016h_miniaod_{mode}_{item['short']}"
    log_name = f"run2016h_miniaod_{item['short']}_{'smoke' if mode == 'smoke' else 'full'}_extraction.log"
    log_path = LOGS / log_name
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES=/data/{item['relpath']}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{CMSSW_WORK}:/work",
        "-v", f"{DATA_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    suffix = "1000_event_features.csv" if mode == "smoke" else "miniaod_event_features.csv"
    out_name = f"{item['short']}_run2016h_{suffix}" if mode == "smoke" else f"run2016h_{item['short']}_{suffix}"
    out_csv = out_dir / out_name
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    n = inject(raw, out_csv, item) if status == "success" else 0
    return {
        "mode": mode,
        "primary_dataset": item["primary_dataset"],
        "record_id": item["record_id"],
        "source_file": item["filename"],
        "max_events": max_events,
        "status": status,
        "events_written": n,
        "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path),
        "returncode": proc.returncode,
    }


def validate_smoke(out_dir: Path, status: pd.DataFrame) -> pd.DataFrame:
    required = [
        "sample_id", "primary_dataset", "record_id", "source_file", "source_file_stem", "run", "lumi", "event",
        "MET_pt", "MET_phi", "HT", "N_jets_30", "N_jets_50", "leading_jet_pt", "subleading_jet_pt",
        "N_muons", "N_electrons", "N_leptons", "N_btags_loose", "N_btags_medium", "N_btags_tight",
        "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count",
    ]
    rows = []
    for path in out_dir.glob("*_1000_event_features.csv"):
        df = pd.read_csv(path, nrows=1005)
        rows.append({
            "file": path.name,
            "rows": len(pd.read_csv(path, usecols=["event"])),
            "missing_required_columns": ";".join([c for c in required if c not in df.columns]),
            "trigger_filter_columns": ";".join([c for c in df.columns if c.startswith("HLT_") or c.startswith("pass_")]),
        })
    validation = pd.DataFrame(rows)
    validation.to_csv(TABLES / "run2016h_miniaod_smoke_validation.csv", index=False)
    report = [
        "# Run2016H MiniAOD Smoke Extraction Report",
        "",
        "Date: 2026-06-09",
        "",
        "Smoke extraction used maxEvents=1000 for each independent real Run2016H MiniAOD file.",
        "",
        "## Extraction Status",
        "",
        status.to_markdown(index=False),
        "",
        "## Variable Validation",
        "",
        validation.to_markdown(index=False),
    ]
    (REPORTS / "RUN2016H_MINIAOD_SMOKE_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    args = parser.parse_args()
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / "data" / "processed" / ("independent_validation_miniaod_smoke" if args.mode == "smoke" else "independent_validation_miniaod_full")
    out_dir.mkdir(parents=True, exist_ok=True)
    max_events = 1000 if args.mode == "smoke" else -1
    rows = []
    for item in FILES:
        result = run_one(item, args.mode, max_events, out_dir)
        rows.append(result)
        status = pd.DataFrame(rows)
        status.to_csv(TABLES / f"run2016h_miniaod_{args.mode}_extraction_status.csv", index=False)
        if result["status"] != "success":
            print(status.to_string(index=False))
            raise SystemExit(2)
    status = pd.DataFrame(rows)
    if args.mode == "smoke":
        validation = validate_smoke(out_dir, status)
        if validation["missing_required_columns"].fillna("").ne("").any():
            raise SystemExit(2)
    else:
        frames = [pd.read_csv(p) for p in status["output_csv"]]
        combined = pd.concat(frames, ignore_index=True)
        combined_path = out_dir / "run2016h_miniaod_event_features_combined.csv"
        combined.to_csv(combined_path, index=False)
        summary = combined.groupby(["sample_id", "primary_dataset", "source_file"], as_index=False).agg(events=("event", "count"), runs=("run", "nunique"))
        summary.to_csv(TABLES / "run2016h_miniaod_full_extraction_summary.csv", index=False)
        report = [
            "# Run2016H MiniAOD Full Extraction Report",
            "",
            "Date: 2026-06-09",
            "",
            "Full extraction used maxEvents=-1 for each independent real Run2016H MiniAOD file.",
            "",
            "## Extraction Status",
            "",
            status.to_markdown(index=False),
            "",
            "## Summary",
            "",
            summary.to_markdown(index=False),
            "",
            f"Combined output: `{combined_path}`",
        ]
        (REPORTS / "RUN2016H_MINIAOD_FULL_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(status.to_string(index=False))


if __name__ == "__main__":
    main()
