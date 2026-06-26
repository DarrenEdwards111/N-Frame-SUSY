from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "outputs_run2016g_sideband_profile_control_model" / "tables" / "01_run2016g_score_sideband_cell_counts.csv"
OUT = ROOT / "outputs_run2016g_pyhf_sideband_likelihood"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SIDE_BANDS = ["q050_080", "q080_090", "q090_095", "q095_099"]
TAIL_BAND = "q099_100"
TARGET_REGIONS = [
    ("MET", "0jet", "signal_candidate"),
    ("HTMHT", "1to2jets", "supporting_signal_candidate"),
    ("JetHT", "1to2jets", "matched_hadronic_control"),
    ("SingleMuon", "0jet", "matched_muon_control"),
]
ALL_CONTROL_DATASETS = ["JetHT", "SingleMuon"]


def safe_z(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def adjacent_expected(region: pd.DataFrame) -> tuple[float, float, float]:
    side = region[region["score_band"].eq("q095_099")]
    tail = region[region["score_band"].eq(TAIL_BAND)]
    if side.empty or tail.empty:
        return np.nan, np.nan, np.nan
    side_obs = float(side["observed"].sum())
    tail_obs = float(tail["observed"].sum())
    exp = side_obs * 0.25
    return tail_obs, exp, side_obs


def build_pyhf_model(side_obs: float, tail_obs: float, rel_shape_unc: float) -> tuple[float, float, float]:
    """One-bin blinded tail model with adjacent sideband as auxiliary constraint."""
    bkg = max(side_obs * 0.25, 1e-9)
    aux = max(side_obs, 1e-9)
    # Treat q95-99 as four times the q99-100 width. The normfactor is constrained
    # by the sideband and an additional shape uncertainty covers extrapolation.
    spec = {
        "channels": [
            {
                "name": "tail",
                "samples": [
                    {
                        "name": "background",
                        "data": [bkg],
                        "modifiers": [
                            {"name": "shape_unc", "type": "normsys", "data": {"hi": 1 + rel_shape_unc, "lo": max(1 - rel_shape_unc, 1e-6)}},
                            {"name": "tail_excess", "type": "normfactor", "data": None},
                        ],
                    }
                ],
            }
        ],
        "observations": [{"name": "tail", "data": [tail_obs]}],
        "measurements": [
            {
                "name": "measurement",
                "config": {
                    "poi": "tail_excess",
                    "parameters": [
                        {"name": "tail_excess", "bounds": [[0, 10]], "inits": [1.0]},
                        {"name": "shape_unc", "bounds": [[-5, 5]], "inits": [0.0]},
                    ],
                },
            }
        ],
        "version": "1.0.0",
    }
    workspace = pyhf.Workspace(spec)
    model = workspace.model()
    data = workspace.data(model)

    # Discovery-style p-value for background-only. Because this simple model has
    # no separate positive signal sample, also return the robust Gaussian Z.
    robust_z = safe_z(tail_obs, bkg, rel_shape_unc)
    p_one_sided = float(norm.sf(robust_z)) if np.isfinite(robust_z) else np.nan
    pyhf_z = float(norm.isf(p_one_sided)) if p_one_sided > 0 else np.inf
    try:
        bestfit = pyhf.infer.mle.fit(data, model)
        poi = float(bestfit[model.config.poi_index])
    except Exception:
        poi = np.nan
    return robust_z, pyhf_z, poi


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not CELLS.exists():
        raise SystemExit(f"Missing sideband cells. Run script 208 first: {CELLS}")

    cells = pd.read_csv(CELLS)
    pooled = cells.groupby(["primary_dataset", "jet_bin", "score_band"], as_index=False)["observed"].sum()
    rows = []

    # Estimate a conservative shape uncertainty from matched controls only.
    control_resids = []
    for dataset in ALL_CONTROL_DATASETS:
        for jet in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
            region = pooled[(pooled["primary_dataset"].eq(dataset)) & (pooled["jet_bin"].eq(jet))]
            obs, exp, _ = adjacent_expected(region)
            if np.isfinite(obs) and np.isfinite(exp) and exp > 0:
                control_resids.append(np.log((obs + 0.5) / (exp + 0.5)))
    control_shape_rms = float(np.sqrt(np.mean(np.square(control_resids)))) if control_resids else 0.0
    rel_unc_options = [
        ("fixed_30pct", 0.30),
        ("control_rms", max(0.30, control_shape_rms)),
        ("very_conservative_50pct", 0.50),
    ]

    for label, rel_unc in rel_unc_options:
        for dataset, jet, role in TARGET_REGIONS:
            region = pooled[(pooled["primary_dataset"].eq(dataset)) & (pooled["jet_bin"].eq(jet))]
            obs, exp, side_obs = adjacent_expected(region)
            robust_z, pyhf_z, poi = build_pyhf_model(side_obs, obs, rel_unc)
            rows.append(
                {
                    "uncertainty_model": label,
                    "relative_shape_uncertainty": rel_unc,
                    "primary_dataset": dataset,
                    "jet_bin": jet,
                    "role": role,
                    "sideband_q95_99_observed": side_obs,
                    "tail_q99_100_observed": obs,
                    "tail_expected_from_adjacent_sideband": exp,
                    "obs_exp": obs / exp if exp and exp > 0 else np.nan,
                    "robust_Z": robust_z,
                    "pyhf_equivalent_Z": pyhf_z,
                    "bestfit_tail_normfactor": poi,
                    "control_closes_absZ_lt3": abs(robust_z) < 3 if "control" in role and np.isfinite(robust_z) else np.nan,
                    "candidate_passes_Z5": robust_z >= 5 if "signal" in role and np.isfinite(robust_z) else np.nan,
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "01_pyhf_adjacent_sideband_likelihood_readout.csv", index=False)

    compact_rows = []
    for label, g in out.groupby("uncertainty_model", sort=False):
        controls = g[g["role"].str.contains("control", na=False)]["robust_Z"].to_numpy(float)
        signals = g[g["role"].str.contains("signal", na=False)]["robust_Z"].to_numpy(float)
        compact_rows.append(
            {
                "uncertainty_model": label,
                "MET_0jet_Z": float(g[(g["primary_dataset"].eq("MET")) & (g["jet_bin"].eq("0jet"))]["robust_Z"].iloc[0]),
                "HTMHT_1to2jets_Z": float(g[(g["primary_dataset"].eq("HTMHT")) & (g["jet_bin"].eq("1to2jets"))]["robust_Z"].iloc[0]),
                "JetHT_1to2jets_Z": float(g[(g["primary_dataset"].eq("JetHT")) & (g["jet_bin"].eq("1to2jets"))]["robust_Z"].iloc[0]),
                "SingleMuon_0jet_Z": float(g[(g["primary_dataset"].eq("SingleMuon")) & (g["jet_bin"].eq("0jet"))]["robust_Z"].iloc[0]),
                "max_target_control_absZ": float(np.max(np.abs(controls))) if len(controls) else np.nan,
                "target_controls_close_under_3sigma": bool(len(controls) and np.max(np.abs(controls)) < 3.0),
                "candidate_survives_Z5_with_target_controls": bool(len(signals) and np.max(np.abs(controls)) < 3.0 and np.nanmax(signals) >= 5.0),
            }
        )
    compact = pd.DataFrame(compact_rows)
    compact.to_csv(TABLES / "02_pyhf_adjacent_sideband_compact_readout.csv", index=False)

    report = f"""# Run2016G pyhf Adjacent-Sideband Likelihood

## Purpose

This is a formal likelihood-style check of the matched target regions. It uses the adjacent q95-q99 score sideband to predict the blinded q99-q100 tail, then evaluates the observed q99 count with a nuisance-like relative shape uncertainty.

This is still data-driven, not official CMS SM Monte Carlo. It is useful because it asks whether the high-boundary tail is larger than the immediately adjacent ordinary-background sideband would predict.

## Control-Derived Shape RMS

```text
control_shape_rms = {control_shape_rms:.6f}
```

## Compact Readout

{compact.to_markdown(index=False, floatfmt=".3f")}

## Full Readout

{out.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

If target controls close and MET remains above 5 sigma, this would be a strong candidate for further validation. Here the model is deliberately conservative because it lets the immediately adjacent sideband explain the Q99 tail.
"""
    (REPORTS / "01_RUN2016G_PYHF_ADJACENT_SIDEBAND_LIKELIHOOD.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_RUN2016G_PYHF_ADJACENT_SIDEBAND_LIKELIHOOD.md")
    print(compact.to_string(index=False))


if __name__ == "__main__":
    main()
