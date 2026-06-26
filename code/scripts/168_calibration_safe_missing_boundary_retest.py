from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, norm, spearmanr


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_calibration_safe_missing_boundary_retest"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

SCRIPT_164 = ROOT / "scripts/164_apply_residual_nframe_v2_to_real_data.py"
BENCHMARK = ROOT / "outputs_trace_predictive_significance/sources/primary_trace_available_balanced_dataset.csv"
FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
REAL_RUN2016H = ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv"

DATASETS = ["JetHT", "MET", "SingleMuon"]
VISIBLE_COLS = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
WITH_MET_COLS = ["log1p_MET_pt"] + VISIBLE_COLS
SCORES = [
    "old_resid_P_missing",
    "common_missing_z",
    "common_missing_resid_with_MET",
    "common_missing_resid_visible_only",
]


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def load_164():
    spec = importlib.util.spec_from_file_location("nframe164", SCRIPT_164)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def weighted_stats(x: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    mean = float(np.average(x[mask], weights=w[mask]))
    var = float(np.average((x[mask] - mean) ** 2, weights=w[mask]))
    return mean, np.sqrt(max(var, 1e-12))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0:
        return np.nan
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def fit_weighted_lstsq(df: pd.DataFrame, y_col: str, x_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    x = df[x_cols].apply(pd.to_numeric, errors="coerce")
    med = x.median().to_numpy(dtype=float)
    x = x.fillna(pd.Series(med, index=x_cols)).to_numpy(dtype=float)
    y = pd.to_numeric(df[y_col], errors="coerce").to_numpy(dtype=float)
    y_fill = np.nanmedian(y)
    y = np.where(np.isfinite(y), y, y_fill)
    w = pd.to_numeric(df["event_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=float)
    sw = np.sqrt(np.clip(w, 1e-12, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    return coef, med


def apply_lstsq(df: pd.DataFrame, x_cols: list[str], coef: np.ndarray, med: np.ndarray) -> np.ndarray:
    x = df[x_cols].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(med, index=x_cols)).to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def build_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    mod = load_164()
    benchmark = mod.normalise_schema(pd.read_csv(BENCHMARK, low_memory=False), "benchmark_training")
    benchmark["target"] = pd.to_numeric(benchmark["target"], errors="coerce").astype(int)
    residualizer = mod.fit_residualizer(benchmark)

    sm = mod.normalise_schema(pd.read_csv(FULL_WEIGHTED_SM, low_memory=False), "full_weighted_sm")
    sm = sm[sm["event_weight"].notna()].copy()
    sm = mod.apply_residualizer(sm, residualizer)

    real = mod.normalise_schema(pd.read_csv(REAL_RUN2016H, low_memory=False), "run2016h_real")
    real = mod.apply_residualizer(real, residualizer)

    for df in [real, sm]:
        for col in ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "P_missing", "resid_P_missing", "event_weight"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "event_weight" not in df.columns:
            df["event_weight"] = 1.0
        df["log1p_MET_pt"] = np.log1p(df["MET_pt"].clip(lower=0))
        df["log1p_HT"] = np.log1p(df["HT"].clip(lower=0))
        df["old_resid_P_missing"] = df["resid_P_missing"]

    w = sm["event_weight"].fillna(1.0).to_numpy(dtype=float)
    mean_logmet, sd_logmet = weighted_stats(sm["log1p_MET_pt"].to_numpy(dtype=float), w)
    for df in [real, sm]:
        df["common_missing_z"] = (df["log1p_MET_pt"] - mean_logmet) / sd_logmet

    coef_met, med_met = fit_weighted_lstsq(sm, "common_missing_z", WITH_MET_COLS)
    coef_vis, med_vis = fit_weighted_lstsq(sm, "common_missing_z", VISIBLE_COLS)
    for df in [real, sm]:
        df["common_missing_pred_with_MET"] = apply_lstsq(df, WITH_MET_COLS, coef_met, med_met)
        df["common_missing_pred_visible_only"] = apply_lstsq(df, VISIBLE_COLS, coef_vis, med_vis)
        df["common_missing_resid_with_MET"] = df["common_missing_z"] - df["common_missing_pred_with_MET"]
        df["common_missing_resid_visible_only"] = df["common_missing_z"] - df["common_missing_pred_visible_only"]
    return real, sm


def count_z(obs: int, n: int, p: float) -> tuple[float, float, float]:
    p = float(np.clip(p, 1e-12, 1 - 1e-12))
    exp = n * p
    z = (obs - exp) / np.sqrt(max(n * p * (1 - p), 1e-12))
    p_up = float(binom.sf(obs - 1, n, p)) if obs >= exp else 1.0
    return exp, z, p_up


def tail_test(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, score: str, tail_frac: float = 0.05) -> dict:
    rs = pd.to_numeric(real[score], errors="coerce").to_numpy(dtype=float)
    ss = pd.to_numeric(sm[score], errors="coerce").to_numpy(dtype=float)
    sw = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=float)
    thr = weighted_quantile(ss, sw, 1.0 - tail_frac)
    p = float(sw[ss >= thr].sum() / sw.sum())
    obs = int((rs >= thr).sum())
    exp, z, p_up = count_z(obs, len(real), p)
    return {
        "primary_dataset": dataset,
        "score": score,
        "conditioning": "none_global_shape",
        "tail_fraction": tail_frac,
        "threshold": thr,
        "real_observed": obs,
        "expected_shape_normalized": exp,
        "observed_over_expected": obs / exp if exp > 0 else np.inf,
        "Z_signed": z,
        "p_upward": p_up,
    }


def conditioned_tail(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, score: str, cond: str, n_bins: int = 10, tail_frac: float = 0.05) -> dict:
    rs = pd.to_numeric(real[score], errors="coerce").to_numpy(dtype=float)
    ss = pd.to_numeric(sm[score], errors="coerce").to_numpy(dtype=float)
    rc = pd.to_numeric(real[cond], errors="coerce").to_numpy(dtype=float)
    sc = pd.to_numeric(sm[cond], errors="coerce").to_numpy(dtype=float)
    sw = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=float)
    edges = [weighted_quantile(sc, sw, q) for q in np.linspace(0, 1, n_bins + 1)]
    edges[0], edges[-1] = -np.inf, np.inf
    total_obs = 0
    total_exp = 0.0
    total_var = 0.0
    bins = 0
    for lo, hi in zip(edges[:-1], edges[1:]):
        sm_bin = (sc >= lo) & (sc < hi)
        real_bin = (rc >= lo) & (rc < hi)
        if sm_bin.sum() < 25 or real_bin.sum() < 5:
            continue
        thr = weighted_quantile(ss[sm_bin], sw[sm_bin], 1.0 - tail_frac)
        p = float(sw[sm_bin & (ss >= thr)].sum() / sw[sm_bin].sum())
        obs = int((rs[real_bin] >= thr).sum())
        n = int(real_bin.sum())
        total_obs += obs
        total_exp += n * p
        total_var += n * p * (1 - p)
        bins += 1
    z = (total_obs - total_exp) / np.sqrt(max(total_var, 1e-12))
    p_up = float(norm.sf(z)) if z > 0 else 1.0
    return {
        "primary_dataset": dataset,
        "score": score,
        "conditioning": cond,
        "tail_fraction": tail_frac,
        "threshold": np.nan,
        "real_observed": int(total_obs),
        "expected_shape_normalized": total_exp,
        "observed_over_expected": total_obs / total_exp if total_exp > 0 else np.inf,
        "Z_signed": float(z),
        "p_upward": p_up,
        "used_bins": bins,
    }


def summary_stats(real: pd.DataFrame, sm: pd.DataFrame, dataset: str) -> pd.DataFrame:
    rows = []
    for score in SCORES + ["MET_pt", "log1p_MET_pt", "P_missing"]:
        for source, frame, weights in [
            ("real", real, np.ones(len(real))),
            ("sm", sm, sm["event_weight"].fillna(1.0).to_numpy(dtype=float)),
        ]:
            values = pd.to_numeric(frame[score], errors="coerce").to_numpy(dtype=float)
            rows.append(
                {
                    "primary_dataset": dataset,
                    "source": source,
                    "variable": score,
                    "mean": float(np.nanmean(values)),
                    "q05": weighted_quantile(values, weights, 0.05),
                    "q50": weighted_quantile(values, weights, 0.50),
                    "q95": weighted_quantile(values, weights, 0.95),
                    "q99": weighted_quantile(values, weights, 0.99),
                }
            )
    return pd.DataFrame(rows)


def correlations(real: pd.DataFrame, sm: pd.DataFrame, dataset: str) -> pd.DataFrame:
    rows = []
    for source, frame in [("real", real), ("sm", sm)]:
        for score in SCORES:
            for var in ["MET_pt", "log1p_MET_pt", "P_missing", "HT", "N_jets_30"]:
                vals = frame[[score, var]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(vals) < 20:
                    continue
                rows.append(
                    {
                        "primary_dataset": dataset,
                        "source": source,
                        "score": score,
                        "variable": var,
                        "pearson_r": vals[score].corr(vals[var]),
                        "spearman_r": spearmanr(vals[score], vals[var]).statistic,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    real, sm = build_frames()
    test_rows, stats_frames, corr_frames = [], [], []
    for dataset in DATASETS:
        real_ds = real[real["primary_dataset"].astype(str).eq(dataset)].copy()
        sm_pool = sm.copy()
        for score in SCORES:
            test_rows.append(tail_test(real_ds, sm_pool, dataset, score))
            for cond in ["MET_pt", "common_missing_z", "HT", "N_jets_30"]:
                test_rows.append(conditioned_tail(real_ds, sm_pool, dataset, score, cond))
        stats_frames.append(summary_stats(real_ds, sm_pool, dataset))
        corr_frames.append(correlations(real_ds, sm_pool, dataset))

    tests = pd.DataFrame(test_rows)
    stats = pd.concat(stats_frames, ignore_index=True)
    corr = pd.concat(corr_frames, ignore_index=True)

    tests.to_csv(TABLES / "01_calibration_safe_missing_tail_tests.csv", index=False)
    stats.to_csv(TABLES / "02_calibration_safe_missing_distribution_summaries.csv", index=False)
    corr.to_csv(TABLES / "03_calibration_safe_missing_correlations.csv", index=False)

    keep = ["primary_dataset", "sample_id", "record_id", "run", "lumi", "event", "source_file", "MET_pt", "P_missing"] + SCORES
    real[keep].to_csv(SOURCES / "run2016h_real_with_calibration_safe_missing_scores.csv", index=False)

    key = tests[
        tests["conditioning"].isin(["none_global_shape", "MET_pt", "common_missing_z"])
        & tests["score"].isin(["old_resid_P_missing", "common_missing_resid_with_MET", "common_missing_resid_visible_only"])
    ].copy()
    with_met = tests[
        tests["score"].eq("common_missing_resid_with_MET")
        & tests["conditioning"].eq("none_global_shape")
    ]
    visible = tests[
        tests["score"].eq("common_missing_resid_visible_only")
        & tests["conditioning"].eq("none_global_shape")
    ]

    report = f"""# Calibration-Safe Missing Boundary Retest

## Purpose

Resolve whether the N-Frame v3 `resid_P_missing` anomaly is a real boundary effect or a calibration artefact from comparing differently scaled `P_missing` components between real data and SM simulation.

## What Changed

The old score used fitted `P_missing` components already present in each table. Those components were not guaranteed to be on a common real/SM scale.

This retest rebuilds missing-energy variables from raw `MET_pt` using a common SM-derived calibration:

- `common_missing_z`: shared z-score of `log1p(MET_pt)`.
- `common_missing_resid_with_MET`: common missing score residualized against MET + visible variables. This should collapse if the old anomaly was caused by calibration.
- `common_missing_resid_visible_only`: common missing score residualized against visible event structure only, excluding MET. This asks whether missing energy is high relative to visible topology.

## Key Results

Old score and calibration-safe replacement scores:

{key[['primary_dataset','score','conditioning','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

Common missing residual including MET:

{with_met[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

Common missing residual relative to visible-only topology:

{visible[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

## Interpretation

If `common_missing_resid_with_MET` collapses while the old `resid_P_missing` remains huge, then the old v3 score was not calibration-safe. It was mostly detecting an inconsistent fitted `P_missing` scale.

If `common_missing_resid_visible_only` remains positive, then there is still a simpler missing-energy/visible-topology mismatch to investigate, but it is no longer the same as the old N-Frame v3 residual.

This retest is designed to stop us from mistaking a scaling artefact for a hidden-sector boundary trace.
"""
    (REPORTS / "01_CALIBRATION_SAFE_MISSING_BOUNDARY_RETEST_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Calibration-Safe Missing Boundary Retest

We rebuilt the missing-energy boundary variable from raw `MET_pt` on a common SM-derived scale.

The old v3 score was `resid_P_missing`. The calibration-safe sanity check is `common_missing_resid_with_MET`, where the missing score is residualized against MET itself plus visible variables.

Result:

{with_met[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

Interpretation: if this collapses relative to the old hundreds-sigma result, then the old v3 anomaly was largely a real/SM `P_missing` calibration mismatch, not a clean N-Frame boundary trace.

Visible-only missing residual still tests a simpler question: whether real data has more missing energy relative to visible topology than SM predicts.

{visible[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_CALIBRATION_SAFE_MISSING_RETEST.md").write_text(short, encoding="utf-8")

    print("CALIBRATION-SAFE MISSING BOUNDARY RETEST COMPLETE")
    print(with_met[["primary_dataset", "real_observed", "expected_shape_normalized", "observed_over_expected", "Z_signed"]].to_string(index=False))
    print(visible[["primary_dataset", "real_observed", "expected_shape_normalized", "observed_over_expected", "Z_signed"]].to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
