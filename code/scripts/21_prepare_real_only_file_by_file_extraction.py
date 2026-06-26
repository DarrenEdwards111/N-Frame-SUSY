from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REAL_ROOT = Path(r"D:\cern_open_data\nframe_stage2_real_collision_20gb")
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

SAMPLES = {
    "cms_met_run2016g_collision": ("MET", 30509),
    "cms_jetht_run2016g_collision": ("JetHT", 30508),
    "cms_singlemuon_run2016g_collision": ("SingleMuon", 30513),
}


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for sample_id, (primary_dataset, record_id) in SAMPLES.items():
        files = sorted((REAL_ROOT / sample_id / str(record_id)).glob("*.root"))
        for i, path in enumerate(files):
            rel = path.relative_to(REAL_ROOT).as_posix()
            rows.append({
                "sample_id": sample_id,
                "primary_dataset": primary_dataset,
                "record_id": record_id,
                "source_file_index": i,
                "source_file": path.name,
                "source_file_stem": path.stem,
                "local_input_path": str(path),
                "container_input_path": "/data/" + rel,
                "size_gib": path.stat().st_size / 1024**3,
                "is_real_collision": True,
                "is_simulated": False,
                "include_in_real_only_analysis": True,
            })
    manifest = pd.DataFrame(rows)
    out = TABLES / "real_only_file_by_file_manifest.csv"
    manifest.to_csv(out, index=False)
    report = [
        "# Source File Provenance Implementation",
        "",
        "Date: 2026-06-08",
        "",
        "The current C++ analyser does not directly write the input ROOT file name per event. To make provenance exact, extraction is now run one ROOT file at a time using `NFRAME_INPUT_FILES`.",
        "",
        "After each file is extracted, the runner injects these metadata columns into every row before saving the per-file CSV:",
        "",
        "- `sample_id`",
        "- `primary_dataset`",
        "- `record_id`",
        "- `source_file`",
        "- `source_file_stem`",
        "- `source_file_index`",
        "- `local_input_path_or_container_path`",
        "- `event_index_within_file`",
        "- `event_index_global_within_sample`",
        "",
        "This gives exact per-event source-file provenance without relying on CMSSW internals to expose the file name.",
        "",
        f"Manifest: `{out}`",
        "",
        "Files prepared:",
        "",
        manifest[["sample_id", "primary_dataset", "record_id", "source_file_index", "source_file", "size_gib"]].to_markdown(index=False),
    ]
    (REPORTS / "SOURCE_FILE_PROVENANCE_IMPLEMENTATION.md").write_text("\n".join(report), encoding="utf-8")
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
