from __future__ import annotations

import json
import shutil
import ssl
import urllib.request
from pathlib import Path

import awkward as ak
import numpy as np
import pandas as pd
import uproot


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
OUT = ROOT / "data" / "processed" / "expanded_benchmark_features"
DOWNLOAD = Path(r"D:\cern_open_data\nframe_benchmark_expansion")
DATE = "2026-06-09"
MAX_EVENTS = 50_000
MAX_BYTES = 20 * 1024**3

SAMPLES = [
    {"sample_id": "wjets_lnu_nanoaodsim_pilot", "process_label": "WJetsToLNu", "classification": "SM_background", "record_id": 69747, "priority": 1, "topology_class": "W+jets/leptonic missing-energy background"},
    {"sample_id": "qcd_ht500to700_nanoaodsim_pilot", "process_label": "QCD HT500to700", "classification": "SM_background", "record_id": 63127, "priority": 2, "topology_class": "QCD multijet lower high-HT bin"},
    {"sample_id": "qcd_ht1000to1500_nanoaodsim_pilot", "process_label": "QCD HT1000to1500", "classification": "SM_background", "record_id": 63079, "priority": 3, "topology_class": "QCD multijet very high-HT bin"},
    {"sample_id": "sms_t2tt_compressed_nanoaodsim_pilot", "process_label": "SMS-T2tt compressed stop mStop300 mLSP290", "classification": "signal", "record_id": 63451, "priority": 4, "topology_class": "compressed stop; missing-energy plus b/top-like structure"},
]


