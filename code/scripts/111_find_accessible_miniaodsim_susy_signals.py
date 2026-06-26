from __future__ import annotations

import json
import re
import ssl
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
LOGS = ROOT / "results" / "logs"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
DATE = "2026-06-09"

SEARCHES = [
    ("SMS-T5Wg", "SMS-T5Wg MINIAODSIM", 1, "gluino/photon high-MET benchmark"),
    ("T5Wg", "T5Wg MINIAODSIM", 1, "gluino/photon high-MET benchmark"),
    ("SMS-T1tttt", "SMS-T1tttt MINIAODSIM", 2, "gluino/top-rich high multiplicity"),
    ("SMS-T1bbbb", "SMS-T1bbbb MINIAODSIM", 2, "gluino/b-rich heavy flavour"),
    ("SMS-T1qqqq", "SMS-T1qqqq MINIAODSIM", 3, "gluino/light-jet high multiplicity"),
    ("SMS-T2tt", "SMS-T2tt MINIAODSIM", 4, "stop/compressed benchmark"),
    ("SMS-T2bb", "SMS-T2bb MINIAODSIM", 4, "sbottom/heavy flavour benchmark"),
    ("SMS-T2qq", "SMS-T2qq MINIAODSIM", 4, "squark/light-jet benchmark"),
    ("SMS-TChi", "SMS-TChi MINIAODSIM", 5, "electroweakino high-MET benchmark"),
    ("chargino", "chargino MINIAODSIM", 5, "electroweakino benchmark"),
    ("neutralino", "neutralino MINIAODSIM", 5, "electroweakino benchmark"),
    ("gluino", "gluino MINIAODSIM", 2, "gluino high-MET benchmark"),
    ("squark", "squark MINIAODSIM", 3, "squark high-MET benchmark"),
]


def api_search(query: str, size: int = 20) -> list[dict]:
    url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": query, "size": size})
    with urllib.request.urlopen(url, timeout=90) as response:
        return json.loads(response.read().decode("utf-8")).get("hits", {}).get("hits", [])


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []):
        out.extend(idx.get("files", []))
    return out


def data_tier(title: str) -> str:
    match = re.search(r"/([^/]+)/?$", title)
    return match.group(1) if match else ("MINIAODSIM" if "MINIAODSIM" in title.upper() else "")


def campaign(title: str) -> str:
    parts = title.split("/")
    return parts[2].split("-")[0] if len(parts) > 2 else ""


def mass_point(title: str) -> str:
    found = re.findall(r"m(?:Gluino|Stop|LSP|Chi|Chargino|Neutralino|Squark)?-?\d+|m[A-Za-z]+-\d+", title)
    return ";".join(dict.fromkeys(found))


def topology(title: str, label: str) -> str:
    text = f"{title} {label}".lower()
    if "t5wg" in text:
        return "gluino/photon high-MET"
    if "t1tttt" in text:
        return "gluino four-top"
    if "t1bbbb" in text:
        return "gluino b-rich"
    if "t1qqqq" in text:
        return "gluino light-jet"
    if "t2tt" in text:
        return "stop/compressed"
    if "t2bb" in text:
        return "sbottom b-rich"
    if "tchi" in text or "chargino" in text or "neutralino" in text:
        return "electroweakino"
    if "long" in text or "displaced" in text:
        return "long-lived/displaced"
    return "generic SUSY"


def relation(title: str) -> str:
    text = title.lower()
    rel = ["missing-information stress"]
    if any(x in text for x in ["gluino", "t1", "t5", "t2", "jet"]):
        rel.extend(["visible recoil", "multiplicity"])
    if any(x in text for x in ["bbbb", "t1bbbb", "t2bb", "stop", "t2tt", "tttt"]):
        rel.append("b-tag/heavy flavour")
    if any(x in text for x in ["long", "displaced", "ll"]):
        rel.append("displacement/reconstruction")
    return "; ".join(dict.fromkeys(rel))


def root_to_https(url: str) -> str:
    if url.startswith("root://eospublic.cern.ch//"):
        return "https://eospublic.cern.ch/" + url.split("root://eospublic.cern.ch//", 1)[1]
    return url


def root_path(url: str) -> str:
    if url.startswith("root://eospublic.cern.ch//"):
        return "/" + url.split("root://eospublic.cern.ch//", 1)[1].lstrip("/")
    return ""


