from __future__ import annotations

"""Control-calibrated process-mixture transfer test for frozen OPQ bands.

Only JetHT and SingleMuon bands are used to fit non-negative SM process
coefficients. The fitted mixture is then transferred, without MET data in the
fit, to predict the MET 0-jet frozen-reference microbands.
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
OUT = ROOT / "outputs_frozen_reference_control_mixture_transfer"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

PROCESS_TIERS = ["exact_record_sumw", "metadata_unit_weight_record"]
SAMPLES = MOD.SAMPLES
BANDS = MOD.BANDS
UPPER = MOD.UPPER


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def real_region(frame: pd.DataFrame, region: str) -> pd.DataFrame:
    if region == "JetHT_control":
        return frame[frame["primary_dataset"].eq("JetHT") & frame["jet_bin"].isin(["1to2jets", "3to4jets", "5plusjets"])]
    if region == "SingleMuon_control":
        return frame[frame["primary_dataset"].eq("SingleMuon")]
    if region == "MET_trace":
        return frame[frame["primary_dataset"].eq("MET") & frame["jet_bin"].eq("0jet")]
    raise ValueError(region)


def mc_region(frame: pd.DataFrame, region: str) -> pd.DataFrame:
    if region == "JetHT_control":
        return frame[frame["n_jets"].ge(1)]
    if region == "SingleMuon_control":
        return frame[frame["n_muons"].ge(1)]
    if region == "MET_trace":
        return frame[frame["n_jets"].le(0) & frame["n_muons"].le(0) & frame["n_electrons"].le(0)]
    raise ValueError(region)


def band_counts(frame: pd.DataFrame, weight: str | None = None) -> np.ndarray:
    if weight is None:
        return np.asarray([(frame["microband_frozen_reference"] == band).sum() for band in BANDS], dtype=float)
    return np.asarray(
        [frame.loc[frame["microband_frozen_reference"].eq(band), weight].sum() for band in BANDS],
        dtype=float,
    )


def fit_controls(real: pd.DataFrame, mc: pd.DataFrame, processes: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    rows = []
    target = []
    labels = []
    for region in ["JetHT_control", "SingleMuon_control"]:
        obs = band_counts(real_region(real, region))
        target.extend(obs)
        labels.extend([f"{region}:{band}" for band in BANDS])
        cols = []
        for process in processes:
            cols.append(band_counts(mc_region(mc[mc["process_family"].eq(process)], region), "template_weight"))
        rows.extend(np.column_stack(cols))
    a = np.asarray(rows, dtype=float)
    y = np.asarray(target, dtype=float)
    # Pearson-like weighting prevents the largest control bin dominating every
    # process coefficient while retaining Poisson-count scaling.
    scale = np.sqrt(np.maximum(y, 1.0))
    coeff, _resid = nnls(a / scale[:, None], y / scale)
    return coeff, a, y, labels


def chi2_readout(observed: np.ndarray, expected: np.ndarray) -> tuple[float, int, float, float]:
    expected = np.maximum(expected, 1e-9)
    stat = float(np.sum((observed - expected) ** 2 / expected))
    dof = max(len(observed) - 1, 1)
    p = float(chi2.sf(stat, dof))
    return stat, dof, p, p_to_z(p)


def main() -> None:
    for path in [TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)

    calibration = json.loads((MOD.TABLES / "01_frozen_reference_calibration.json").read_text(encoding="utf-8"))
    thresholds = pd.read_csv(MOD.TABLES / "02_frozen_reference_microband_thresholds.csv")
    real = pd.read_csv(MOD.TABLES / "03_heldout_real_events_frozen_reference_scored.csv", low_memory=False)
    # Re-tag MC for each stream calibration, so a JetHT or SingleMuon control
    # is compared using the same frozen numerical boundaries as that stream.
    mc_raw = MOD.prepare(MOD.quality(pd.read_csv(MOD.SM_EVENTS, low_memory=False)), dataset_override="MET")
    tiers = pd.read_csv(MOD.TIERS)
    usable = tiers[tiers["normalisation_tier"].isin(PROCESS_TIERS)].copy()
    mc_raw = mc_raw[mc_raw["record_id"].isin(usable["record_id"])].copy()
    scales = usable.set_index("record_id")["base_event_scale_for_generator_weight"].to_dict()
    mc_raw["template_weight"] = pd.to_numeric(mc_raw["generator_weight"], errors="coerce").fillna(0.0) * mc_raw["record_id"].map(scales).fillna(0.0)

    tagged_mc = []
    for dataset in ["MET", "JetHT", "SingleMuon"]:
        tagged = MOD.tag(mc_raw.assign(primary_dataset=dataset), calibration, thresholds, mc=False)
        tagged["calibration_stream"] = dataset
        tagged_mc.append(tagged)
    mc = pd.concat(tagged_mc, ignore_index=True)
    mc.to_csv(TABLES / "01_stream_calibrated_sm_events.csv", index=False)

    processes = sorted(mc["process_family"].dropna().unique().tolist())
    coefficient_rows = []
    control_rows = []
    transfer_rows = []
    channel_rows = []

    for sample_id in SAMPLES:
        real_sample = real[real["sample_validation_id"].eq(sample_id)].copy()
        # The MC template is common across data eras; only the data controls
        # determine the era-specific mixture coefficients.
        mc_controls = mc[mc["calibration_stream"].isin(["JetHT", "SingleMuon"])].copy()
        coeff, matrix, target, labels = fit_controls(real_sample, mc_controls, processes)
        predicted_controls = matrix @ coeff
        stat, dof, p, z = chi2_readout(target, predicted_controls)
        control_rows.append(
            {
                "sample_validation_id": sample_id,
                "fit_scope": "JetHT_and_SingleMuon_only",
                "control_chi2": stat,
                "control_dof": dof,
                "control_p": p,
                "control_Z": z,
                "controls_closed_at_p_ge_0_05": bool(p >= 0.05),
            }
        )
        for process, value in zip(processes, coeff):
            coefficient_rows.append({"sample_validation_id": sample_id, "process_family": process, "fitted_nonnegative_coefficient": value})
        for label, obs, exp in zip(labels, target, predicted_controls):
            region, band = label.split(":", 1)
            channel_rows.append({"sample_validation_id": sample_id, "fit_stage": "control_fit", "region": region, "microband": band, "observed": obs, "expected": exp})

        # Target prediction: MET calibration and MET 0-jet selection. No MET
        # counts were used to fit the coefficients above.
        mc_met = mc[mc["calibration_stream"].eq("MET")]
        pred_bands = np.zeros(len(BANDS), dtype=float)
        for value, process in zip(coeff, processes):
            pred_bands += value * band_counts(mc_region(mc_met[mc_met["process_family"].eq(process)], "MET_trace"), "template_weight")
        obs_bands = band_counts(real_region(real_sample, "MET_trace"))
        met_stat, met_dof, met_p, met_z = chi2_readout(obs_bands, pred_bands)
        upper_obs = float(obs_bands[1:].sum())
        upper_exp = float(pred_bands[1:].sum())
        upper_var = max(upper_exp, 1.0)
        upper_z = float((upper_obs - upper_exp) / np.sqrt(upper_var))
        transfer_rows.append(
            {
                "sample_validation_id": sample_id,
                "control_fit_closed": bool(p >= 0.05),
                "met_all_bands_chi2": met_stat,
                "met_all_bands_dof": met_dof,
                "met_all_bands_p": met_p,
                "met_all_bands_Z": met_z,
                "met_upper_observed": upper_obs,
                "met_upper_expected": upper_exp,
                "met_upper_obs_over_exp": upper_obs / max(upper_exp, 1e-12),
                "met_upper_naive_signed_Z_no_systematics": upper_z,
                "valid_MET_transfer_test": bool(p >= 0.05),
            }
        )
        for band, obs, exp in zip(BANDS, obs_bands, pred_bands):
            channel_rows.append({"sample_validation_id": sample_id, "fit_stage": "heldout_MET_prediction", "region": "MET_trace", "microband": band, "observed": obs, "expected": exp})

    coefficients = pd.DataFrame(coefficient_rows)
    controls = pd.DataFrame(control_rows)
    transfer = pd.DataFrame(transfer_rows)
    channels = pd.DataFrame(channel_rows)
    coefficients.to_csv(TABLES / "02_fitted_control_process_coefficients.csv", index=False)
    controls.to_csv(TABLES / "03_control_fit_closure.csv", index=False)
    transfer.to_csv(TABLES / "04_MET_transfer_prediction.csv", index=False)
    channels.to_csv(TABLES / "05_control_and_MET_channels.csv", index=False)

    report = f"""# Frozen-Reference Control-Mixture Transfer Test

## Purpose

This is the next validity test after the fixed-reference OPQ model showed that
the broad SM template did not close controls. For each held-out CMS era, the
non-negative process mixture is fitted using only JetHT and SingleMuon
microbands. The MET 0-jet microbands are then predicted without being used in
the fit.

The score calibration and numerical microband boundaries are frozen from the
original Run2016G reference sample.

## Control Closure

{controls.to_markdown(index=False, floatfmt='.6g')}

## MET Transfer Prediction

{transfer.to_markdown(index=False, floatfmt='.6g')}

## Interpretation Rule

A MET discrepancy is meaningful only for rows with `control_fit_closed=True`.
If the control fit does not close, a MET difference can still be ordinary
process-mixture, trigger, or detector-transfer mismatch. The naive signed Z is
diagnostic only: it has no systematic uncertainty model and is not a discovery
significance.
"""
    (REPORTS / "01_FROZEN_REFERENCE_CONTROL_MIXTURE_TRANSFER.md").write_text(report, encoding="utf-8")
    print(controls.to_string(index=False))
    print(transfer.to_string(index=False))
    print(REPORTS / "01_FROZEN_REFERENCE_CONTROL_MIXTURE_TRANSFER.md")


if __name__ == "__main__":
    main()
