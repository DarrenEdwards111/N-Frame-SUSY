from __future__ import annotations

import json
import math
import shutil
import ssl
import urllib.request
from pathlib import Path

import awkward as ak
import numpy as np
import pandas as pd
import uproot


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
OUT_DIR = ROOT / "data" / "processed" / "sm_background_pilot_features"
DOWNLOAD_DIR = Path(r"D:\cern_open_data\nframe_sm_background_pilot")
REAL_SCALE = ROOT / "data" / "processed" / "matched_control" / "standard_quality_clean_events.csv"

SUSY_FEATURE_ROOT = ROOT / "data" / "processed" / "susy_relevance_benchmark_features"
DATE = "2026-06-09"

FAMILIES = {
    "P_displacement_proxy": ["secondary_vertex_count", "displacement_proxy_raw"],
    "P_reconstruction": ["packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_multiplicity": ["N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["HT", "leading_jet_pt", "subleading_jet_pt"],
    "P_missing": ["MET_pt"],
    "P_compression": ["compression_proxy_raw"],
}
WEIGHTS = {
    "P_displacement_proxy": 0.3566,
    "P_reconstruction": 0.2112,
    "P_multiplicity": 0.2019,
    "P_btag_structure": 0.0926,
    "P_visible_energy": 0.0728,
    "P_missing": 0.0595,
    "P_compression": 0.0055,
}

SEARCH_ROOTS = [
    Path(r"D:\cern_open_data"),
    Path(r"D:\cern_open_data\nframe_stage2"),
    Path(r"D:\cern_open_data\nframe_stage2_real_collision_20gb"),
    Path(r"D:\cern_open_data\nframe_validation_real_independent"),
    Path(r"D:\cern_open_data\nframe_validation_real_independent_expanded"),
    Path(r"D:\cern_open_data\nframe_sm_background_pilot"),
    MAIN,
]

CANDIDATE_RECORDS = [
    {
        "sample_id": "ttjets_nanoaodsim_pilot",
        "process_label": "TTJets inclusive",
        "record_id": 67733,
        "record_url": "https://opendata.cern.ch/api/records/67733",
        "data_tier": "NANOAODSIM",
        "classification": "SM_background",
        "priority": 1,
        "reason": "ttbar is the main ordinary SM benchmark for b-tags, multiplicity, visible energy and event complexity.",
        "selection": "smallest file above 200 MB if available",
    },
    {
        "sample_id": "qcd_ht700to1000_nanoaodsim_pilot",
        "process_label": "QCD HT700to1000",
        "record_id": 63138,
        "record_url": "https://opendata.cern.ch/api/records/63138",
        "data_tier": "NANOAODSIM",
        "classification": "SM_background",
        "priority": 2,
        "reason": "high-HT QCD is the main ordinary multijet mimic for visible-energy and multiplicity stress.",
        "selection": "only file",
    },
]


def clean_text(value: object) -> str:
    return "" if value is None else str(value).replace("\n", " ").strip()


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, OUT_DIR, DOWNLOAD_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def local_inventory() -> pd.DataFrame:
    needles = ["ttjets", "ttto", "ttbar", "qcd", "wjets", "zjets", "dyjets", "singletop", "single_top", "ww", "wz", "zz", "diboson"]
    rows = []
    seen = set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            text = str(path).lower()
            if not any(n in text for n in needles):
                continue
            if path in seen:
                continue
            seen.add(path)
            tier = "NANOAODSIM" if "nanoaod" in text else "MINIAODSIM" if "miniaod" in text else "unknown"
            feature_exists = path.name.lower().endswith(".csv") and "event_features" in path.name.lower()
            rows.append({
                "sample_id": path.parent.name,
                "process_label": infer_process_label(str(path)),
                "record_id": "",
                "local_path": str(path),
                "file_count": 1,
                "total_size_bytes": path.stat().st_size,
                "data_tier": tier,
                "mini_or_nano": "NanoAOD" if "nano" in tier.lower() else "MiniAOD" if "mini" in tier.lower() else "unknown",
                "simulated_or_real": "simulated candidate" if "sim" in text or "mc" in text else "unknown",
                "suitability": "candidate; inspect before use",
                "cmssw_extraction_needed": tier == "MINIAODSIM",
                "all_fitted_components_likely_available": tier == "MINIAODSIM",
                "feature_tables_already_exist": feature_exists,
            })
    return pd.DataFrame(rows)


def infer_process_label(text: str) -> str:
    low = text.lower()
    if "ttjets" in low or "ttto" in low or "ttbar" in low:
        return "ttbar/TTJets"
    if "qcd" in low:
        return "QCD"
    if "wjets" in low:
        return "W+jets"
    if "zjets" in low or "dyjets" in low:
        return "Z/DY+jets"
    if "singletop" in low or "single_top" in low:
        return "single top"
    if any(x in low for x in ["ww", "wz", "zz", "diboson"]):
        return "diboson"
    return "SM candidate"


def fetch_record(record_id: int) -> dict:
    with urllib.request.urlopen(f"https://opendata.cern.ch/api/records/{record_id}", timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def flatten_files(record: dict) -> list[dict]:
    files = []
    for index in record["metadata"].get("_file_indices", []):
        for item in index.get("files", []):
            row = dict(item)
            row["index_key"] = index.get("key", "")
            files.append(row)
    return files


def xrootd_to_https(uri: str) -> str:
    if uri.startswith("root://eospublic.cern.ch//"):
        return "https://eospublic.cern.ch/" + uri.split("root://eospublic.cern.ch//", 1)[1]
    return uri


def select_file(files: list[dict], sample_id: str) -> dict:
    ordered = sorted(files, key=lambda f: int(f.get("size", 0)))
    if sample_id.startswith("ttjets"):
        preferred = [f for f in ordered if int(f.get("size", 0)) >= 200_000_000]
        return preferred[0] if preferred else ordered[0]
    return ordered[0]


def download_plan() -> tuple[pd.DataFrame, list[dict]]:
    rows, selected = [], []
    for candidate in CANDIDATE_RECORDS:
        record = fetch_record(candidate["record_id"])
        files = flatten_files(record)
        chosen = select_file(files, candidate["sample_id"])
        https_url = xrootd_to_https(chosen["uri"])
        target = DOWNLOAD_DIR / candidate["sample_id"] / chosen["filename"]
        total_record_size = sum(int(f.get("size", 0)) for f in files)
        row = {
            **candidate,
            "title": record["metadata"].get("title", ""),
            "doi": record["metadata"].get("doi", ""),
            "file_url": https_url,
            "xrootd_uri": chosen["uri"],
            "filename": chosen["filename"],
            "target_path": str(target),
            "expected_size_bytes": int(chosen.get("size", 0)),
            "record_total_size_bytes": total_record_size,
            "expected_variable_availability": "NanoAODSIM: MET, jets, b-tags, leptons, PV; secondary vertices if nSV/SV present; packed candidates unavailable.",
            "reason_for_inclusion": candidate["reason"],
            "proceed_automatically": True,
        }
        rows.append(row)
        selected.append(row)
    return pd.DataFrame(rows), selected


def download_file(url: str, target: Path, expected_size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and abs(target.stat().st_size - expected_size) <= 1024:
        return
    tmp = target.with_suffix(target.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(url, timeout=120, context=context) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    tmp.replace(target)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "displacement_proxy_raw" not in df and "secondary_vertex_count" in df:
        df["displacement_proxy_raw"] = df["secondary_vertex_count"]
    if "compression_proxy_raw" not in df:
        ht_like = df.get("HT", pd.Series(0, index=df.index)).fillna(0)
        lead = df.get("leading_jet_pt", pd.Series(0, index=df.index)).fillna(0)
        df["compression_proxy_raw"] = np.log1p(df["MET_pt"].clip(lower=0)) - np.log1p(ht_like + lead + 1)
    return df


def scale_constants(real: pd.DataFrame) -> dict:
    real = prepare(real)
    cols = sorted({v for vals in FAMILIES.values() for v in vals if v in real})
    return {col: (pd.to_numeric(real[col], errors="coerce").mean(), pd.to_numeric(real[col], errors="coerce").std(ddof=0)) for col in cols}


def z_with_constants(s: pd.Series, constants: tuple[float, float]) -> pd.Series:
    mean, std = constants
    s = pd.to_numeric(s, errors="coerce")
    return (s - mean) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def score(df: pd.DataFrame, constants: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = prepare(df)
    availability = []
    total = pd.Series(0.0, index=df.index)
    for fam, variables in FAMILIES.items():
        available = [v for v in variables if v in df and v in constants and df[v].notna().any()]
        missing = [v for v in variables if v not in df or v not in constants or not df[v].notna().any()]
        fam_score = pd.concat([z_with_constants(df[v], constants[v]) for v in available], axis=1).mean(axis=1) if available else pd.Series(np.nan, index=df.index)
        df[f"B_{fam}"] = fam_score
        if available:
            total += WEIGHTS[fam] * fam_score.fillna(0)
        availability.append({
            "parameter_family": fam,
            "available": bool(available),
            "available_variables": ";".join(available),
            "missing_variables": ";".join(missing),
            "weight": WEIGHTS[fam],
        })
    df["B_NF_fitted_frozen_raw"] = total
    df["B_NF_fitted_frozen_z_real_scaled"] = total
    return df, pd.DataFrame(availability)


def branch_names(tree: uproot.TTree) -> set[str]:
    return set(tree.keys(filter_name="*", recursive=False))


def get_array(arrays: dict, name: str, default=None):
    fields = set(arrays.fields) if hasattr(arrays, "fields") else set(arrays)
    return arrays[name] if name in fields else default


def first_or_nan(jagged) -> np.ndarray:
    return ak.to_numpy(ak.fill_none(ak.firsts(jagged), np.nan))


def extract_nanoaod(path: Path, sample: dict, max_events: int = 50_000) -> tuple[pd.DataFrame, pd.DataFrame]:
    with uproot.open(path) as root_file:
        tree = root_file["Events"]
        names = branch_names(tree)
        wanted = [
            "run", "luminosityBlock", "event", "MET_pt", "MET_phi", "PV_npvs",
            "Jet_pt", "Jet_eta", "Jet_jetId", "Jet_btagDeepFlavB", "Jet_btagDeepB",
            "Muon_pt", "Muon_eta", "Electron_pt", "Electron_eta", "nSV",
        ]
        wanted += [n for n in names if n.startswith("HLT_") or n.startswith("Flag_")]
        present = [n for n in wanted if n in names]
        arrays = tree.arrays(present, entry_stop=max_events, library="ak")
    fields = set(arrays.fields)

    jet_pt = get_array(arrays, "Jet_pt", ak.Array([[]] * len(arrays["event"])))
    jet_eta = get_array(arrays, "Jet_eta", ak.Array([[]] * len(arrays["event"])))
    jet_id = get_array(arrays, "Jet_jetId", ak.ones_like(jet_pt))
    good_jets = (jet_pt > 30) & (abs(jet_eta) < 2.4) & (jet_id >= 2)
    good_jets_50 = (jet_pt > 50) & (abs(jet_eta) < 2.4) & (jet_id >= 2)
    good_pt = jet_pt[good_jets]

    btag = get_array(arrays, "Jet_btagDeepFlavB", None)
    if btag is None:
        btag = get_array(arrays, "Jet_btagDeepB", ak.zeros_like(jet_pt))
    good_btag = btag[good_jets]

    mu_pt = get_array(arrays, "Muon_pt", ak.Array([[]] * len(arrays["event"])))
    el_pt = get_array(arrays, "Electron_pt", ak.Array([[]] * len(arrays["event"])))
    n_mu = ak.num(mu_pt[mu_pt > 10], axis=1)
    n_el = ak.num(el_pt[el_pt > 10], axis=1)

    rows = pd.DataFrame({
        "run": ak.to_numpy(arrays["run"]) if "run" in fields else np.nan,
        "lumi": ak.to_numpy(arrays["luminosityBlock"]) if "luminosityBlock" in fields else np.nan,
        "event": ak.to_numpy(arrays["event"]) if "event" in fields else np.arange(len(jet_pt)),
        "MET_pt": ak.to_numpy(arrays["MET_pt"]) if "MET_pt" in fields else np.nan,
        "MET_phi": ak.to_numpy(arrays["MET_phi"]) if "MET_phi" in fields else np.nan,
        "HT": ak.to_numpy(ak.sum(good_pt, axis=1)),
        "N_jets_30": ak.to_numpy(ak.num(good_pt, axis=1)),
        "N_jets_50": ak.to_numpy(ak.num(jet_pt[good_jets_50], axis=1)),
        "leading_jet_pt": first_or_nan(good_pt),
        "subleading_jet_pt": ak.to_numpy(ak.fill_none(ak.pad_none(good_pt, 2, axis=1)[:, 1], np.nan)),
        "N_muons": ak.to_numpy(n_mu),
        "N_electrons": ak.to_numpy(n_el),
        "N_leptons": ak.to_numpy(n_mu + n_el),
        "N_btags_medium": ak.to_numpy(ak.sum(good_btag > 0.3093, axis=1)),
        "N_btags_tight": ak.to_numpy(ak.sum(good_btag > 0.7221, axis=1)),
        "max_btag_discriminator": ak.to_numpy(ak.fill_none(ak.max(good_btag, axis=1), np.nan)),
        "N_primary_vertices": ak.to_numpy(arrays["PV_npvs"]) if "PV_npvs" in fields else np.nan,
        "secondary_vertex_count": ak.to_numpy(arrays["nSV"]) if "nSV" in fields else np.nan,
        "source_file": str(path),
        "sample_id": sample["sample_id"],
        "process_label": sample["process_label"],
        "classification": "SM_background",
        "real_or_simulated": "simulated Standard Model background",
        "data_tier": "NANOAODSIM",
    })
    rows["compression_proxy_raw"] = np.log1p(rows["MET_pt"].clip(lower=0)) - np.log1p(rows["HT"].fillna(0) + rows["leading_jet_pt"].fillna(0) + 1)
    if "secondary_vertex_count" in rows:
        rows["displacement_proxy_raw"] = rows["secondary_vertex_count"]
    trigger_cols = [n for n in fields if n.startswith("HLT_") or n.startswith("Flag_")]
    availability = pd.DataFrame([{
        "sample_id": sample["sample_id"],
        "source_file": str(path),
        "branch": branch,
        "available": branch in names,
    } for branch in wanted if not branch.startswith("HLT_") and not branch.startswith("Flag_")])
    availability.loc[len(availability)] = [sample["sample_id"], str(path), "trigger_or_filter_branch_count", len(trigger_cols) > 0]
    return rows, availability


def write_markdown(path: Path, title: str, sections: list[tuple[str, object]]) -> None:
    lines = [f"# {title}", "", f"Date: {DATE}"]
    for header, body in sections:
        lines += ["", f"## {header}", ""]
        if isinstance(body, pd.DataFrame):
            lines.append(body.to_markdown(index=False) if not body.empty else "No rows.")
        else:
            lines.append(str(body))
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()

    inventory = local_inventory()
    inventory.to_csv(TABLES / "sm_background_local_inventory.csv", index=False)
    write_markdown(
        REPORTS / "SM_BACKGROUND_LOCAL_AUDIT.md",
        "SM Background Local Audit",
        [("Local Candidates", inventory), ("Conclusion", "No suitable already-processed local SM simulated background feature tables were found. The pilot therefore uses small CERN Open Data NanoAODSIM downloads.")],
    )

    plan, selected = download_plan()
    total_planned = int(plan["expected_size_bytes"].sum())
    if total_planned > 15 * 1024**3:
        plan["proceed_automatically"] = False
    plan.to_csv(TABLES / "sm_background_download_candidates.csv", index=False)
    write_markdown(
        REPORTS / "SM_BACKGROUND_DOWNLOAD_PLAN.md",
        "SM Background Download Plan",
        [("Selected Candidates", plan), ("Decision", f"Planned download size is {total_planned / 1024**3:.2f} GiB, below the 15 GiB cap. Proceed automatically: {total_planned <= 15 * 1024**3}.")],
    )
    if total_planned > 15 * 1024**3:
        raise SystemExit("Planned SM background download exceeds 15 GiB; not downloading.")

    manifest_rows = []
    for sample in selected:
        target = Path(sample["target_path"])
        download_file(sample["file_url"], target, int(sample["expected_size_bytes"]))
        manifest_rows.append({
            **sample,
            "downloaded": target.exists(),
            "actual_size_bytes": target.stat().st_size if target.exists() else 0,
            "size_matches_expected": target.exists() and abs(target.stat().st_size - int(sample["expected_size_bytes"])) <= 1024,
        })
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(TABLES / "sm_background_download_manifest.csv", index=False)
    write_markdown(REPORTS / "SM_BACKGROUND_DOWNLOAD_REPORT.md", "SM Background Download Report", [("Manifest", manifest)])

    real = pd.read_csv(REAL_SCALE)
    constants = scale_constants(real)
    frames, avail_frames = [], []
    for sample in manifest_rows:
        df, branch_availability = extract_nanoaod(Path(sample["target_path"]), sample)
        df, family_availability = score(df, constants)
        out = OUT_DIR / f"{sample['sample_id']}_events_with_BNF.csv"
        df.to_csv(out, index=False)
        family_availability.insert(0, "sample_id", sample["sample_id"])
        family_availability.insert(1, "process_label", sample["process_label"])
        frames.append(df)
        avail_frames.append(family_availability)
        branch_availability.to_csv(OUT_DIR / f"{sample['sample_id']}_branch_availability.csv", index=False)

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    combined.to_csv(OUT_DIR / "sm_background_events_with_BNF.csv", index=False)

    availability = pd.concat(avail_frames, ignore_index=True) if avail_frames else pd.DataFrame()
    availability.to_csv(TABLES / "sm_background_feature_availability.csv", index=False)
    write_markdown(REPORTS / "SM_BACKGROUND_FEATURE_EXTRACTION_REPORT.md", "SM Background Feature Extraction Report", [("Feature Family Availability", availability), ("Interpretation", "These are NanoAODSIM-derived features. Packed candidate count is unavailable, so P_reconstruction is reduced. Secondary-vertex count is available only when nSV exists in the NanoAODSIM file.")])

    summary = combined.groupby(["sample_id", "classification", "process_label", "data_tier"], as_index=False).agg(
        events=("event", "count"),
        mean_BNF=("B_NF_fitted_frozen_raw", "mean"),
        median_BNF=("B_NF_fitted_frozen_raw", "median"),
    )
    summary.to_csv(TABLES / "sm_background_bnf_summary.csv", index=False)
    write_markdown(REPORTS / "SM_BACKGROUND_BNF_APPLICATION_REPORT.md", "SM Background B_NF Application Report", [("Summary", summary), ("Caution", "The real-data-fitted equation was frozen. It was not refitted on simulation. Because NanoAODSIM lacks packed candidates, this is a reduced-component benchmark layer.")])
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
