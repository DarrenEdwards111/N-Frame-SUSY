from __future__ import annotations

"""Run a transparent likelihood stress test on the frozen OPQ remote samples.

The inputs are compact feature CSVs made from remote CMS MiniAOD reads. This is
not an official CMS SM likelihood: no luminosity-normalised process-complete MC
template exists for this exact feature-equivalent OPQ construction. It instead
quantifies how much independent, control-derived per-band transfer uncertainty
is required before the trace/control shape difference is no longer significant.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs_opq_remote_holdout_statistical_robustness" / "tables" / "02_opq_heldout_microband_vectors.csv"
OUT = ROOT / "outputs_opq_remote_control_shape_likelihood_stress"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

SAMPLES = ["Run2015D_remote_mht_aware_holdout", "Run2016H_remote_mht_aware"]
BANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
UNCERTAINTIES = [0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00]


def p_to_z(value: float) -> float:
    return float(norm.isf(float(np.clip(value, np.nextafter(0, 1), 1.0))))


def build_model(sample: pd.DataFrame, rel_transfer_unc: float) -> tuple[pyhf.Model, list[float], pd.DataFrame]:
    sample = sample.set_index("microband").loc[BANDS].reset_index()
    # A control-derived band transfer factor: normalise to the q90-95 bin and
    # predict the MET trace shape from the complete JetHT+SingleMuon controls.
    trace = sample["trace_count"].to_numpy(float)
    control = sample["control_count"].to_numpy(float)
    scale = trace[0] / max(control[0], 1.0)
    expected = np.maximum(control * scale, 1e-9)

    channels = []
    observations: dict[str, float] = {}
    for band, obs, exp in zip(BANDS, trace, expected):
        channel = str(band)
        observations[channel] = float(obs)
        modifiers = [
            {"name": f"control_stat_{band}", "type": "staterror", "data": [float(max(np.sqrt(exp), 1.0))]},
        ]
        if rel_transfer_unc > 0:
            modifiers.insert(
                0,
                {
                    "name": f"transfer_shape_{band}",
                    "type": "normsys",
                    "data": {"hi": 1 + rel_transfer_unc, "lo": max(1 - rel_transfer_unc, 1e-6)},
                },
            )
        signal = exp if band != "q90_95" else 0.0
        channels.append(
            {
                "name": channel,
                "samples": [
                    {
                        "name": "opq_trace_difference",
                        "data": [float(signal)],
                        "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}],
                    },
                    {"name": "control_transferred_background", "data": [float(exp)], "modifiers": modifiers},
                ],
            }
        )
    model = pyhf.Model(
        {"channels": channels, "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}]},
        poi_name="mu_trace",
    )
    data = [observations[name] for name in model.config.channels] + model.config.auxdata
    audit = pd.DataFrame({"microband": BANDS, "observed_trace": trace, "control_transferred_expected": expected})
    return model, data, audit


def main() -> None:
    for path in [TABLES, REPORTS, JSON]:
        path.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(INPUT)
    rows = []
    audits = []
    for sample_id in SAMPLES:
        sample = raw[raw["sample_validation_id"].eq(sample_id)].copy()
        if set(BANDS) - set(sample["microband"]):
            raise RuntimeError(f"Missing microbands for {sample_id}")
        for unc in UNCERTAINTIES:
            model, data, audit = build_model(sample, unc)
            p_value = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
            fit = pyhf.infer.mle.fit(data, model)
            params = {name: float(fit[i]) for i, name in enumerate(model.config.par_order)}
            rows.append(
                {
                    "sample_validation_id": sample_id,
                    "relative_control_to_trace_transfer_uncertainty": unc,
                    "background_only_p": p_value,
                    "background_only_Z": p_to_z(p_value),
                    "fit_mu_trace": params.get("mu_trace", np.nan),
                }
            )
            audit["sample_validation_id"] = sample_id
            audit["relative_control_to_trace_transfer_uncertainty"] = unc
            audits.append(audit)
            (JSON / f"{sample_id}_transfer_unc_{unc:.2f}.json").write_text(
                json.dumps(model.spec, indent=2), encoding="utf-8"
            )

    summary = pd.DataFrame(rows)
    audit_df = pd.concat(audits, ignore_index=True)
    threshold = (
        summary[summary["background_only_Z"].lt(5)]
        .groupby("sample_validation_id", as_index=False)["relative_control_to_trace_transfer_uncertainty"]
        .min()
        .rename(columns={"relative_control_to_trace_transfer_uncertainty": "first_tested_uncertainty_below_Z5"})
    )
    summary.to_csv(TABLES / "01_opq_control_shape_likelihood_stress.csv", index=False)
    audit_df.to_csv(TABLES / "02_opq_control_transferred_templates.csv", index=False)
    threshold.to_csv(TABLES / "03_opq_transfer_uncertainty_thresholds.csv", index=False)

    report = f"""# Frozen OPQ Remote Control-Shape Likelihood Stress Test

## Purpose

This evaluates the frozen OPQ score on the two held-out remote CMS samples with
a HistFactory/pyhf likelihood. Each score microband is a channel. The background
shape is transferred from the complete JetHT plus SingleMuon control vector,
normalised in q90-95, and then given independent control-to-trace transfer
uncertainties.

The score is fixed as:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

## Results

{summary.to_markdown(index=False, floatfmt='.6g')}

## First Tested Uncertainty That Lowers the Shape Test Below 5 Sigma

{threshold.to_markdown(index=False, floatfmt='.6g')}

## Scope and Limit

This is deliberately a **stress test**, not an official CMS background-only
measurement. The input is real CMS data and the controls are explicitly used,
but the transfer uncertainty is scanned rather than derived from a complete
luminosity-weighted, process-complete Standard Model simulation and detector
systematic model. It answers a useful intermediate question: how large a
control-to-trace shape uncertainty is needed to remove the frozen OPQ contrast.
It cannot establish a particle discovery or a hidden-sector interpretation.
"""
    (REPORTS / "01_OPQ_REMOTE_CONTROL_SHAPE_LIKELIHOOD_STRESS.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(threshold.to_string(index=False))
    print(REPORTS / "01_OPQ_REMOTE_CONTROL_SHAPE_LIKELIHOOD_STRESS.md")


if __name__ == "__main__":
    main()
