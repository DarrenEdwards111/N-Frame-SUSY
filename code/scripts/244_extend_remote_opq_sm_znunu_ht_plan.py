from __future__ import annotations

"""Extend the remote OPQ SM manifest with available ZNuNu HT-binned samples."""

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
AUDIT_TAG = "2026-06-22T_ZNuNuHT_extension"
ZNUNU_HT_RECORDS = [74893, 74897, 74901, 74903, 74905, 74895, 74899]


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []) or []:
        out.extend(idx.get("files", []) or [])
    out.extend(md.get("files", []) or [])
    return out


def main() -> None:
    records = pd.read_csv(RECORDS)
    manifest = pd.read_csv(MANIFEST)
    record_rows = []
    manifest_rows = []
    existing = set(records["record_id"].astype(int))
    for rid in ZNUNU_HT_RECORDS:
        if rid in existing:
            continue
        payload = requests.get(f"{API}{rid}", timeout=60)
        payload.raise_for_status()
        md = payload.json().get("metadata", {})
        title = str(md.get("title", ""))
        xsec = md.get("cross_section", {}) or {}
        dist = md.get("distribution", {}) or {}
        all_files = files(md)
        online = [f for f in all_files if str(f.get("availability", "")).lower() == "online"]
        if not online:
            continue
        f = online[0]
        record_rows.append(
            {
                "audit_utc": AUDIT_TAG,
                "record_id": rid,
                "process_family": "ZNuNu",
                "purpose": "invisible-Z HT-binned component",
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
                "process_family": "ZNuNu",
                "purpose": "invisible-Z HT-binned component",
                "file_index": 0,
                "selection_rank": 1,
                "xrootd_url": f.get("uri", ""),
                "file_size_bytes": f.get("size", np.nan),
                "planned_events_from_file": EVENTS_PER_FILE,
                "data_tier": "MINIAODSIM",
                "remote_only": True,
            }
        )
    if record_rows:
        records = pd.concat([records, pd.DataFrame(record_rows)], ignore_index=True, sort=False).drop_duplicates("record_id", keep="last")
        manifest = pd.concat([manifest, pd.DataFrame(manifest_rows)], ignore_index=True, sort=False).drop_duplicates(["record_id", "xrootd_url"], keep="last")
    records.to_csv(RECORDS, index=False)
    manifest.to_csv(MANIFEST, index=False)
    summary = pd.DataFrame(record_rows)
    summary.to_csv(TABLES / "10_znunu_ht_extension_records.csv", index=False)
    report = f"""# ZNuNu HT-Binned Remote Extension

Added available online ZNuNu HT-binned UL16 MiniAODSIM records to the remote OPQ
SM background manifest.

{summary.to_markdown(index=False) if not summary.empty else '_No new records added._'}

Top/TT records were searched separately and were not available through the same
RunIISummer20UL16MiniAODv2 MiniAODSIM portal route.
"""
    (REPORTS / "06_ZNUNU_HT_EXTENSION_PLAN.md").write_text(report, encoding="utf-8")
    print(summary[["record_id", "title", "online_file_count", "planned_events"]] if not summary.empty else "No new records")


if __name__ == "__main__":
    main()
