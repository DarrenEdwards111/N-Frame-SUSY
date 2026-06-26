from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import norm

import pyhf


ROOT = Path(__file__).resolve().parents[1]
IN_READOUT = ROOT / "outputs_sm_robustness_extension" / "tables" / "04_augmented_sm_template_target_readout.csv"
OUT = ROOT / "outputs_pyhf_augmented_sm_trace_likelihood"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

TRACE_DATASET = "MET"
TRACE_JET_BIN = "0jet"
CONTROL_ROWS = [("JetHT", "1to2jets"), ("SingleMuon", "0jet")]
SUPPORT_ROWS = [("HTMHT", "1to2jets")]
SCENARIO = "Run2016G_plus_Run2016H"
MODES = ["all_weighted_sm_augmented", "full_component_only_augmented"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, JSON]:
        path.mkdir(parents=True, exist_ok=True)


def one_sided_z_from_p(p: float) -> float:
    p = float(np.clip(p, np.nextafter(0, 1), 1.0))
    return float(norm.isf(p))


def gaussian_z(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def read_target_rows(mode: str) -> pd.DataFrame:
    df = pd.read_csv(IN_READOUT)
    sub = df[(df["sm_template_mode"].eq(mode)) & (df["scenario"].eq(SCENARIO))].copy()
    required = [(TRACE_DATASET, TRACE_JET_BIN), *SUPPORT_ROWS, *CONTROL_ROWS]
    rows = []
    for dataset, jet_bin in required:
        hit = sub[(sub["primary_dataset"].eq(dataset)) & (sub["jet_bin"].eq(jet_bin))]
        if hit.empty:
            raise RuntimeError(f"Missing readout row for {mode} {dataset} {jet_bin}")
        rows.append(hit.iloc[0].to_dict())
    out = pd.DataFrame(rows)
    for col in ["q99_observed", "q99_expected_sm_shape", "relative_shape_uncertainty_needed_for_controls"]:
        out[col] = pd.to_numeric(out[col], errors="raise")
    return out


def build_pyhf_model(rows: pd.DataFrame, rel_unc: float, include_htmht_support: bool) -> tuple[pyhf.Model, list[float], list[str]]:
    channels = []
    observations = []
    labels = []

    for r in rows.itertuples(index=False):
        dataset = str(r.primary_dataset)
        jet_bin = str(r.jet_bin)
        if (dataset, jet_bin) in SUPPORT_ROWS and not include_htmht_support:
            continue
        obs = float(r.q99_observed)
        bkg = max(float(r.q99_expected_sm_shape), 1e-9)
        is_trace = dataset == TRACE_DATASET and jet_bin == TRACE_JET_BIN
        labels.append(f"{dataset}_{jet_bin}")
        observations.append(obs)

        # Signal-like excess only in the MET trace channel. The POI scales the
        # expected SM trace yield, so mu roughly means "extra SM-equivalent
        # trace units"; testing mu=0 is the background-only discovery test.
        signal_yield = bkg if is_trace else 0.0
        samples = [
            {
                "name": "nframe_trace_excess",
                "data": [signal_yield],
                "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}],
            },
            {
                "name": "sm_background",
                "data": [bkg],
                "modifiers": [
                    {
                        "name": "correlated_sm_shape",
                        "type": "normsys",
                        "data": {"hi": 1.0 + rel_unc, "lo": max(1.0 - rel_unc, 1e-6)},
                    },
                    {
                        "name": f"mcstat_{dataset}_{jet_bin}",
                        "type": "staterror",
                                               "data": [float(max(np.sqrt(bkg), 1.0))],
                    },
                ],
            },
        ]
        channels.append({"name": labels[-1], "samples": samples})

    spec = {
        "channels": channels,
        "parameters": [
            {
                "name": "mu_trace",
                "bounds": [[0.0, 20.0]],
                "inits": [0.0],
            }
        ],
    }
    model = pyhf.Model(spec, poi_name="mu_trace")
    obs_by_label = dict(zip(labels, observations))
    ordered_observations = []
    for channel_name in model.config.channels:
        ordered_observations.extend([obs_by_label[channel_name]])
    data = pyhf.tensorlib.astensor(ordered_observations + model.config.auxdata)
    return model, data, labels


def run_pyhf(model: pyhf.Model, data) -> dict[str, float]:
    # Discovery-style background-only p-value for mu=0 using q0.
    p_value = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
    pars = pyhf.infer.mle.fit(data, model)
    par_map = {name: float(pars[i]) for i, name in enumerate(model.config.par_order)}
    return {
        "pyhf_background_only_p": p_value,
        "pyhf_background_only_Z": one_sided_z_from_p(p_value),
        "fit_mu_trace": par_map.get("mu_trace", np.nan),
        "fit_correlated_sm_shape": par_map.get("correlated_sm_shape", np.nan),
    }


def run_mode(mode: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = read_target_rows(mode)
    rel_unc = float(rows["relative_shape_uncertainty_needed_for_controls"].iloc[0])
    summaries = []
    channel_rows = []

    for include_htmht in [False, True]:
        model, data, labels = build_pyhf_model(rows, rel_unc, include_htmht_support=include_htmht)
        result = run_pyhf(model, data)
        variant = "MET_plus_controls" if not include_htmht else "MET_HTMHT_plus_controls"

        trace = rows[(rows["primary_dataset"].eq(TRACE_DATASET)) & (rows["jet_bin"].eq(TRACE_JET_BIN))].iloc[0]
        controls = rows[rows.apply(lambda r: (r["primary_dataset"], r["jet_bin"]) in CONTROL_ROWS, axis=1)]
        max_control_z = max(abs(gaussian_z(r.q99_observed, r.q99_expected_sm_shape, rel_unc)) for r in controls.itertuples())
        summaries.append(
            {
                "sm_template_mode": mode,
                "scenario": SCENARIO,
                "likelihood_variant": variant,
                "relative_shape_uncertainty": rel_unc,
                "MET_0jet_observed": float(trace.q99_observed),
                "MET_0jet_expected": float(trace.q99_expected_sm_shape),
                "MET_0jet_gaussian_Z": gaussian_z(float(trace.q99_observed), float(trace.q99_expected_sm_shape), rel_unc),
                "max_control_abs_gaussian_Z": max_control_z,
                **result,
                "pyhf_version": pyhf.__version__,
            }
        )
        spec_path = JSON / f"pyhf_model_{mode}_{variant}.json"
        spec_path.write_text(json.dumps(model.spec, indent=2), encoding="utf-8")
        for r in rows.itertuples(index=False):
            if (str(r.primary_dataset), str(r.jet_bin)) in SUPPORT_ROWS and not include_htmht:
                continue
            channel_rows.append(
                {
                    "sm_template_mode": mode,
                    "likelihood_variant": variant,
                    "primary_dataset": r.primary_dataset,
                    "jet_bin": r.jet_bin,
                    "role": r.role,
                    "observed": float(r.q99_observed),
                    "expected_sm": float(r.q99_expected_sm_shape),
                    "obs_exp": float(r.obs_exp),
                    "gaussian_Z": gaussian_z(float(r.q99_observed), float(r.q99_expected_sm_shape), rel_unc),
                }
            )
    return pd.DataFrame(summaries), pd.DataFrame(channel_rows)


def main() -> None:
    ensure_dirs()
    all_summaries = []
    all_channels = []
    for mode in MODES:
        summary, channels = run_mode(mode)
        all_summaries.append(summary)
        all_channels.append(channels)

    summary = pd.concat(all_summaries, ignore_index=True)
    channels = pd.concat(all_channels, ignore_index=True)
    summary.to_csv(TABLES / "01_pyhf_trace_likelihood_summary.csv", index=False)
    channels.to_csv(TABLES / "02_pyhf_trace_likelihood_channels.csv", index=False)

    best = summary[
        (summary["sm_template_mode"].eq("all_weighted_sm_augmented"))
        & (summary["likelihood_variant"].eq("MET_plus_controls"))
    ].iloc[0]

    report = f"""# pyhf Augmented-SM N-Frame Trace Likelihood

## Purpose

This stage converts the augmented SM robustness readout into a HistFactory-style pyhf likelihood. The tested trace is the frozen N-Frame Q99 MET 0-jet region in combined Run2016G plus Run2016H. JetHT 1-2 jets and SingleMuon 0-jet are included as controls, not ignored.

This is still a boundary-trace test, not a direct SUSY-particle discovery test.

## Model

- Signal-like parameter: `mu_trace`, an excess-yield parameter active only in the MET 0-jet trace channel.
- Background: augmented weighted Standard Model template from W/Z+jets plus hard-QCD robustness extension.
- Correlated nuisance: `correlated_sm_shape`, using the control-calibrated shape uncertainty from the augmented SM readout.
- Per-channel finite-template uncertainty: `staterror` with Poisson-scale uncertainty on the expected SM count.
- Discovery test: background-only `mu_trace = 0`, pyhf `q0`.

## Main Result

For `all_weighted_sm_augmented`, MET plus controls:

- MET 0-jet observed: {best.MET_0jet_observed:.0f}
- MET 0-jet expected SM: {best.MET_0jet_expected:.3f}
- Control-calibrated shape uncertainty: {100 * best.relative_shape_uncertainty:.2f}%
- Gaussian cross-check Z: {best.MET_0jet_gaussian_Z:.3f}
- pyhf background-only p-value: {best.pyhf_background_only_p:.3e}
- pyhf sigma-equivalent Z: {best.pyhf_background_only_Z:.3f}
- Best-fit trace excess yield `mu_trace`: {best.fit_mu_trace:.3f}
- Fitted correlated SM-shape nuisance: {best.fit_correlated_sm_shape:.3f}
- Max control absolute Gaussian Z: {best.max_control_abs_gaussian_Z:.3f}

## Summary Table

{summary.to_markdown(index=False, floatfmt=".6g")}

## Channel Table

{channels.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The likelihood asks whether the augmented SM background model, with a correlated control-calibrated shape nuisance and finite-template uncertainties, can absorb the MET 0-jet N-Frame trace while the controls remain closed. A large positive pyhf Z means the background-only model still struggles specifically in the MET trace channel.

This strengthens or weakens the boundary-trace claim depending on whether the pyhf Z remains high. It should not be described as direct evidence for supersymmetric particles.
"""
    (REPORTS / "01_PYHF_AUGMENTED_SM_TRACE_LIKELIHOOD.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_PYHF_AUGMENTED_SM_TRACE_LIKELIHOOD.md")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
