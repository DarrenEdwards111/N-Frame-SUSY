from __future__ import annotations

import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from stage2_common import INTERIM, LOGS, PROCESSED, TABLES, ensure_dirs, manifest_path


JET_PREFIX = "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates"
JET_PT = f"{JET_PREFIX}.fPt"
JET_ETA = f"{JET_PREFIX}.fEta"
JET_MASS = f"{JET_PREFIX}.fM"
JET_HADRON_FLAVOUR = "patJets_slimmedJets__PAT.obj.jetFlavourInfo_.m_hadronFlavour"

NANO_CANDIDATES = {
    "MET_pt": ["MET_pt", "PuppiMET_pt"],
    "Jet_pt": ["Jet_pt"],
    "Jet_eta": ["Jet_eta"],
    "Muon_pt": ["Muon_pt"],
    "Electron_pt": ["Electron_pt"],
    "Btag": ["Jet_btagDeepB", "Jet_btagDeepFlavB"],
}


def find_exact(branches: set[str], candidates: list[str]) -> str | None:
    return next((candidate for candidate in candidates if candidate in branches), None)


def find_edm_branch(branches: set[str], leaf_name: str) -> str | None:
    if leaf_name in branches:
        return leaf_name
    for branch in branches:
        if branch.endswith("/" + leaf_name) or branch.endswith(leaf_name):
            return branch
    for branch in branches:
        if leaf_name in branch:
            return branch
    return None


def nth_or_nan(ak, array, index: int) -> np.ndarray:
    padded = ak.pad_none(array, index + 1, clip=True)
    return ak.to_numpy(ak.fill_none(padded[:, index], np.nan))


def extract_nanoaod(tree, branches: set[str], sample_id: str, file_name: str, entry_stop: int) -> pd.DataFrame | None:
    import awkward as ak

    met_branch = find_exact(branches, NANO_CANDIDATES["MET_pt"])
    jet_pt = find_exact(branches, NANO_CANDIDATES["Jet_pt"])
    if not jet_pt:
        return None
    jet_eta = find_exact(branches, NANO_CANDIDATES["Jet_eta"])
    muon_pt = find_exact(branches, NANO_CANDIDATES["Muon_pt"])
    electron_pt = find_exact(branches, NANO_CANDIDATES["Electron_pt"])
    btag = find_exact(branches, NANO_CANDIDATES["Btag"])
    names = [name for name in [met_branch, jet_pt, jet_eta, muon_pt, electron_pt, btag] if name]
    arrays = tree.arrays(names, entry_stop=entry_stop, library="ak")
    pt = arrays[jet_pt]
    eta = arrays[jet_eta] if jet_eta else pt * 0
    selected30 = (pt > 30) & (abs(eta) < 2.4)
    selected50 = (pt > 50) & (abs(eta) < 2.4)
    n = len(pt)
    out = pd.DataFrame(
        {
            "sample_id": sample_id,
            "source_file": file_name,
            "event_index": np.arange(n),
            "extraction_mode": "uproot_nanoaod",
            "MET_pt": ak.to_numpy(arrays[met_branch]) if met_branch else np.nan,
            "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
            "N_jets_50": ak.to_numpy(ak.sum(selected50, axis=1)),
            "HT": ak.to_numpy(ak.sum(pt * selected30, axis=1)),
            "leading_jet_pt": nth_or_nan(ak, pt, 0),
            "subleading_jet_pt": nth_or_nan(ak, pt, 1),
            "N_muons": ak.to_numpy(ak.sum(arrays[muon_pt] > 10, axis=1)) if muon_pt else np.nan,
            "N_electrons": ak.to_numpy(ak.sum(arrays[electron_pt] > 10, axis=1)) if electron_pt else np.nan,
            "N_btags_medium": ak.to_numpy(ak.sum((arrays[btag] > 0.6321) & selected30, axis=1)) if btag else np.nan,
            "N_b_hadron_flavour_proxy": np.nan,
            "available_features": "jets;MET" if met_branch else "jets",
            "extraction_limitations": "NanoAOD-like extraction; optional objects may be missing",
        }
    )
    return out


