from __future__ import annotations

import traceback
from pathlib import Path

import pandas as pd

from real_collision_common import LOGS, TABLES, ensure_dirs


VALIDATED_MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"


def inspect_file(path: Path, row: pd.Series) -> tuple[dict, str]:
    out = {
        "sample_id": row["sample_id"],
        "primary_dataset": row["primary_dataset"],
        "record_id": row["record_id"],
        "local_path": str(path),
        "file_name": path.name,
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "size_gib": path.stat().st_size / 1024**3 if path.exists() else 0.0,
        "opens_with_uproot": False,
        "top_level_keys": "",
        "has_events_tree": False,
        "events_entries": "",
        "events_branch_count": "",
        "first_200_branches": "",
        "error": "",
        "notes": "",
    }
    log = [f"=== {row['sample_id']} :: {path} ==="]
    if not path.exists():
        out["error"] = "file_missing"
        log.append("File missing.")
        return out, "\n".join(log)
    try:
        import uproot

        with uproot.open(path) as root_file:
            keys = list(root_file.keys())
            clean_keys = [key.split(";")[0] for key in keys]
            out["opens_with_uproot"] = True
            out["top_level_keys"] = ";".join(keys)
            out["has_events_tree"] = "Events" in clean_keys
            log.append(f"Top-level keys: {keys}")
            if out["has_events_tree"]:
                tree_key = keys[clean_keys.index("Events")]
                tree = root_file[tree_key]
                branches = list(tree.keys())
                out["events_entries"] = tree.num_entries
                out["events_branch_count"] = len(branches)
                out["first_200_branches"] = ";".join(branches[:200])
                out["notes"] = "MiniAOD Events tree visible to uproot"
                log.append(f"Events entries: {tree.num_entries}")
                log.append(f"Events branch count: {len(branches)}")
                log.append("First branches: " + ", ".join(branches[:80]))
            else:
                out["notes"] = "opened with uproot but no Events tree found"
    except Exception as exc:
        out["error"] = repr(exc)
        out["notes"] = "uproot open or inspection failed"
        log.append(traceback.format_exc())
    return out, "\n".join(log)


def main() -> None:
    ensure_dirs()
    manifest = pd.read_csv(VALIDATED_MANIFEST)
    manifest = manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)]
    rows = []
    logs = []
    for _, manifest_row in manifest.sort_values(["sample_id", "file_name"]).iterrows():
        row, log = inspect_file(Path(manifest_row["local_path"]), manifest_row)
        rows.append(row)
        logs.append(log)
    pd.DataFrame(rows).to_csv(TABLES / "root_file_inspection_summary.csv", index=False)
    (LOGS / "root_file_inspection_log.txt").write_text("\n\n".join(logs), encoding="utf-8")
    print(f"Wrote {TABLES / 'root_file_inspection_summary.csv'}")
    print(f"Wrote {LOGS / 'root_file_inspection_log.txt'}")


if __name__ == "__main__":
    main()
