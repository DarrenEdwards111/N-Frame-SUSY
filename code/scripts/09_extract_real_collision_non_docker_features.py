from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from real_collision_common import INTERIM, LOGS, PROCESSED, TABLES, ensure_dirs


MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"

JET_PREFIX = "patJets_slimmedJets__PAT./patJets_slimmedJets__PAT.obj/patJets_slimmedJets__PAT.obj"
JET_PT = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fPt"
JET_ETA = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fEta"
JET_PHI = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fPhi"
JET_MASS = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fM"
JET_HADRON_FLAVOUR = f"{JET_PREFIX}.jetFlavourInfo_.m_hadronFlavour"
JET_PARTON_FLAVOUR = f"{JET_PREFIX}.jetFlavourInfo_.m_partonFlavour"

PFC_PREFIX = "patPackedCandidates_packedPFCandidates__PAT./patPackedCandidates_packedPFCandidates__PAT.obj/patPackedCandidates_packedPFCandidates__PAT.obj"
PFC_PT = f"{PFC_PREFIX}.packedPt_"
PFC_DXY = f"{PFC_PREFIX}.packedDxy_"
PFC_DZ = f"{PFC_PREFIX}.packedDz_"
PFC_PDGID = f"{PFC_PREFIX}.pdgId_"
PFC_QUALITY = f"{PFC_PREFIX}.qualityFlags_"

VTX_PREFIX = "recoVertexs_offlineSlimmedPrimaryVertices__PAT./recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj/recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj"
VTX_X = f"{VTX_PREFIX}.position_.fCoordinates.fX"
VTX_Y = f"{VTX_PREFIX}.position_.fCoordinates.fY"
VTX_Z = f"{VTX_PREFIX}.position_.fCoordinates.fZ"
VTX_CHI2 = f"{VTX_PREFIX}.chi2_"
VTX_NDOF = f"{VTX_PREFIX}.ndof_"


def nth_or_nan(ak, array, index: int) -> np.ndarray:
    padded = ak.pad_none(array, index + 1, clip=True)
    return ak.to_numpy(ak.fill_none(padded[:, index], np.nan))


def safe_abs_max(ak, array) -> np.ndarray:
    values = ak.max(abs(array), axis=1)
    return ak.to_numpy(ak.fill_none(values, np.nan))