def extract_edm_partial(tree, branches: set[str], sample_id: str, file_name: str, entry_stop: int) -> pd.DataFrame | None:
    import awkward as ak

    jet_pt = find_edm_branch(branches, JET_PT)
    jet_eta = find_edm_branch(branches, JET_ETA)
    jet_mass = find_edm_branch(branches, JET_MASS)
    jet_hadron_flavour = find_edm_branch(branches, JET_HADRON_FLAVOUR)
    if not all([jet_pt, jet_eta, jet_mass]):
        return None
    names = [jet_pt, jet_eta, jet_mass]
    if jet_hadron_flavour:
        names.append(jet_hadron_flavour)
    arrays = tree.arrays(names, entry_stop=entry_stop, library="ak")
    pt = arrays[jet_pt]
    eta = arrays[jet_eta]
    selected30 = (pt > 30) & (abs(eta) < 2.4)
    selected50 = (pt > 50) & (abs(eta) < 2.4)
    n = len(pt)
    hadron_flavour = arrays[jet_hadron_flavour] if jet_hadron_flavour else None
    return pd.DataFrame(
        {
            "sample_id": sample_id,
            "source_file": file_name,
            "event_index": np.arange(n),
            "extraction_mode": "uproot_edm_partial_jets",
            "MET_pt": np.nan,
            "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
            "N_jets_50": ak.to_numpy(ak.sum(selected50, axis=1)),
            "HT": ak.to_numpy(ak.sum(pt * selected30, axis=1)),
            "leading_jet_pt": nth_or_nan(ak, pt, 0),
            "subleading_jet_pt": nth_or_nan(ak, pt, 1),
            "jet_mass_sum_30": ak.to_numpy(ak.sum(arrays[jet_mass] * selected30, axis=1)),
            "N_muons": np.nan,
            "N_electrons": np.nan,
            "N_btags_medium": np.nan,
            "N_b_hadron_flavour_proxy": (
                ak.to_numpy(ak.sum((abs(hadron_flavour) == 5) & selected30, axis=1))
                if hadron_flavour is not None
                else np.nan
            ),
            "available_features": "jets",
            "extraction_limitations": "MiniAOD EDM partial extraction; MET/leptons/b-tags require CMSSW",
        }
    )


def main() -> None:
    ensure_dirs()
    import uproot

    manifest = pd.read_csv(manifest_path())
    usable = manifest[(manifest["exists"] == True) & (manifest["readable_by_python_uproot_success"] == True)]
    frames = []
    log_rows = []
    for _, row in usable.iterrows():
        sample_id = row["sample_id"]
        path = Path(row["local_path"])
        try:
            with uproot.open(path) as root_file:
                if "Events" not in root_file:
                    log_rows.append({"sample_id": sample_id, "file_name": path.name, "status": "no_events_tree", "events": 0})
                    continue
                tree = root_file["Events"]
                branches = set(tree.keys())
                frame = extract_nanoaod(tree, branches, sample_id, path.name, tree.num_entries)
                if frame is None:
                    frame = extract_edm_partial(tree, branches, sample_id, path.name, tree.num_entries)
                if frame is None:
                    log_rows.append({"sample_id": sample_id, "file_name": path.name, "status": "no_usable_branches", "events": 0})
                    continue
                out_path = INTERIM / f"uproot_partial_{sample_id}_partial_events.csv"
                frame.to_csv(out_path, index=False)
                frames.append(frame)
                log_rows.append({"sample_id": sample_id, "file_name": path.name, "status": frame["extraction_mode"].iloc[0], "events": len(frame)})
        except Exception as exc:
            log_rows.append({"sample_id": sample_id, "file_name": path.name, "status": f"failed: {exc}", "events": 0})
            (LOGS / f"uproot_partial_{sample_id}_error.txt").write_text(traceback.format_exc(), encoding="utf-8")

    pd.DataFrame(log_rows).to_csv(TABLES / "uproot_partial_extraction_log.csv", index=False)
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_csv(PROCESSED / "stage2_uproot_partial_event_features.csv", index=False)
        print(f"Wrote {len(combined)} rows")
    else:
        (LOGS / "uproot_partial_no_features.txt").write_text("No useful event features could be extracted with uproot. CMSSW is required.\n", encoding="utf-8")
        print("No useful event features extracted")


if __name__ == "__main__":
    main()

