from __future__ import annotations

import shutil
import ssl
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
LOGS = ROOT / "results" / "logs"
OUT = ROOT / "data" / "processed" / "fuller_component_benchmarks"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_fuller_component_benchmarks")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
DATE = "2026-06-09"
MAX_BYTES = 25 * 1024**3

FAMILIES = {
    "P_displacement_proxy": ["secondary_vertex_count", "displacement_proxy_raw"],
    "P_reconstruction": ["packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_multiplicity": ["N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["HT", "leading_jet_pt", "subleading_jet_pt"],
    "P_missing": ["MET_pt"],
    "P_compression": ["compression_proxy_raw"],
}
WEIGHTS = {
    "P_displacement_proxy": 0.3566,
    "P_reconstruction": 0.2112,
    "P_multiplicity": 0.2019,
    "P_btag_structure": 0.0926,
    "P_visible_energy": 0.0728,
    "P_missing": 0.0595,
    "P_compression": 0.0055,
}


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, LOGS, OUT, DOWNLOAD_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


def read_plan() -> pd.DataFrame:
    plan = pd.read_csv(TABLES / "fuller_component_download_plan.csv")
    plan = plan[plan["proceed_automatically"].astype(str).str.lower().eq("true")].copy()
    total = pd.to_numeric(plan["expected_size_bytes"], errors="coerce").fillna(0).sum()
    if total > MAX_BYTES:
        raise SystemExit(f"Planned download is {total} bytes, above 25 GB cap.")
    plan["sample_slug"] = plan.apply(sample_slug, axis=1)
    return plan


def sample_slug(row: pd.Series) -> str:
    def clean(value: object) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value)

    label = clean(row.get("process_label")) or clean(row.get("model_label")) or clean(row.get("title")) or clean(row.get("record_id"))
    label = label.lower().replace("+", "plus").replace("/", "_").replace(" ", "_")
    keep = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in label)
    return f"{keep.strip('_')}_{int(row['record_id'])}"


def url_to_https(url: str) -> str:
    if url.startswith("root://eospublic.cern.ch//"):
        return "https://eospublic.cern.ch/" + url.split("root://eospublic.cern.ch//", 1)[1]
    return url


def local_root_path(row: pd.Series) -> Path:
    return DOWNLOAD_ROOT / row["sample_slug"] / Path(str(row["selected_file_url"])).name


