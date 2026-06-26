from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TABLES = ROOT / "results" / "tables"
DATE = "2026-06-09"

QUERIES = [
    ("SMS-T5Wg", "SMS-T5Wg MINIAODSIM", 1),
    ("T5Wg", "T5Wg MINIAODSIM", 1),
    ("SMS-T1tttt", "SMS-T1tttt MINIAODSIM", 2),
    ("T1tttt", "T1tttt MINIAODSIM", 2),
    ("SMS-T1bbbb", "SMS-T1bbbb MINIAODSIM", 2),
    ("T1bbbb", "T1bbbb MINIAODSIM", 2),
    ("SMS-T1qqqq", "SMS-T1qqqq MINIAODSIM", 3),
    ("T1qqqq", "T1qqqq MINIAODSIM", 3),
    ("T1", "T1 MINIAODSIM gluino", 4),
    ("T5", "T5 MINIAODSIM gluino", 4),
    ("gluino simplified model", "gluino simplified model MINIAODSIM", 4),
    ("high MET SUSY", "high MET SUSY MINIAODSIM", 5),
    ("gluino neutralino jets MET", "gluino neutralino jets MET MINIAODSIM", 4),
    ("squark gluino neutralino", "squark gluino neutralino MINIAODSIM", 5),
]


def search(q: str) -> list[dict]:
    url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": q, "size": 15})
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("hits", {}).get("hits", [])


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []):
        out.extend(idx.get("files", []))
    return out


def https_check(url: str) -> tuple[bool, str]:
    if url.startswith("root://eospublic.cern.ch//"):
        url = "https://eospublic.cern.ch/" + url.split("root://eospublic.cern.ch//", 1)[1]
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": "nframe-targeted-check"})
    try:
        with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=25) as r:
            r.read(1)
            return r.status in (200, 206), f"HTTP {r.status}"
    except Exception as exc:
        return False, repr(exc)


def mass(title: str) -> str:
    found = re.findall(r"m(?:Gluino|Stop|LSP|Chi|Neutralino|Squark)?-?\d+|M-\d+|MSquark-\d+|MChi-\d+", title)
    return ";".join(dict.fromkeys(found))


def topology(title: str) -> str:
    t = title.lower()
    if "t5wg" in t:
        return "T5Wg gluino/photon high-MET"
    if "t1tttt" in t:
        return "T1tttt gluino four-top high-MET"
    if "t1bbbb" in t:
        return "T1bbbb gluino b-rich high-MET"
    if "t1qqqq" in t:
        return "T1qqqq gluino light-jet high-MET"
    if "gluinogluino" in t and "neutralino" in t:
        return "gluino-to-neutralino high-MET"
    if "gluino" in t:
        return "gluino-like high-MET"
    if "squark" in t:
        return "squark-like high-MET"
    return "targeted SUSY high-MET"


def priority(label: str, title: str, base: int, accessible: bool, size: int) -> float:
    t = f"{label} {title}".lower()
    score = 100 - base * 10
    if accessible:
        score += 100
    if "t5wg" in t:
        score += 80
    if any(x in t for x in ["t1tttt", "t1bbbb", "t1qqqq"]):
        score += 60
    if "gluinogluino" in t and "neutralino" in t:
        score += 45
    if "runiisummer20ul16miniaodv2" in t:
        score += 25
    if size and size < 2 * 1024**3:
        score += 15
    return score


def main() -> None:
    seen = {}
    for label, query, base in QUERIES:
        for q in [f"{query} RunIISummer20UL16MiniAODv2", query]:
            try:
                hits = search(q)
            except Exception:
                continue
            for hit in hits:
                md = hit.get("metadata", {})
                title = md.get("title", "")
                if "MINIAODSIM" not in title.upper():
                    continue
                if not any(x in title.upper() for x in ["T5", "T1", "GLUINO", "SQUARK", "NEUTRALINO", "SMS"]):
                    continue
                key = (hit.get("id"), title)
                if key not in seen or base < seen[key]["base"]:
                    seen[key] = {"hit": hit, "label": label, "base": base}
    rows = []
    for item in seen.values():
        hit = item["hit"]
        md = hit.get("metadata", {})
        title = md.get("title", "")
        fs = sorted(files(md), key=lambda x: int(x.get("size", 0) or 0))
        first = fs[:20]
        verified_url, verified_size, details = "", 0, []
        for f in first[:8]:
            url = f.get("uri", "")
            ok, msg = https_check(url)
            details.append(f"{Path(url).name}: {ok} {msg}")
            if ok:
                verified_url = url
                verified_size = int(f.get("size", 0) or 0)
                break
        sizes = [int(f.get("size", 0) or 0) for f in fs]
        parts = title.split("/")
        sample = parts[1] if len(parts) > 1 else item["label"]
        campaign = parts[2].split("-")[0] if len(parts) > 2 else ""
        row = {
            "record_id": hit.get("id"),
            "title": title,
            "sample_model_name": sample,
            "topology_class": topology(title),
            "mass_point": mass(title),
            "data_tier": "MINIAODSIM",
            "campaign": campaign,
            "file_count": len(fs),
            "total_size_bytes": sum(sizes),
            "first_20_file_urls": ";".join(f.get("uri", "") for f in first),
            "first_20_file_sizes": ";".join(map(str, sizes[:20])),
            "verified_accessible": bool(verified_url),
            "verified_file_url": verified_url,
            "verified_file_size_bytes": verified_size,
            "verification_details": " || ".join(details),
            "priority_score": priority(item["label"], title, item["base"], bool(verified_url), verified_size or (sizes[0] if sizes else 0)),
            "expected_relevance_to_trace_hypothesis": "missing-information stress; visible recoil; multiplicity; possible b/reconstruction boundary stress",
        }
        rows.append(row)
        pd.DataFrame(rows).to_csv(TABLES / "targeted_t5wg_t1_highmet_miniaodsim_candidates.partial.csv", index=False)
        print(f"checked {hit.get('id')} accessible={bool(verified_url)} {sample[:80]}", flush=True)
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["record_id", "title"]).sort_values(["verified_accessible", "priority_score"], ascending=[False, False])
    out.to_csv(TABLES / "targeted_t5wg_t1_highmet_miniaodsim_candidates.csv", index=False)
    report = [
        "# Targeted T5Wg/T1 High-MET MiniAODSIM Search Report",
        "",
        f"Date: {DATE}",
        "",
        "This targeted search looked for SMS-T5Wg/T1/T5/gluino high-MET MiniAODSIM candidates and verified candidate ROOT URLs with HTTPS byte-range reads before any download.",
        "",
        out.to_markdown(index=False) if not out.empty else "No candidates found.",
    ]
    (REPORTS / "TARGETED_T5WG_T1_HIGHMET_MINIAODSIM_SEARCH_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.head(20).to_string(index=False) if not out.empty else "No candidates found.")


if __name__ == "__main__":
    main()
