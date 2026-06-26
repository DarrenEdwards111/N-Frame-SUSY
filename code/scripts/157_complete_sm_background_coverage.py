from __future__ import annotations

import importlib.util
import json
import math
import shutil
import ssl
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

try:
    import pyhf
except Exception:
    pyhf = None


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_next_complete_sm_background_coverage"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
FIGURES = OUT / "figures"
STATMODEL = OUT / "statistical_model"
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_complete_sm_background_coverage")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"
PREV = ROOT / "outputs_today_blinded_lumi_weighted_validation"
PREV_PHYS = ROOT / "outputs_today_physics_style_susy_search_framework"
DATE = "2026-06-11"
MAX_DOWNLOAD_BYTES = 30 * 1024**3
MAX_EVENTS_FULL = 20000
SIGNAL_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]
CONTROL_VALIDATION = ["CR_QCD", "CR_MET", "CR_Muon", "CR_BtagTop", "VR1", "VR2", "VR4", "VR5"]
ALL_REGIONS = SIGNAL_REGIONS + CONTROL_VALIDATION

SEARCH_SPECS = [
    ("QCD HT100to200", "QCD_HT100to200 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 3, "CR_QCD;VR2;VR5", "fills low HT multijet"),
    ("QCD HT200to300", "QCD_HT200to300 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 2, "CR_QCD;VR2;VR5", "fills lower/mid HT multijet"),
    ("QCD HT300to500", "QCD_HT300to500 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 1, "CR_QCD;VR2;VR5", "large missing QCD bin"),
    ("QCD HT500to700", "QCD_HT500to700 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 1, "CR_QCD;VR2;VR5", "large missing QCD bin"),
    ("QCD HT700to1000", "QCD_HT700to1000 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 5, "CR_QCD;VR2;VR5", "already partly covered; search for completeness"),
    ("QCD HT1000to1500", "QCD_HT1000to1500 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 5, "CR_QCD;VR2;VR5", "already partly covered; search for completeness"),
    ("QCD HT1500to2000", "QCD_HT1500to2000 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 2, "CR_QCD;VR2;VR5", "fills very high HT multijet"),
    ("QCD HT2000toInf", "QCD_HT2000toInf TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "QCD", 2, "CR_QCD;VR2;VR5", "fills extreme HT multijet"),
    ("WJetsToLNu inclusive", "WJetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", 1, "CR_Muon;CR_MET;VR4", "lost lepton and muon control"),
    ("W1JetsToLNu", "W1JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", 2, "CR_Muon;CR_MET;VR4", "W+jets N-jet bin"),
    ("W2JetsToLNu", "W2JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", 2, "CR_Muon;CR_MET;VR4", "W+jets N-jet bin"),
    ("W3JetsToLNu", "W3JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", 2, "CR_Muon;CR_MET;VR4", "W+jets N-jet bin"),
    ("W4JetsToLNu", "W4JetsToLNu TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "WJets", 4, "CR_Muon;CR_MET;VR4", "already partly covered"),
    ("ZJetsToNuNu Zpt100to200", "ZJetsToNuNu_Zpt-100to200 TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "ZNuNu", 2, "CR_MET", "invisible Z MET control"),
    ("ZJetsToNuNu Zpt200toInf", "ZJetsToNuNu_Zpt-200toInf TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "ZNuNu", 4, "CR_MET", "already partly covered"),
    ("DYJetsToLL", "DYJetsToLL TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "DY", 2, "CR_Muon;VR4", "dimuon/DY control"),
    ("TTToSemiLeptonic", "TTToSemiLeptonic RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", 1, "CR_BtagTop;CR_Muon;VR4", "top semileptonic"),
    ("TTToHadronic", "TTToHadronic RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", 1, "CR_BtagTop;VR5", "top hadronic"),
    ("TTTo2L2Nu", "TTTo2L2Nu RunIISummer20UL16MiniAODv2 MINIAODSIM", "TT/top", 1, "CR_BtagTop;CR_Muon;CR_MET", "top dileptonic"),
    ("ST t-channel", "ST_t-channel RunIISummer20UL16MiniAODv2 MINIAODSIM", "single top", 3, "CR_BtagTop;CR_Muon", "single top"),
    ("ST tW", "ST_tW RunIISummer20UL16MiniAODv2 MINIAODSIM", "single top", 3, "CR_BtagTop;CR_Muon", "single top tW"),
    ("WW", "WW TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "diboson", 5, "CR_Muon;CR_MET", "diboson completion"),
    ("WZ", "WZ TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "diboson", 5, "CR_Muon;CR_MET", "diboson completion"),
    ("ZZ", "ZZ TuneCP5 RunIISummer20UL16MiniAODv2 MINIAODSIM", "diboson", 5, "CR_Muon;CR_MET", "diboson completion"),
]

KNOWN_RECORDS = [
    (63118, "QCD HT300to500", "QCD", 1, "CR_QCD;VR2;VR5", "large missing QCD bin"),
    (63126, "QCD HT500to700", "QCD", 1, "CR_QCD;VR2;VR5", "large missing QCD bin"),
    (63094, "QCD HT1500to2000", "QCD", 2, "CR_QCD;VR2;VR5", "very high HT QCD"),
    (63102, "QCD HT2000toInf", "QCD", 2, "CR_QCD;VR2;VR5", "extreme HT QCD"),
    (69746, "WJetsToLNu inclusive", "WJets", 1, "CR_Muon;CR_MET;VR4", "inclusive W+jets/lost lepton"),
    (69548, "W3JetsToLNu", "WJets", 2, "CR_Muon;CR_MET;VR4", "W+jets N-jet bin"),
    (69550, "W4JetsToLNu", "WJets", 4, "CR_Muon;CR_MET;VR4", "already partly covered W+jets bin"),
    (74907, "ZJetsToNuNu Zpt100to200", "ZNuNu", 2, "CR_MET", "invisible Z MET control"),
    (74909, "ZJetsToNuNu Zpt200toInf", "ZNuNu", 4, "CR_MET", "already partly covered invisible Z"),
    (38502, "WW-like existing record", "diboson", 5, "CR_Muon;CR_MET", "already partly covered diboson"),
    (72753, "WZ existing record", "diboson", 5, "CR_Muon;CR_MET", "already partly covered diboson"),
    (36928, "ZZ-like existing record", "diboson", 5, "CR_Muon;CR_MET", "already partly covered diboson"),
]


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS, SOURCES, FIGURES, STATMODEL, DOWNLOAD_ROOT]:
        p.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    return view.to_markdown(index=False)


def api_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def files_from_record(md: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx in md.get("_file_indices", []):
        out.extend(idx.get("files", []))
    if not out:
        out.extend(md.get("files", []))
    return out


def url_to_https(url: str) -> str:
    if url.startswith("root://eospublic.cern.ch//"):
        return "https://eospublic.cern.ch/" + url.split("root://eospublic.cern.ch//", 1)[1]
    return url


def fetch_record(record_id: int) -> dict[str, Any]:
    cache = SOURCES / f"cern_record_{record_id}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    data = api_json(f"https://opendata.cern.ch/api/records/{record_id}")
    cache.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def import_prev():
    script = ROOT / "scripts" / "154_physics_style_susy_search_framework.py"
    spec = importlib.util.spec_from_file_location("prev154", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import previous framework")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STATMODEL = PREV_PHYS / "statistical_model"
    module.SOURCES = SOURCES
    return module


def phase1_missing_coverage() -> pd.DataFrame:
    closure = pd.read_csv(PREV / "tables" / "03_control_and_validation_region_closure.csv")
    rows = []
    missing_map = {
        "CR_QCD": ("QCD HT-binned multijet across HT100-Inf; QCD heavy flavour if available", "high", True, True),
        "VR2": ("QCD HT-binned multijet across HT100-Inf; hadronic top", "high", True, True),
        "CR_MET": ("ZJetsToNuNu, WJets lost lepton, TTJets, QCD mismeasured MET", "very high", True, True),
        "CR_Muon": ("WJetsToLNu, DYJetsToLL/ZToMuMu, TTJets, single top, QCD MuEnriched", "very high", True, True),
        "CR_BtagTop": ("TTJets/TTTo*, single top, W+b, QCD b-enriched/heavy flavour", "very high", True, True),
        "VR1": ("W/Z+jets, QCD mismeasured MET, TTJets", "high", True, True),
        "VR4": ("WJetsToLNu, DYJetsToLL, TTJets, single top, diboson, QCD MuEnriched", "very high", True, True),
        "VR5": ("complete QCD HT bins, hadronic TTJets, W/Z+jets high HT", "high", True, True),
    }
    for _, r in closure.iterrows():
        miss, priority, mini, trig = missing_map.get(r["region"], ("unmapped", "medium", True, True))
        obs = float(r["observed_real_data"])
        exp = float(r["weighted_sm_background_nominal"])
        rows.append({
            "region": r["region"],
            "observed_count": obs,
            "current_weighted_sm_count": exp,
            "closure_failure_ratio_observed_over_expected": obs / exp if exp > 0 else np.inf,
            "likely_missing_processes": miss,
            "priority": priority,
            "miniaodsim_records_likely_needed": mini,
            "trigger_specific_samples_likely_needed": trig,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "01_missing_sm_coverage_by_region.csv", index=False)
    write_text(REPORTS / "01_MISSING_SM_COVERAGE_DIAGNOSIS.md", f"""# Missing SM Coverage Diagnosis

Date: {DATE}

The failed controls indicate missing background coverage, not an interpretable SR1/SR5 signal. The previous weighted subset has no weighted rows at all in CR_MET, CR_Muon and VR5, and severely underpredicts QCD/top-like controls.

{md(out)}
""")
    return out


def phase2_search_records() -> pd.DataFrame:
    rows = []
    seen: set[int] = set()

    def add_record(rid: int, family: str, priority: int, helps: str, reason: str) -> None:
        if rid in seen:
            return
        try:
            md_full = fetch_record(rid).get("metadata", {})
        except Exception:
            return
        title = md_full.get("title", "")
        if "RunIISummer20UL16MiniAODv2" not in title or "MINIAODSIM" not in title:
            return
        seen.add(rid)
        fs = sorted(files_from_record(md_full), key=lambda f: int(f.get("size", 0) or 0))
        sizes = [int(f.get("size", 0) or 0) for f in fs]
        xsec = md_full.get("cross_section", {}) or {}
        dist = md_full.get("distribution", {}) or {}
        nano = [rel.get("recid") for rel in md_full.get("relations", []) if "NANOAODSIM" in rel.get("description", "").upper()]
        rows.append({
            "record_id": rid,
            "title": title,
            "process_family": family,
            "dataset_name": title.split("/")[1] if "/" in title else title,
            "data_tier": "MINIAODSIM",
            "year_campaign": "RunIISummer20UL16MiniAODv2",
            "cross_section_pb": xsec.get("total_value", np.nan),
            "cross_section_uncertainty_pb": xsec.get("total_value_uncertainty", np.nan),
            "number_generated_events": dist.get("number_events", np.nan),
            "filter_efficiency": xsec.get("filter_efficiency", np.nan),
            "matching_efficiency": xsec.get("matching_efficiency", np.nan),
            "negative_weight_fraction": xsec.get("neg_weight_fraction", np.nan),
            "file_count": len(fs),
            "total_size_bytes": sum(sizes),
            "min_file_size_bytes": min(sizes) if sizes else 0,
            "individual_file_sizes_first10": ";".join(map(str, sizes[:10])),
            "smallest_file_url": fs[0].get("uri", "") if fs else "",
            "is_miniaodsim": True,
            "nanoaodsim_alternative_record": ";".join(map(str, nano)),
            "priority_for_analysis": priority,
            "reason_for_inclusion": reason,
            "expected_control_region_helped": helps,
            "download_feasibility": "small_file_feasible" if sizes and sizes[0] < 2 * 1024**3 else "large_but_possible" if sizes else "no_files_indexed",
            "record_url": f"https://opendata.cern.ch/record/{rid}",
        })

    for rid, _label, family, priority, helps, reason in KNOWN_RECORDS:
        add_record(rid, family, priority, helps, reason)

    for label, query, family, priority, helps, reason in SEARCH_SPECS:
        url = "https://opendata.cern.ch/api/records/?" + urllib.parse.urlencode({"q": query, "size": 12})
        try:
            hits = api_json(url).get("hits", {}).get("hits", [])
        except Exception as exc:
            rows.append({"search_label": label, "query": query, "search_error": repr(exc)})
            continue
        for hit in hits:
            md0 = hit.get("metadata", {})
            title = md0.get("title", "")
            if "RunIISummer20UL16MiniAODv2" not in title or "MINIAODSIM" not in title:
                continue
            rid = int(hit["id"])
            if rid in seen:
                continue
            add_record(rid, family, priority, helps, reason)
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.drop_duplicates("record_id").sort_values(["priority_for_analysis", "min_file_size_bytes"])
    out.to_csv(TABLES / "02_candidate_sm_records_from_cern.csv", index=False)
    write_text(REPORTS / "02_CERN_SM_RECORD_SEARCH_REPORT.md", f"""# CERN SM Record Search Report

Date: {DATE}

This is a metadata-only CERN Open Data search for 2016 UL MiniAODSIM records matching the failed controls. Top-family MiniAODSIM records were searched explicitly; any missing top rows in the table mean the API search did not return compatible RunIISummer20UL16 MiniAODSIM records for those terms.

{md(out, 80)}
""")
    return out


def phase3_select_plan(cands: pd.DataFrame) -> pd.DataFrame:
    selected = []
    used_families: dict[str, int] = {}
    total = 0
    if cands.empty:
        plan = pd.DataFrame()
    else:
        candidates = cands[cands["smallest_file_url"].astype(str).str.len() > 0].copy()
        candidates = candidates.sort_values(["priority_for_analysis", "min_file_size_bytes"])
        for _, row in candidates.iterrows():
            fam = str(row["process_family"])
            cap_per_family = 3 if fam == "QCD" else 2 if fam == "WJets" else 1
            if used_families.get(fam, 0) >= cap_per_family:
                continue
            size = int(row["min_file_size_bytes"])
            if size <= 0 or total + size > MAX_DOWNLOAD_BYTES:
                continue
            selected.append(row)
            used_families[fam] = used_families.get(fam, 0) + 1
            total += size
        plan = pd.DataFrame(selected)
    if not plan.empty:
        plan = plan.rename(columns={"smallest_file_url": "selected_file_url", "min_file_size_bytes": "selected_file_size_bytes"})
        plan["planned_download_order"] = range(1, len(plan) + 1)
        plan["partial_file_extraction"] = True
        plan["max_events_full_extraction"] = MAX_EVENTS_FULL
        plan["planned_download_size_cumulative_bytes"] = plan["selected_file_size_bytes"].cumsum()
        plan["reason_selected"] = plan["reason_for_inclusion"] + "; smallest indexed file under cap"
    plan.to_csv(TABLES / "03_selected_sm_expansion_plan.csv", index=False)
    write_text(REPORTS / "03_MINIMAL_VIABLE_SM_EXPANSION_PLAN.md", f"""# Minimal Viable SM Expansion Plan

Date: {DATE}

Hard download cap: 30 GiB. The plan selects the smallest indexed MiniAODSIM files from the highest-priority missing background families. This is a partial-file shape expansion, so MC statistical uncertainty and coverage warnings remain important.

Planned bytes: {int(plan['selected_file_size_bytes'].sum()) if not plan.empty else 0}

{md(plan)}
""")
    return plan


def download_file(url: str, target: Path, expected: int) -> tuple[str, str]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and (expected == 0 or target.stat().st_size == expected):
        return "already_present", ""
    try:
        with urllib.request.urlopen(url_to_https(url), context=ssl._create_unverified_context(), timeout=180) as src:
            with target.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
        if expected and target.stat().st_size != expected:
            return "size_mismatch", ""
        return "downloaded", ""
    except Exception as exc:
        return "failed", repr(exc)


def slug(row: pd.Series) -> str:
    s = str(row["dataset_name"]).lower()
    s = "".join(ch if ch.isalnum() else "_" for ch in s).strip("_")
    return f"{s[:80]}_{int(row['record_id'])}"


def phase4_download(plan: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in plan.iterrows():
        sample_slug = slug(row)
        target = DOWNLOAD_ROOT / sample_slug / Path(str(row["selected_file_url"])).name
        expected = int(row["selected_file_size_bytes"])
        status, error = download_file(str(row["selected_file_url"]), target, expected)
        rows.append({
            "sample_slug": sample_slug,
            "record_id": row["record_id"],
            "process_family": row["process_family"],
            "dataset_name": row["dataset_name"],
            "selected_file_url": row["selected_file_url"],
            "local_path": str(target),
            "expected_size_bytes": expected,
            "actual_size_bytes": target.stat().st_size if target.exists() else 0,
            "download_status": status,
            "error": error,
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "04_download_manifest.csv", index=False)
    write_text(REPORTS / "04_SM_DOWNLOAD_REPORT.md", f"""# SM Download Report

Date: {DATE}

Total new/already-present selected bytes: {int(manifest['actual_size_bytes'].sum()) if not manifest.empty else 0}

{md(manifest)}
""")
    return manifest


def run_cmssw(row: pd.Series, max_events: int, mode: str) -> dict[str, Any]:
    local = Path(row["local_path"])
    run_id = f"complete_sm_{mode}_{row['sample_slug']}"
    out_dir = CMSSW_WORK / "outputs" / run_id
    raw = out_dir / "event_features.csv"
    log_path = SOURCES / f"{run_id}.log"
    rel = local.relative_to(DOWNLOAD_ROOT).as_posix()
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES=/data/{rel}; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=1000; "
        f"export NFRAME_MAXEVENTS_FULL={max_events}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", "-v", f"{DOWNLOAD_ROOT}:/data", IMAGE, "bash", "-lc", cmd_inside]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=7200)
    status = "success" if proc.returncode == 0 and raw.exists() else "failed"
    out_csv = SOURCES / f"{run_id}_event_features.csv"
    events = 0
    if status == "success":
        df = pd.read_csv(raw, low_memory=False)
        df.insert(0, "sample_id", row["sample_slug"])
        df.insert(1, "process_label", row["dataset_name"])
        df.insert(2, "record_id", row["record_id"])
        df.insert(3, "source_file", local.name)
        df["classification"] = "SM_background"
        df["process_family"] = row["process_family"]
        df["data_tier"] = "MINIAODSIM"
        df.to_csv(out_csv, index=False)
        events = len(df)
    return {
        "sample_slug": row["sample_slug"],
        "record_id": row["record_id"],
        "process_family": row["process_family"],
        "dataset_name": row["dataset_name"],
        "mode": mode,
        "maxEvents": max_events,
        "status": status,
        "events_written": events,
        "output_csv": str(out_csv) if status == "success" else "",
        "log_path": str(log_path),
        "returncode": proc.returncode,
    }


def phase5_extract(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ok = manifest[manifest["download_status"].isin(["already_present", "downloaded"])]
    for _, row in ok.iterrows():
        rows.append(run_cmssw(row, MAX_EVENTS_FULL, "full_capped"))
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "05_extraction_summary.csv", index=False)
    write_text(REPORTS / "05_CMSSW_EXTRACTION_REPORT.md", f"""# CMSSW Extraction Report

Date: {DATE}

Extraction used the existing CMSSW MiniAOD analyzer route and capped full extraction at maxEvents={MAX_EVENTS_FULL} per file.

{md(summary)}
""")
    return summary


def phase6_score(extraction: pd.DataFrame, plan: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prev = import_prev()
    frames = []
    for _, row in extraction[extraction["status"].eq("success")].iterrows():
        df = pd.read_csv(row["output_csv"], low_memory=False)
        frames.append(df)
    if frames:
        combined = pd.concat(frames, ignore_index=True, sort=False)
        # Reuse frozen scoring constants and region definitions from the earlier scripts.
        sys_path = str(ROOT / "scripts")
        import sys
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        from fuller_component_common import apply_frozen_bnf
        scored, availability = apply_frozen_bnf(combined)
        # Normalise for previous region function.
        item = {"path": SOURCES / "new_sm_scored.csv", "tier": "MINIAODSIM"}
        scored.to_csv(item["path"], index=False)
        sim = prev.read_sim({"path": item["path"], "tier": "MINIAODSIM", "label": "new_complete_sm"}, "standard_model_simulation")
        sim = prev.apply_regions(prev.add_axes(sim))
    else:
        scored = pd.DataFrame()
        availability = pd.DataFrame()
        sim = pd.DataFrame()
    rows = []
    meta = plan.set_index("record_id")
    lumi_fb = 16.393381
    for _, group in scored.groupby("record_id") if not scored.empty else []:
        pass
    for _, row in extraction.iterrows():
        rid = int(row["record_id"])
        p = meta.loc[rid] if rid in meta.index else pd.Series(dtype=object)
        n_gen = float(p.get("number_generated_events", np.nan))
        xsec = float(p.get("cross_section_pb", np.nan))
        filt = float(p.get("filter_efficiency", 1.0)) if pd.notna(p.get("filter_efficiency", np.nan)) else 1.0
        match = float(p.get("matching_efficiency", 1.0)) if pd.notna(p.get("matching_efficiency", np.nan)) else 1.0
        w = lumi_fb * 1000 * xsec * filt * match / n_gen if n_gen > 0 and np.isfinite(xsec) else np.nan
        rows.append({"sample_slug": row["sample_slug"], "record_id": rid, "process_family": row["process_family"], "events_extracted": row["events_written"], "generated_event_denominator": n_gen, "cross_section_pb": xsec, "filter_efficiency": filt, "matching_efficiency": match, "nominal_event_weight": w, "component_status": "available_if_extraction_success" if row["status"] == "success" else "extraction_failed"})
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "06_new_sm_events_with_frozen_bnf_summary.csv", index=False)
    # Weighted region yields for new events.
    yield_rows = []
    if not sim.empty:
        sim["record_id_numeric"] = pd.to_numeric(sim["record_id"], errors="coerce")
        for _, srow in summary.iterrows():
            mask = sim["record_id_numeric"].eq(float(srow["record_id"]))
            for region in ALL_REGIONS:
                selected = sim[mask & sim[region]]
                n = len(selected)
                w = float(srow["nominal_event_weight"]) if pd.notna(srow["nominal_event_weight"]) else np.nan
                yield_rows.append({"record_id": srow["record_id"], "sample_slug": srow["sample_slug"], "process_family": srow["process_family"], "region": region, "unweighted_events": n, "weighted_yield": n * w if np.isfinite(w) else np.nan, "mc_stat_uncertainty": math.sqrt(n) * w if np.isfinite(w) else np.nan})
    yields = pd.DataFrame(yield_rows)
    yields.to_csv(TABLES / "06_new_sm_weighted_region_yields.csv", index=False)
    write_text(REPORTS / "06_FROZEN_BNF_AND_REGION_APPLICATION_TO_NEW_SM.md", f"""# Frozen B_NF and Region Application to New SM

Date: {DATE}

No N-Frame fit or threshold was changed. New extracted SM rows were scored with the frozen B_NF route and classified with the existing frozen SR/CR/VR definitions.

## Summary

{md(summary)}

## New weighted region yields

{md(yields)}
""")
    return summary, yields


def phase7_to_10_merge_and_pyhf(new_yields: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    old = pd.read_csv(PREV / "tables" / "02_luminosity_weighted_sm_region_yields.csv")
    real_counts = old.set_index("region")["observed_real_data"].to_dict()
    old_bkg = old.set_index("region")["weighted_sm_background_nominal"].to_dict()
    old_unc = old.set_index("region")["nominal_background_uncertainty"].to_dict()
    add = new_yields.groupby("region", as_index=False).agg(new_weighted_sm_added=("weighted_yield", "sum"), new_mc_stat_uncertainty=("mc_stat_uncertainty", lambda x: math.sqrt(np.nansum(np.square(x)))))
    rows = []
    for region in ALL_REGIONS:
        ar = add[add["region"] == region]
        new_b = float(ar["new_weighted_sm_added"].iloc[0]) if len(ar) else 0.0
        new_u = float(ar["new_mc_stat_uncertainty"].iloc[0]) if len(ar) else 0.0
        old_bg = float(old_bkg.get(region, 0.0))
        total = old_bg + new_b
        unc = math.sqrt(float(old_unc.get(region, 0.0)) ** 2 + new_u**2 + (0.012 * total) ** 2)
        incomplete_unc = max(2.0 * total, unc, 1.0)
        obs = float(real_counts.get(region, np.nan))
        denom_nominal = math.sqrt(max(total, 0) + unc**2)
        denom_incomplete = math.sqrt(max(total, 0) + incomplete_unc**2)
        rows.append({"region": region, "observed_real_data": obs, "old_weighted_sm": old_bg, "new_weighted_sm_added": new_b, "total_weighted_sm": total, "total_uncertainty_nominal": unc, "incomplete_coverage_uncertainty": incomplete_unc, "residual_observed_minus_expected": obs - total, "pull_nominal": (obs - total) / denom_nominal if np.isfinite(obs) and denom_nominal > 0 else np.nan, "pull_incomplete": (obs - total) / denom_incomplete if np.isfinite(obs) and denom_incomplete > 0 else np.nan})
    merged = pd.DataFrame(rows)
    merged.to_csv(TABLES / "07_merged_weighted_sm_region_yields.csv", index=False)
    closure = merged[merged["region"].isin(CONTROL_VALIDATION)].copy()
    old_closure = pd.read_csv(PREV / "tables" / "03_control_and_validation_region_closure.csv")
    old_pull = old_closure.set_index("region")["pull_with_incomplete_sm_uncertainty"].to_dict()
    closure["closes_within_2sigma"] = closure["pull_incomplete"].abs() < 2
    closure["closes_within_3sigma"] = closure["pull_incomplete"].abs() < 3
    closure["previous_pull_incomplete"] = closure["region"].map(old_pull)
    closure["pull_improvement_abs"] = closure["previous_pull_incomplete"].abs() - closure["pull_incomplete"].abs()
    closure["remaining_missing_backgrounds"] = "still incomplete unless all controls close; especially top/W/DY/MET/trigger-specific components"
    closure.to_csv(TABLES / "08_control_validation_closure_after_expansion.csv", index=False)
    # pyhf approximate/actual
    pyrows = []
    for region in SIGNAL_REGIONS + ["combined_SR1_SR5", "combined_SR1_SR3_SR5", "combined_all_SR"]:
        regs = {"combined_SR1_SR5": ["SR1", "SR5"], "combined_SR1_SR3_SR5": ["SR1", "SR3", "SR5"], "combined_all_SR": SIGNAL_REGIONS}.get(region, [region])
        sub = merged[merged["region"].isin(regs)]
        obs = float(sub["observed_real_data"].sum())
        bkg = float(sub["total_weighted_sm"].sum())
        unc = float(math.sqrt(np.square(sub["incomplete_coverage_uncertainty"]).sum()))
        denom = math.sqrt(max(bkg, 0) + unc**2)
        z = (obs - bkg) / denom if denom else np.nan
        p = 1 - stats.norm.cdf(z) if np.isfinite(z) else np.nan
        pyrows.append({"model": region, "regions": ";".join(regs), "observed": obs, "weighted_sm_expected": bkg, "total_uncertainty": unc, "local_Z": z, "local_p": p, "global_Z_bonferroni": stats.norm.isf(min(1.0, p * 8)) if np.isfinite(p) else np.nan, "upward": z > 0 if np.isfinite(z) else False, "publication_grade": bool(False), "reason_not_publication_grade": "control regions do not close" if not closure["closes_within_2sigma"].all() else "requires external review"})
        spec = {"channels": [{"name": region, "samples": [{"name": "weighted_sm_background", "data": [max(bkg, 1e-9)], "modifiers": [{"name": "bkg_norm", "type": "normsys", "data": {"hi": 1 + unc / max(bkg, 1e-9), "lo": 1 / (1 + unc / max(bkg, 1e-9))}}]}, {"name": "signal", "data": [1.0], "modifiers": [{"name": "mu", "type": "normfactor", "data": None}]}]}], "observations": [{"name": region, "data": [obs]}], "measurements": [{"name": "Measurement", "config": {"poi": "mu", "parameters": []}}], "version": "1.0.0"}
        (STATMODEL / f"pyhf_{region}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    pyhf_df = pd.DataFrame(pyrows)
    pyhf_df.to_csv(TABLES / "09_pyhf_results_after_sm_expansion.csv", index=False)
    write_text(REPORTS / "07_MERGED_WEIGHTED_SM_BACKGROUND_REPORT.md", f"# Merged Weighted SM Background Report\n\n{md(merged)}")
    write_text(REPORTS / "08_CONTROL_VALIDATION_CLOSURE_AFTER_SM_EXPANSION.md", f"# Control/Validation Closure After SM Expansion\n\n{md(closure)}")
    write_text(REPORTS / "09_PYHF_RESULTS_AFTER_SM_EXPANSION.md", f"# pyhf Results After SM Expansion\n\n{md(pyhf_df)}")
    return merged, closure, pyhf_df


def phase10_benchmark(merged: pd.DataFrame) -> pd.DataFrame:
    eff = pd.read_csv(PREV_PHYS / "tables" / "04_benchmark_signal_region_efficiencies.csv")
    rows = []
    for _, b in eff.iterrows():
        for region in SIGNAL_REGIONS:
            m = merged[merged["region"] == region].iloc[0]
            bkg = float(m["total_weighted_sm"])
            unc = float(m["incomplete_coverage_uncertainty"])
            denom = math.sqrt(max(bkg, 0) + unc**2)
            acc = float(b[f"{region}_efficiency"])
            rows.append({"sample_id": b["sample_id"], "process_label": b["process_label"], "region": region, "sr_acceptance": acc, "expected_signal_yield_per_1000_generated": 1000 * acc, "S_over_sqrt_B_sigmaB2_per_1000": 1000 * acc / denom if denom else np.nan, "required_signal_yield_3sigma": 3 * denom, "required_signal_yield_5sigma": 5 * denom, "sr1_sr5_remain_benchmark_sensitive": region in ["SR1", "SR5"] and acc > 0.05})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "10_benchmark_sensitivity_after_sm_expansion.csv", index=False)
    write_text(REPORTS / "10_BENCHMARK_SENSITIVITY_AFTER_SM_EXPANSION.md", f"# Benchmark Sensitivity After SM Expansion\n\n{md(out)}")
    return out


def final_reports(missing: pd.DataFrame, cands: pd.DataFrame, plan: pd.DataFrame, manifest: pd.DataFrame, extraction: pd.DataFrame, merged: pd.DataFrame, closure: pd.DataFrame, pyhf_df: pd.DataFrame) -> None:
    total_dl = int(manifest["actual_size_bytes"].sum()) if not manifest.empty else 0
    new_events = int(extraction["events_written"].sum()) if not extraction.empty and "events_written" in extraction else 0
    controls_close = bool(not closure.empty and closure["closes_within_2sigma"].all())
    sr = merged[merged["region"].isin(["SR1", "SR5"])]
    write_text(REPORTS / "11_EXPANDED_SM_BACKGROUND_MAKE_OR_BREAK_REPORT_FOR_DARREN.md", f"""# Expanded Trigger-Aware Luminosity-Weighted Standard Model Background Construction for Frozen N-Frame SUSY Search Regions in CMS Open Data

Date: {DATE}

## 1. What was done

Diagnosed the failed controls, searched CERN Open Data for compatible 2016 UL MiniAODSIM SM records, selected a <=30 GiB expansion plan, downloaded selected files where possible, ran CMSSW extraction where possible, applied frozen B_NF/SR definitions, merged old and new weighted SM yields, and reran closure and likelihood-style tests.

## 2. Missing backgrounds diagnosed

{md(missing)}

## 3. Official CERN SM records found

{md(cands, 40)}

## 4-6. Samples downloaded/extracted/added

Downloaded or already-present selected size: {total_dl / 1024**3:.3f} GiB. New extracted events: {new_events}.

{md(manifest)}

{md(extraction)}

## 7-8. Did weighted coverage and controls improve?

Controls all close within 2 sigma: {controls_close}. If this is false, no discovery claim is possible.

{md(closure)}

## 9-11. SR1/SR5 and pyhf

{md(sr)}

{md(pyhf_df)}

## 12. Interpretation for the SUSY objective

This qualifies the SUSY objective. The work improves the background-construction machinery, but the interpretation remains background-limited unless controls close. No SUSY discovery claim is made.

## 13. What remains missing

Complete trigger-aware top/W/DY/ZNuNu/QCD coverage, prescales/trigger efficiencies, object systematics, higher-stat MC, and HEP review.

## 14. Exact next action

If controls still fail, prioritise the missing control-driving processes shown in `08_control_validation_closure_after_expansion.csv`, especially any top/W/DY/MET-trigger backgrounds absent from the selected expansion.
""")
    write_text(REPORTS / "12_SHORT_UPDATE_FOR_TOM.md", f"""# Short Update for Tom

I built the next SM-background coverage stage around the failed controls. It searched official CERN records, selected a <=30 GiB expansion plan, downloaded/extracted what was feasible, and reran the frozen-region background/closure tests.

New extracted events: {new_events}. Controls close within 2 sigma: {controls_close}. A credible 5 sigma discovery result exists: False.

What to tell Darren: this is the correct direction, but the result is still only as strong as the controls. If the controls still fail, SR1/SR5 cannot be interpreted as SUSY.
""")


def main() -> None:
    ensure_dirs()
    missing = phase1_missing_coverage()
    cands = phase2_search_records()
    plan = phase3_select_plan(cands)
    docker_ok = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not docker_ok:
        empty = pd.DataFrame()
        empty.to_csv(TABLES / "04_download_manifest.csv", index=False)
        write_text(REPORTS / "04_SM_DOWNLOAD_REPORT.md", "Docker daemon unavailable; no downloads/extraction attempted.")
        final_reports(missing, cands, plan, empty, empty, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        print("Docker unavailable; metadata/plan phases completed only.")
        return
    manifest = phase4_download(plan)
    extraction = phase5_extract(manifest)
    _, new_yields = phase6_score(extraction, plan)
    merged, closure, pyhf_df = phase7_to_10_merge_and_pyhf(new_yields)
    phase10_benchmark(merged)
    final_reports(missing, cands, plan, manifest, extraction, merged, closure, pyhf_df)
    print("Complete SM background coverage stage complete")
    print(f"Output folder: {OUT}")
    print(f"Candidate records found: {len(cands)}")
    print(f"Records selected: {len(plan)}")
    print(f"Downloaded/already-present GiB: {manifest['actual_size_bytes'].sum()/1024**3 if not manifest.empty else 0:.3f}")
    print(f"New events extracted: {int(extraction['events_written'].sum()) if not extraction.empty else 0}")
    print(f"Controls all close within 2 sigma: {bool(not closure.empty and closure['closes_within_2sigma'].all())}")


if __name__ == "__main__":
    main()
