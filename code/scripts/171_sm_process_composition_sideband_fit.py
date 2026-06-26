from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_sm_process_composition_sideband_fit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
REAL_SAMPLES = [
    ("Run2016G_main_MET", ROOT / "data/processed/nframe_parameter_fit/real_data_with_fitted_nframe_boundary_score.csv"),
    ("Run2016H_independent_MET", ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv"),
    ("Run2016H_expanded_MET", ROOT / "data/processed/expanded_run2016h_miniaod_full/expanded_run2016h_miniaod_with_fitted_nframe_score.csv"),
    ("Run2016H_new_independent_MET", ROOT / "data/processed/new_independent_real_miniaod_validation/full/new_real_events_with_frozen_BNF.csv"),
]

FEATURES = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.95, 1.0]
SCORE_BANDS = ["control_low_0_50", "control_mid_50_80", "control_high_80_95", "signal_tail_95_100"]
SIGNAL_BAND = "signal_tail_95_100"
CONTROL_BANDS = [b for b in SCORE_BANDS if b != SIGNAL_BAND]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    mean = float(np.average(values[mask], weights=weights[mask]))
    var = float(np.average((values[mask] - mean) ** 2, weights=weights[mask]))
    return mean, np.sqrt(max(var, 1e-12))


def base_family(label: object) -> str:
    text = str(label)
    if "QCD" in text:
        return "QCD"
    if "WJets" in text:
        return "WJets"
    if "TT" in text or "top" in text:
        return "Top"
    if "ZNuNu" in text or "ZJets" in text or text.startswith("Z"):
        return "ZNuNu"
    if "diboson" in text:
        return "Diboson"
    return "Other"


def read_sm() -> pd.DataFrame:
    header = pd.read_csv(FULL_WEIGHTED_SM, nrows=0).columns
    use = [c for c in FEATURES + ["event_weight", "process_family_norm", "component_layer", "sample_id", "record_id", "source_file"] if c in header]
    sm = pd.read_csv(FULL_WEIGHTED_SM, usecols=use, low_memory=False)
    for col in FEATURES + ["event_weight"]:
        if col not in sm:
            sm[col] = 1.0 if col == "event_weight" else np.nan
        sm[col] = pd.to_numeric(sm[col], errors="coerce")
    sm["event_weight"] = sm["event_weight"].fillna(1.0)
    if "process_family_norm" not in sm:
        sm["process_family_norm"] = "unknown"
    sm["process_family_base"] = sm["process_family_norm"].map(base_family)
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    return sm


def read_real_met(path: Path, sample_name: str) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0).columns
    use = [c for c in ["primary_dataset", "sample_id", "record_id", "run", "lumi", "event", "source_file"] + FEATURES if c in header]
    frames: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=use, chunksize=200_000, low_memory=False):
        if "primary_dataset" not in chunk:
            continue
        chunk = chunk[chunk["primary_dataset"].astype(str).eq("MET")].copy()
        if chunk.empty:
            continue
        for col in FEATURES + ["run", "lumi", "event"]:
            if col not in chunk:
                chunk[col] = np.nan
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        for col in ["sample_id", "record_id", "source_file"]:
            if col not in chunk:
                chunk[col] = ""
        chunk["real_sample"] = sample_name
        chunk["event_key"] = (
            chunk["run"].astype("Int64").astype(str)
            + ":"
            + chunk["lumi"].astype("Int64").astype(str)
            + ":"
            + chunk["event"].astype("Int64").astype(str)
        )
        frames.append(chunk)
    if not frames:
        return pd.DataFrame()
    real = pd.concat(frames, ignore_index=True)
    real["log1p_MET_pt"] = np.log1p(real["MET_pt"].clip(lower=0))
    real["log1p_HT"] = np.log1p(real["HT"].clip(lower=0))
    return real


