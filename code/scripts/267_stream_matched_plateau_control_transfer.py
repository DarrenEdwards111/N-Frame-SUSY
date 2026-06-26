from __future__ import annotations

"""Stream-matched offline-plateau control-to-MET transfer test.

This is a stricter successor to the generic proxy fit. Data streams keep their
observed broad trigger bit and all samples use the same offline plateau-like
selection: MET >=150 GeV, JetHT HT >=900 GeV, or at least one muon.
"""

import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls
from scipy.stats import chi2, norm


ROOT = Path(__file__).resolve().parents[1]
MOD = SourceFileLoader("frozen_reference", str(ROOT / "scripts" / "265_frozen_reference_opq_sm_shape_likelihood.py")).load_module()
OUT = ROOT / "outputs_stream_matched_plateau_control_transfer"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
PROCESS_TIERS = ["exact_record_sumw", "metadata_unit_weight_record"]
SAMPLES = MOD.SAMPLES
BANDS = MOD.BANDS


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def selected(frame: pd.DataFrame, stream: str, data: bool) -> pd.DataFrame:
    if stream == "MET":
        mask = frame["MET_pt"].ge(150)
        if data:
            mask &= pd.to_numeric(frame["HLT_MET_paths_any"], errors="coerce").fillna(0).eq(1)
    elif stream == "JetHT":
        mask = frame["HT"].ge(900) & frame["n_jets"].ge(1)
        if data:
            mask &= pd.to_numeric(frame["HLT_HT_paths_any"], errors="coerce").fillna(0).eq(1)
    elif stream == "SingleMuon":
        mask = frame["n_muons"].ge(1)
        if data:
            mask &= pd.to_numeric(frame["HLT_Mu_paths_any"], errors="coerce").fillna(0).eq(1)
    else:
        raise ValueError(stream)
    return frame.loc[mask].copy()


def counts(frame: pd.DataFrame, weight: str | None = None) -> np.ndarray:
    if weight is None:
        return np.asarray([(frame["microband_frozen_reference"] == b).sum() for b in BANDS], dtype=float)
    return np.asarray([frame.loc[frame["microband_frozen_reference"].eq(b), weight].sum() for b in BANDS], dtype=float)


