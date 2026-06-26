from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_cloud_remote_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
PACKAGE = ROOT / "cloud_remote_nframe_package"
ZIP = ROOT / "cloud_remote_nframe_package.zip"


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def build_real_manifest() -> pd.DataFrame:
    src = ROOT / "outputs_overnight_frozen_trace_validation" / "tables" / "00_selected_overnight_root_manifest.csv"
    manifest = pd.read_csv(src)
    remote = pd.DataFrame(
        {
            "dataset_label": manifest["record_title"].astype(str).str.strip("/").str.replace("/", "__", regex=False),
            "record_id": manifest["record_id"],
            "process_family": "real_collision_data",
            "primary_dataset": manifest["primary_dataset"],
            "run_era": manifest["era"],
            "data_tier": "MINIAOD",
            "xrootd_url": manifest["uri"],
            "file_index": manifest.groupby(["era", "primary_dataset"]).cumcount(),
            "planned_max_events": 20000,
            "status": "pending",
            "output_path": "",
            "notes": "fresh independent real CMS MiniAOD validation; remote/cloud processing; no local ROOT retention",
            "size_gb": manifest["size_gb"],
            "selection_order": manifest["selection_order"],
        }
    )
    TABLES.mkdir(parents=True, exist_ok=True)
    remote.to_csv(TABLES / "01_real_cms_miniaod_remote_cloud_manifest.csv", index=False)
    summary = remote.groupby(["run_era", "primary_dataset"], as_index=False).agg(
        files=("xrootd_url", "count"), gb=("size_gb", "sum")
    )
    summary.to_csv(TABLES / "02_real_cms_miniaod_remote_cloud_manifest_summary.csv", index=False)
    return summary


def rebuild_package(summary: pd.DataFrame) -> None:
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    (PACKAGE / "scripts").mkdir(parents=True, exist_ok=True)
    (PACKAGE / "manifests").mkdir(parents=True, exist_ok=True)
    (PACKAGE / "cmssw_full_extraction").mkdir(parents=True, exist_ok=True)

    copy_if_exists(ROOT / "CLOUD_REMOTE_NFRAME_RUNBOOK.md", PACKAGE / "CLOUD_REMOTE_NFRAME_RUNBOOK.md")
    shutil.copytree(ROOT / "scripts" / "remote_xrootd", PACKAGE / "scripts" / "remote_xrootd")

    cmssw = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
    shutil.copytree(cmssw / "NFrame", PACKAGE / "cmssw_full_extraction" / "NFrame")
    for name in [
        "run_one_sample.sh",
        "run_one_sample_python_compat.sh",
        "compute_full_event_score.py",
        "validate_and_make_pseudo_regions.py",
        "README.md",
    ]:
        copy_if_exists(cmssw / name, PACKAGE / "cmssw_full_extraction" / name)

    for src in [
        TABLES / "01_real_cms_miniaod_remote_cloud_manifest.csv",
        TABLES / "02_real_cms_miniaod_remote_cloud_manifest_summary.csv",
        ROOT / "outputs_breakthrough_full_push_nframe_susy" / "remote_xrootd" / "manifest_priority1_top_dy_w_z_qcd.csv",
        ROOT / "outputs_breakthrough_full_push_nframe_susy" / "remote_xrootd" / "manifest_priority2_more_qcd_met_muon.csv",
        ROOT / "outputs_breakthrough_full_push_nframe_susy" / "tables" / "04_cern_record_search_and_xrootd_manifest_candidates.csv",
        ROOT / "outputs_breakthrough_full_push_nframe_susy" / "tables" / "04_xrootd_file_accessibility_scan.csv",
        ROOT / "outputs_breakthrough_full_push_nframe_susy" / "tables" / "04_xrootd_full_file_accessibility_scan.csv",
        ROOT / "outputs_breakthrough_full_push_nframe_susy" / "tables" / "02_remote_xrootd_smoke_test_summary.csv",
    ]:
        copy_if_exists(src, PACKAGE / "manifests" / src.name)

    if ZIP.exists():
        ZIP.unlink()
    shutil.make_archive(str(ZIP.with_suffix("")), "zip", PACKAGE)

    REPORTS.mkdir(parents=True, exist_ok=True)
    report = f"""# Cloud Remote Validation Package

This package was rebuilt to support broad N-Frame validation without local bulk ROOT downloads.

## Real CMS MiniAOD Manifest

The real-data cloud manifest contains 105 CMS MiniAOD files, 134.481 GB nominal input, across Run2015D, Run2016G, and Run2016H.

{summary.to_markdown(index=False, floatfmt=".3f")}

## Package

- Folder: `{PACKAGE}`
- Zip: `{ZIP}`

The package contains scripts, CMSSW extractor config, real-data cloud manifests, and prior MC/XRootD manifests. It intentionally excludes ROOT files and bulky local outputs.
"""
    (REPORTS / "01_CLOUD_REMOTE_VALIDATION_PACKAGE.md").write_text(report, encoding="utf-8")


def main() -> None:
    summary = build_real_manifest()
    rebuild_package(summary)
    print(REPORTS / "01_CLOUD_REMOTE_VALIDATION_PACKAGE.md")
    print(ZIP)


if __name__ == "__main__":
    main()
