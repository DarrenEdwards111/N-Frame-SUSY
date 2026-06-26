from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"

QUERIES = [
    ("TTJets", "TTJets RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "main ttbar/top mimic"),
    ("TTToHadronic", "TTToHadronic RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "top all-hadronic mimic"),
    ("TTToSemiLeptonic", "TTToSemiLeptonic RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "top semileptonic mimic"),
    ("QCD HT1000to1500", "QCD_HT1000to1500 RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "strongest current QCD mimic"),
    ("QCD HT700to1000", "QCD_HT700to1000 RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "current QCD mimic"),
    ("QCD HT500to700", "QCD_HT500to700 RunIISummer20UL16MiniAODv2 MINIAODSIM", 3, "lower high-HT QCD control"),
    ("WJetsToLNu", "WJetsToLNu RunIISummer20UL16MiniAODv2 MINIAODSIM", 3, "W+jets missing-energy background"),
    ("DYJetsToLL", "DYJetsToLL RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "DY/Z lepton background"),
    ("ZJetsToNuNu", "ZJetsToNuNu RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "invisible Z background"),
    ("SingleTop", "ST_t RunIISummer20UL16MiniAODv2 MINIAODSIM", 5, "single-top background"),
    ("Diboson", "WW WZ ZZ RunIISummer20UL16MiniAODv2 MINIAODSIM", 6, "diboson background"),
]


def api_search(q: str) -> list[dict]:
    url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": q, "size": 8})
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("hits", {}).get("hits", [])


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []):
        out += idx.get("files", [])
    return out


def main() -> None:
    rows = []
    for label, query, priority, reason in QUERIES:
        for hit in api_search(query):
            md = hit.get("metadata", {})
            title = md.get("title", "")
            if "MINIAODSIM" not in title.upper():
                continue
            fs = files(md)
            sizes = sorted([int(f.get("size", 0)) for f in fs])
            urls = [f.get("uri", "") for f in sorted(fs, key=lambda x: int(x.get("size", 0)))[:3]]
            rows.append({
                "record_id": hit.get("id"), "process_label": label, "title": title, "data_tier": "MINIAODSIM",
                "campaign": "RunIISummer20UL16MiniAODv2", "file_count": len(fs), "total_size_bytes": sum(sizes),
                "min_file_size_bytes": sizes[0] if sizes else 0, "max_file_size_bytes": sizes[-1] if sizes else 0,
                "first_file_urls": ";".join(urls), "first_file_sizes": ";".join(map(str, sizes[:3])),
                "likely_cmssw_compatible": True, "priority": priority, "reason_for_inclusion": reason,
                "addresses_current_weakness": "Adds MiniAODSIM packed candidates and secondary vertices for fuller P_reconstruction/P_displacement testing.",
            })
    out = pd.DataFrame(rows).drop_duplicates(subset=["record_id", "title"]).sort_values(["priority", "min_file_size_bytes"])
    out.to_csv(TABLES / "miniaodsim_background_candidates.csv", index=False)
    report = ["# MiniAODSIM Background Candidate Search Report", "", f"Date: {DATE}", "", "Metadata-only search; no files downloaded in this phase.", "", out.to_markdown(index=False)]
    (REPORTS / "MINIAODSIM_BACKGROUND_CANDIDATE_SEARCH_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
