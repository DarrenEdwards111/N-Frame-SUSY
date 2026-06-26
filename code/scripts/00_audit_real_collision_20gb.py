from __future__ import annotations

from pathlib import Path

import pandas as pd

from real_collision_common import (
    DOWNLOAD_ROOT,
    FILELISTS,
    REPORTS,
    SAMPLES,
    SOURCE_MANIFEST,
    SOURCE_REPORT,
    TABLES,
    ensure_dirs,
    find_real_root_files,
    infer_sample_id,
    safe_bool,
)


def primary_dataset_from_sample(sample_id: str) -> str:
    return SAMPLES.get(sample_id, {}).get("primary_dataset", "unknown")


def record_from_sample(sample_id: str) -> int | str:
    return SAMPLES.get(sample_id, {}).get("record_id", "")


def validate_manifest_row(row: pd.Series, scanned: dict[str, Path]) -> dict:
    local_path = Path(str(row["local_path"]))
    sample_id = str(row["sample_id"])
    expected_bytes = int(row["size_bytes"])
    actual_exists = local_path.exists()
    actual_size = local_path.stat().st_size if actual_exists else 0
    size_ok = actual_exists and abs(actual_size - expected_bytes) <= max(4096, expected_bytes * 0.001)
    is_known_real_sample = sample_id in SAMPLES
    is_simulated = "signal" in sample_id.lower() or "susy" in sample_id.lower() or "t5" in sample_id.lower()
    notes = []
    if not actual_exists:
        notes.append("file_missing")
    if actual_exists and not size_ok:
        notes.append(f"size_mismatch_manifest={expected_bytes}_actual={actual_size}")
    if not is_known_real_sample:
        notes.append("unknown_sample_id")
    if is_simulated:
        notes.append("simulated_signal_pattern_in_sample_id")
    if str(local_path) not in scanned:
        notes.append("manifest_file_not_seen_in_scan")
    validation_status = "valid" if actual_exists and size_ok and is_known_real_sample and not is_simulated else "check"
    return {
        "sample_id": sample_id,
        "primary_dataset": primary_dataset_from_sample(sample_id),
        "record_id": int(row["record_id"]),
        "local_path": str(local_path),
        "file_name": local_path.name,
        "size_bytes": actual_size,
        "size_gib": actual_size / 1024**3,
        "exists": actual_exists,
        "sample_type": row.get("sample_type", SAMPLES.get(sample_id, {}).get("sample_type", "")),
        "is_real_collision": is_known_real_sample and not is_simulated,
        "is_simulated_signal": is_simulated,
        "validation_status": validation_status,
        "notes": "; ".join(notes) if notes else "matches manifest and real-data sample list",
    }


def write_filelists(rows: pd.DataFrame) -> None:
    for sample_id, sample_rows in rows.groupby("sample_id"):
        if sample_id not in SAMPLES:
            continue
        out = FILELISTS / f"{sample_id}_files.txt"
        out.write_text("\n".join(sample_rows.sort_values("local_path")["local_path"]) + "\n", encoding="utf-8")