def extract_file(path: Path, sample_id: str, primary_dataset: str) -> tuple[pd.DataFrame | None, dict]:
    import awkward as ak
    import uproot

    status = {"sample_id": sample_id, "source_file": path.name, "status": "not_started", "events": 0, "notes": ""}
    try:
        with uproot.open(path) as root_file:
            tree = root_file["Events"]
            branches = set(tree.keys())
            required = [JET_PT, JET_ETA, JET_PHI, JET_MASS]
            missing = [name for name in required if name not in branches]
            if missing:
                status.update({"status": "missing_jet_branches", "notes": ";".join(missing)})
                return None, status
            optional = [name for name in [JET_HADRON_FLAVOUR, JET_PARTON_FLAVOUR, PFC_PT, PFC_DXY, PFC_DZ, PFC_PDGID, PFC_QUALITY, VTX_X, VTX_Y, VTX_Z, VTX_CHI2, VTX_NDOF] if name in branches]
            arrays = tree.arrays(required + optional, library="ak")
            pt = arrays[JET_PT]
            eta = arrays[JET_ETA]
            phi = arrays[JET_PHI]
            mass = arrays[JET_MASS]
            selected30 = (pt > 30) & (abs(eta) < 2.4)
            selected50 = (pt > 50) & (abs(eta) < 2.4)
            n_events = len(pt)

            frame = pd.DataFrame(
                {
                    "sample_id": sample_id,
                    "primary_dataset": primary_dataset,
                    "source_file": path.name,
                    "source_path": str(path),
                    "event_index": np.arange(n_events, dtype=np.int64),
                    "run": np.nan,
                    "lumi": np.nan,
                    "event": np.nan,
                    "MET_pt": np.nan,
                    "MET_phi": np.nan,
                    "N_jets": ak.to_numpy(ak.num(pt, axis=1)),
                    "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
                    "N_jets_50": ak.to_numpy(ak.sum(selected50, axis=1)),
                    "HT": ak.to_numpy(ak.sum(pt * selected30, axis=1)),
                    "leading_jet_pt": nth_or_nan(ak, pt, 0),
                    "subleading_jet_pt": nth_or_nan(ak, pt, 1),
                    "leading_jet_eta": nth_or_nan(ak, eta, 0),
                    "leading_jet_phi": nth_or_nan(ak, phi, 0),
                    "sum_jet_pt": ak.to_numpy(ak.sum(pt, axis=1)),
                    "jet_mass_sum_30": ak.to_numpy(ak.sum(mass * selected30, axis=1)),
                    "N_muons": np.nan,
                    "N_electrons": np.nan,
                    "N_btags_loose": np.nan,
                    "N_btags_medium": np.nan,
                    "max_btag_discriminator": np.nan,
                }
            )
            if JET_HADRON_FLAVOUR in arrays.fields:
                had = arrays[JET_HADRON_FLAVOUR]
                frame["N_b_hadron_flavour_proxy"] = ak.to_numpy(ak.sum((abs(had) == 5) & selected30, axis=1))
            else:
                frame["N_b_hadron_flavour_proxy"] = np.nan
            if JET_PARTON_FLAVOUR in arrays.fields:
                part = arrays[JET_PARTON_FLAVOUR]
                frame["N_b_parton_flavour_proxy"] = ak.to_numpy(ak.sum((abs(part) == 5) & selected30, axis=1))
            else:
                frame["N_b_parton_flavour_proxy"] = np.nan

            if PFC_PT in arrays.fields:
                pfc_pt = arrays[PFC_PT]
                frame["N_packed_pf_candidates"] = ak.to_numpy(ak.num(pfc_pt, axis=1))
                frame["N_pfc_pt_gt_1"] = ak.to_numpy(ak.sum(pfc_pt > 1, axis=1))
            else:
                frame["N_packed_pf_candidates"] = np.nan
                frame["N_pfc_pt_gt_1"] = np.nan
            if PFC_DXY in arrays.fields:
                dxy = arrays[PFC_DXY]
                frame["max_abs_pfc_dxy"] = safe_abs_max(ak, dxy)
                frame["N_pfc_abs_dxy_gt_0p05"] = ak.to_numpy(ak.sum(abs(dxy) > 0.05, axis=1))
                frame["N_pfc_abs_dxy_gt_0p10"] = ak.to_numpy(ak.sum(abs(dxy) > 0.10, axis=1))
            else:
                frame["max_abs_pfc_dxy"] = np.nan
                frame["N_pfc_abs_dxy_gt_0p05"] = np.nan
                frame["N_pfc_abs_dxy_gt_0p10"] = np.nan
            if PFC_DZ in arrays.fields:
                dz = arrays[PFC_DZ]
                frame["max_abs_pfc_dz"] = safe_abs_max(ak, dz)
                frame["N_pfc_abs_dz_gt_0p10"] = ak.to_numpy(ak.sum(abs(dz) > 0.10, axis=1))
            else:
                frame["max_abs_pfc_dz"] = np.nan
                frame["N_pfc_abs_dz_gt_0p10"] = np.nan

            if VTX_Z in arrays.fields:
                frame["N_primary_vertices"] = ak.to_numpy(ak.num(arrays[VTX_Z], axis=1))
                frame["primary_vertex_z"] = nth_or_nan(ak, arrays[VTX_Z], 0)
            else:
                frame["N_primary_vertices"] = np.nan
                frame["primary_vertex_z"] = np.nan
            if VTX_CHI2 in arrays.fields:
                frame["primary_vertex_chi2"] = nth_or_nan(ak, arrays[VTX_CHI2], 0)
            else:
                frame["primary_vertex_chi2"] = np.nan
            if VTX_NDOF in arrays.fields:
                frame["primary_vertex_ndof"] = nth_or_nan(ak, arrays[VTX_NDOF], 0)
            else:
                frame["primary_vertex_ndof"] = np.nan

            object_parts = ["N_jets_30", "N_pfc_pt_gt_1", "N_primary_vertices"]
            frame["object_multiplicity"] = frame[object_parts].sum(axis=1, skipna=True)
            feature_cols = [
                "N_jets_30",
                "HT",
                "N_b_hadron_flavour_proxy",
                "N_packed_pf_candidates",
                "max_abs_pfc_dxy",
                "max_abs_pfc_dz",
                "N_primary_vertices",
            ]
            frame["available_feature_count"] = frame[feature_cols].notna().sum(axis=1)
            frame["extraction_limitations"] = (
                "Non-Docker uproot leaf extraction. MET, run/lumi/event IDs, lepton counts, "
                "experimental b-tag discriminators and named trigger decisions remain unavailable. "
                "Packed-candidate dxy/dz are displacement-like proxies, not a validated lifetime measurement."
            )
            status.update({"status": "extracted", "events": len(frame), "notes": "jets;flavour proxies;packed candidates;vertices"})
            return frame, status
    except Exception as exc:
        status.update({"status": "failed", "notes": repr(exc)})
        (LOGS / f"non_docker_extract_error_{sample_id}_{path.stem}.txt").write_text(str(exc), encoding="utf-8")
        return None, status


def main() -> None:
    ensure_dirs()
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)]
    frames = []
    statuses = []
    for _, row in manifest.sort_values(["sample_id", "file_name"]).iterrows():
        frame, status = extract_file(Path(row["local_path"]), row["sample_id"], row["primary_dataset"])
        statuses.append(status)
        if frame is not None and not frame.empty:
            frames.append(frame)
    status_df = pd.DataFrame(statuses)
    status_df.to_csv(TABLES / "non_docker_feature_extraction_status.csv", index=False)
    if not frames:
        raise SystemExit("No non-Docker features extracted.")
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(PROCESSED / "real_collision_20gb_non_docker_event_features.csv", index=False)
    for sample_id, sample_frame in combined.groupby("sample_id"):
        sample_frame.to_csv(INTERIM / f"non_docker_real_collision_{sample_id}_event_features.csv", index=False)
    print(f"Wrote {len(combined)} rows to {PROCESSED / 'real_collision_20gb_non_docker_event_features.csv'}")


if __name__ == "__main__":
    main()