def fit_nnls(real: pd.DataFrame, mc: pd.DataFrame, processes: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    matrices = []
    targets = []
    labels = []
    for stream in ["JetHT", "SingleMuon"]:
        data_stream = selected(real[real["primary_dataset"].eq(stream)], stream, data=True)
        targets.extend(counts(data_stream))
        labels.extend([f"{stream}:{b}" for b in BANDS])
        process_cols = []
        for process in processes:
            sim = selected(mc[(mc["calibration_stream"].eq(stream)) & mc["process_family"].eq(process)], stream, data=False)
            process_cols.append(counts(sim, "template_weight"))
        matrices.append(np.column_stack(process_cols))
    a = np.vstack(matrices)
    y = np.asarray(targets, dtype=float)
    scale = np.sqrt(np.maximum(y, 1.0))
    coeff, _ = nnls(a / scale[:, None], y / scale)
    return coeff, a, y, labels


def closure(observed: np.ndarray, expected: np.ndarray) -> tuple[float, int, float, float]:
    exp = np.maximum(expected, 1e-9)
    stat = float(np.sum((observed - exp) ** 2 / exp))
    dof = max(len(observed) - 1, 1)
    p = float(chi2.sf(stat, dof))
    return stat, dof, p, p_to_z(p)


def main() -> None:
    for p in [TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)
    ref = MOD.prepare(MOD.quality(pd.read_csv(MOD.REFERENCE, low_memory=False)))
    # Fit each calibration only on the corresponding stream's trigger-plus-
    # plateau reference events. Other stream rows are left empty deliberately.
    ref_streams = []
    for stream in ["MET", "JetHT", "SingleMuon"]:
        tmp = selected(ref[ref["primary_dataset"].eq(stream)], stream, data=True)
        ref_streams.append(tmp)
    calibration_ref = pd.concat(ref_streams, ignore_index=True)
    calibrations, thresholds = MOD.fit_reference(calibration_ref)
    (TABLES / "01_stream_matched_calibration.json").write_text(json.dumps(calibrations, indent=2), encoding="utf-8")
    thresholds.to_csv(TABLES / "02_stream_matched_thresholds.csv", index=False)

    real_raw = MOD.prepare(MOD.quality(pd.read_csv(MOD.REAL, low_memory=False)))
    real_raw = real_raw[real_raw["sample_validation_id"].isin(SAMPLES) & real_raw["primary_dataset"].isin(["MET", "JetHT", "SingleMuon"])].copy()
    real_tagged = MOD.tag(real_raw, calibrations, thresholds)
    real_tagged.to_csv(TABLES / "03_stream_matched_real_scored.csv", index=False)

    mc_raw = MOD.prepare(MOD.quality(pd.read_csv(MOD.SM_EVENTS, low_memory=False)), dataset_override="MET")
    tiers = pd.read_csv(MOD.TIERS)
    usable = tiers[tiers["normalisation_tier"].isin(PROCESS_TIERS)]
    mc_raw = mc_raw[mc_raw["record_id"].isin(usable["record_id"])].copy()
    scale = usable.set_index("record_id")["base_event_scale_for_generator_weight"].to_dict()
    mc_raw["template_weight"] = pd.to_numeric(mc_raw["generator_weight"], errors="coerce").fillna(0.0) * mc_raw["record_id"].map(scale).fillna(0.0)
    mc_streams = []
    for stream in ["MET", "JetHT", "SingleMuon"]:
        tag = MOD.tag(mc_raw.assign(primary_dataset=stream), calibrations, thresholds)
        tag["calibration_stream"] = stream
        mc_streams.append(tag)
    mc = pd.concat(mc_streams, ignore_index=True)
    mc.to_csv(TABLES / "04_stream_matched_sm_scored.csv", index=False)

    processes = sorted(mc["process_family"].unique().tolist())
    coeff_rows, control_rows, met_rows, channel_rows = [], [], [], []
    for sample in SAMPLES:
        real = real_tagged[real_tagged["sample_validation_id"].eq(sample)]
        coeff, a, y, labels = fit_nnls(real, mc, processes)
        pred = a @ coeff
        stat, dof, p, z = closure(y, pred)
        control_rows.append({"sample_validation_id": sample, "control_chi2": stat, "control_dof": dof, "control_p": p, "control_Z": z, "controls_closed_at_p_ge_0_05": bool(p >= 0.05)})
        for proc, val in zip(processes, coeff):
            coeff_rows.append({"sample_validation_id": sample, "process_family": proc, "fitted_coefficient": val})
        for label, obs, exp in zip(labels, y, pred):
            stream, band = label.split(":", 1)
            channel_rows.append({"sample_validation_id": sample, "stage": "control_fit", "stream": stream, "microband": band, "observed": obs, "expected": exp})

        obs_met = counts(selected(real[real["primary_dataset"].eq("MET")], "MET", data=True))
        pred_met = np.zeros(len(BANDS), dtype=float)
        for val, proc in zip(coeff, processes):
            sim = selected(mc[(mc["calibration_stream"].eq("MET")) & mc["process_family"].eq(proc)], "MET", data=False)
            pred_met += val * counts(sim, "template_weight")
        ms, mdof, mp, mz = closure(obs_met, pred_met)
        met_rows.append({
            "sample_validation_id": sample,
            "control_fit_closed": bool(p >= 0.05),
            "met_chi2": ms, "met_dof": mdof, "met_p": mp, "met_Z": mz,
            "met_upper_observed": float(obs_met[1:].sum()),
            "met_upper_expected": float(pred_met[1:].sum()),
            "met_upper_ratio": float(obs_met[1:].sum() / max(pred_met[1:].sum(), 1e-12)),
            "valid_transfer": bool(p >= 0.05),
        })
        for band, obs, exp in zip(BANDS, obs_met, pred_met):
            channel_rows.append({"sample_validation_id": sample, "stage": "MET_transfer", "stream": "MET", "microband": band, "observed": obs, "expected": exp})

    coeff_df, control_df, met_df, channel_df = map(pd.DataFrame, [coeff_rows, control_rows, met_rows, channel_rows])
    coeff_df.to_csv(TABLES / "05_fitted_process_coefficients.csv", index=False)
    control_df.to_csv(TABLES / "06_stream_matched_control_closure.csv", index=False)
    met_df.to_csv(TABLES / "07_stream_matched_MET_transfer.csv", index=False)
    channel_df.to_csv(TABLES / "08_stream_matched_channels.csv", index=False)
    report = f"""# Stream-Matched Plateau Control Transfer

## Fixed Selections

- MET: observed MET trigger and MET >= 150 GeV.
- JetHT: observed HT trigger, HT >= 900 GeV and at least one jet.
- SingleMuon: observed muon trigger and at least one reconstructed muon.

The same offline cuts are applied to MC. Trigger bits are retained only for
data because the broad MC trigger aggregates are known to be non-discriminating.

## Control Closure

{control_df.to_markdown(index=False, floatfmt='.6g')}

## MET Transfer

{met_df.to_markdown(index=False, floatfmt='.6g')}

## Interpretation Rule

Only rows with `control_fit_closed=True` can be read as a valid transfer test.
If none close, the remaining limitation is MC selection/process modelling, not
the N-Frame score itself.
"""
    (REPORTS / "01_STREAM_MATCHED_PLATEAU_CONTROL_TRANSFER.md").write_text(report, encoding="utf-8")
    print(control_df.to_string(index=False))
    print(met_df.to_string(index=False))
    print(REPORTS / "01_STREAM_MATCHED_PLATEAU_CONTROL_TRANSFER.md")


if __name__ == "__main__":
    main()
