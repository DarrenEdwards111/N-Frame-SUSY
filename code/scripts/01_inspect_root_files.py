from __future__ import annotations

import traceback
from pathlib import Path

import pandas as pd

from stage2_common import LOGS, SAMPLES, TABLES, ensure_dirs, find_root_files, infer_sample_id, manifest_path


def inspect_file(path: Path) -> tuple[dict, list[dict], str]:
    sample_id = infer_sample_id(path)
    sample = SAMPLES.get(sample_id, {"sample_type": "unknown", "record_id": ""})
    base = {
        "sample_id": sample_id,
        "sample_type": sample["sample_type"],
        "record_id": sample["record_id"],
        "local_path": str(path),
        "file_name": path.name,
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "size_gib": (path.stat().st_size / 1024**3) if path.exists() else 0,
        "exists": path.exists(),
        "readable_by_python_uproot_attempted": True,
        "readable_by_python_uproot_success": False,
        "notes": "",
    }
    tree_rows: list[dict] = []
    log_lines = [f"=== {sample_id}: {path} ==="]
    try:
        import uproot

        with uproot.open(path) as root_file:
            keys = list(root_file.keys())
            clean_keys = [key.split(";")[0] for key in keys]
            has_events = "Events" in clean_keys
            base["readable_by_python_uproot_success"] = True
            base["notes"] = "opened_with_uproot; Events tree found" if has_events else "opened_with_uproot; no Events tree"
            log_lines.append(f"keys: {keys[:50]}")
            for key in keys:
                clean_key = key.split(";")[0]
                row = {
                    "sample_id": sample_id,
                    "record_id": sample["record_id"],
                    "file_name": path.name,
                    "key": key,
                    "clean_key": clean_key,
                    "class_name": "",
                    "num_entries": "",
                    "n_branches": "",
                    "first_100_branches": "",
                    "notes": "",
                }
                try:
                    obj = root_file[key]
                    row["class_name"] = obj.classname
                    if hasattr(obj, "num_entries"):
                        row["num_entries"] = obj.num_entries
                    if hasattr(obj, "keys"):
                        branches = list(obj.keys())
                        row["n_branches"] = len(branches)
                        row["first_100_branches"] = ";".join(branches[:100])
                        log_lines.append(f"{key}: {obj.classname}, entries={row['num_entries']}, branches={len(branches)}")
                        log_lines.append("  branches: " + ", ".join(branches[:80]))
                except Exception as exc:
                    row["notes"] = f"object_inspection_failed: {exc}"
                tree_rows.append(row)
    except Exception as exc:
        base["notes"] = f"uproot_open_failed: {exc}"
        log_lines.append(traceback.format_exc())
    return base, tree_rows, "\n".join(log_lines)


def main() -> None:
    ensure_dirs()
    root_files = find_root_files()
    manifest_rows = []
    tree_rows = []
    logs = []
    seen = set()
    for path in root_files:
        row, trees, log = inspect_file(path)
        manifest_rows.append(row)
        tree_rows.extend(trees)
        logs.append(log)
        seen.add(row["sample_id"])

    missing = sorted(set(SAMPLES) - seen)
    if missing:
        logs.append("MISSING EXPECTED SAMPLES: " + ", ".join(missing))

    pd.DataFrame(manifest_rows).to_csv(manifest_path(), index=False)
    pd.DataFrame(tree_rows).to_csv(TABLES / "root_file_tree_summary.csv", index=False)
    (LOGS / "root_file_inspection_log.txt").write_text("\n\n".join(logs), encoding="utf-8")
    print(f"Wrote {manifest_path()}")
    print(f"Wrote {TABLES / 'root_file_tree_summary.csv'}")
    print(f"Wrote {LOGS / 'root_file_inspection_log.txt'}")
    if missing:
        raise SystemExit(f"Missing expected samples: {', '.join(missing)}")


if __name__ == "__main__":
    main()

