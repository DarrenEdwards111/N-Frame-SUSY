from __future__ import annotations

import json
import ssl
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from fuller_component_common import DATE, IMAGE, LOGS, MAIN, MAX_BYTES, REPORTS, ROOT, TABLES, apply_frozen_bnf, url_to_https


DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_expanded_sm_after_signal_parity")
OUT = ROOT / "data" / "processed" / "expanded_sm_after_signal_parity"
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
QUERIES = [
    ("TTbar", "TTToHadronic RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "top pair all-hadronic mimic"),
    ("TTbar", "TTToSemiLeptonic RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "top pair semileptonic mimic"),
    ("TTJets", "TTJets RunIISummer20UL16MiniAODv2 MINIAODSIM", 1, "inclusive ttbar/top mimic"),
    ("DYJetsToLL", "DYJetsToLL RunIISummer20UL16MiniAODv2 MINIAODSIM", 3, "Drell-Yan/lepton background"),
    ("ZJetsToNuNu", "ZJetsToNuNu RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "invisible Z plus jets background"),
    ("SingleTop", "ST_t-channel RunIISummer20UL16MiniAODv2 MINIAODSIM", 2, "single-top background"),
    ("WW", "WW RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "diboson background"),
    ("WZ", "WZ RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "diboson background"),
    ("ZZ", "ZZ RunIISummer20UL16MiniAODv2 MINIAODSIM", 4, "diboson background"),
]


def api_search(q: str) -> list[dict]:
    url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": q, "size": 10})
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("hits", {}).get("hits", [])


def files(md: dict) -> list[dict]:
    out = []
    for idx in md.get("_file_indices", []):
        out.extend(idx.get("files", []))
    return out


def check(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url_to_https(url), headers={"Range": "bytes=0-0", "User-Agent": "nframe-sm-check"})
    try:
        with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=20) as r:
            r.read(1)
            return r.status in (200, 206), f"HTTP {r.status}"
    except Exception as exc:
        return False, repr(exc)


def slug(label: str, record_id: int) -> str:
    s = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in label.lower()).strip("_")
    return f"{s}_{int(record_id)}"


def search_candidates() -> pd.DataFrame:
    rows, seen = [], set()
    for label, query, prio, reason in QUERIES:
        for hit in api_search(query):
            md = hit.get("metadata", {})
            title = md.get("title", "")
            if "MINIAODSIM" not in title.upper():
                continue
            key = (hit.get("id"), title)
            if key in seen:
                continue
            seen.add(key)
            fs = sorted(files(md), key=lambda f: int(f.get("size", 0) or 0))
            verified_url, verified_size, detail = "", 0, []
            for f in fs[:8]:
                url = f.get("uri", "")
                ok, msg = check(url)
                detail.append(f"{Path(url).name}: {ok} {msg}")
                if ok:
                    verified_url = url
                    verified_size = int(f.get("size", 0) or 0)
                    break
            sizes = [int(f.get("size", 0) or 0) for f in fs]
            rows.append({
                "record_id": hit.get("id"),
                "sample_name": title.split("/")[1] if "/" in title else label,
                "process_label": label,
                "title": title,
                "tier": "MINIAODSIM",
                "campaign": title.split("/")[2].split("-")[0] if len(title.split("/")) > 2 else "",
                "file_count": len(fs),
                "total_size_bytes": sum(sizes),
                "verified_accessible": bool(verified_url),
                "verified_url": verified_url,
                "verified_size_bytes": verified_size,
                "verification_details": " || ".join(detail),
                "priority": prio,
                "expected_component_availability": "full MiniAODSIM components if CMSSW extraction succeeds",
                "reason_for_inclusion": reason,
            })
            pd.DataFrame(rows).to_csv(TABLES / "expanded_sm_after_signal_parity_candidates.partial.csv", index=False)
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["verified_accessible", "priority", "verified_size_bytes"], ascending=[False, True, True])
    out.to_csv(TABLES / "expanded_sm_after_signal_parity_candidates.csv", index=False)
    return out


def download(row: pd.Series) -> dict:
    sample_id = slug(row["process_label"], row["record_id"])
    target = DOWNLOAD_ROOT / sample_id / Path(row["verified_url"]).name
    target.parent.mkdir(parents=True, exist_ok=True)
    status, error = "already_present", ""
    expected = int(row["verified_size_bytes"])
    if not target.exists() or target.stat().st_size != expected:
        try:
            status = "downloaded"
            with urllib.request.urlopen(url_to_https(row["verified_url"]), context=ssl._create_unverified_context(), timeout=180) as src:
                with target.open("wb") as dst:
                    while True:
                        chunk = src.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        dst.write(chunk)
        except Exception as exc:
            status, error = "failed", repr(exc)
    size = target.stat().st_size if target.exists() else 0
    return {
        "sample_id": sample_id,
        "record_id": row["record_id"],
        "process_label": row["process_label"],
        "tier": "MINIAODSIM",
        "url": row["verified_url"],
        "local_path": str(target),
        "expected_size_bytes": expected,
        "actual_size_bytes": size,
        "download_status": status if size == expected else "size_mismatch" if status != "failed" else status,
        "error": error,
    }


def add_provenance(df: pd.DataFrame, row: pd.Series, local: Path) -> pd.DataFrame:
    df = df.copy()
    df.insert(0, "sample_id", row["sample_id"])
    df.insert(1, "process_label", row["process_label"])
    df.insert(2, "record_id", row["record_id"])
    df.insert(3, "source_file", local.name)
    df.insert(4, "source_file_stem", local.stem)
    df.insert(5, "source_file_index", 0)
    df.insert(6, "local_input_path_or_container_path", f"{local} | /data/{local.relative_to(DOWNLOAD_ROOT).as_posix()}")
    df.insert(7, "event_index_within_file", range(len(df)))
    df.insert(8, "event_index_global_within_sample", range(len(df)))
    df["is_real_collision"] = False
    df["is_simulated"] = True
    df["include_in_real_only_analysis"] = False
    df["data_tier"] = "MINIAODSIM"
    df["classification"] = "SM_background"
    if "N_jets" not in df.columns and "N_jets_all" in df.columns:
        df["N_jets"] = df["N_jets_all"]
    return df


def extract(row: pd.Series) -> dict:
    local = Path(row["local_path"])
    run_id = f"expanded_sm_after_parity_{row['sample_id']}"
    log_path = LOGS / f"{run_id}.log"
    rel = local.relative_to(DOWNLOAD_ROOT).as_posix()
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES=/data/{rel}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=20; "
        "export NFRAME_MAXEVENTS_FULL=50000; "
        "bash /work/run_one_sample.sh"
    )
    cmd = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", "-v", f"{DOWNLOAD_ROOT}:/data", IMAGE, "bash", "-lc", cmd_inside]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    out_csv = OUT / "full_features" / f"{row['sample_id']}_event_features.csv"
    status, events = ("success", 0) if proc.returncode == 0 and raw.exists() else ("failed", 0)
    if status == "success":
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df = add_provenance(pd.read_csv(raw), row, local)
        df.to_csv(out_csv, index=False)
        events = len(df)
    return {**row.to_dict(), "extraction_status": status, "events_written": events, "output_csv": str(out_csv) if status == "success" else "", "log_path": str(log_path), "returncode": proc.returncode}


def main() -> None:
    for path in [DOWNLOAD_ROOT, OUT, TABLES, REPORTS, LOGS]:
        path.mkdir(parents=True, exist_ok=True)
    candidates = search_candidates()
    selected = []
    used_processes = set()
    total = 0
    for _, row in candidates[candidates["verified_accessible"].astype(str).str.lower().eq("true")].iterrows():
        if row["process_label"] in used_processes:
            continue
        size = int(row["verified_size_bytes"])
        if total + size > MAX_BYTES:
            continue
        selected.append(row)
        used_processes.add(row["process_label"])
        total += size
        if len(selected) >= 5:
            break
    manifest = pd.DataFrame([download(r) for r in selected]) if selected else pd.DataFrame()
    manifest.to_csv(TABLES / "expanded_sm_after_signal_parity_manifest.csv", index=False)
    ok = manifest[manifest["download_status"].isin(["already_present", "downloaded"])] if not manifest.empty else pd.DataFrame()
    extraction = pd.DataFrame([extract(r) for _, r in ok.iterrows()]) if not ok.empty else pd.DataFrame()
    frames = [pd.read_csv(p, low_memory=False) for p in extraction[extraction["extraction_status"].eq("success")]["output_csv"]] if not extraction.empty else []
    combined = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    if not combined.empty:
        scored, availability = apply_frozen_bnf(combined)
    else:
        scored, availability = combined, pd.DataFrame()
    scored.to_csv(OUT / "expanded_sm_backgrounds_with_BNF.csv", index=False)
    extraction.to_csv(TABLES / "expanded_sm_after_signal_parity_extraction_summary.csv", index=False)
    availability.to_csv(TABLES / "expanded_sm_after_signal_parity_feature_availability.csv", index=False)
    report = [
        "# Expanded SM After Signal Parity Report",
        "",
        f"Date: {DATE}",
        "",
        f"Selected download bytes: {int(manifest['actual_size_bytes'].sum()) if not manifest.empty else 0}",
        "",
        "## Candidates",
        "",
        candidates.head(40).to_markdown(index=False) if not candidates.empty else "No candidates found.",
        "",
        "## Manifest",
        "",
        manifest.to_markdown(index=False) if not manifest.empty else "No files downloaded.",
        "",
        "## Extraction",
        "",
        extraction.to_markdown(index=False) if not extraction.empty else "No extraction attempted.",
    ]
    (REPORTS / "EXPANDED_SM_AFTER_SIGNAL_PARITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(extraction.to_string(index=False) if not extraction.empty else "No expanded SM extraction.")


if __name__ == "__main__":
    main()
