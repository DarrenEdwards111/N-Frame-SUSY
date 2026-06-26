from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".atlas_pydeps"))

import awkward as ak
import numpy as np
import pandas as pd
import requests
import uproot
import urllib3


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_validation_real_independent_nanoaod")
OUT_DIR = ROOT / "data" / "processed" / "independent_validation_nanoaod"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

FILES = [
    {
        "record_id": 30558,
        "primary_dataset": "JetHT",
        "filename": "1CD54B78-99CC-7C4F-A89C-7A9103D28135.root",
        "size_bytes": 407947139,
        "url": "https://eospublic.cern.ch/eos/opendata/cms/Run2016H/JetHT/NANOAOD/UL2016_MiniAODv2_NanoAODv9-v1/70000/1CD54B78-99CC-7C4F-A89C-7A9103D28135.root",
    },
    {
        "record_id": 30559,
        "primary_dataset": "MET",
        "filename": "C42412D7-7FA8-FA44-B636-9DDB703D1559.root",
        "size_bytes": 94354394,
        "url": "https://eospublic.cern.ch/eos/opendata/cms/Run2016H/MET/NANOAOD/UL2016_MiniAODv2_NanoAODv9-v1/70000/C42412D7-7FA8-FA44-B636-9DDB703D1559.root",
    },
    {
        "record_id": 30563,
        "primary_dataset": "SingleMuon",
        "filename": "61FC1E38-F75C-6B44-AD19-A9894155874E.root",
        "size_bytes": 14695266,
        "url": "https://eospublic.cern.ch/eos/opendata/cms/Run2016H/SingleMuon/NANOAOD/UL2016_MiniAODv2_NanoAODv9-v1/120000/61FC1E38-F75C-6B44-AD19-A9894155874E.root",
    },
]


