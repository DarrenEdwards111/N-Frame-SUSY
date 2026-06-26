from __future__ import annotations

import shutil
import ssl
import subprocess
import urllib.request
from pathlib import Path

import pandas as pd

from fuller_component_common import DATE, IMAGE, LOGS, MAIN, MAX_BYTES, REPORTS, ROOT, TABLES, apply_frozen_bnf, url_to_https


SIGNAL_ROOT = Path(r"D:\cern_open_data\nframe_fuller_component_susy_signals")
SIGNAL_OUT = ROOT / "data" / "processed" / "fuller_component_susy_signals"
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"


def ensure_dirs() -> None:
    for path in [SIGNAL_ROOT, SIGNAL_OUT, TABLES, REPORTS, LOGS]:
        path.mkdir(parents=True, exist_ok=True)


def clean_slug(text: str, record_id: int) -> str:
    text = str(text).lower().replace("+", "plus").replace("/", "_").replace(" ", "_")
    text = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in text).strip("_")
    return f"{text[:80]}_{int(record_id)}"


def selected_plan() -> pd.DataFrame:
    plan = pd.read_csv(TABLES / "accessible_susy_signal_download_plan.csv")
    total = pd.to_numeric(plan["expected_size_bytes"], errors="coerce").fillna(0).sum()
    if total > MAX_BYTES:
        raise SystemExit(f"Planned SUSY signal download is {total} bytes, above 25 GB cap.")
    return plan


def local_path(row: pd.Series) -> Path:
    return SIGNAL_ROOT / row["sample_id"] / Path(str(row["url"])).name


def download_plan_files() -> pd.DataFrame:
    ensure_dirs()
    ctx = ssl._create_unverified_context()
    rows = []
    for _, row in selected_plan().iterrows():
        target = local_path(row)
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = int(row["expected_size_bytes"])
        status = "already_present"
        error = ""
        if not target.exists() or (expected and target.stat().st_size != expected):
            try:
                status = "downloaded"
                with urllib.request.urlopen(url_to_https(str(row["url"])), context=ctx, timeout=180) as src:
                    with target.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
            except Exception as exc:
                status = "failed"
                error = repr(exc)
        size = target.stat().st_size if target.exists() else 0
        if expected and size != expected and status != "failed":
            status = "size_mismatch"
        rows.append({
            "sample_id": row["sample_id"],
            "record_id": row["record_id"],
            "model_label": row["model_label"],
            "topology_class": row["topology_class"],
            "url": row["url"],
            "local_path": str(target),
            "expected_size_bytes": expected,
            "actual_size_bytes": size,
            "download_status": status,
            "classification": "signal",
            "data_tier": "MINIAODSIM",
            "root_readability_proxy": "downloaded_size_matches" if size == expected and size > 0 else "not_confirmed",
            "error": error,
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "accessible_susy_signal_download_manifest.csv", index=False)
    (REPORTS / "ACCESSIBLE_SUSY_SIGNAL_DOWNLOAD_REPORT.md").write_text(
        "# Accessible SUSY Signal Download Report\n\n"
        f"Date: {DATE}\n\n"
        + manifest.to_markdown(index=False),
        encoding="utf-8",
    )
    return manifest


def add_signal_provenance(df: pd.DataFrame, row: pd.Series, local: Path) -> pd.DataFrame:
    df = df.copy()
    df.insert(0, "sample_id", row["sample_id"])
    df.insert(1, "process_label", row["model_label"])
    df.insert(2, "record_id", row["record_id"])
    df.insert(3, "source_file", local.name)
    df.insert(4, "source_file_stem", local.stem)
    df.insert(5, "source_file_index", 0)
    df.insert(6, "local_input_path_or_container_path", f"{local} | /data/{local.relative_to(SIGNAL_ROOT).as_posix()}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(len(df)))
    df["is_real_collision"] = False
    df["is_simulated"] = True
    df["include_in_real_only_analysis"] = False
    df["data_tier"] = "MINIAODSIM"
    df["classification"] = "signal"
    df["model_label"] = row["model_label"]
    df["topology_class"] = row["topology_class"]
    df["mass_point"] = row.get("mass_point", "")
    if "N_jets" not in df.columns and "N_jets_all" in df.columns:
        df["N_jets"] = df["N_jets_all"]
    return df


def run_cmssw_signal(row: pd.Series, mode: str, max_events: int) -> dict:
    local = Path(row["local_path"])
    run_id = f"susy_{mode}_{row['sample_id']}"
    rel = local.relative_to(SIGNAL_ROOT).as_posix()
    log_path = LOGS / f"{run_id}.log"
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES=/data/{rel}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=20; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{CMSSW_WORK}:/work",
        "-v", f"{SIGNAL_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    out_dir = SIGNAL_OUT / ("smoke_features" if mode == "smoke" else "full_features")
    out_csv = out_dir / f"{row['sample_id']}_event_features.csv"
    events = 0
    if status == "success":
        out_dir.mkdir(parents=True, exist_ok=True)
        df = add_signal_provenance(pd.read_csv(raw), row, local)
        df.to_csv(out_csv, index=False)
        events = len(df)
    return {
        "mode": mode,
        "sample_id": row["sample_id"],
        "record_id": row["record_id"],
        "model_label": row["model_label"],
        "topology_class": row["topology_class"],
        "max_events": max_events,
        "status": status,
        "events_written": events,
        "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path),
        "returncode": proc.returncode,
    }


def score_signal_file(src: Path, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored, availability = apply_frozen_bnf(pd.read_csv(src, low_memory=False))
    out.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out, index=False)
    return scored, availability
