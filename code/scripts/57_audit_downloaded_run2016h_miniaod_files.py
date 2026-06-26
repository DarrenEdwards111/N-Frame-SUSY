from pathlib import Path

import pandas as pd
import uproot


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

FILES = [
    ("JetHT", 30541, Path(r"D:\cern_open_data\nframe_validation_real_independent\jetht_run2016h_validation\30541\FC0EE8E8-8640-8649-B22A-F0C750DD5DE0.root"), 365969251),
    ("MET", 30542, Path(r"D:\cern_open_data\nframe_validation_real_independent\met_run2016h_validation\30542\6D1DA38B-AEFA-3849-B346-3B2653B46C9E.root"), 584950164),
    ("SingleMuon", 30546, Path(r"D:\cern_open_data\nframe_validation_real_independent\singlemuon_run2016h_validation\30546\E5768FBE-A1B2-F047-999D-0B5C0B051827.root"), 729986939),
]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for primary, record_id, path, expected_size in FILES:
        exists = path.exists()
        actual = path.stat().st_size if exists else 0
        readable = False
        keys = ""
        if exists:
            try:
                with uproot.open(path) as f:
                    keys = ";".join(f.keys()[:10])
                    readable = True
            except Exception as exc:
                keys = f"uproot_read_error: {exc}"
        rows.append({
            "primary_dataset": primary,
            "record_id": record_id,
            "data_tier": "MiniAOD",
            "real_or_simulated": "real collision",
            "path": str(path),
            "exists": exists,
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual,
            "size_matches": actual == expected_size,
            "root_readable_by_uproot": readable,
            "top_level_keys_or_error": keys,
        })
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "run2016h_miniaod_validation_file_audit.csv", index=False)
    report = [
        "# Run2016H MiniAOD File Audit",
        "",
        "Date: 2026-06-09",
        "",
        "These are independent real CMS Run2016H MiniAOD files. No simulated samples are included.",
        "",
        df.to_markdown(index=False),
    ]
    (REPORTS / "RUN2016H_MINIAOD_FILE_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(df.to_string(index=False))
    if not df["exists"].all() or not df["size_matches"].all():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
