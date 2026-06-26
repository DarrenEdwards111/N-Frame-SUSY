from __future__ import annotations

"""Create a remote, distributed-file SM plan for the frozen OPQ model.

Only CERN metadata is read here. The plan deliberately avoids local ROOT
downloads and replaces the prior single-file, partial-sample background route.
"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
API = "https://opendata.cern.ch/api/records/"
FILES_PER_RECORD = 3
EVENTS_PER_FILE = 5_000

# Existing API-audited UL16 MiniAODSIM records. Top is resolved through the
# live API because its exact available record can change.
FIXED = [
    (69746, "WJets", "inclusive lost-lepton component"),
    (69548, "WJets", "three-jet lost-lepton component"),
    (74907, "ZNuNu", "invisible-Z 100-200 GeV component"),
    (74909, "ZNuNu", "invisible-Z >200 GeV component"),
    (63118, "QCD", "QCD HT 300-500 component"),
    (63126, "QCD", "QCD HT 500-700 component"),
    (63102, "QCD", "QCD HT >2000 component"),
    (72753, "diboson", "WZ component"),
    (75592, "diboson", "ZZ component"),
]
TOP_QUERIES = ["TTTo2L2Nu RunIISummer20UL16MiniAODv2 MINIAODSIM", "TTToSemiLeptonic RunIISummer20UL16MiniAODv2 MINIAODSIM"]


def record(record_id: int) -> dict:
    response = requests.get(f"{API}{record_id}", timeout=60)
    response.raise_for_status()
    return response.json()


def find_top_records() -> list[tuple[int, str, str]]:
    out = []
    seen: set[int] = set()
    for query in TOP_QUERIES:
        response = requests.get(API, params={"q": query, "size": 20}, timeout=60)
        response.raise_for_status()
        for hit in response.json().get("hits", {}).get("hits", []):
            title = str(hit.get("metadata", {}).get("title", ""))
            rid = int(hit["id"])
            if rid in seen or "RunIISummer20UL16MiniAODv2" not in title or "MINIAODSIM" not in title:
                continue
            seen.add(rid)
            out.append((rid, "TTTop", "top control component resolved from current API"))
            break
    return out


def xrootd(uri: str) -> str:
    return uri if uri.startswith("root://") else uri.replace("/eos/", "root://eospublic.cern.ch//eos/")


def indexed_files(metadata: dict) -> list[dict]:
    """Flatten the current Open Data file-index representation."""
    direct = metadata.get("files", []) or []
    if direct:
        return direct
    files: list[dict] = []
    for index in metadata.get("_file_indices", []) or []:
        files.extend(index.get("files", []) or [])
    return files


def main() -> None:
    for path in [TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)
    audit_time = datetime.now(timezone.utc).isoformat()
    records = [*FIXED, *find_top_records()]
    manifest_rows = []
    record_rows = []
    for record_id, family, purpose in records:
        payload = record(record_id)
        md = payload.get("metadata", {})
        title = str(md.get("title", ""))
        if "MINIAODSIM" not in title:
            continue
        files = indexed_files(md)
        if not files:
            continue
        # Use online files only. On-demand files are not reliable for an
        # unattended remote extraction and are explicitly excluded.
        online = [f for f in files if str(f.get("availability", "")).lower() == "online"]
        if not online:
            continue
        # Evenly spaced online-file positions avoid the old one-smallest-file bias.
        indexes = np.unique(np.linspace(0, len(online) - 1, min(FILES_PER_RECORD, len(online)), dtype=int))
        xsec = md.get("cross_section", {}) or {}
        distribution = md.get("distribution", {}) or {}
        record_rows.append(
            {
                "audit_utc": audit_time,
                "record_id": record_id,
                "process_family": family,
                "purpose": purpose,
                "title": title,
                "cross_section_pb": xsec.get("total_value", np.nan),
                "cross_section_uncertainty_pb": xsec.get("total_value_uncertainty", np.nan),
                "generated_events": distribution.get("number_events", np.nan),
                "filter_efficiency": xsec.get("filter_efficiency", np.nan),
                "matching_efficiency": xsec.get("matching_efficiency", np.nan),
                "negative_weight_fraction": xsec.get("neg_weight_fraction", np.nan),
                "record_file_count": len(files),
                "online_file_count": len(online),
                "selected_file_count": len(indexes),
                "planned_events": len(indexes) * EVENTS_PER_FILE,
                "record_url": f"https://opendata.cern.ch/record/{record_id}",
                "normalisation_rule": "use per-event generator_weight and record-level sum of generator weights when available; otherwise mark yield non-final",
            }
        )
        for selection_rank, index in enumerate(indexes, start=1):
            f = online[int(index)]
            manifest_rows.append(
                {
                    "audit_utc": audit_time,
                    "record_id": record_id,
                    "process_family": family,
                    "purpose": purpose,
                    "file_index": int(index),
                    "selection_rank": selection_rank,
                    "xrootd_url": xrootd(str(f.get("uri", ""))),
                    "file_size_bytes": f.get("size", np.nan),
                    "planned_events_from_file": EVENTS_PER_FILE,
                    "data_tier": "MINIAODSIM",
                    "remote_only": True,
                }
            )

    record_df = pd.DataFrame(record_rows)
    manifest = pd.DataFrame(manifest_rows)
    record_df.to_csv(TABLES / "01_remote_sm_record_metadata.csv", index=False)
    manifest.to_csv(TABLES / "02_remote_sm_distributed_file_manifest.csv", index=False)
    report = f"""# Remote OPQ Standard-Model Background Build Plan

## Purpose

This plan is the corrective replacement for partial-file SM normalisation. It
uses distributed, remote XRootD files from record-level CMS UL16 MiniAODSIM
datasets and will retain only compact extracted features. No ROOT file is
downloaded locally.

The extraction includes the generator event weight. A final luminosity-normalised
yield will be reported only where the relevant record-level normalisation and
per-event weight information are available and auditable.

## Record Coverage

{record_df.to_markdown(index=False)}

## File Manifest

{manifest.to_markdown(index=False)}

## Limit

This is a finite, distributed Monte Carlo sample for shape and control closure.
It is not the full official CMS production sample. The subsequent likelihood
must retain finite-MC uncertainties and must not call the result official CMS
unless closure tests pass.
"""
    (REPORTS / "01_REMOTE_OPQ_SM_BACKGROUND_BUILD_PLAN.md").write_text(report, encoding="utf-8")
    print(record_df[["record_id", "process_family", "record_file_count", "selected_file_count", "planned_events"]].to_string(index=False))
    print(REPORTS / "01_REMOTE_OPQ_SM_BACKGROUND_BUILD_PLAN.md")


if __name__ == "__main__":
    main()
