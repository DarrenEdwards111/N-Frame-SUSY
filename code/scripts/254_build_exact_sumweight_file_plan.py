from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = SM / "tables"
REPORTS = SM / "reports"
CMSSW = ROOT / "cloud_remote_nframe_package" / "cmssw_full_extraction"
API = "https://opendata.cern.ch/api/records/"

# Full online coverage and non-trivial weights make these the most important
# records to compute exactly rather than approximate.
FULL_ONLINE_TARGET_RECORDS = {
    69548: "WJets",
    68072: "TTAssoc",
    68082: "TTAssoc",
    # These records expose every file online. The QCD records are large, so
    # the resumable runner can process them in bounded chunks.
    63118: "QCD",
    63126: "QCD",
    63102: "QCD",
    72753: "diboson",
    75592: "diboson",
}

# Probe-only records: useful for documenting the remaining normalisation gap,
# but not a full-record exact sumweight because the portal exposes only a
# subset of the files online for these records.
PARTIAL_ONLINE_PROBE_RECORDS = {
    69746: "WJets",
    68196: "TTAssoc",
    68205: "TTAssoc",
    74907: "ZNuNu",
    74909: "ZNuNu",
}


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []) or []:
        out.extend(idx.get("files", []) or [])
    out.extend(md.get("files", []) or [])
    return out


def collect_record(record_id: int, family: str, mode: str) -> list[dict[str, object]]:
    payload = requests.get(f"{API}{record_id}", timeout=60)
    payload.raise_for_status()
    md = payload.json().get("metadata", {})
    all_files = files(md)
    online = [f for f in all_files if str(f.get("availability", "")).lower() == "online"]
    rows = []
    for idx, file_info in enumerate(online):
        rows.append(
            {
                "record_id": record_id,
                "process_family": family,
                "mode": mode,
                "file_index": idx,
                "xrootd_url": file_info.get("uri", ""),
                "file_size_bytes": file_info.get("size", None),
                "all_file_count": len(all_files),
                "online_file_count": len(online),
                "record_complete_online": len(all_files) == len(online) and len(online) > 0,
                "record_url": f"https://opendata.cern.ch/record/{record_id}",
            }
        )
    return rows


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for rid, family in FULL_ONLINE_TARGET_RECORDS.items():
        rows.extend(collect_record(rid, family, "full_online_exact_target"))
    for rid, family in PARTIAL_ONLINE_PROBE_RECORDS.items():
        rows.extend(collect_record(rid, family, "partial_online_probe"))
    plan = pd.DataFrame(rows)
    plan.to_csv(TABLES / "14_exact_genfilter_sumweight_file_plan.csv", index=False)

    # The ROOT macro expects no header and a simple four-field CSV:
    # record_id,process_family,file_index,xrootd_url
    macro_rows = plan[["record_id", "process_family", "file_index", "xrootd_url"]].copy()
    macro_rows.to_csv(CMSSW / "exact_genfilter_sumweight_input.csv", index=False, header=False, lineterminator="\n")

    summary = (
        plan.groupby(["record_id", "process_family", "mode", "record_complete_online"], as_index=False)
        .agg(files=("xrootd_url", "count"), all_file_count=("all_file_count", "max"), online_file_count=("online_file_count", "max"))
        .sort_values(["mode", "record_id"])
    )
    summary.to_csv(TABLES / "15_exact_genfilter_sumweight_file_plan_summary.csv", index=False)
    report = f"""# Exact GenFilter Sumweight File Plan

## Purpose

This plan targets exact `GenFilterInfo` sums from the `LuminosityBlocks` tree.
Records with full online file coverage can be promoted to full-record exact
normalisation after the ROOT macro completes.

## Summary

{summary.to_markdown(index=False)}

## Interpretation

`full_online_exact_target` records can be summed over every online file because
the CERN record exposes the full file set online. `partial_online_probe` records
are probes only; they document the gap but cannot be used as full-record exact
normalisation unless the missing files or official sumweights are obtained.
"""
    (REPORTS / "09_EXACT_GENFILTER_SUMWEIGHT_FILE_PLAN.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(CMSSW / "exact_genfilter_sumweight_input.csv")


if __name__ == "__main__":
    main()
