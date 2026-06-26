from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "201_overnight_frozen_trace_validation.py"


def load_stage201():
    spec = importlib.util.spec_from_file_location("stage201", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    stage201 = load_stage201()
    stage201.ensure_dirs()

    download_path = stage201.TABLES / "01_download_audit.csv"
    if not download_path.exists():
        raise SystemExit(f"Missing download audit: {download_path}")

    download = stage201.pd.read_csv(download_path)
    ok = download[download["download_status"].isin(["downloaded", "already_present"])].copy()
    if ok.empty:
        raise SystemExit("No downloaded/already_present files available for extraction")

    print(
        f"[resume] using {len(ok)} downloaded/already_present files "
        f"({ok['size_gb'].sum():.3f} GB); no download step will run",
        flush=True,
    )
    chunks = stage201.make_chunks(ok)
    print(
        "[resume] prepared "
        f"{chunks.groupby(['era','primary_dataset','record_id','chunk_index']).ngroups if not chunks.empty else 0} chunks",
        flush=True,
    )
    extraction = stage201.extract_chunks(chunks)
    print("[resume] extraction complete", flush=True)

    valid = extraction[extraction["status"].isin(["extracted", "existing"])]
    if valid.empty:
        raise SystemExit("No successfully extracted chunks; cannot score")

    stage_table, quality, readout = stage201.score_and_validate(valid)
    stage_table.to_csv(stage201.TABLES / "06_downloaded_only_stage_validation.csv", index=False)
    quality.to_csv(stage201.TABLES / "07_downloaded_only_quality_checks.csv", index=False)
    readout.to_csv(stage201.TABLES / "08_downloaded_only_readout_summary.csv", index=False)
    stage201.write_reports(stage201.pd.read_csv(stage201.TABLES / "00_selected_overnight_root_manifest.csv"), ok, extraction, quality, readout)
    print("[resume] validation complete", flush=True)
    print(f"[resume] outputs: {stage201.OUT}", flush=True)


if __name__ == "__main__":
    main()
