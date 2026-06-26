from __future__ import annotations

import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from real_collision_common import INTERIM, LOGS, PROCESSED, REPORTS, TABLES, ensure_dirs


MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"

JET_PREFIX = "patJets_slimmedJets__PAT./patJets_slimmedJets__PAT.obj/patJets_slimmedJets__PAT.obj"
JET_PT = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fPt"
JET_ETA = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fEta"
JET_PHI = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fPhi"
JET_MASS = f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fM"
JET_HADRON_FLAVOUR = f"{JET_PREFIX}.jetFlavourInfo_.m_hadronFlavour"


def nth_or_nan(ak, array, index: int) -> np.ndarray:
    padded = ak.pad_none(array, index + 1, clip=True)
    return ak.to_numpy(ak.fill_none(padded[:, index], np.nan))


def extract_file(path: Path, sample_id: str, primary_dataset: str) -> tuple[pd.DataFrame | None, dict, str]:
    import awkward as ak
    import uproot

    log_lines = [f"=== {sample_id} :: {path.name} ==="]
    status = {
        "sample_id": sample_id,
        "primary_dataset": primary_dataset,
        "source_file": path.name,
        "status": "not_started",
        "events_extracted": 0,
        "available_features": "",
        "unavailable_features": "run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement",
        "error": "",
    }
    try:
        with uproot.open(path) as root_file:
            if "Events" not in root_file:
                status["status"] = "no_events_tree"
                return None, status, "\n".join(log_lines)
            tree = root_file["Events"]
            branches = set(tree.keys())
            required = [JET_PT, JET_ETA, JET_PHI, JET_MASS]
            missing = [name for name in required if name not in branches]
            if missing:
                status["status"] = "missing_required_jet_branches"
                status["error"] = ";".join(missing)
                return None, status, "\n".join(log_lines)
            names = required + ([JET_HADRON_FLAVOUR] if JET_HADRON_FLAVOUR in branches else [])
            arrays = tree.arrays(names, library="ak")
            pt = arrays[JET_PT]
            eta = arrays[JET_ETA]
            phi = arrays[JET_PHI]
            mass = arrays[JET_MASS]
            selected30 = (pt > 30) & (abs(eta) < 2.4)
            selected50 = (pt > 50) & (abs(eta) < 2.4)
            hadron_flavour = arrays[JET_HADRON_FLAVOUR] if JET_HADRON_FLAVOUR in arrays.fields else None
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
                    "extraction_mode": "uproot_miniaod_visible_jets_only",
                    "MET_pt": np.nan,
                    "MET_phi": np.nan,
                    "N_jets": ak.to_numpy(ak.num(pt, axis=1)),
                    "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
                    "N_jets_50": ak.to_numpy(ak.sum(selected50, axis=1)),
                    "HT": ak.to_numpy(ak.sum(pt * selected30, axis=1)),
                    "sum_jet_pt": ak.to_numpy(ak.sum(pt, axis=1)),
                    "leading_jet_pt": nth_or_nan(ak, pt, 0),
                    "subleading_jet_pt": nth_or_nan(ak, pt, 1),
                    "leading_jet_eta": nth_or_nan(ak, eta, 0),
                    "leading_jet_phi": nth_or_nan(ak, phi, 0),
                    "jet_mass_sum_30": ak.to_numpy(ak.sum(mass * selected30, axis=1)),
                    "N_muons": np.nan,
                    "N_electrons": np.nan,
                    "N_isolated_muons": np.nan,
                    "N_isolated_electrons": np.nan,
                    "N_btags_medium": np.nan,
                    "max_btag_discriminator": np.nan,
                    "N_b_hadron_flavour_proxy": (
                        ak.to_numpy(ak.sum((abs(hadron_flavour) == 5) & selected30, axis=1))
                        if hadron_flavour is not None
                        else np.nan
                    ),
                    "object_multiplicity": ak.to_numpy(ak.sum(selected30, axis=1)),
                    "available_features": "jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy"
                    if hadron_flavour is not None
                    else "jets;HT;jet_multiplicity;jet_phi_eta",
                    "extraction_limitations": "MiniAOD via uproot; MET, leptons, b-tag discriminators, triggers, run/lumi/event IDs, and displacement variables require CMSSW",
                }
            )
            status["status"] = "extracted_visible_jets_only"
            status["events_extracted"] = len(frame)
            status["available_features"] = frame["available_features"].iloc[0]
            log_lines.append(f"Extracted {len(frame)} rows")
            return frame, status, "\n".join(log_lines)
    except Exception as exc:
        status["status"] = "failed"
        status["error"] = repr(exc)
        log_lines.append(traceback.format_exc())
        return None, status, "\n".join(log_lines)


def write_report(log_rows: pd.DataFrame, combined_rows: int) -> None:
    extracted = int((log_rows["events_extracted"] > 0).sum()) if not log_rows.empty else 0
    unavailable = "run/lumi/event IDs, MET pt/phi, muon/electron counts, b-tag discriminators, trigger decisions, lifetime/displacement variables"
    report = f"""# Uproot Partial Extraction Report

## Summary

The Python/uproot fallback extracted {combined_rows:,} event rows from {extracted} ROOT files.

What was extractable: jet four-vector leaves from MiniAOD (`pt`, `eta`, `phi`, mass), jet multiplicity, HT from jets with pt > 30 GeV, leading/subleading jet pt, sum jet pt, object multiplicity based on selected jets, and a hadron-flavour proxy where the MiniAOD leaf was readable.

What was not extractable honestly with this lightweight path: {unavailable}.

This output is useful for a limited real-data boundary dry run based on visible jet activity only. It is not sufficient for a serious N-Frame boundary analysis because the missing-information component requires MET, and the reconstruction-complexity components need leptons, b-tags, triggers, and quality information. CMSSW remains required for the proper analysis layer.

## Per-File Status

{log_rows.to_markdown(index=False) if not log_rows.empty else 'No files were processed.'}
"""
    (REPORTS / "UPROOT_PARTIAL_EXTRACTION_REPORT.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)]
    frames = []
    status_rows = []
    logs = []
    for _, row in manifest.sort_values(["sample_id", "file_name"]).iterrows():
        frame, status, log = extract_file(Path(row["local_path"]), row["sample_id"], row["primary_dataset"])
        status_rows.append(status)
        logs.append(log)
        if frame is not None and not frame.empty:
            frames.append(frame)

    status_df = pd.DataFrame(status_rows)
    status_df.to_csv(TABLES / "uproot_real_collision_partial_extraction_log.csv", index=False)
    (LOGS / "uproot_real_collision_partial_extraction_log.txt").write_text("\n\n".join(logs), encoding="utf-8")

    combined_rows = 0
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined_rows = len(combined)
        for sample_id, sample_frame in combined.groupby("sample_id"):
            sample_frame.to_csv(INTERIM / f"uproot_real_collision_partial_{sample_id}_partial_events.csv", index=False)
        combined.to_csv(PROCESSED / "real_collision_20gb_uproot_partial_event_features.csv", index=False)
    write_report(status_df, combined_rows)
    print(f"Extracted {combined_rows} rows")
    print(f"Wrote {PROCESSED / 'real_collision_20gb_uproot_partial_event_features.csv'}")
    print(f"Wrote {REPORTS / 'UPROOT_PARTIAL_EXTRACTION_REPORT.md'}")


if __name__ == "__main__":
    main()
