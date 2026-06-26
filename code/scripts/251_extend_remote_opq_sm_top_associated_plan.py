from __future__ import annotations

"""Extend the remote OPQ SM manifest with rare top-associated samples."""

from pathlib import Path

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
MANIFEST = TABLES / "02_remote_sm_distributed_file_manifest.csv"
RECORDS = TABLES / "01_remote_sm_record_metadata.csv"
API = "https://opendata.cern.ch/api/records/"
EVENTS_PER_FILE = 5_000
AUDIT_TAG = "2026-06-22T_TTAssoc_extension"

# Non-overlapping rare top-associated components found through the CERN API.
TOP_ASSOCIATED_RECORDS = [
    (68205, "TTAssoc", "TTZToQQ rare top-associated background component"),
    (68196, "TTAssoc", "TTZToLL rare top-associated background component"),
    (68072, "TTAssoc", "TTWJetsToLNu rare top-associated background component"),
    (68082, "TTAssoc", "TTWJetsToQQ rare top-associated background component"),
]


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []) or []:
        out.extend(idx.get("files", []) or [])
    out.extend(md.get("files", []) or [])
    return out


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    records = pd.read_csv(RECORDS)
    manifest = pd.read_csv(MANIFEST)
    record_rows = []
    manifest_rows = []
    search_rows = []
    existing = set(records["record_id"].astype(int))

    for rid, family, purpose in TOP_ASSOCIATED_RECORDS:
        payload = requests.get(f"{API}{rid}", timeout=60)
        payload.raise_for_status()
        md = payload.json().get("metadata", {})
        title = str(md.get("title", ""))
        xsec = md.get("cross_section", {}) or {}
        dist = md.get("distribution", {}) or {}
        all_files = files(md)
        online = [f for f in all_files if str(f.get("availability", "")).lower() == "online"]
        search_rows.append(
            {
                "record_id": rid,
                "title": title,
                "all_file_count": len(all_files),
                "online_file_count": len(online),
                "record_url": f"https://opendata.cern.ch/record/{rid}",
                "usable_for_remote_extraction": bool(online),
            }
        )
        if rid in existing or not online:
            continue
        f = online[0]
        record_rows.append(
            {
                "audit_utc": AUDIT_TAG,
                "record_id": rid,
                "process_family": family,
                "purpose": purpose,
                "title": title,
                "cross_section_pb": xsec.get("total_value", np.nan),
                "cross_section_uncertainty_pb": xsec.get("total_value_uncertainty", np.nan),
                "generated_events": dist.get("number_events", np.nan),
                "filter_efficiency": xsec.get("filter_efficiency", np.nan),
                "matching_efficiency": xsec.get("matching_efficiency", np.nan),
                "negative_weight_fraction": xsec.get("neg_weight_fraction", np.nan),
                "record_file_count": len(all_files),
                "online_file_count": len(online),
                "selected_file_count": 1,
                "planned_events": EVENTS_PER_FILE,
                "record_url": f"https://opendata.cern.ch/record/{rid}",
                "normalisation_rule": "use per-event generator_weight and record-level sum of generator weights when available; otherwise tiered approximation",
            }
        )
        manifest_rows.append(
            {
                "audit_utc": AUDIT_TAG,
                "record_id": rid,
                "process_family": family,
                "purpose": purpose,
                "file_index": 0,
                "selection_rank": 1,
                "xrootd_url": f.get("uri", ""),
                "file_size_bytes": f.get("size", np.nan),
                "planned_events_from_file": EVENTS_PER_FILE,
                "data_tier": "MINIAODSIM",
                "remote_only": True,
            }
        )

    search = pd.DataFrame(search_rows)
    added = pd.DataFrame(record_rows)
    search.to_csv(TABLES / "12_top_associated_search_records.csv", index=False)
    added.to_csv(TABLES / "13_top_associated_extension_records.csv", index=False)
    if not added.empty:
        records = pd.concat([records, added], ignore_index=True, sort=False).drop_duplicates("record_id", keep="last")
        manifest = pd.concat([manifest, pd.DataFrame(manifest_rows)], ignore_index=True, sort=False).drop_duplicates(
            ["record_id", "xrootd_url"], keep="last"
        )
    records.to_csv(RECORDS, index=False)
    manifest.to_csv(MANIFEST, index=False)

    report = f"""# TTZ/TTW Top-Associated Remote Extension Plan

## CERN API Check

{search.to_markdown(index=False)}

## Added Records

{added.to_markdown(index=False) if not added.empty else '_No new records added; records may already have been present or unavailable online._'}

These samples cover rare top-associated TTZ/TTW backgrounds. They are not
expected to dominate the MET boundary tail, but including them closes another
SM-composition objection.
"""
    (REPORTS / "08_TOP_ASSOCIATED_EXTENSION_PLAN.md").write_text(report, encoding="utf-8")
    print(search.to_string(index=False))
    print(added[["record_id", "title", "online_file_count", "planned_events"]] if not added.empty else "No new records")


if __name__ == "__main__":
    main()