def download_selected_files() -> pd.DataFrame:
    ensure_dirs()
    rows = []
    ctx = ssl._create_unverified_context()
    for _, row in read_plan().iterrows():
        target = local_root_path(row)
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = int(row["expected_size_bytes"]) if pd.notna(row["expected_size_bytes"]) else 0
        status = "already_present"
        error = ""
        if not target.exists() or (expected and target.stat().st_size != expected):
            try:
                status = "downloaded"
                with urllib.request.urlopen(url_to_https(str(row["selected_file_url"])), context=ctx, timeout=120) as src:
                    with target.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
            except Exception as exc:
                xrd = xrdcp_download(str(row["selected_file_url"]), target)
                status = xrd["status"]
                error = repr(exc) + ("; " + xrd["error"] if xrd["error"] else "")
        size = target.stat().st_size if target.exists() else 0
        if expected and size != expected and status != "failed":
            status = "size_mismatch"
        rows.append({
            "sample_slug": row["sample_slug"],
            "record_id": row["record_id"],
            "process_label": row.get("process_label", ""),
            "classification": row.get("classification", ""),
            "selected_file_url": row["selected_file_url"],
            "local_path": str(target),
            "expected_size_bytes": expected,
            "actual_size_bytes": size,
            "download_status": status,
            "error": error,
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "fuller_component_download_manifest.csv", index=False)
    (REPORTS / "FULLER_COMPONENT_DOWNLOAD_REPORT.md").write_text(
        "# Fuller Component MiniAODSIM Download Report\n\n"
        f"Date: {DATE}\n\n"
        f"Planned bytes: {int(manifest['expected_size_bytes'].sum())}\n\n"
        + manifest.to_markdown(index=False),
        encoding="utf-8",
    )
    return manifest


def xrdcp_download(url: str, target: Path) -> dict[str, str]:
    target.parent.mkdir(parents=True, exist_ok=True)
    rel = target.relative_to(DOWNLOAD_ROOT).as_posix()
    log_path = LOGS / f"xrdcp_{target.stem}.log"
    cmd_inside = f"mkdir -p /data/{target.parent.relative_to(DOWNLOAD_ROOT).as_posix()} && xrdcp -f '{url}' '/data/{rel}'"
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{DOWNLOAD_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    try:
        with log_path.open("w", encoding="utf-8", errors="replace") as log:
            log.write(" ".join(cmd) + "\n")
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=600)
    except Exception as exc:
        return {"status": "failed", "error": f"xrdcp exception: {exc!r}"}
    if proc.returncode == 0 and target.exists():
        return {"status": "downloaded_xrdcp", "error": ""}
    return {"status": "failed", "error": f"xrdcp failed; log={log_path}; returncode={proc.returncode}"}


def run_cmssw(row: pd.Series, mode: str, max_events: int) -> dict:
    run_id = f"fuller_{mode}_{row['sample_slug']}"
    local = Path(row["local_path"])
    rel = local.relative_to(DOWNLOAD_ROOT).as_posix()
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
        "-v", f"{DOWNLOAD_ROOT}:/data",
        IMAGE,
        "bash", "-lc", cmd_inside,
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    out_csv = OUT / mode / f"{row['sample_slug']}_event_features.csv"
    events = 0
    if status == "success":
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(raw)
        df = add_provenance(df, row, local)
        df.to_csv(out_csv, index=False)
        events = len(df)
    return {
        "mode": mode,
        "sample_slug": row["sample_slug"],
        "record_id": row["record_id"],
        "process_label": row.get("process_label", ""),
        "classification": row.get("classification", ""),
        "max_events": max_events,
        "status": status,
        "events_written": events,
        "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path),
        "returncode": proc.returncode,
    }


def add_provenance(df: pd.DataFrame, row: pd.Series, local: Path) -> pd.DataFrame:
    df = df.copy()
    process = row.get("process_label") or row.get("model_label") or row["sample_slug"]
    df.insert(0, "sample_id", row["sample_slug"])
    df.insert(1, "process_label", process)
    df.insert(2, "record_id", row["record_id"])
    df.insert(3, "source_file", local.name)
    df.insert(4, "source_file_stem", local.stem)
    df.insert(5, "source_file_index", 0)
    df.insert(6, "local_input_path_or_container_path", f"{local} | /data/{local.relative_to(DOWNLOAD_ROOT).as_posix()}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(len(df)))
    df["is_real_collision"] = False
    df["is_simulated"] = True
    df["include_in_real_only_analysis"] = False
    df["data_tier"] = "MINIAODSIM"
    df["classification"] = row.get("classification", "")
    df["model_label"] = row.get("model_label", "")
    df["topology_class"] = row.get("topology_class", "")
    df["mass_point"] = row.get("mass_point", "")
    if "N_jets" not in df.columns and "N_jets_all" in df.columns:
        df["N_jets"] = df["N_jets_all"]
    return df


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "displacement_proxy_raw" not in df.columns and "secondary_vertex_count" in df.columns:
        df["displacement_proxy_raw"] = df["secondary_vertex_count"]
    if "compression_proxy_raw" not in df.columns:
        met = pd.to_numeric(df.get("MET_pt", 0), errors="coerce").fillna(0).clip(lower=0)
        ht = pd.to_numeric(df.get("HT", 0), errors="coerce").fillna(0).clip(lower=0)
        lead = pd.to_numeric(df.get("leading_jet_pt", 0), errors="coerce").fillna(0).clip(lower=0)
        df["compression_proxy_raw"] = np.log1p(met) - np.log1p(ht + lead + 1)
    return df


def scoring_constants() -> dict[str, tuple[float, float]]:
    real = prepare(pd.read_csv(ROOT / "data" / "processed" / "matched_control" / "standard_quality_clean_events.csv"))
    cols = sorted({v for vals in FAMILIES.values() for v in vals if v in real.columns})
    return {
        c: (
            float(pd.to_numeric(real[c], errors="coerce").mean()),
            float(pd.to_numeric(real[c], errors="coerce").std(ddof=0)),
        )
        for c in cols
    }


def zscore(s: pd.Series, const: tuple[float, float]) -> pd.Series:
    mean, std = const
    values = pd.to_numeric(s, errors="coerce")
    return (values - mean) / std if std else pd.Series(np.nan, index=s.index)


def apply_frozen_bnf(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    const = scoring_constants()
    df = prepare(df)
    total = pd.Series(0.0, index=df.index)
    avail_rows = []
    for fam, variables in FAMILIES.items():
        avail = [v for v in variables if v in df.columns and v in const and df[v].notna().any()]
        missing = [v for v in variables if v not in df.columns or v not in const or not df[v].notna().any()]
        fam_score = pd.concat([zscore(df[v], const[v]) for v in avail], axis=1).mean(axis=1) if avail else pd.Series(np.nan, index=df.index)
        df[f"B_{fam}"] = fam_score
        if avail:
            total += WEIGHTS[fam] * fam_score.fillna(0)
        for sample, group in df.groupby("sample_id"):
            avail_rows.append({
                "sample_id": sample,
                "process_label": group["process_label"].iloc[0],
                "classification": group["classification"].iloc[0],
                "parameter_family": fam,
                "available": bool(avail),
                "available_variables": ";".join(avail),
                "missing_variables": ";".join(missing),
                "weight": WEIGHTS[fam],
            })
    df["B_NF_fitted_frozen_raw"] = total
    df["B_NF_fitted_frozen_z_real_scaled"] = total
    df["component_mode"] = np.where(df[[f"B_{f}" for f in FAMILIES]].notna().all(axis=1), "full-component", "reduced-component")
    return df, pd.DataFrame(avail_rows).drop_duplicates()


def component_cols() -> list[str]:
    return [f"B_{c}" for c in FAMILIES]
