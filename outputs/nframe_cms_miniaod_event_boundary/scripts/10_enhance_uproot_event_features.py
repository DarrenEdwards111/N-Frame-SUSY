import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from common import FILELIST_DIR, PROCESSED_DIR, TABLES_DIR, FIGURES_DIR, read_features, write_features, ensure_dirs


PF_PREFIX = "patPackedCandidates_packedPFCandidates__PAT.obj"
PV_PREFIX = "recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj"


def zscore(series):
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def find_branch(branches, leaf):
    if leaf in branches:
        return leaf
    suffix = "/" + leaf
    for branch in branches:
        if branch.endswith(suffix) or branch.endswith(leaf):
            return branch
    for branch in branches:
        if leaf in branch:
            return branch
    return None


def extract_aux_for_file(path, entry_stop):
    import awkward as ak
    import uproot

    with uproot.open(path) as root_file:
        tree = root_file["Events"]
        branches = set(tree.keys())
        wanted = {}
        for name, leaf in {
            "pf_pdgId": f"{PF_PREFIX}.pdgId_",
            "pf_iso_ch": f"{PF_PREFIX}.isIsolatedChargedHadron_",
            "pf_packed_pt_word": f"{PF_PREFIX}.packedPt_",
            "pv_chi2": f"{PV_PREFIX}.chi2_",
            "pv_ndof": f"{PV_PREFIX}.ndof_",
            "pv_z": f"{PV_PREFIX}.position_.fCoordinates.fZ",
            "pv_valid": f"{PV_PREFIX}.validity_",
        }.items():
            branch = find_branch(branches, leaf)
            if branch:
                wanted[name] = branch
        arrays = tree.arrays(list(wanted.values()), entry_stop=entry_stop, library="ak") if wanted else {}

    def arr(name):
        branch = wanted.get(name)
        return arrays[branch] if branch else None

    pdg = arr("pf_pdgId")
    iso = arr("pf_iso_ch")
    ptw = arr("pf_packed_pt_word")
    pv_ndof = arr("pv_ndof")
    pv_z = arr("pv_z")
    pv_valid = arr("pv_valid")
    n = len(pdg) if pdg is not None else (len(pv_ndof) if pv_ndof is not None else entry_stop)

    if pdg is not None:
        abs_pdg = abs(pdg)
        n_pf = ak.to_numpy(ak.num(pdg, axis=1))
        n_pf_mu = ak.to_numpy(ak.sum(abs_pdg == 13, axis=1))
        n_pf_e = ak.to_numpy(ak.sum(abs_pdg == 11, axis=1))
        n_pf_gamma = ak.to_numpy(ak.sum(abs_pdg == 22, axis=1))
        n_pf_ch_had = ak.to_numpy(ak.sum((abs_pdg == 211) | (abs_pdg == 321) | (abs_pdg == 2212), axis=1))
        n_pf_neutral = ak.to_numpy(ak.sum((abs_pdg == 130) | (abs_pdg == 2112), axis=1))
    else:
        n_pf = n_pf_mu = n_pf_e = n_pf_gamma = n_pf_ch_had = n_pf_neutral = np.full(n, np.nan)

    if iso is not None:
        n_iso = ak.to_numpy(ak.sum(iso, axis=1))
    else:
        n_iso = np.full(n, np.nan)
    if ptw is not None:
        packed_pt_word_sum = ak.to_numpy(ak.sum(ptw, axis=1))
    else:
        packed_pt_word_sum = np.full(n, np.nan)

    if pv_ndof is not None:
        n_pv = ak.to_numpy(ak.num(pv_ndof, axis=1))
        good = pv_ndof > 4
        if pv_valid is not None:
            good = good & pv_valid
        n_good_pv = ak.to_numpy(ak.sum(good, axis=1))
        leading_pv_ndof = ak.to_numpy(ak.fill_none(ak.pad_none(pv_ndof, 1, clip=True)[:, 0], np.nan))
    else:
        n_pv = n_good_pv = leading_pv_ndof = np.full(n, np.nan)
    if pv_z is not None:
        pv_abs_z_max = ak.to_numpy(ak.fill_none(ak.max(abs(pv_z), axis=1), np.nan))
    else:
        pv_abs_z_max = np.full(n, np.nan)

    return pd.DataFrame(
        {
            "N_PF_candidates": n_pf,
            "N_PF_muon_proxy": n_pf_mu,
            "N_PF_electron_proxy": n_pf_e,
            "N_PF_photon_proxy": n_pf_gamma,
            "N_PF_charged_hadron_proxy": n_pf_ch_had,
            "N_PF_neutral_hadron_proxy": n_pf_neutral,
            "N_isolated_charged_hadron": n_iso,
            "packed_pt_word_sum": packed_pt_word_sum,
            "N_primary_vertices": n_pv,
            "N_good_primary_vertices": n_good_pv,
            "leading_pv_ndof": leading_pv_ndof,
            "pv_abs_z_max": pv_abs_z_max,
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Enhance real MiniAOD uproot table with readable packed-PF and vertex proxies.")
    parser.add_argument("--input", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    parser.add_argument("--output", default=str(PROCESSED_DIR / "event_features_uproot_enhanced_scored.parquet"))
    args = parser.parse_args()
    ensure_dirs()
    base = read_features(Path(args.input)).copy()
    files = [line.strip() for line in (FILELIST_DIR / "miniaod_files.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

    frames = []
    for root_path in files:
        n = int((base["source_file"] == Path(root_path).name).sum())
        if n == 0:
            continue
        aux = extract_aux_for_file(root_path, n)
        aux["source_file"] = Path(root_path).name
        aux["source_entry"] = np.arange(len(aux))
        frames.append(aux)
        print(f"Enhanced {Path(root_path).name}: {len(aux)} events")
    aux_all = pd.concat(frames, ignore_index=True)
    enhanced = base.merge(aux_all, on=["source_file", "source_entry"], how="left", suffixes=("", "_aux"))
    if "N_PF_candidates_aux" in enhanced:
        enhanced["N_PF_candidates"] = enhanced["N_PF_candidates_aux"].combine_first(enhanced.get("N_PF_candidates"))
        enhanced = enhanced.drop(columns=[c for c in enhanced.columns if c.endswith("_aux")])

    enhanced["S_reco_proxy"] = np.log1p(
        enhanced["N_jets_30"].fillna(0)
        + enhanced["N_PF_candidates"].fillna(0) / 100.0
        + enhanced["N_good_primary_vertices"].fillna(0)
        + enhanced["N_isolated_charged_hadron"].fillna(0)
    )
    enhanced["B_event_reco"] = (
        zscore(enhanced["HT"])
        + zscore(enhanced["N_jets_30"])
        + zscore(enhanced["N_jets_50"])
        + zscore(enhanced["N_PF_candidates"])
        + zscore(enhanced["N_good_primary_vertices"])
        + zscore(enhanced["N_isolated_charged_hadron"])
        + zscore(enhanced["S_reco_proxy"])
    )
    enhanced["B_event_reco_z"] = zscore(enhanced["B_event_reco"])
    enhanced["full_boundary_features_available"] = 0
    enhanced["enhanced_reco_proxy_available"] = 1

    write_features(enhanced, Path(args.output))
    enhanced.to_csv(PROCESSED_DIR / "event_features_uproot_enhanced_scored.csv", index=False)
    enhanced.head(1000).to_csv(PROCESSED_DIR / "event_features_uproot_enhanced_scored_head.csv", index=False)

    cols = [
        "HT",
        "N_jets_30",
        "N_PF_candidates",
        "N_PF_muon_proxy",
        "N_PF_electron_proxy",
        "N_isolated_charged_hadron",
        "N_primary_vertices",
        "N_good_primary_vertices",
        "S_reco_proxy",
        "B_event_reco_z",
    ]
    enhanced[cols].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99]).T.to_csv(TABLES_DIR / "uproot_enhanced_event_summary.csv")
    top = enhanced.sort_values("B_event_reco_z", ascending=False).head(max(100, int(0.001 * len(enhanced))))
    top.to_csv(TABLES_DIR / "top_reco_boundary_events.csv", index=False)
    print(f"Wrote enhanced table with {len(enhanced)} events")


if __name__ == "__main__":
    main()
