from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
QUERIES = [
    ("SMS-T5Wg", "SMS-T5Wg RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "missing-energy plus photon/jets gluino-like trace"),
    ("SMS-T1tttt", "SMS-T1tttt RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "gluino/top-rich high multiplicity"),
    ("SMS-T1bbbb", "SMS-T1bbbb RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "gluino/b-rich heavy-flavour"),
    ("SMS-T1qqqq", "SMS-T1qqqq RunIISummer20UL16MiniAODv2 MINIAODSIM", 3, "gluino/light jets high multiplicity"),
    ("SMS-T2tt", "SMS-T2tt RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "compressed/stop benchmark"),
    ("chargino neutralino", "chargino neutralino RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "electroweakino style benchmark"),
    ("long lived", "long lived RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "long-lived/displaced-like benchmark"),
]


def api_search(q: str) -> list[dict]:
    url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": q, "size": 10})
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("hits", {}).get("hits", [])


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []):
        out += idx.get("files", [])
    return out


def mass_point(title: str) -> str:
    found = re.findall(r"m[A-Za-z]+-?\d+|m(?:Gluino|Stop|LSP|Chi)-?\d+", title)
    return ";".join(found)


def main() -> None:
    rows = []
    for label, query, priority, topology in QUERIES:
        for hit in api_search(query):
            md = hit.get("metadata", {})
            title = md.get("title", "")
            if "MINIAODSIM" not in title.upper() or "SMS" not in title.upper():
                continue
            fs = files(md)
            sizes = sorted([int(f.get("size", 0)) for f in fs])
            urls = [f.get("uri", "") for f in sorted(fs, key=lambda x: int(x.get("size", 0)))[:3]]
            rows.append({
                "record_id": hit.get("id"), "model_label": label, "title": title, "topology_class": topology,
                "mass_point": mass_point(title), "data_tier": "MINIAODSIM", "file_count": len(fs),
                "total_size_bytes": sum(sizes), "min_file_size_bytes": sizes[0] if sizes else 0,
                "max_file_size_bytes": sizes[-1] if sizes else 0, "first_file_urls": ";".join(urls),
                "first_file_sizes": ";".join(map(str, sizes[:3])), "priority": priority,
                "relevance_to_trace_hypothesis": "Tests missing-information stress, visible recoil, multiplicity and possibly b/displacement/reconstruction structure in a fuller MiniAODSIM benchmark.",
            })
    out = pd.DataFrame(rows).drop_duplicates(subset=["record_id", "title"]).sort_values(["priority", "min_file_size_bytes"])
    out.to_csv(TABLES / "miniaodsim_susy_candidate_samples.csv", index=False)
    report = ["# MiniAODSIM SUSY Candidate Search Report", "", f"Date: {DATE}", "", "Metadata-only search; no files downloaded in this phase.", "", out.to_markdown(index=False) if not out.empty else "No MiniAODSIM SUSY candidates found from the searched terms."]
    (REPORTS / "MINIAODSIM_SUSY_CANDIDATE_SEARCH_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.head(30).to_string(index=False) if not out.empty else "No SUSY MiniAODSIM candidates found.")


if __name__ == "__main__":
    main()
