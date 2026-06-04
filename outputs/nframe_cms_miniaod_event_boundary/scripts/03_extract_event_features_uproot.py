import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from common import FILELIST_DIR, PROCESSED_DIR, ensure_dirs


JET_PREFIX = "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates"
JET_PT = f"{JET_PREFIX}.fPt"
JET_ETA = f"{JET_PREFIX}.fEta"
JET_PHI = f"{JET_PREFIX}.fPhi"
JET_MASS = f"{JET_PREFIX}.fM"
JET_HADRON_FLAVOUR = "patJets_slimmedJets__PAT.obj.jetFlavourInfo_.m_hadronFlavour"
NANO_CANDIDATES = {
    "MET_pt": ["MET_pt", "PuppiMET_pt"],
    "MET_phi": ["MET_phi", "PuppiMET_phi"],
    "Jet_pt": ["Jet_pt"],
    "Jet_eta": ["Jet_eta"],
    "Muon_pt": ["Muon_pt"],
    "Electron_pt": ["Electron_pt"],
    "Btag": ["Jet_btagDeepB", "Jet_btagDeepFlavB"],
}


def fail_cmssw(message: str) -> None:
    raise SystemExit(
        message
        + "\nMiniAOD requires CMSSW/FWLite analyzer for full event-object extraction. "
        + "Use cmssw/NFrameMiniAODAnalyzer.cc and cmssw/run_nframe_miniAOD_cfg.py."
    )


def find_exact(branches, candidates):
    branch_set = set(branches)
    for candidate in candidates:
        if candidate in branch_set:
            return candidate
    return None


def find_edm_branch(branches, leaf_name):
    if leaf_name in branches:
        return leaf_name
    suffix = "/" + leaf_name
    for branch in branches:
        if branch.endswith(suffix) or branch.endswith(leaf_name):
            return branch
    for branch in branches:
        if leaf_name in branch:
            return branch
    return None


def nth_or_nan(ak, array, index):
    filled = ak.pad_none(array, index + 1, clip=True)
    return ak.to_numpy(ak.fill_none(filled[:, index], np.nan))


def extract_nanoaod(tree, branches, entry_stop, event_offset):
    import awkward as ak

    met_branch = find_exact(branches, NANO_CANDIDATES["MET_pt"])
    jet_pt_branch = find_exact(branches, NANO_CANDIDATES["Jet_pt"])
    if not met_branch or not jet_pt_branch:
        return None

    names = [met_branch, jet_pt_branch]
    optional = {
        "MET_phi": find_exact(branches, NANO_CANDIDATES["MET_phi"]),
        "Jet_eta": find_exact(branches, NANO_CANDIDATES["Jet_eta"]),
        "Muon_pt": find_exact(branches, NANO_CANDIDATES["Muon_pt"]),
        "Electron_pt": find_exact(branches, NANO_CANDIDATES["Electron_pt"]),
        "Btag": find_exact(branches, NANO_CANDIDATES["Btag"]),
    }
    names.extend([name for name in optional.values() if name])
    arrays = tree.arrays(names, entry_stop=entry_stop, library="ak")

    met = ak.to_numpy(arrays[met_branch])
    jets = arrays[jet_pt_branch]
    jet_eta = arrays[optional["Jet_eta"]] if optional["Jet_eta"] else jets * 0
    selected30 = (jets > 30) & (abs(jet_eta) < 2.4)
    selected50 = (jets > 50) & (abs(jet_eta) < 2.4)
    n = len(met)
    muons = arrays[optional["Muon_pt"]] if optional["Muon_pt"] else None
    electrons = arrays[optional["Electron_pt"]] if optional["Electron_pt"] else None
    btag = arrays[optional["Btag"]] if optional["Btag"] else None
    nb_med = ak.to_numpy(ak.sum((btag > 0.6321) & selected30, axis=1)) if btag is not None else np.full(n, np.nan)

    n_muons = ak.to_numpy(ak.sum(muons > 10, axis=1)) if muons is not None else np.full(n, np.nan)
    n_electrons = ak.to_numpy(ak.sum(electrons > 10, axis=1)) if electrons is not None else np.full(n, np.nan)
    n_leptons = n_muons + n_electrons if muons is not None or electrons is not None else np.full(n, np.nan)

    return pd.DataFrame(
        {
            "event_id": np.arange(event_offset, event_offset + n),
            "source_file": "",
            "source_entry": np.arange(n),
            "extraction_mode": "uproot_nanoaod",
            "full_boundary_features_available": int(np.isfinite(nb_med).any()),
            "jet_only_features_available": 1,
            "MET_pt": met,
            "MET_phi": ak.to_numpy(arrays[optional["MET_phi"]]) if optional["MET_phi"] else np.full(n, np.nan),
            "N_jets": ak.to_numpy(ak.sum(selected30, axis=1)),
            "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
            "N_jets_50": ak.to_numpy(ak.sum(selected50, axis=1)),
            "HT": ak.to_numpy(ak.sum(jets * selected30, axis=1)),
            "leading_jet_pt": nth_or_nan(ak, jets, 0),
            "subleading_jet_pt": nth_or_nan(ak, jets, 1),
            "N_leptons": n_leptons,
            "N_muons": n_muons,
            "N_electrons": n_electrons,
            "N_btags_loose": np.full(n, np.nan),
            "N_btags_medium": nb_med,
            "N_btags_tight": np.full(n, np.nan),
            "N_PF_candidates": np.full(n, np.nan),
            "event_weight": 1.0,
            "missing_MET": 0,
            "missing_leptons": int(muons is None and electrons is None),
            "missing_btags": int(btag is None),
        }
    )