def fetch_record(record_id: int) -> dict:
    with urllib.request.urlopen(f"https://opendata.cern.ch/api/records/{record_id}", timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def files(record: dict) -> list[dict]:
    out = []
    for idx in record["metadata"].get("_file_indices", []):
        out += idx.get("files", [])
    return out


def https(uri: str) -> str:
    return "https://eospublic.cern.ch/" + uri.split("root://eospublic.cern.ch//", 1)[1] if uri.startswith("root://eospublic.cern.ch//") else uri


def choose(fs: list[dict], sample_id: str) -> dict:
    ordered = sorted(fs, key=lambda f: int(f["size"]))
    if "wjets" in sample_id:
        preferred = [f for f in ordered if int(f["size"]) >= 100_000_000]
        return preferred[0] if preferred else ordered[0]
    if "qcd_ht500" in sample_id:
        preferred = [f for f in ordered if int(f["size"]) >= 100_000_000]
        return preferred[0] if preferred else ordered[0]
    if "qcd_ht1000" in sample_id:
        return ordered[0]
    if "sms_t2tt" in sample_id:
        preferred = [f for f in ordered if int(f["size"]) >= 100_000_000]
        return preferred[0] if preferred else ordered[0]
    return ordered[0]


def download(url: str, target: Path, size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and abs(target.stat().st_size - size) <= 1024:
        return
    tmp = target.with_suffix(target.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(url, timeout=120, context=ctx) as r, tmp.open("wb") as out:
        shutil.copyfileobj(r, out, 1024 * 1024)
    tmp.replace(target)


def arrget(arrays, name, default):
    return arrays[name] if name in set(arrays.fields) else default


def first_or_nan(jagged):
    return ak.to_numpy(ak.fill_none(ak.firsts(jagged), np.nan))


def extract(path: Path, sample: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    with uproot.open(path) as f:
        tree = f["Events"]
        names = set(tree.keys(filter_name="*", recursive=False))
        wanted = ["run", "luminosityBlock", "event", "MET_pt", "MET_phi", "PV_npvs", "Jet_pt", "Jet_eta", "Jet_jetId", "Jet_btagDeepFlavB", "Jet_btagDeepB", "Muon_pt", "Electron_pt", "nSV"]
        present = [w for w in wanted if w in names]
        arrays = tree.arrays(present, entry_stop=MAX_EVENTS, library="ak")
    n = len(arrays["event"]) if "event" in set(arrays.fields) else len(arrays[present[0]])
    empty = ak.Array([[]] * n)
    jet_pt = arrget(arrays, "Jet_pt", empty)
    jet_eta = arrget(arrays, "Jet_eta", empty)
    jet_id = arrget(arrays, "Jet_jetId", ak.ones_like(jet_pt))
    good = (jet_pt > 30) & (abs(jet_eta) < 2.4) & (jet_id >= 2)
    good50 = (jet_pt > 50) & (abs(jet_eta) < 2.4) & (jet_id >= 2)
    good_pt = jet_pt[good]
    btag = arrget(arrays, "Jet_btagDeepFlavB", arrget(arrays, "Jet_btagDeepB", ak.zeros_like(jet_pt)))
    good_btag = btag[good]
    mu = arrget(arrays, "Muon_pt", empty)
    ele = arrget(arrays, "Electron_pt", empty)
    n_mu = ak.num(mu[mu > 10], axis=1)
    n_ele = ak.num(ele[ele > 10], axis=1)
    df = pd.DataFrame({
        "run": ak.to_numpy(arrays["run"]) if "run" in set(arrays.fields) else np.nan,
        "lumi": ak.to_numpy(arrays["luminosityBlock"]) if "luminosityBlock" in set(arrays.fields) else np.nan,
        "event": ak.to_numpy(arrays["event"]) if "event" in set(arrays.fields) else np.arange(n),
        "MET_pt": ak.to_numpy(arrays["MET_pt"]) if "MET_pt" in set(arrays.fields) else np.nan,
        "MET_phi": ak.to_numpy(arrays["MET_phi"]) if "MET_phi" in set(arrays.fields) else np.nan,
        "HT": ak.to_numpy(ak.sum(good_pt, axis=1)),
        "N_jets_30": ak.to_numpy(ak.num(good_pt, axis=1)),
        "N_jets_50": ak.to_numpy(ak.num(jet_pt[good50], axis=1)),
        "leading_jet_pt": first_or_nan(good_pt),
        "subleading_jet_pt": ak.to_numpy(ak.fill_none(ak.pad_none(good_pt, 2, axis=1)[:, 1], np.nan)),
        "N_muons": ak.to_numpy(n_mu),
        "N_electrons": ak.to_numpy(n_ele),
        "N_leptons": ak.to_numpy(n_mu + n_ele),
        "N_btags_medium": ak.to_numpy(ak.sum(good_btag > 0.3093, axis=1)),
        "N_btags_tight": ak.to_numpy(ak.sum(good_btag > 0.7221, axis=1)),
        "max_btag_discriminator": ak.to_numpy(ak.fill_none(ak.max(good_btag, axis=1), np.nan)),
        "N_primary_vertices": ak.to_numpy(arrays["PV_npvs"]) if "PV_npvs" in set(arrays.fields) else np.nan,
        "secondary_vertex_count": ak.to_numpy(arrays["nSV"]) if "nSV" in set(arrays.fields) else np.nan,
        "packed_candidate_count": np.nan,
        "source_file": str(path),
        **{k: sample[k] for k in ["sample_id", "process_label", "classification", "topology_class"]},
        "data_tier": "NANOAODSIM",
    })
    df["compression_proxy_raw"] = np.log1p(df["MET_pt"].clip(lower=0)) - np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1)
    df["displacement_proxy_raw"] = df["secondary_vertex_count"]
    avail = pd.DataFrame([{"sample_id": sample["sample_id"], "branch": b, "available": b in names} for b in wanted])
    return df, avail


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOWNLOAD.mkdir(parents=True, exist_ok=True)
    plan_rows, selected = [], []
    for sample in SAMPLES:
        rec = fetch_record(sample["record_id"])
        fs = files(rec)
        chosen = choose(fs, sample["sample_id"])
        target = DOWNLOAD / sample["sample_id"] / chosen["filename"]
        row = {**sample, "title": rec["metadata"]["title"], "doi": rec["metadata"].get("doi", ""), "data_tier": "NANOAODSIM", "file_url": https(chosen["uri"]), "target_path": str(target), "expected_size_bytes": int(chosen["size"]), "expected_variables": "NanoAODSIM object counts, MET, HT, jets, b-tags, PV, nSV; packed candidates unavailable", "full_or_reduced_expected": "reduced-component", "reason_for_inclusion": sample["topology_class"], "proceed_automatically": True}
        plan_rows.append(row)
        selected.append(row)
    plan = pd.DataFrame(plan_rows)
    plan.to_csv(TABLES / "additional_sm_background_candidates.csv", index=False)
    plan[plan["classification"].eq("signal")].to_csv(TABLES / "additional_susy_benchmark_candidates.csv", index=False)
    total = int(plan["expected_size_bytes"].sum())
    if total > MAX_BYTES:
        raise SystemExit(f"Planned download exceeds 20 GB: {total}")
    manifest_rows, frames, avails = [], [], []
    for sample in selected:
        target = Path(sample["target_path"])
        download(sample["file_url"], target, int(sample["expected_size_bytes"]))
        manifest_rows.append({**sample, "downloaded": target.exists(), "actual_size_bytes": target.stat().st_size if target.exists() else 0, "size_matches_expected": target.exists() and abs(target.stat().st_size - int(sample["expected_size_bytes"])) <= 1024})
        df, avail = extract(target, sample)
        frames.append(df)
        avails.append(avail)
        df.to_csv(OUT / f"{sample['sample_id']}_event_features.csv", index=False)
    manifest = pd.DataFrame(manifest_rows)
    features = pd.concat(frames, ignore_index=True, sort=False)
    availability = pd.concat(avails, ignore_index=True)
    manifest.to_csv(TABLES / "expanded_benchmark_download_manifest.csv", index=False)
    features.to_csv(OUT / "expanded_benchmark_event_features.csv", index=False)
    availability.to_csv(TABLES / "expanded_benchmark_feature_availability.csv", index=False)
    (REPORTS / "ADDITIONAL_SM_BACKGROUND_DOWNLOAD_PLAN.md").write_text("# Additional SM Background Download Plan\n\n" + plan[plan["classification"].eq("SM_background")].to_markdown(index=False), encoding="utf-8")
    (REPORTS / "ADDITIONAL_SUSY_BENCHMARK_DOWNLOAD_PLAN.md").write_text("# Additional SUSY Benchmark Download Plan\n\n" + plan[plan["classification"].eq("signal")].to_markdown(index=False), encoding="utf-8")
    (REPORTS / "EXPANDED_BENCHMARK_DOWNLOAD_REPORT.md").write_text("# Expanded Benchmark Download Report\n\n" + manifest.to_markdown(index=False), encoding="utf-8")
    (REPORTS / "EXPANDED_BENCHMARK_FEATURE_EXTRACTION_REPORT.md").write_text("# Expanded Benchmark Feature Extraction Report\n\n" + availability.groupby(["sample_id", "available"]).size().reset_index(name="branches").to_markdown(index=False), encoding="utf-8")
    print(manifest[["sample_id", "actual_size_bytes", "size_matches_expected"]].to_string(index=False))
    print(features.groupby(["sample_id", "classification"]).size().reset_index(name="events").to_string(index=False))


if __name__ == "__main__":
    main()