def fit_visible_residual(sm: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    weights = sm["event_weight"].to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), weights)
    sm = sm.copy()
    sm["common_missing_z"] = (sm["log1p_MET_pt"] - mean_met) / sd_met
    x = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = x.median().to_numpy(float)
    x = x.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
    y = sm["common_missing_z"].to_numpy(float)
    sw = np.sqrt(np.clip(weights, 1e-12, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    sm["common_missing_resid_visible_only"] = y - design @ coef
    return {"mean_logmet": mean_met, "sd_logmet": sd_met, "visible_median": med, "coef": coef}, sm


def apply_visible_residual(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    out["common_missing_z"] = (out["log1p_MET_pt"] - params["mean_logmet"]) / params["sd_logmet"]
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["visible_median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["common_missing_resid_visible_only"] = out["common_missing_z"].to_numpy(float) - design @ params["coef"]
    return out


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    weights = sm["event_weight"].to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, weights, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score_edges: dict[int, list[float]] = {}
    score = sm["common_missing_resid_visible_only"].to_numpy(float)
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        mask = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[mask], weights[mask], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_cells(df: pd.DataFrame, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["met_bin"] = pd.cut(out["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(out), None, dtype=object)
    score = out["common_missing_resid_visible_only"].to_numpy(float)
    met_bin_values = out["met_bin"].to_numpy()
    for i in range(MET_BINS):
        mask = met_bin_values == i
        edges = score_edges[i]
        for band_name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = band_name
    out["score_band"] = band
    return out[out["score_band"].notna()].copy()


def build_sm_cell_table(sm: pd.DataFrame) -> pd.DataFrame:
    cells = (
        sm.groupby(["process_family_base", "met_bin", "score_band"], dropna=False)["event_weight"]
        .sum()
        .reset_index(name="sm_weight")
    )
    families = sorted(sm["process_family_base"].dropna().unique())
    full_index = pd.DataFrame(
        [(fam, mb, band) for fam, mb, band in product(families, range(MET_BINS), SCORE_BANDS)],
        columns=["process_family_base", "met_bin", "score_band"],
    )
    cells = full_index.merge(cells, on=["process_family_base", "met_bin", "score_band"], how="left").fillna({"sm_weight": 0.0})
    return cells


def build_real_cell_table(real: pd.DataFrame, sample: str) -> pd.DataFrame:
    obs = real.groupby(["met_bin", "score_band"]).size().reset_index(name="observed")
    full_index = pd.DataFrame(
        [(mb, band) for mb, band in product(range(MET_BINS), SCORE_BANDS)],
        columns=["met_bin", "score_band"],
    )
    obs = full_index.merge(obs, on=["met_bin", "score_band"], how="left").fillna({"observed": 0})
    obs["observed"] = obs["observed"].astype(int)
    obs["real_sample"] = sample
    return obs


def prediction_from_alpha(
    sm_cells: pd.DataFrame,
    real_cells: pd.DataFrame,
    families: list[str],
    alpha: np.ndarray,
) -> pd.DataFrame:
    alpha_map = dict(zip(families, alpha))
    sm = sm_cells.copy()
    sm["alpha"] = sm["process_family_base"].map(alpha_map).fillna(0.0)
    sm["weighted"] = sm["sm_weight"] * sm["alpha"]
    pred = sm.groupby(["met_bin", "score_band"])["weighted"].sum().reset_index(name="mix_weight")
    denom = pred.groupby("met_bin")["mix_weight"].sum().rename("mix_met_total").reset_index()
    pred = pred.merge(denom, on="met_bin", how="left")
    real_tot = real_cells.groupby("met_bin")["observed"].sum().rename("real_met_total").reset_index()
    pred = pred.merge(real_tot, on="met_bin", how="left")
    pred["predicted_fraction"] = pred["mix_weight"] / pred["mix_met_total"].replace(0, np.nan)
    pred["expected"] = pred["real_met_total"] * pred["predicted_fraction"]
    out = real_cells.merge(pred[["met_bin", "score_band", "predicted_fraction", "expected"]], on=["met_bin", "score_band"], how="left")
    out["expected"] = out["expected"].fillna(0.0)
    out["predicted_fraction"] = out["predicted_fraction"].fillna(0.0)
    return out


def fit_family_weights(
    sm_cells: pd.DataFrame,
    real_cells: pd.DataFrame,
    families: list[str],
    scenario: str,
    log_bound: float | None,
    penalty_sigma: float | None,
) -> tuple[np.ndarray, dict, pd.DataFrame]:
    bounds = None if log_bound is None else [(-log_bound, log_bound)] * len(families)
    control_mask = real_cells["score_band"].isin(CONTROL_BANDS)

    def nll(theta: np.ndarray) -> float:
        alpha = np.exp(theta)
        pred = prediction_from_alpha(sm_cells, real_cells, families, alpha)
        obs = pred.loc[control_mask, "observed"].to_numpy(float)
        exp = np.clip(pred.loc[control_mask, "expected"].to_numpy(float), 1e-9, np.inf)
        value = float(np.sum(exp - obs * np.log(exp)))
        if penalty_sigma is not None:
            value += float(0.5 * np.sum((theta / penalty_sigma) ** 2))
        return value

    result = minimize(nll, np.zeros(len(families)), method="L-BFGS-B", bounds=bounds, options={"maxiter": 5000})
    theta = result.x if result.success else np.zeros(len(families))
    alpha = np.exp(theta)
    pred = prediction_from_alpha(sm_cells, real_cells, families, alpha)
    summary = summarize_prediction(pred, scenario, result.fun, result.success)
    return alpha, summary, pred


def summarize_prediction(pred: pd.DataFrame, scenario: str, objective: float, converged: bool) -> dict:
    rows = []
    for label, bands in [
        ("control_all_0_95", CONTROL_BANDS),
        ("control_high_80_95", ["control_high_80_95"]),
        ("signal_tail_95_100", [SIGNAL_BAND]),
    ]:
        sub = pred[pred["score_band"].isin(bands)]
        obs = float(sub["observed"].sum())
        exp = float(sub["expected"].sum())
        var = float(np.sum(np.clip(sub["expected"], 0, np.inf) * (1 - np.clip(sub["predicted_fraction"], 0, 1))))
        z = (obs - exp) / np.sqrt(max(var, 1e-12))
        rows.append(
            {
                "region": label,
                "observed": obs,
                "expected": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "signed_Z_stat_only": z,
            }
        )
    out = {"fit_scenario": scenario, "fit_objective": objective, "fit_converged": converged}
    for row in rows:
        prefix = row["region"]
        for key, value in row.items():
            if key != "region":
                out[f"{prefix}_{key}"] = value
    return out


def z_with_rel_uncertainty(obs: float, exp: float, rel_unc: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel_unc * exp) ** 2, 1e-12)))


def run_sample_fit(
    sample_name: str,
    real_cells: pd.DataFrame,
    sm_cells: pd.DataFrame,
    families: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scenarios = [
        ("official_lumi_mix_no_fit", 0.0, None),
        ("sideband_fit_3x_family_bounds", np.log(3.0), np.log(3.0) / 2),
        ("sideband_fit_10x_family_bounds", np.log(10.0), np.log(10.0) / 2),
        ("sideband_fit_unconstrained_stress", np.log(1_000.0), None),
    ]
    summary_rows = []
    alpha_rows = []
    pred_frames = []
    for scenario, bound, penalty in scenarios:
        if scenario == "official_lumi_mix_no_fit":
            alpha = np.ones(len(families))
            pred = prediction_from_alpha(sm_cells, real_cells, families, alpha)
            summary = summarize_prediction(pred, scenario, 0.0, True)
        else:
            alpha, summary, pred = fit_family_weights(sm_cells, real_cells, families, scenario, bound, penalty)
        summary["real_sample"] = sample_name
        for rel_unc in [0.127, 0.20, 0.30]:
            summary[f"signal_tail_95_100_Z_with_{int(rel_unc * 1000) / 10:g}pct_uncertainty"] = z_with_rel_uncertainty(
                summary["signal_tail_95_100_observed"],
                summary["signal_tail_95_100_expected"],
                rel_unc,
            )
        summary_rows.append(summary)
        for family, value in zip(families, alpha):
            alpha_rows.append({"real_sample": sample_name, "fit_scenario": scenario, "process_family_base": family, "family_multiplier": value})
        pred["real_sample"] = sample_name
        pred["fit_scenario"] = scenario
        pred_frames.append(pred)
    return pd.DataFrame(summary_rows), pd.DataFrame(alpha_rows), pd.concat(pred_frames, ignore_index=True)


def cross_sample_prediction(
    fit_sample: str,
    target_sample: str,
    fit_real_cells: pd.DataFrame,
    target_real_cells: pd.DataFrame,
    sm_cells: pd.DataFrame,
    families: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    alpha, _, _ = fit_family_weights(
        sm_cells,
        fit_real_cells,
        families,
        "sideband_fit_3x_family_bounds",
        np.log(3.0),
        np.log(3.0) / 2,
    )
    pred = prediction_from_alpha(sm_cells, target_real_cells, families, alpha)
    summary = summarize_prediction(pred, "cross_sample_3x_family_bounds", 0.0, True)
    summary["fit_sample"] = fit_sample
    summary["target_sample"] = target_sample
    for rel_unc in [0.127, 0.20, 0.30]:
        summary[f"signal_tail_95_100_Z_with_{int(rel_unc * 1000) / 10:g}pct_uncertainty"] = z_with_rel_uncertainty(
            summary["signal_tail_95_100_observed"],
            summary["signal_tail_95_100_expected"],
            rel_unc,
        )
    alpha_rows = [
        {"fit_sample": fit_sample, "target_sample": target_sample, "process_family_base": fam, "family_multiplier": val}
        for fam, val in zip(families, alpha)
    ]
    return pd.DataFrame([summary]), pd.DataFrame(alpha_rows)


def main() -> None:
    ensure_dirs()
    sm = read_sm()
    params, sm = fit_visible_residual(sm)
    met_edges, score_edges = define_bins(sm)
    sm = assign_cells(sm, met_edges, score_edges)
    sm_cells = build_sm_cell_table(sm)
    families = sorted(sm["process_family_base"].dropna().unique())

    real_cells_by_sample: dict[str, pd.DataFrame] = {}
    audit_rows = []
    for sample_name, path in REAL_SAMPLES:
        real = read_real_met(path, sample_name)
        if real.empty:
            continue
        real = apply_visible_residual(real, params)
        real = assign_cells(real, met_edges, score_edges)
        real_cells = build_real_cell_table(real, sample_name)
        real_cells_by_sample[sample_name] = real_cells
        audit_rows.append({"real_sample": sample_name, "path": str(path.relative_to(ROOT)), "met_events": len(real)})
        real[["real_sample", "event_key", "MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "common_missing_resid_visible_only", "met_bin", "score_band"]].to_csv(
            SOURCES / f"{sample_name}_strict_met_cells.csv",
            index=False,
        )

    fit_summaries = []
    family_weights = []
    predictions = []
    for sample_name, real_cells in real_cells_by_sample.items():
        summary, alpha, pred = run_sample_fit(sample_name, real_cells, sm_cells, families)
        fit_summaries.append(summary)
        family_weights.append(alpha)
        predictions.append(pred)

    cross_summaries = []
    cross_weights = []
    names = list(real_cells_by_sample)
    for fit_sample in names:
        for target_sample in names:
            if fit_sample == target_sample:
                continue
            summary, alpha = cross_sample_prediction(
                fit_sample,
                target_sample,
                real_cells_by_sample[fit_sample],
                real_cells_by_sample[target_sample],
                sm_cells,
                families,
            )
            cross_summaries.append(summary)
            cross_weights.append(alpha)

    audit = pd.DataFrame(audit_rows)
    summary = pd.concat(fit_summaries, ignore_index=True)
    weights = pd.concat(family_weights, ignore_index=True)
    pred = pd.concat(predictions, ignore_index=True)
    cross_summary = pd.concat(cross_summaries, ignore_index=True)
    cross_alpha = pd.concat(cross_weights, ignore_index=True)

    audit.to_csv(TABLES / "00_met_sample_audit.csv", index=False)
    sm_cells.to_csv(TABLES / "01_sm_process_family_cell_template.csv", index=False)
    summary.to_csv(TABLES / "02_sideband_fit_signal_predictions.csv", index=False)
    weights.to_csv(TABLES / "03_sideband_fit_family_multipliers.csv", index=False)
    pred.to_csv(TABLES / "04_sideband_fit_cell_predictions.csv", index=False)
    cross_summary.to_csv(TABLES / "05_cross_sample_sideband_fit_predictions.csv", index=False)
    cross_alpha.to_csv(TABLES / "06_cross_sample_family_multipliers.csv", index=False)

    strict = summary[
        summary["fit_scenario"].isin(
            [
                "official_lumi_mix_no_fit",
                "sideband_fit_3x_family_bounds",
                "sideband_fit_10x_family_bounds",
                "sideband_fit_unconstrained_stress",
            ]
        )
    ].copy()
    strict_cols = [
        "real_sample",
        "fit_scenario",
        "control_all_0_95_observed_over_expected",
        "control_high_80_95_observed_over_expected",
        "signal_tail_95_100_observed",
        "signal_tail_95_100_expected",
        "signal_tail_95_100_observed_over_expected",
        "signal_tail_95_100_signed_Z_stat_only",
        "signal_tail_95_100_Z_with_12.7pct_uncertainty",
        "signal_tail_95_100_Z_with_20pct_uncertainty",
        "signal_tail_95_100_Z_with_30pct_uncertainty",
    ]
    report = f"""# SM Process-Composition Sideband Fit for Strict MET Boundary

## Question

Can a wrong Standard Model process mixture explain the strict calibration-safe MET boundary tail?

## Method

- Score: `common_missing_resid_visible_only`
- Conditioning variable: raw `MET_pt`
- Signal region: top 5% score band inside each MET bin
- Fit region: the lower 95% score sidebands inside the same MET bins
- SM process families: {", ".join(families)}
- Fit target: process-family multipliers fitted to real-data sidebands only, then used to predict the hidden top-tail signal band

This is a direct test of the remaining process-composition caveat. If changing the SM mixture can make the sidebands close and also raise the expected top-tail enough, the N-Frame trace is not yet robust. If sideband-fitted mixtures still leave the top-tail high, the trace is harder to explain as a Standard Model recipe error.

## Samples

{audit.to_markdown(index=False)}

## Main Sideband-Fit Result

{strict[strict_cols].to_markdown(index=False)}

## Cross-Sample Test

For this test, process-family multipliers are fitted on one MET sample sidebands and then applied to a different MET sample top-tail.

{cross_summary[["fit_sample", "target_sample", "control_all_0_95_observed_over_expected", "signal_tail_95_100_observed", "signal_tail_95_100_expected", "signal_tail_95_100_observed_over_expected", "signal_tail_95_100_Z_with_12.7pct_uncertainty", "signal_tail_95_100_Z_with_20pct_uncertainty", "signal_tail_95_100_Z_with_30pct_uncertainty"]].to_markdown(index=False)}

## Interpretation

The decisive rows are the sideband-fit rows. They ask whether a fitted SM process mixture, learned only from non-tail data, can predict the strict MET boundary tail.

The `sideband_fit_3x_family_bounds` scenario is the main conservative physics-style test: every broad SM process family is allowed to move by up to a factor of three, but not arbitrarily.

The `sideband_fit_unconstrained_stress` row is intentionally extreme. If that row also leaves a large tail excess, process composition alone is unlikely to be enough. If it removes the excess, the result is composition-limited.
"""
    (REPORTS / "01_SM_PROCESS_COMPOSITION_SIDEBAND_FIT_REPORT.md").write_text(report, encoding="utf-8")

    main_rows = strict[strict["fit_scenario"].eq("sideband_fit_3x_family_bounds")][
        [
            "real_sample",
            "control_all_0_95_observed_over_expected",
            "control_high_80_95_observed_over_expected",
            "signal_tail_95_100_observed_over_expected",
            "signal_tail_95_100_Z_with_12.7pct_uncertainty",
            "signal_tail_95_100_Z_with_30pct_uncertainty",
        ]
    ]
    short = f"""# Short Update: SM Process-Composition Sideband Fit

We fitted broad Standard Model process-family weights using only the non-tail sidebands of each MET sample, then predicted the strict N-Frame MET boundary top-tail.

Main 3x-bounded sideband-fit result:

{main_rows.to_markdown(index=False)}

This directly attacks the remaining caveat: whether a wrong SM process mixture can explain the boundary trace.
"""
    (REPORTS / "02_SHORT_UPDATE_SM_PROCESS_COMPOSITION_SIDEBAND_FIT.md").write_text(short, encoding="utf-8")

    print("SM PROCESS-COMPOSITION SIDEBAND FIT COMPLETE")
    print(main_rows.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
