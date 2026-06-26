import argparse
import subprocess
from pathlib import Path

import pandas as pd
import requests
import uproot
import urllib3


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
OLD_DATA_ROOT = Path(r"D:\cern_open_data\nframe_validation_real_independent")
NEW_DATA_ROOT = Path(r"D:\cern_open_data\nframe_validation_real_independent_expanded")
OLD_PROCESSED = ROOT / "data" / "processed" / "independent_validation_miniaod_full"
SMOKE_DIR = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_smoke"
FULL_DIR = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
LOGS = ROOT / "results" / "logs"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"

RECORDS = {
    30541: ("JetHT", 2),
    30542: ("MET", 2),
    30546: ("SingleMuon", 1),
}
EXISTING_COMBINED = OLD_PROCESSED / "run2016h_miniaod_event_features_combined.csv"
EXISTING_SCORED = OLD_PROCESSED / "run2016h_miniaod_with_fitted_nframe_score.csv"


def safe(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


def existing_filenames() -> set[str]:
    roots = [OLD_DATA_ROOT, NEW_DATA_ROOT]
    out = set()
    for root in roots:
        if root.exists():
            out.update(p.name for p in root.rglob("*.root"))
    return out


def fetch_files(record_id: int) -> list[dict]:
    rec = requests.get(f"https://opendata.cern.ch/api/records/{record_id}", timeout=30).json()
    md = rec["metadata"]
    files = []
    for index in md.get("_file_indices", []):
        files.extend(index.get("files", []))
    return files


def audit_current() -> None:
    reports = [
        REPORTS / "RUN2016H_MINIAOD_INDEPENDENT_VALIDATION_REPORT.md",
        REPORTS / "MINIAOD_VS_NANOAOD_VALIDATION_COMPARISON.md",
        REPORTS / "UPDATE_TO_DARREN_RUN2016H_MINIAOD_VALIDATION.md",
        REPORTS / "FITTED_NFRAME_PARAMETER_INTERPRETATION_FOR_DARREN.md",
        REPORTS / "FITTED_NFRAME_BOUNDARY_EQUATION.md",
    ]
    df = pd.read_csv(EXISTING_SCORED)
    summary = df.groupby(["sample_id", "primary_dataset", "source_file"], as_index=False).agg(
        events=("event", "count"),
        runs=("run", "nunique"),
        lumis=("lumi", "nunique"),
        mean_fitted=("B_NF_fitted_run2016h_z", "mean"),
    )
    tails = pd.read_csv(TABLES / "run2016h_miniaod_fitted_top_tail_composition.csv")
    drivers = pd.read_csv(TABLES / "run2016h_miniaod_fitted_parameter_drivers.csv")
    state = summary.copy()
    state["combined_exists"] = EXISTING_COMBINED.exists()
    state["scored_exists"] = EXISTING_SCORED.exists()
    state.to_csv(TABLES / "expanded_run2016h_validation_current_state.csv", index=False)
    report = [
        "# Expanded Run2016H Validation Audit",
        "",
        "Date: 2026-06-09",
        "",
        "This audits the current one-file-per-dataset Run2016H MiniAOD validation before adding more real collision files.",
        "",
        "## Existing Reports",
        "",
        pd.DataFrame({"report": [str(p),], "exists": [p.exists()]} for p in reports).to_markdown(index=False),
        "",
        "## Current Events",
        "",
        summary.to_markdown(index=False),
        "",
        "## Current Top-Tail Composition",
        "",
        tails.to_markdown(index=False),
        "",
        "## Current Parameter Drivers",
        "",
        drivers.to_markdown(index=False),
        "",
        "## Current Limitations",
        "",
        "- Only one independent Run2016H MiniAOD file per dataset has been tested.",
        "- JetHT enrichment and SingleMuon depletion replicated, but MET remained mixed.",
        "- The next check is whether more MET and JetHT files make the MET result clearer or show it is file-specific.",
    ]
    (REPORTS / "EXPANDED_RUN2016H_VALIDATION_AUDIT.md").write_text("\n".join(report), encoding="utf-8")


def identify_candidates() -> pd.DataFrame:
    already = existing_filenames()
    rows = []
    selected_rows = []
    for record_id, (primary, target_n) in RECORDS.items():
        files = sorted(fetch_files(record_id), key=lambda f: f["size"])
        eligible = []
        for f in files:
            row = {
                "record_id": record_id,
                "primary_dataset": primary,
                "filename": f["filename"],
                "size_bytes": int(f["size"]),
                "size_gb": f["size"] / 1e9,
                "url": uri_to_https(f["uri"]),
                "already_downloaded": f["filename"] in already,
                "priority": "",
                "reason": "",
            }
            if row["already_downloaded"]:
                row["priority"] = "exclude"
                row["reason"] = "already downloaded"
            else:
                row["priority"] = "candidate"
                row["reason"] = "real Run2016H MiniAOD; manageable candidate"
                eligible.append(row)
            rows.append(row)
        for i, row in enumerate(eligible[:target_n], start=1):
            row = dict(row)
            row["priority"] = f"selected_{i}"
            row["reason"] = "selected to expand MET/JetHT coverage" if primary in {"MET", "JetHT"} else "selected as manageable SingleMuon control"
            selected_rows.append(row)
    candidates = pd.DataFrame(rows)
    for row in selected_rows:
        mask = (candidates.record_id.eq(row["record_id"]) & candidates.filename.eq(row["filename"]))
        candidates.loc[mask, ["priority", "reason"]] = [row["priority"], row["reason"]]
    candidates.to_csv(TABLES / "expanded_run2016h_miniaod_candidate_files.csv", index=False)
    selected = pd.DataFrame(selected_rows)
    selected.to_csv(TABLES / "expanded_run2016h_miniaod_selected_files.csv", index=False)
    total = selected["size_gb"].sum()
    report = [
        "# Expanded Run2016H MiniAOD Download Plan",
        "",
        "Date: 2026-06-09",
        "",
        f"Selected new real Run2016H MiniAOD download size: {total:.3f} GB.",
        "",
        "The selection prioritises two extra MET files and two extra JetHT files, plus one manageable SingleMuon file for control balance. No simulated samples are included.",
        "",
        "## Selected Files",
        "",
        selected.to_markdown(index=False),
        "",
        "## Candidate Inventory",
        "",
        candidates.head(60).to_markdown(index=False),
    ]
    (REPORTS / "EXPANDED_RUN2016H_MINIAOD_DOWNLOAD_PLAN.md").write_text("\n".join(report), encoding="utf-8")
    print(selected.to_string(index=False))
    print(f"Selected total GB: {total:.3f}")
    return selected


def download_selected(selected: pd.DataFrame) -> pd.DataFrame:
    if selected["size_gb"].sum() > 15:
        raise SystemExit("Selected download is above 15 GB; user approval required.")
    urllib3.disable_warnings()
    rows = []
    for row in selected.itertuples(index=False):
        target = NEW_DATA_ROOT / row.primary_dataset.lower() / str(row.record_id) / row.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.stat().st_size != int(row.size_bytes):
            with requests.get(row.url, stream=True, timeout=60, verify=False) as r:
                r.raise_for_status()
                tmp = target.with_suffix(target.suffix + ".part")
                with tmp.open("wb") as fh:
                    for chunk in r.iter_content(1024 * 1024 * 8):
                        if chunk:
                            fh.write(chunk)
                tmp.replace(target)
        readable = False
        keys = ""
        try:
            with uproot.open(target) as f:
                keys = ";".join(f.keys()[:8])
                readable = True
        except Exception as exc:
            keys = f"uproot_read_error: {exc}"
        rows.append({
            "record_id": row.record_id,
            "primary_dataset": row.primary_dataset,
            "filename": row.filename,
            "expected_size_bytes": int(row.size_bytes),
            "actual_size_bytes": target.stat().st_size,
            "size_matches": target.stat().st_size == int(row.size_bytes),
            "path": str(target),
            "root_readable_by_uproot": readable,
            "top_level_keys_or_error": keys,
            "real_or_simulated": "real collision",
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "expanded_run2016h_miniaod_download_manifest.csv", index=False)
    report = [
        "# Expanded Run2016H MiniAOD Download Report",
        "",
        "Date: 2026-06-09",
        "",
        "Additional real CMS Run2016H MiniAOD files were downloaded into a separate expanded-validation folder. Previous outputs were preserved.",
        "",
        manifest.to_markdown(index=False),
    ]
    (REPORTS / "EXPANDED_RUN2016H_MINIAOD_DOWNLOAD_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(manifest.to_string(index=False))
    return manifest


def inject_metadata(raw_csv: Path, out_csv: Path, item: pd.Series, mode: str) -> int:
    df = pd.read_csv(raw_csv)
    stem = Path(item.filename).stem
    df.insert(0, "sample_id", f"expanded_validation_{item.primary_dataset.lower()}_run2016h_miniaod_collision")
    df.insert(1, "primary_dataset", item.primary_dataset)
    df.insert(2, "record_id", int(item.record_id))
    df.insert(3, "source_file", item.filename)
    df.insert(4, "source_file_stem", stem)
    df.insert(5, "source_file_index", 0)
    df.insert(6, "local_input_path_or_container_path", f"{item.path} | /data/{item.primary_dataset.lower()}/{item.record_id}/{item.filename}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(len(df)))
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df["include_in_real_only_analysis"] = True
    if "N_jets" not in df.columns and "N_jets_all" in df.columns:
        df["N_jets"] = df["N_jets_all"]
    df["validation_route"] = "expanded_independent_run2016h_miniaod"
    df["extraction_limitations"] = f"expanded Run2016H MiniAOD {mode} extraction"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return len(df)


def run_cmssw_one(item: pd.Series, mode: str, max_events: int, out_dir: Path) -> dict:
    stem = Path(item.filename).stem
    run_id = f"expanded_run2016h_{mode}_{safe(item.primary_dataset)}_{stem}"
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"expanded_run2016h_miniaod_{safe(item.primary_dataset)}_{stem}_{mode}_extraction.log"
    container_path = f"/data/{item.primary_dataset.lower()}/{item.record_id}/{item.filename}"
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={container_path}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{CMSSW_WORK}:/work",
        "-v", f"{NEW_DATA_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    suffix = "1000_event_features.csv" if mode == "smoke" else "event_features.csv"
    out_csv = out_dir / f"{safe(item.primary_dataset)}_{stem}_{suffix}"
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    n = inject_metadata(raw, out_csv, item, mode) if status == "success" else 0
    return {
        "mode": mode,
        "primary_dataset": item.primary_dataset,
        "record_id": int(item.record_id),
        "source_file": item.filename,
        "status": status,
        "events_written": n,
        "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path),
        "returncode": proc.returncode,
    }


def smoke_and_full(manifest: pd.DataFrame) -> None:
    SMOKE_DIR.mkdir(parents=True, exist_ok=True)
    FULL_DIR.mkdir(parents=True, exist_ok=True)
    smoke_rows = []
    for item in manifest.itertuples(index=False):
        res = run_cmssw_one(item, "smoke", 1000, SMOKE_DIR)
        smoke_rows.append(res)
        pd.DataFrame(smoke_rows).to_csv(TABLES / "expanded_run2016h_miniaod_smoke_status.csv", index=False)
    smoke = pd.DataFrame(smoke_rows)
    required = ["MET_pt", "HT", "N_jets_30", "N_jets_50", "N_btags_medium", "N_leptons", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count", "run", "lumi", "event"]
    val_rows = []
    for path in smoke.loc[smoke.status.eq("success"), "output_csv"]:
        df = pd.read_csv(path, nrows=5)
        val_rows.append({"file": Path(path).name, "missing_required_columns": ";".join([c for c in required if c not in df.columns]), "trigger_filter_columns": ";".join([c for c in df.columns if c.startswith("HLT_") or c.startswith("pass_")])})
    smoke_val = pd.DataFrame(val_rows)
    smoke_val.to_csv(TABLES / "expanded_run2016h_miniaod_smoke_validation.csv", index=False)
    (REPORTS / "EXPANDED_RUN2016H_MINIAOD_SMOKE_REPORT.md").write_text(
        "\n".join(["# Expanded Run2016H MiniAOD Smoke Report", "", "Date: 2026-06-09", "", "## Smoke Status", "", smoke.to_markdown(index=False), "", "## Variable Validation", "", smoke_val.to_markdown(index=False)]),
        encoding="utf-8",
    )
    full_rows = []
    for item in manifest[manifest.filename.isin(smoke.loc[smoke.status.eq("success"), "source_file"])].itertuples(index=False):
        res = run_cmssw_one(item, "full", -1, FULL_DIR)
        full_rows.append(res)
        pd.DataFrame(full_rows).to_csv(TABLES / "expanded_run2016h_miniaod_full_status.csv", index=False)
    full = pd.DataFrame(full_rows)
    frames = []
    if EXISTING_COMBINED.exists():
        frames.append(pd.read_csv(EXISTING_COMBINED))
    frames.extend(pd.read_csv(path) for path in full.loc[full.status.eq("success"), "output_csv"])
    combined = pd.concat(frames, ignore_index=True)
    combined_path = FULL_DIR / "expanded_run2016h_miniaod_event_features_combined.csv"
    combined.to_csv(combined_path, index=False)
    summary = combined.groupby(["primary_dataset", "source_file"], as_index=False).agg(events=("event", "count"), runs=("run", "nunique"))
    (REPORTS / "EXPANDED_RUN2016H_MINIAOD_FULL_EXTRACTION_REPORT.md").write_text(
        "\n".join(["# Expanded Run2016H MiniAOD Full Extraction Report", "", "Date: 2026-06-09", "", "## Full Status", "", full.to_markdown(index=False), "", "## Combined Summary", "", summary.to_markdown(index=False), "", f"Combined output: `{combined_path}`"]),
        encoding="utf-8",
    )
    print(full.to_string(index=False))
    print(summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["audit_plan", "download", "extract", "all"], default="all")
    args = parser.parse_args()
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if args.phase in {"audit_plan", "all"}:
        audit_current()
        selected = identify_candidates()
    else:
        selected = pd.read_csv(TABLES / "expanded_run2016h_miniaod_selected_files.csv")
    if args.phase == "audit_plan":
        return
    if args.phase in {"download", "all"}:
        manifest = download_selected(selected)
    else:
        manifest = pd.read_csv(TABLES / "expanded_run2016h_miniaod_download_manifest.csv")
    if args.phase == "download":
        return
    if args.phase in {"extract", "all"}:
        smoke_and_full(manifest)


if __name__ == "__main__":
    main()