def extract_edm_partial(tree, branches, entry_stop, event_offset):
    import awkward as ak

    jet_pt = find_edm_branch(branches, JET_PT)
    jet_eta = find_edm_branch(branches, JET_ETA)
    jet_phi = find_edm_branch(branches, JET_PHI)
    jet_mass = find_edm_branch(branches, JET_MASS)
    jet_hadron_flavour = find_edm_branch(branches, JET_HADRON_FLAVOUR)
    required = [jet_pt, jet_eta, jet_phi, jet_mass]
    if not all(required):
        return None

    names = required.copy()
    if jet_hadron_flavour:
        names.append(jet_hadron_flavour)
    arrays = tree.arrays(names, entry_stop=entry_stop, library="ak")

    pt = arrays[jet_pt]
    eta = arrays[jet_eta]
    selected30 = (pt > 30) & (abs(eta) < 2.4)
    selected50 = (pt > 50) & (abs(eta) < 2.4)
    n = len(pt)
    hadron_flavour = arrays[jet_hadron_flavour] if jet_hadron_flavour else None

    # This is a truth-label proxy in simulation-style branches, not a data b-tag discriminator.
    nb_hadron_proxy = (
        ak.to_numpy(ak.sum((abs(hadron_flavour) == 5) & selected30, axis=1))
        if hadron_flavour is not None
        else np.full(n, np.nan)
    )

    return pd.DataFrame(
        {
            "event_id": np.arange(event_offset, event_offset + n),
            "source_file": "",
            "source_entry": np.arange(n),
            "extraction_mode": "uproot_edm_partial_jets",
            "full_boundary_features_available": 0,
            "jet_only_features_available": 1,
            "MET_pt": np.full(n, np.nan),
            "MET_phi": np.full(n, np.nan),
            "N_jets": ak.to_numpy(ak.sum(selected30, axis=1)),
            "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
            "N_jets_50": ak.to_numpy(ak.sum(selected50, axis=1)),
            "HT": ak.to_numpy(ak.sum(pt * selected30, axis=1)),
            "leading_jet_pt": nth_or_nan(ak, pt, 0),
            "subleading_jet_pt": nth_or_nan(ak, pt, 1),
            "leading_jet_eta": nth_or_nan(ak, eta, 0),
            "jet_mass_sum_30": ak.to_numpy(ak.sum(arrays[jet_mass] * selected30, axis=1)),
            "N_leptons": np.full(n, np.nan),
            "N_muons": np.full(n, np.nan),
            "N_electrons": np.full(n, np.nan),
            "N_btags_loose": np.full(n, np.nan),
            "N_btags_medium": np.full(n, np.nan),
            "N_btags_tight": np.full(n, np.nan),
            "N_b_hadron_flavour_proxy": nb_hadron_proxy,
            "N_PF_candidates": np.full(n, np.nan),
            "event_weight": 1.0,
            "missing_MET": 1,
            "missing_leptons": 1,
            "missing_btags": 1,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract event features directly with uproot where possible.")
    parser.add_argument("--filelist", default=str(FILELIST_DIR / "miniaod_files.txt"))
    parser.add_argument("--max-events", type=int, default=200000)
    parser.add_argument("--output", default=str(PROCESSED_DIR / "event_features.parquet"))
    args = parser.parse_args()

    ensure_dirs()
    try:
        import uproot
    except Exception as exc:
        fail_cmssw(f"Missing uproot dependency: {exc}")

    files = [line.strip() for line in Path(args.filelist).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not files:
        fail_cmssw("No ROOT files in filelist.")

    frames = []
    processed = 0
    log_rows = []
    for root_path in files:
        remaining = args.max_events - processed
        if remaining <= 0:
            break
        with uproot.open(root_path) as root_file:
            if "Events" not in root_file:
                log_rows.append({"file": root_path, "status": "no_events_tree", "events": 0})
                continue
            tree = root_file["Events"]
            entry_stop = min(remaining, tree.num_entries)
            branches = set(tree.keys())
            frame = extract_nanoaod(tree, branches, entry_stop, processed)
            if frame is None:
                frame = extract_edm_partial(tree, branches, entry_stop, processed)
            if frame is None:
                log_rows.append({"file": root_path, "status": "no_readable_feature_branches", "events": 0})
                continue
            frame["source_file"] = Path(root_path).name
            frame["source_entry"] = np.arange(len(frame))
            frames.append(frame)
            processed += len(frame)
            log_rows.append(
                {
                    "file": root_path,
                    "status": frame["extraction_mode"].iloc[0],
                    "events": len(frame),
                    "full_boundary_features_available": int(frame["full_boundary_features_available"].max()),
                }
            )

    if not frames:
        pd.DataFrame(log_rows).to_csv(PROCESSED_DIR / "event_extraction_log.csv", index=False)
        fail_cmssw("No flat event feature table could be produced by uproot.")

    df = pd.concat(frames, ignore_index=True)
    output = Path(args.output)
    if output.suffix.lower() == ".parquet":
        df.to_parquet(output, index=False)
    else:
        df.to_csv(output, index=False)
    df.head(1000).to_csv(PROCESSED_DIR / "event_features_head.csv", index=False)
    pd.DataFrame(log_rows).to_csv(PROCESSED_DIR / "event_extraction_log.csv", index=False)
    print(f"Wrote {len(df)} events to {output}")
    print(f"Extraction modes: {', '.join(sorted(df['extraction_mode'].unique()))}")
    print(f"Full boundary features available: {int(df['full_boundary_features_available'].max())}")


if __name__ == "__main__":
    main()
