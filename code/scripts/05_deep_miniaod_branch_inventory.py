from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from real_collision_common import PROJECT, TABLES, ensure_dirs


MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"
OUT_DIR = PROJECT / "results" / "deep_miniAOD_inventory"


def branch_record(tree, name: str, meta: dict) -> dict:
    obj = None
    typename = ""
    interpretation = ""
    notes = ""
    try:
        obj = tree[name]
        typename = str(getattr(obj, "typename", "") or "")
        interpretation = str(getattr(obj, "interpretation", "") or "")
    except Exception as exc:
        notes = f"metadata_read_failed: {exc}"
    leaf_name = name.split("/")[-1].split(".")[-1]
    return {
        **meta,
        "branch_name": name.split("/")[0],
        "leaf_name": leaf_name,
        "full_name": name,
        "typename": typename,
        "interpretation": interpretation,
        "num_entries": getattr(tree, "num_entries", ""),
        "readable_test_status": "not_tested_inventory_only",
        "notes": notes,
    }


def inspect_file(row: pd.Series) -> list[dict]:
    import uproot

    path = Path(row["local_path"])
    meta = {
        "sample_id": row["sample_id"],
        "primary_dataset": row["primary_dataset"],
        "source_file": path.name,
    }
    records: list[dict] = []
    with uproot.open(path) as root_file:
        top_keys = list(root_file.keys())
        tree = root_file["Events"]
        branches = list(tree.keys())
        streamers = []
        try:
            streamers = [str(key) for key in root_file.file.streamers.keys()]
        except Exception:
            streamers = []
        file_json = {
            "source_file": str(path),
            "sample_id": row["sample_id"],
            "primary_dataset": row["primary_dataset"],
            "top_level_keys": top_keys,
            "events_classname": getattr(tree, "classname", ""),
            "events_typename": getattr(tree, "typename", ""),
            "num_entries": tree.num_entries,
            "branch_count": len(branches),
            "branches": branches,
            "streamer_classes": streamers[:2000],
        }
        stem = f"{row['sample_id']}_{path.stem}"
        (OUT_DIR / f"{stem}_branches.json").write_text(json.dumps(file_json, indent=2), encoding="utf-8")
        for name in branches:
            records.append(branch_record(tree, name, meta))
        pd.DataFrame(records).to_csv(OUT_DIR / f"{stem}_branches.csv", index=False)
    return records


def main() -> None:
    ensure_dirs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)]
    all_records: list[dict] = []
    for _, row in manifest.sort_values(["sample_id", "file_name"]).iterrows():
        all_records.extend(inspect_file(row))
    combined = pd.DataFrame(all_records)
    combined.to_csv(TABLES / "deep_miniaod_combined_branch_inventory.csv", index=False)
    print(f"Wrote {len(combined)} branch rows")
    print(f"Wrote {TABLES / 'deep_miniaod_combined_branch_inventory.csv'}")
    print(f"Wrote per-file inventory under {OUT_DIR}")


if __name__ == "__main__":
    main()