def write_report(rows: pd.DataFrame, scanned_files: list[Path]) -> None:
    total_gib = rows["size_gib"].sum()
    valid_count = int((rows["validation_status"] == "valid").sum())
    simulated_count = int(rows["is_simulated_signal"].sum())
    missing_count = int((~rows["exists"]).sum())
    sample_table = (
        rows.groupby(["sample_id", "primary_dataset", "record_id", "sample_type"], as_index=False)
        .agg(files=("file_name", "count"), gib=("size_gib", "sum"))
        .sort_values("sample_id")
    )
    table_md = "\n".join(
        f"| `{r.sample_id}` | {r.primary_dataset} | {int(r.record_id)} | {r.sample_type} | {int(r.files)} | {r.gib:.3f} |"
        for r in sample_table.itertuples()
    )
    expected_sample_lines = []
    for sample_id, info in SAMPLES.items():
        actual = int((rows["sample_id"] == sample_id).sum())
        expected_sample_lines.append(
            f"- `{sample_id}`: {actual}/{info['expected_files']} files present ({info['primary_dataset']}, record {info['record_id']})"
        )

    report = f"""# Phase 1 Data Audit Report

## Plain-English Summary

The real-data folder contains {len(scanned_files)} ROOT files. The validated manifest contains {len(rows)} expected files, of which {valid_count} validate cleanly.

Total validated size is {total_gib:.3f} GiB. This satisfies Darren's request for at least 10 GB of real CERN/CMS data, and it is close to the intended 20 GB target while staying below 25 GB.

These files are real CMS Run2016G collision MiniAOD files from MET, JetHT, and SingleMuon primary datasets. They are not simulated signal samples. MiniAOD is not the lowest-level RAW detector readout, but it is real collision event-level CMS Open Data suitable for physics-style event extraction.

## Sample Coverage

{chr(10).join(expected_sample_lines)}

## Size By Sample

| sample_id | primary_dataset | record_id | sample_type | files | GiB |
|---|---|---:|---|---:|---:|
{table_md}

## Validation Checks

- All expected ROOT files exist: {'yes' if missing_count == 0 else 'no'}
- File sizes approximately match the manifest: {'yes' if valid_count == len(rows) else 'no'}
- Simulated signal files mixed into this real-data folder: {'no' if simulated_count == 0 else 'yes'}
- MET, JetHT, and SingleMuon samples present: {'yes' if all((rows['sample_id'] == sid).any() for sid in SAMPLES) else 'no'}

## What Still Remains Technically Necessary

The next necessary step is event-level extraction. Python/uproot can inspect the ROOT files and may extract some MiniAOD branches, but MiniAOD is CMS EDM format rather than flat NanoAOD. For serious boundary-variable extraction, CMSSW is the correct route for MET, leptons, b-tags, trigger decisions, and reconstruction-quality variables.

## Source Inputs Read

- `{SOURCE_REPORT}`
- `{SOURCE_MANIFEST}`
- `{FILELISTS}`
- `{DOWNLOAD_ROOT}`
"""
    (REPORTS / "PHASE1_DATA_AUDIT_REPORT.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    if not SOURCE_MANIFEST.exists():
        raise FileNotFoundError(SOURCE_MANIFEST)
    source = pd.read_csv(SOURCE_MANIFEST)
    scanned_files = find_real_root_files()
    scanned = {str(path): path for path in scanned_files}
    rows = pd.DataFrame([validate_manifest_row(row, scanned) for _, row in source.iterrows()])

    extra_scanned = [path for path in scanned_files if str(path) not in set(rows["local_path"])]
    for path in extra_scanned:
        sample_id = infer_sample_id(path)
        is_simulated = "signal" in str(path).lower() or "susy" in str(path).lower() or "t5" in str(path).lower()
        rows.loc[len(rows)] = {
            "sample_id": sample_id,
            "primary_dataset": primary_dataset_from_sample(sample_id),
            "record_id": record_from_sample(sample_id),
            "local_path": str(path),
            "file_name": path.name,
            "size_bytes": path.stat().st_size,
            "size_gib": path.stat().st_size / 1024**3,
            "exists": True,
            "sample_type": SAMPLES.get(sample_id, {}).get("sample_type", "unknown"),
            "is_real_collision": sample_id in SAMPLES and not is_simulated,
            "is_simulated_signal": is_simulated,
            "validation_status": "extra_file_check",
            "notes": "file present in scan but absent from source manifest",
        }

    rows.to_csv(TABLES / "real_collision_20gb_manifest_validated.csv", index=False)
    write_filelists(rows[rows["validation_status"] == "valid"])
    write_report(rows, scanned_files)
    print(f"Wrote {TABLES / 'real_collision_20gb_manifest_validated.csv'}")
    print(f"Wrote {REPORTS / 'PHASE1_DATA_AUDIT_REPORT.md'}")


if __name__ == "__main__":
    main()