def https_range_ok(url: str) -> tuple[bool, str]:
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(root_to_https(url), headers={"Range": "bytes=0-0", "User-Agent": "nframe-access-check"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as response:
            response.read(1)
            return response.status in (200, 206), f"HTTP {response.status}"
    except Exception as exc:
        return False, repr(exc)


def xrootd_stat_ok(url: str) -> tuple[bool, str]:
    path = root_path(url)
    if not path:
        return False, "not a root:// EOS URL"
    cmd = [
        "docker", "run", "--rm", IMAGE,
        "bash", "-lc", f"xrdfs root://eospublic.cern.ch stat '{path}'",
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=25)
    except Exception as exc:
        return False, repr(exc)
    text = proc.stdout.strip().replace("\n", " | ")
    return proc.returncode == 0, text[:400]


def candidate_score(label: str, title: str, size: int, accessible: bool, base_priority: int) -> float:
    text = f"{label} {title}".lower()
    score = 100 - 10 * base_priority
    if accessible:
        score += 100
    if "t5wg" in text:
        score += 50
    if any(x in text for x in ["t1tttt", "t1bbbb", "t1qqqq", "gluino"]):
        score += 35
    if any(x in text for x in ["tchi", "chargino", "neutralino"]):
        score += 20
    if any(x in text for x in ["t2tt", "t2bb", "t2qq", "stop", "squark"]):
        score += 15
    if size and size < 2 * 1024**3:
        score += 15
    if size and size < 200 * 1024**2:
        score += 10
    if "runiisummer20ul16miniaodv2" in text:
        score += 15
    return score


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    records = {}
    for label, query, priority, reason in SEARCHES:
        for q in [f"{query} RunIISummer20UL16MiniAODv2", query]:
            try:
                hits = api_search(q, size=8)
            except Exception:
                hits = []
            for hit in hits:
                md = hit.get("metadata", {})
                title = md.get("title", "")
                if "MINIAODSIM" not in title.upper():
                    continue
                if not any(tok in title.upper() for tok in ["SMS", "SUSY", "T5", "T1", "T2", "TCHI", "GLUINO", "SQUARK", "STOP", "CHARGINO", "NEUTRALINO"]):
                    continue
                key = (hit.get("id"), title)
                current = records.get(key)
                if current is None or priority < current["base_priority"]:
                    records[key] = {"hit": hit, "label": label, "base_priority": priority, "reason": reason}
    rows = []
    staged_path = TABLES / "accessible_miniaodsim_susy_signal_candidates.partial.csv"
    for item in records.values():
        hit = item["hit"]
        md = hit.get("metadata", {})
        title = md.get("title", "")
        fs = sorted(files(md), key=lambda f: int(f.get("size", 0) or 0))
        urls = [f.get("uri", "") for f in fs[:10]]
        sizes = [int(f.get("size", 0) or 0) for f in fs]
        verified_url = ""
        verified_size = 0
        verification = []
        for f in fs[:4]:
            url = f.get("uri", "")
            if not url:
                continue
            http_ok, http_msg = https_range_ok(url)
            xrd_ok, xrd_msg = (False, "not_checked")
            if not http_ok:
                xrd_ok, xrd_msg = xrootd_stat_ok(url)
            verification.append(f"{Path(url).name}: https={http_ok}({http_msg}); xrootd={xrd_ok}({xrd_msg})")
            if http_ok or xrd_ok:
                verified_url = url
                verified_size = int(f.get("size", 0) or 0)
                break
        accessible = bool(verified_url)
        rows.append({
            "record_id": hit.get("id"),
            "title": title,
            "sample_or_model_name": title.split("/")[1] if "/" in title else item["label"],
            "model_label": item["label"],
            "topology_class": topology(title, item["label"]),
            "mass_point": mass_point(title),
            "data_tier": data_tier(title),
            "campaign": campaign(title),
            "file_count": len(fs),
            "total_size_bytes": sum(sizes),
            "min_file_size_bytes": sizes[0] if sizes else 0,
            "max_file_size_bytes": sizes[-1] if sizes else 0,
            "first_10_file_urls": ";".join(urls),
            "first_10_file_sizes": ";".join(map(str, sizes[:10])),
            "verified_accessible": accessible,
            "verified_file_url": verified_url,
            "verified_file_size_bytes": verified_size,
            "url_verification_details": " || ".join(verification),
            "priority_score": candidate_score(item["label"], title, verified_size or (sizes[0] if sizes else 0), accessible, item["base_priority"]),
            "reason_for_inclusion": item["reason"],
            "expected_relation_to_trace_hypothesis": relation(title),
        })
        pd.DataFrame(rows).to_csv(staged_path, index=False)
        print(f"checked record {hit.get('id')} accessible={accessible} title={title[:90]}", flush=True)
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["record_id", "title"]).sort_values(["verified_accessible", "priority_score"], ascending=[False, False])
    out.to_csv(TABLES / "accessible_miniaodsim_susy_signal_candidates.csv", index=False)
    report = [
        "# Accessible MiniAODSIM SUSY Signal Search Report",
        "",
        f"Date: {DATE}",
        "",
        "This search queried CERN Open Data metadata and actively checked candidate file paths before any full download. HTTPS byte-range access was tried first; XRootD `xrdfs stat` inside the CMSSW image was used as fallback.",
        "",
        "## Candidates",
        "",
        out.to_markdown(index=False) if not out.empty else "No MiniAODSIM SUSY candidates were found by the searched terms.",
    ]
    (REPORTS / "ACCESSIBLE_MINIAODSIM_SUSY_SIGNAL_SEARCH_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.head(30).to_string(index=False) if not out.empty else "No candidates found.")


if __name__ == "__main__":
    main()
