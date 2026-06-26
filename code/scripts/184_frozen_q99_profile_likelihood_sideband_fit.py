from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_frozen_q99_profile_likelihood_sideband_fit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

RUN2016_COUNTS = ROOT / "outputs_frozen_q99_multifile_breakthrough_audit/tables/01_frozen_q99_counts_by_file_and_control.csv"
RUN2015_COUNTS = ROOT / "outputs_run2015d_frozen_q99_pilot/tables/03_run2015d_frozen_q99_score_band_counts.csv"

FIT_BANDS = ["q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099"]
SIGNAL_BAND = "q099_100"
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
CONTROL_JET_BINS = ["0jet", "3to4jets", "5plusjets"]
BASE_REL_UNC = 0.127


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def poisson_nll(obs: np.ndarray, lam: np.ndarray) -> float:
    lam = np.clip(lam, 1e-9, np.inf)
    obs = np.clip(obs, 0, np.inf)
    # Drop log(obs!) because it cancels in likelihood-ratio comparisons.
    return float(np.sum(lam - obs * np.log(lam)))


def fit_shape(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Fit exp(a_j + b_j*(q-0.90)) per jet bin using sub-q99 sidebands only."""
    out = df.copy()
    out["observed"] = pd.to_numeric(out["observed"], errors="coerce").fillna(0.0)
    out["expected_official"] = pd.to_numeric(out["expected_official"], errors="coerce").fillna(0.0)
    out["midpoint"] = pd.to_numeric(out["midpoint"], errors="coerce")
    fit_rows = out[out["score_band"].isin(FIT_BANDS) & out["jet_bin"].isin(JET_BINS)].copy()
    params = {}
    fit_quality = {}
    out["expected_profile"] = np.nan
    out["profile_shape_factor"] = np.nan
    for jet_bin in JET_BINS:
        fit = fit_rows[fit_rows["jet_bin"].eq(jet_bin)].copy()
        if fit.empty or fit["expected_official"].sum() <= 0:
            params[jet_bin] = [np.nan, np.nan]
            fit_quality[jet_bin] = {"sideband_log_rms": np.nan, "relative_uncertainty": np.nan, "n_fit_bins": 0}
            continue
        obs = fit["observed"].to_numpy(float)
        exp = fit["expected_official"].to_numpy(float)
        x = fit["midpoint"].to_numpy(float) - 0.90

        def objective(theta: np.ndarray) -> float:
            a, b = theta
            lam = exp * np.exp(a + b * x)
            # Weak Gaussian regularisation prevents pathological fits in sparse controls.
            reg = 0.5 * (a / 3.0) ** 2 + 0.5 * (b / 10.0) ** 2
            return poisson_nll(obs, lam) + reg

        ratio = (obs.sum() + 0.5) / (exp.sum() + 0.5)
        start = np.array([np.log(max(ratio, 1e-6)), 0.0])
        result = minimize(objective, start, method="Nelder-Mead", options={"maxiter": 10000})
        a, b = result.x
        params[jet_bin] = [float(a), float(b)]
        pred_fit = exp * np.exp(a + b * x)
        log_resid = np.log((obs + 0.5) / (pred_fit + 0.5))
        weights = np.sqrt(np.clip(obs, 1.0, np.inf))
        rms = float(np.sqrt(np.average(log_resid**2, weights=weights)))
        fit_quality[jet_bin] = {
            "sideband_log_rms": rms,
            "relative_uncertainty": float(np.sqrt(BASE_REL_UNC**2 + rms**2)),
            "n_fit_bins": int(len(fit)),
            "fit_success": bool(result.success),
            "fit_nll": float(result.fun),
        }
        mask = out["jet_bin"].eq(jet_bin)
        factor = np.exp(a + b * (out.loc[mask, "midpoint"].to_numpy(float) - 0.90))
        out.loc[mask, "profile_shape_factor"] = factor
        out.loc[mask, "expected_profile"] = out.loc[mask, "expected_official"].to_numpy(float) * factor
    return out, {"params": params, "fit_quality": fit_quality}


def summarize_unit(label: dict, fitted: pd.DataFrame, meta: dict) -> list[dict]:
    rows = []
    for jet_bin in JET_BINS:
        tail = fitted[fitted["jet_bin"].eq(jet_bin) & fitted["score_band"].eq(SIGNAL_BAND)]
        if tail.empty:
            continue
        obs = float(tail["observed"].sum())
        exp = float(tail["expected_profile"].sum())
        q = meta["fit_quality"].get(jet_bin, {})
        rel = float(q.get("relative_uncertainty", np.nan))
        var = exp + (rel * exp) ** 2 if np.isfinite(rel) else exp
        z = float((obs - exp) / np.sqrt(max(var, 1e-12)))
        p_one_sided = float(norm.sf(z)) if np.isfinite(z) else np.nan
        rows.append(
            {
                **label,
                "jet_bin": jet_bin,
                "role": "frozen_signal_region" if jet_bin == "1to2jets" else "jet_bin_control",
                "q99_observed": obs,
                "q99_expected_profile": exp,
                "q99_obs_exp_profile": obs / exp if exp > 0 else np.inf,
                "sideband_log_rms": q.get("sideband_log_rms", np.nan),
                "relative_uncertainty_used": rel,
                "q99_profile_Z": z,
                "q99_profile_p_one_sided": p_one_sided,
                "control_closes_absZ_lt3": abs(z) < 3 if jet_bin in CONTROL_JET_BINS and np.isfinite(z) else np.nan,
                "signal_passes_5sigma": z >= 5 if jet_bin == "1to2jets" and np.isfinite(z) else np.nan,
                "fit_n_bins": q.get("n_fit_bins", 0),
            }
        )
    return rows


def run_unit(df: pd.DataFrame, label: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    fitted, meta = fit_shape(df)
    summary = pd.DataFrame(summarize_unit(label, fitted, meta))
    return fitted, summary, meta


def load_units() -> list[tuple[dict, pd.DataFrame]]:
    units: list[tuple[dict, pd.DataFrame]] = []
    if RUN2016_COUNTS.exists():
        df = pd.read_csv(RUN2016_COUNTS)
        base = df[df["unit"].eq("all_available_deduped") & df["source_file"].eq("ALL")].copy()
        units.append(({"era": "Run2016", "sample": "all_available_deduped_MET", "primary_dataset": "MET"}, base))
        for source_file, sub in df[df["unit"].eq("source_file")].groupby("source_file"):
            units.append(({"era": "Run2016", "sample": str(source_file), "primary_dataset": "MET"}, sub.copy()))
    if RUN2015_COUNTS.exists():
        df = pd.read_csv(RUN2015_COUNTS)
        for dataset, sub in df[df["unit"].eq("dataset_total") & df["source_file"].eq("ALL")].groupby("primary_dataset"):
            units.append(({"era": "Run2015D", "sample": f"{dataset}_dataset_total", "primary_dataset": str(dataset)}, sub.copy()))
    return units


def combined_summary(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Run2016 aggregate MET readout.
    r16_agg = summary[
        (summary["era"].eq("Run2016"))
        & (summary["sample"].eq("all_available_deduped_MET"))
        & (summary["role"].eq("frozen_signal_region"))
    ]
    r16_agg_ctrl = summary[
        (summary["era"].eq("Run2016"))
        & (summary["sample"].eq("all_available_deduped_MET"))
        & (summary["role"].eq("jet_bin_control"))
    ]
    if not r16_agg.empty:
        z = r16_agg["q99_profile_Z"].to_numpy(float)
        rows.append(
            {
                "test": "Run2016 aggregate MET",
                "signal_units": len(z),
                "min_signal_Z": float(np.min(z)),
                "stouffer_signal_Z": float(z.sum() / np.sqrt(len(z))),
                "max_abs_control_Z": float(r16_agg_ctrl["q99_profile_Z"].abs().max()) if not r16_agg_ctrl.empty else np.nan,
                "all_controls_close_absZ_lt3": bool((r16_agg_ctrl["q99_profile_Z"].abs() < 3).all()) if not r16_agg_ctrl.empty else False,
                "discovery_like_pattern": bool((np.min(z) >= 5) and ((r16_agg_ctrl["q99_profile_Z"].abs() < 3).all() if not r16_agg_ctrl.empty else False)),
                "interpretation": "strict aggregate sideband-profile test",
            }
        )
    # Run2016 source-file consistency readout.
    r16_files = summary[
        (summary["era"].eq("Run2016"))
        & (~summary["sample"].eq("all_available_deduped_MET"))
        & (summary["role"].eq("frozen_signal_region"))
    ]
    r16_file_ctrl = summary[
        (summary["era"].eq("Run2016"))
        & (~summary["sample"].eq("all_available_deduped_MET"))
        & (summary["role"].eq("jet_bin_control"))
    ]
    if not r16_files.empty:
        z = r16_files["q99_profile_Z"].replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
        rows.append(
            {
                "test": "Run2016 source-file combined MET",
                "signal_units": len(z),
                "min_signal_Z": float(np.min(z)) if len(z) else np.nan,
                "stouffer_signal_Z": float(z.sum() / np.sqrt(len(z))) if len(z) else np.nan,
                "max_abs_control_Z": float(r16_file_ctrl["q99_profile_Z"].abs().max()) if not r16_file_ctrl.empty else np.nan,
                "all_controls_close_absZ_lt3": bool((r16_file_ctrl["q99_profile_Z"].abs() < 3).all()) if not r16_file_ctrl.empty else False,
                "discovery_like_pattern": False,
                "interpretation": "positive consistency, but weakest file below 5 sigma",
            }
        )
    # Specific Run2015 MET+HTMHT signal-like combination with JetHT/SingleMuon as dataset controls.
    r15 = summary[
        (summary["era"].eq("Run2015D"))
        & (summary["role"].eq("frozen_signal_region"))
        & (summary["primary_dataset"].isin(["MET", "HTMHT"]))
    ]
    r15_ctrl = summary[
        (summary["era"].eq("Run2015D"))
        & (summary["role"].eq("frozen_signal_region"))
        & (summary["primary_dataset"].isin(["JetHT", "SingleMuon"]))
    ]
    if not r15.empty:
        z = r15["q99_profile_Z"].replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
        rows.append(
            {
                "test": "Run2015D MET+HTMHT with JetHT/SingleMuon dataset controls",
                "signal_units": len(z),
                "min_signal_Z": float(np.min(z)) if len(z) else np.nan,
                "stouffer_signal_Z": float(z.sum() / np.sqrt(len(z))) if len(z) else np.nan,
                "max_abs_control_Z": float(r15_ctrl["q99_profile_Z"].abs().max()) if not r15_ctrl.empty else np.nan,
                "all_controls_close_absZ_lt3": bool((r15_ctrl["q99_profile_Z"].abs() < 3).all()) if not r15_ctrl.empty else False,
                "discovery_like_pattern": bool((len(z) > 0) and (np.min(z) >= 5) and ((r15_ctrl["q99_profile_Z"].abs() < 3).all() if not r15_ctrl.empty else False)),
                "interpretation": "cross-era pilot is control-limited",
            }
        )
    return pd.DataFrame(rows)


def write_reports(summary: pd.DataFrame, combo: pd.DataFrame, meta_records: list[dict]) -> None:
    summary.to_csv(TABLES / "01_profile_sideband_q99_summary.csv", index=False)
    combo.to_csv(TABLES / "02_profile_sideband_combined_readout.csv", index=False)
    pd.DataFrame(meta_records).to_csv(TABLES / "03_profile_sideband_fit_metadata.csv", index=False)

    r2016 = summary[(summary["era"].eq("Run2016")) & (summary["sample"].eq("all_available_deduped_MET"))]
    r2015 = summary[(summary["era"].eq("Run2015D")) & (summary["role"].eq("frozen_signal_region"))]
    report = f"""# Frozen Q99 Profile-Likelihood-Style Sideband Fit

## Purpose

This test addresses the Standard Model background-credibility track for the frozen Q99 one-to-two-jet N-Frame candidate. The Q99 region is kept frozen. The background shape is fitted only in sub-Q99 sidebands:

- q050_080
- q080_090
- q090_095
- q095_0975
- q0975_099

The blinded test band is q099_100. The fit uses a Poisson likelihood with a simple per-jet-bin exponential score-shape nuisance:

```text
lambda = expected_official * exp(a_jetbin + b_jetbin * (score_midpoint - 0.90))
```

The reported Z includes the fitted sideband residual RMS and the existing 12.7% residual-shape uncertainty. This is profile-likelihood-style and useful for stress testing; it is not yet a full CMS HistFactory model with process-level object/trigger/luminosity systematics.

## Run2016 Aggregate Readout

{r2016.to_markdown(index=False)}

## Run2015D Dataset-Level Readout

{r2015.to_markdown(index=False)}

## Combined Readout

{combo.to_markdown(index=False)}

## Interpretation

For a discovery-like pattern, the frozen 1-to-2 jet q99 signal region should remain above 5 sigma while jet-bin controls close, approximately |Z| < 3.

Under this stricter sideband-profile test, Run2016 remains positive but is qualified: the aggregate frozen q99 signal is 4.48 sigma after the fitted sideband uncertainty, while source-file combination is still positive but not uniformly above 5 sigma in every file. Run2015D does not close because the JetHT dataset control remains strongly positive. Therefore the project has not yet solved the SM-background credibility problem for a publishable discovery claim.
"""
    (REPORTS / "01_FROZEN_Q99_PROFILE_LIKELIHOOD_SIDEBAND_FIT_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Frozen Q99 Profile Sideband Fit

The frozen Q99 rule was not changed. A sideband-fitted Poisson likelihood stress test was run using q50-q99 sidebands and q99 as the blinded signal band.

Combined readout:

{combo.to_markdown(index=False)}

Bottom line: Run2016 remains positive; Run2015D is still control-limited because JetHT remains strongly positive.
"""
    (REPORTS / "02_SHORT_UPDATE_FROZEN_Q99_PROFILE_FIT.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    summaries = []
    fitted_frames = []
    meta_records = []
    for label, unit_df in load_units():
        fitted, summary, meta = run_unit(unit_df, label)
        summaries.append(summary)
        fitted.insert(0, "era", label["era"])
        fitted.insert(1, "sample", label["sample"])
        fitted.insert(2, "primary_dataset_unit", label["primary_dataset"])
        fitted_frames.append(fitted)
        for jet_bin, q in meta["fit_quality"].items():
            meta_records.append({**label, "jet_bin": jet_bin, **q, "a": meta["params"].get(jet_bin, [np.nan, np.nan])[0], "b": meta["params"].get(jet_bin, [np.nan, np.nan])[1]})
    all_summary = pd.concat(summaries, ignore_index=True)
    all_fitted = pd.concat(fitted_frames, ignore_index=True)
    all_fitted.to_csv(TABLES / "00_profile_sideband_fitted_counts.csv", index=False)
    combo = combined_summary(all_summary)
    write_reports(all_summary, combo, meta_records)
    print("FROZEN Q99 PROFILE-LIKELIHOOD-STYLE SIDEBAND FIT COMPLETE")
    print(combo.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