def download(item) -> Path:
    target = DOWNLOAD_ROOT / item["primary_dataset"].lower() / str(item["record_id"]) / item["filename"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == item["size_bytes"]:
        return target
    urllib3.disable_warnings()
    with requests.get(item["url"], stream=True, timeout=60, verify=False) as r:
        r.raise_for_status()
        tmp = target.with_suffix(".root.part")
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(1024 * 1024 * 8):
                if chunk:
                    fh.write(chunk)
        tmp.replace(target)
    return target


def first_available(branches, names):
    for name in names:
        if name in branches:
            return name
    return None


def count_pt(arr, threshold):
    return ak.to_numpy(ak.sum(arr > threshold, axis=1))


def extract_one(path: Path, item) -> tuple[pd.DataFrame, dict]:
    with uproot.open(path) as f:
        tree = f["Events"]
        branches = set(tree.keys())
        btag = first_available(branches, ["Jet_btagDeepB", "Jet_btagDeepFlavB"])
        needed = [
            "run", "luminosityBlock", "event", "MET_pt", "MET_phi", "Jet_pt",
            "Muon_pt", "Electron_pt", "PV_npvs",
        ]
        if btag:
            needed.append(btag)
        for name in ["HLT_PFMET170_HBHECleaned", "HLT_PFHT900", "HLT_IsoMu24", "HLT_Ele27_WPTight_Gsf"]:
            if name in branches:
                needed.append(name)
        for name in [
            "Flag_HBHENoiseFilter", "Flag_HBHENoiseIsoFilter", "Flag_goodVertices",
            "Flag_EcalDeadCellTriggerPrimitiveFilter", "Flag_BadPFMuonFilter",
            "Flag_globalSuperTightHalo2016Filter",
        ]:
            if name in branches:
                needed.append(name)
        arr = tree.arrays(list(dict.fromkeys(needed)), library="ak")
    jets = arr["Jet_pt"]
    jet_sort = ak.sort(jets, axis=1, ascending=False)
    leading = ak.to_numpy(ak.fill_none(ak.firsts(jet_sort), 0))
    subleading = ak.to_numpy(ak.fill_none(ak.firsts(jet_sort[:, 1:]), 0))
    ht = ak.to_numpy(ak.sum(jets[jets > 30], axis=1))
    bvals = arr[btag] if btag else None
    medium_wp = 0.6321 if btag == "Jet_btagDeepB" else 0.3093
    tight_wp = 0.8953 if btag == "Jet_btagDeepB" else 0.7221
    df = pd.DataFrame({
        "sample_id": f"validation_{item['primary_dataset'].lower()}_run2016h_nanoaod_collision",
        "primary_dataset": item["primary_dataset"],
        "record_id": item["record_id"],
        "source_file": item["filename"],
        "source_file_stem": Path(item["filename"]).stem,
        "source_file_index": 0,
        "local_input_path_or_container_path": str(path),
        "event_index_within_file": np.arange(len(arr["event"])),
        "event_index_global_within_sample": np.arange(len(arr["event"])),
        "run": ak.to_numpy(arr["run"]),
        "lumi": ak.to_numpy(arr["luminosityBlock"]),
        "event": ak.to_numpy(arr["event"]),
        "MET_pt": ak.to_numpy(arr["MET_pt"]),
        "MET_phi": ak.to_numpy(arr["MET_phi"]),
        "N_jets_all": ak.to_numpy(ak.num(jets)),
        "N_jets_30": count_pt(jets, 30),
        "N_jets_50": count_pt(jets, 50),
        "HT": ht,
        "jet_pt_sum": ak.to_numpy(ak.sum(jets, axis=1)),
        "leading_jet_pt": leading,
        "subleading_jet_pt": subleading,
        "N_muons": ak.to_numpy(ak.sum(arr["Muon_pt"] > 10, axis=1)),
        "N_electrons": ak.to_numpy(ak.sum(arr["Electron_pt"] > 10, axis=1)),
        "N_primary_vertices": ak.to_numpy(arr["PV_npvs"]),
        "is_real_collision": True,
        "is_simulated": False,
        "include_in_real_only_analysis": True,
        "validation_route": "independent_run2016h_nanoaod",
    })
    df["N_leptons"] = df["N_muons"] + df["N_electrons"]
    if bvals is not None:
        df["N_btags_medium"] = ak.to_numpy(ak.sum(bvals > medium_wp, axis=1))
        df["N_btags_tight"] = ak.to_numpy(ak.sum(bvals > tight_wp, axis=1))
        df["max_btag_discriminator"] = ak.to_numpy(ak.fill_none(ak.max(bvals, axis=1), -999))
    else:
        df["N_btags_medium"] = np.nan
        df["N_btags_tight"] = np.nan
        df["max_btag_discriminator"] = np.nan
    hlt_map = {
        "HLT_MET_paths_any": ["HLT_PFMET170_HBHECleaned"],
        "HLT_HT_paths_any": ["HLT_PFHT900"],
        "HLT_Mu_paths_any": ["HLT_IsoMu24"],
        "HLT_Ele_paths_any": ["HLT_Ele27_WPTight_Gsf"],
    }
    for out, names in hlt_map.items():
        present = [n for n in names if n in arr.fields]
        df[out] = ak.to_numpy(arr[present[0]]).astype(int) if present else -1
    flag_map = {
        "pass_HBHENoiseFilter": "Flag_HBHENoiseFilter",
        "pass_HBHENoiseIsoFilter": "Flag_HBHENoiseIsoFilter",
        "pass_goodVertices": "Flag_goodVertices",
        "pass_EcalDeadCellTriggerPrimitiveFilter": "Flag_EcalDeadCellTriggerPrimitiveFilter",
        "pass_BadPFMuonFilter": "Flag_BadPFMuonFilter",
        "pass_globalSuperTightHalo2016Filter": "Flag_globalSuperTightHalo2016Filter",
    }
    for out, name in flag_map.items():
        df[out] = ak.to_numpy(arr[name]).astype(int) if name in arr.fields else -1
    df["trigger_filter_extraction_status"] = 1
    df["extraction_limitations"] = "NanoAOD validation: secondary vertices and packed candidates unavailable; fitted score must be reduced/partial"
    meta = {"file": str(path), "events": len(df), "btag_branch": btag or "", "medium_wp": medium_wp, "tight_wp": tight_wp}
    return df, meta


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    manifest, frames, summaries = [], [], []
    for item in FILES:
        path = download(item)
        df, meta = extract_one(path, item)
        out = OUT_DIR / f"validation_nanoaod_{item['primary_dataset'].lower()}_{Path(item['filename']).stem}_event_features.csv"
        df.to_csv(out, index=False)
        frames.append(df)
        manifest.append({**item, "downloaded_path": str(path), "actual_size_bytes": path.stat().st_size, "output_csv": str(out), **meta})
    combined = pd.concat(frames, ignore_index=True)
    combined_path = OUT_DIR / "validation_nanoaod_event_features.csv"
    combined.to_csv(combined_path, index=False)
    man = pd.DataFrame(manifest)
    man.to_csv(TABLES / "independent_validation_nanoaod_download_manifest.csv", index=False)
    summary = combined.groupby(["sample_id", "primary_dataset", "source_file"], as_index=False).agg(events=("event", "count"), runs=("run", "nunique"))
    summary.to_csv(TABLES / "independent_nanoaod_validation_summary.csv", index=False)
    report = [
        "# Independent NanoAOD Validation Extraction Report",
        "",
        "Date: 2026-06-09",
        "",
        "Independent Run2016H NanoAOD real collision files were downloaded and extracted with Python/uproot. This is a partial validation because NanoAOD does not provide the same secondary-vertex and packed-candidate information as MiniAOD.",
        "",
        "## Manifest",
        "",
        man.to_markdown(index=False),
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False),
        "",
        f"Combined output: `{combined_path}`",
    ]
    (REPORTS / "INDEPENDENT_NANOAOD_VALIDATION_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
