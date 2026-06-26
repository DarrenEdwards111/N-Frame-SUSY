from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, norm, spearmanr


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_full_lumi_v3_mismatch_diagnostics"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

SCRIPT_164 = ROOT / "scripts/164_apply_residual_nframe_v2_to_real_data.py"
BENCHMARK = ROOT / "outputs_trace_predictive_significance/sources/primary_trace_available_balanced_dataset.csv"
FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
REAL_RUN2016H = ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv"

V3_SCORE = "resid_P_missing"
DATASET_TO_TRIGGER = {
    "JetHT": "HLT_HT_paths_any",
    "MET": "HLT_MET_paths_any",
    "SingleMuon": "HLT_Mu_paths_any",
}
DIAG_VARS = ["MET_pt", "P_missing", V3_SCORE, "standard_score", "HT", "N_jets_30", "N_btags_medium"]


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def load_164():
    spec = importlib.util.spec_from_file_location("nframe164", SCRIPT_164)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


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


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not mask.any():
        return np.nan
    return float(np.average(values[mask], weights=weights[mask]))


def count_z(obs: int, n: int, p: float) -> tuple[float, float, float, float]:
    p = float(np.clip(p, 1e-12, 1 - 1e-12))
    exp = n * p
    var = n * p * (1 - p)
    z = (obs - exp) / np.sqrt(max(var, 1e-12))
    p_up = float(binom.sf(obs - 1, n, p)) if obs >= exp else 1.0
    p_down = float(binom.cdf(obs, n, p)) if obs <= exp else 1.0
    return exp, z, p_up, p_down


def build_scored_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    mod = load_164()
    benchmark = mod.normalise_schema(pd.read_csv(BENCHMARK, low_memory=False), "benchmark_training")
    benchmark["target"] = pd.to_numeric(benchmark["target"], errors="coerce").astype(int)
    residualizer = mod.fit_residualizer(benchmark)
    benchmark = mod.apply_residualizer(benchmark, residualizer)

    std_model = mod.model()
    nf_model = mod.model()
    std_model.fit(benchmark[mod.STANDARD_FEATURES], benchmark["target"])
    nf_model.fit(benchmark[mod.NFRAME_V2_FEATURES], benchmark["target"])

    sm = mod.normalise_schema(pd.read_csv(FULL_WEIGHTED_SM, low_memory=False), "full_weighted_sm")
    sm = sm[sm["event_weight"].notna()].copy()
    sm = mod.apply_residualizer(sm, residualizer)
    sm = mod.score_frame(sm, std_model, nf_model)

    real = mod.normalise_schema(pd.read_csv(REAL_RUN2016H, low_memory=False), "run2016h_real")
    real = mod.apply_residualizer(real, residualizer)
    real = mod.score_frame(real, std_model, nf_model)

    for df in [sm, real]:
        for col in DIAG_VARS + ["event_weight"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "event_weight" not in df.columns:
            df["event_weight"] = 1.0
    return real, sm


def sm_pools(sm: pd.DataFrame, dataset: str) -> dict[str, pd.DataFrame]:
    layer = sm["component_layer"].fillna("").astype(str) if "component_layer" in sm.columns else pd.Series("", index=sm.index)
    trigger = DATASET_TO_TRIGGER[dataset]
    trigger_values = pd.to_numeric(sm.get(trigger, pd.Series(np.nan, index=sm.index)), errors="coerce")
    return {
        "all_luminosity_weighted_sm": sm,
        "full_component_sm_only": sm[layer.str.contains("MINIAODSIM_full_component", case=False, na=False)],
        "reduced_component_sm_only": sm[layer.str.contains("NANOAODSIM_reduced_component", case=False, na=False)],
        f"hlt_matched_{trigger}": sm[trigger_values > 0],
    }


def global_tail(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, pool_name: str) -> pd.DataFrame:
    rows = []
    rs = real[V3_SCORE].to_numpy(float)
    ss = sm[V3_SCORE].to_numpy(float)
    sw = sm["event_weight"].fillna(1.0).to_numpy(float)
    for frac in [0.10, 0.05, 0.01, 0.005, 0.001]:
        thr = weighted_quantile(ss, sw, 1.0 - frac)
        sm_frac = float(sw[ss >= thr].sum() / sw.sum()) if np.isfinite(thr) and sw.sum() > 0 else np.nan
        obs = int((rs >= thr).sum()) if np.isfinite(thr) else 0
        exp, z, p_up, p_down = count_z(obs, len(rs), sm_frac) if np.isfinite(sm_frac) else (np.nan, np.nan, np.nan, np.nan)
        rows.append(
            {
                "primary_dataset": dataset,
                "sm_pool": pool_name,
                "test": "global_v3_tail",
                "tail_fraction": frac,
                "threshold": thr,
                "real_observed": obs,
                "real_total": len(real),
                "expected_shape_normalized": exp,
                "observed_over_expected": obs / exp if exp and exp > 0 else np.inf,
                "Z_signed": z,
                "p_upward": p_up,
                "p_downward": p_down,
            }
        )
    return pd.DataFrame(rows)


def conditioned_tail(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, pool_name: str, n_bins: int = 8, tail_frac: float = 0.05) -> pd.DataFrame:
    rows = []
    rs = real[V3_SCORE].to_numpy(float)
    ss = sm[V3_SCORE].to_numpy(float)
    rstd = real["standard_score"].to_numpy(float)
    sstd = sm["standard_score"].to_numpy(float)
    sw = sm["event_weight"].fillna(1.0).to_numpy(float)
    edges = [weighted_quantile(sstd, sw, q) for q in np.linspace(0, 1, n_bins + 1)]
    if not np.all(np.isfinite(edges[1:-1])):
        return pd.DataFrame()
    edges[0], edges[-1] = -np.inf, np.inf
    total_obs = 0
    total_exp = 0.0
    total_var = 0.0
    used_bins = 0
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        sm_bin = (sstd >= lo) & (sstd < hi)
        real_bin = (rstd >= lo) & (rstd < hi)
        if sm_bin.sum() < 25 or real_bin.sum() < 5:
            continue
        thr = weighted_quantile(ss[sm_bin], sw[sm_bin], 1.0 - tail_frac)
        p = float(sw[sm_bin & (ss >= thr)].sum() / sw[sm_bin].sum())
        obs = int((rs[real_bin] >= thr).sum())
        n = int(real_bin.sum())
        exp, z, p_up, p_down = count_z(obs, n, p)
        total_obs += obs
        total_exp += exp
        total_var += n * p * (1 - p)
        used_bins += 1
        rows.append(
            {
                "primary_dataset": dataset,
                "sm_pool": pool_name,
                "standard_score_bin": i,
                "real_bin_n": n,
                "tail_fraction": tail_frac,
                "threshold": thr,
                "real_observed": obs,
                "expected_shape_normalized": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "Z_signed": z,
                "p_upward": p_up,
                "p_downward": p_down,
            }
        )
    z = (total_obs - total_exp) / np.sqrt(max(total_var, 1e-12))
    rows.append(
        {
            "primary_dataset": dataset,
            "sm_pool": pool_name,
            "standard_score_bin": "combined",
            "real_bin_n": len(real),
            "tail_fraction": tail_frac,
            "threshold": np.nan,
            "real_observed": int(total_obs),
            "expected_shape_normalized": float(total_exp),
            "observed_over_expected": total_obs / total_exp if total_exp > 0 else np.inf,
            "Z_signed": float(z),
            "p_upward": float(norm.sf(z)) if z > 0 else 1.0,
            "p_downward": float(norm.cdf(z)) if z < 0 else 1.0,
        }
    )
    return pd.DataFrame(rows)


def variable_conditioned_tail(
    real: pd.DataFrame,
    sm: pd.DataFrame,
    dataset: str,
    pool_name: str,
    condition_variable: str,
    n_bins: int = 10,
    tail_frac: float = 0.05,
) -> pd.DataFrame:
    rows = []
    rs = real[V3_SCORE].to_numpy(float)
    ss = sm[V3_SCORE].to_numpy(float)
    rcond = pd.to_numeric(real[condition_variable], errors="coerce").to_numpy(float)
    scond = pd.to_numeric(sm[condition_variable], errors="coerce").to_numpy(float)
    sw = sm["event_weight"].fillna(1.0).to_numpy(float)
    edges = [weighted_quantile(scond, sw, q) for q in np.linspace(0, 1, n_bins + 1)]
    if not np.all(np.isfinite(edges[1:-1])):
        return pd.DataFrame()
    edges[0], edges[-1] = -np.inf, np.inf
    total_obs = 0
    total_exp = 0.0
    total_var = 0.0
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        sm_bin = (scond >= lo) & (scond < hi)
        real_bin = (rcond >= lo) & (rcond < hi)
        if sm_bin.sum() < 25 or real_bin.sum() < 5:
            continue
        thr = weighted_quantile(ss[sm_bin], sw[sm_bin], 1.0 - tail_frac)
        p = float(sw[sm_bin & (ss >= thr)].sum() / sw[sm_bin].sum())
        obs = int((rs[real_bin] >= thr).sum())
        n = int(real_bin.sum())
        exp, z, p_up, p_down = count_z(obs, n, p)
        total_obs += obs
        total_exp += exp
        total_var += n * p * (1 - p)
        rows.append(
            {
                "primary_dataset": dataset,
                "sm_pool": pool_name,
                "condition_variable": condition_variable,
                "condition_bin": i,
                "real_bin_n": n,
                "tail_fraction": tail_frac,
                "threshold": thr,
                "real_observed": obs,
                "expected_shape_normalized": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "Z_signed": z,
                "p_upward": p_up,
                "p_downward": p_down,
            }
        )
    z = (total_obs - total_exp) / np.sqrt(max(total_var, 1e-12))
    rows.append(
        {
            "primary_dataset": dataset,
            "sm_pool": pool_name,
            "condition_variable": condition_variable,
            "condition_bin": "combined",
            "real_bin_n": len(real),
            "tail_fraction": tail_frac,
            "threshold": np.nan,
            "real_observed": int(total_obs),
            "expected_shape_normalized": float(total_exp),
            "observed_over_expected": total_obs / total_exp if total_exp > 0 else np.inf,
            "Z_signed": float(z),
            "p_upward": float(norm.sf(z)) if z > 0 else 1.0,
            "p_downward": float(norm.cdf(z)) if z < 0 else 1.0,
        }
    )
    return pd.DataFrame(rows)


def distribution_summary(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, pool_name: str) -> pd.DataFrame:
    rows = []
    sw = sm["event_weight"].fillna(1.0).to_numpy(float)
    for var in DIAG_VARS:
        for source, frame, weights in [
            ("real", real, np.ones(len(real))),
            ("sm", sm, sw),
        ]:
            if var not in frame.columns:
                continue
            values = pd.to_numeric(frame[var], errors="coerce").to_numpy(float)
            rows.append(
                {
                    "primary_dataset": dataset,
                    "sm_pool": pool_name,
                    "source": source,
                    "variable": var,
                    "n": int(np.isfinite(values).sum()),
                    "weighted_mean": weighted_mean(values, weights),
                    "q01": weighted_quantile(values, weights, 0.01),
                    "q05": weighted_quantile(values, weights, 0.05),
                    "q50": weighted_quantile(values, weights, 0.50),
                    "q95": weighted_quantile(values, weights, 0.95),
                    "q99": weighted_quantile(values, weights, 0.99),
                }
            )
    return pd.DataFrame(rows)


def correlation_diagnostics(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, pool_name: str) -> pd.DataFrame:
    rows = []
    for source, frame in [("real", real), ("sm", sm)]:
        for x in ["MET_pt", "P_missing", "standard_score", "HT", "N_jets_30"]:
            vals = frame[[V3_SCORE, x]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(vals) < 20:
                continue
            pearson = vals[V3_SCORE].corr(vals[x], method="pearson")
            spearman = spearmanr(vals[V3_SCORE], vals[x]).statistic
            rows.append(
                {
                    "primary_dataset": dataset,
                    "sm_pool": pool_name,
                    "source": source,
                    "v3_score": V3_SCORE,
                    "compared_variable": x,
                    "n": len(vals),
                    "pearson_r": pearson,
                    "spearman_r": spearman,
                }
            )
    return pd.DataFrame(rows)


def concentration(real: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset, sub in real.groupby("primary_dataset"):
        thr = sub[V3_SCORE].quantile(0.95)
        tail = sub[sub[V3_SCORE] >= thr]
        for field in ["source_file", "run", "lumi"]:
            counts = tail[field].astype(str).value_counts()
            total_counts = sub[field].astype(str).value_counts()
            top = counts.head(10)
            for val, n in top.items():
                rows.append(
                    {
                        "primary_dataset": dataset,
                        "tail": "dataset_top5pct_v3",
                        "field": field,
                        "value": val,
                        "tail_count": int(n),
                        "tail_fraction": float(n / len(tail)),
                        "overall_count": int(total_counts.get(val, 0)),
                        "overall_fraction": float(total_counts.get(val, 0) / len(sub)),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    real, sm = build_scored_frames()
    keep_real = ["primary_dataset", "sample_id", "record_id", "run", "lumi", "event", "source_file"] + DIAG_VARS
    real[keep_real].to_csv(SOURCES / "run2016h_real_scored_for_full_lumi_v3_diagnostics.csv", index=False)

    audit_rows = [
        {
            "item": "real_run2016h_rows",
            "value": len(real),
            "note": "Independent Run2016H MiniAOD real collision sample, not full Run2016H luminosity.",
        },
        {
            "item": "full_weighted_sm_rows",
            "value": len(sm),
            "note": "All available luminosity-weighted SM simulation rows.",
        },
        {
            "item": "full_weighted_sm_weight_sum",
            "value": float(sm["event_weight"].sum()),
            "note": "Used for weighted shape thresholds; not directly compared as absolute yield to partial real extraction.",
        },
    ]
    global_frames, conditioned_frames, var_conditioned_frames, dist_frames, corr_frames = [], [], [], [], []
    for dataset in DATASET_TO_TRIGGER:
        real_ds = real[real["primary_dataset"].astype(str).eq(dataset)].copy()
        pools = sm_pools(sm, dataset)
        audit_rows.append({"item": f"real_{dataset}_rows", "value": len(real_ds), "note": ""})
        for pool_name, sm_pool in pools.items():
            audit_rows.append({"item": f"{dataset}_{pool_name}_rows", "value": len(sm_pool), "note": ""})
            if len(real_ds) < 20 or len(sm_pool) < 50:
                continue
            global_frames.append(global_tail(real_ds, sm_pool, dataset, pool_name))
            conditioned_frames.append(conditioned_tail(real_ds, sm_pool, dataset, pool_name))
            for condition_variable in ["MET_pt", "P_missing", "HT"]:
                var_conditioned_frames.append(variable_conditioned_tail(real_ds, sm_pool, dataset, pool_name, condition_variable))
            dist_frames.append(distribution_summary(real_ds, sm_pool, dataset, pool_name))
            corr_frames.append(correlation_diagnostics(real_ds, sm_pool, dataset, pool_name))

    audit = pd.DataFrame(audit_rows)
    global_tests = pd.concat(global_frames, ignore_index=True)
    conditioned = pd.concat(conditioned_frames, ignore_index=True)
    var_conditioned = pd.concat(var_conditioned_frames, ignore_index=True)
    distributions = pd.concat(dist_frames, ignore_index=True)
    correlations = pd.concat(corr_frames, ignore_index=True)
    conc = concentration(real)

    audit.to_csv(TABLES / "00_full_lumi_v3_diagnostic_audit.csv", index=False)
    global_tests.to_csv(TABLES / "01_full_lumi_global_v3_tail_tests.csv", index=False)
    conditioned.to_csv(TABLES / "02_full_lumi_standard_conditioned_v3_tail_tests.csv", index=False)
    var_conditioned.to_csv(TABLES / "03_full_lumi_variable_conditioned_v3_tail_tests.csv", index=False)
    distributions.to_csv(TABLES / "04_met_pmissing_residual_calibration_summaries.csv", index=False)
    correlations.to_csv(TABLES / "05_v3_residual_correlation_diagnostics.csv", index=False)
    conc.to_csv(TABLES / "06_real_high_v3_tail_file_run_lumi_concentration.csv", index=False)

    main_cond = conditioned[
        conditioned["standard_score_bin"].astype(str).eq("combined")
        & conditioned["sm_pool"].eq("all_luminosity_weighted_sm")
    ].copy()
    hlt_cond = conditioned[
        conditioned["standard_score_bin"].astype(str).eq("combined")
        & conditioned["sm_pool"].str.startswith("hlt_matched")
    ].copy()
    red_cond = conditioned[
        conditioned["standard_score_bin"].astype(str).eq("combined")
        & conditioned["sm_pool"].eq("reduced_component_sm_only")
    ].copy()
    full_cond = conditioned[
        conditioned["standard_score_bin"].astype(str).eq("combined")
        & conditioned["sm_pool"].eq("full_component_sm_only")
    ].copy()

    # Compact calibration table for the actual v3 variable.
    cal = distributions[
        distributions["variable"].isin(["MET_pt", "P_missing", V3_SCORE])
        & distributions["sm_pool"].isin(["all_luminosity_weighted_sm", "full_component_sm_only", "reduced_component_sm_only"])
    ]
    met_conditioned = var_conditioned[
        var_conditioned["condition_bin"].astype(str).eq("combined")
        & var_conditioned["sm_pool"].eq("all_luminosity_weighted_sm")
        & var_conditioned["condition_variable"].eq("MET_pt")
    ].copy()
    pmissing_conditioned = var_conditioned[
        var_conditioned["condition_bin"].astype(str).eq("combined")
        & var_conditioned["sm_pool"].eq("all_luminosity_weighted_sm")
        & var_conditioned["condition_variable"].eq("P_missing")
    ].copy()

    report = f"""# Full-Luminosity N-Frame v3 Mismatch Diagnostics

## Purpose

Run the N-Frame v3 missing-residual boundary score against the full available luminosity-weighted SM model, then test whether the effect is explainable as residual MET/P_missing calibration or SM trigger-sample mismatch.

The v3 score is:

`B_NF_v3_real_boundary_score = resid_P_missing`

## Critical Scope Note

The SM side is luminosity-weighted simulation. The real side is the extracted 49,143-event independent Run2016H MiniAOD validation sample, not the full Run2016H delivered-luminosity dataset. Therefore these tests are shape-normalized to the real sample size. They are not absolute event-yield discovery significances.

## Audit

{audit.to_markdown(index=False)}

## Full Luminosity-Weighted SM Result

Standard-score-conditioned top-5% v3 tail using all available weighted SM rows:

{main_cond[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed','p_upward','p_downward']].to_markdown(index=False)}

## Component/Trigger Robustness

Full-component SM only:

{full_cond[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

Reduced-component SM only:

{red_cond[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

HLT-matched full-component subset:

{hlt_cond[['primary_dataset','sm_pool','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

## Raw Missing-Energy Conditioning Stress Test

MET-conditioned top-5% v3 tail using all luminosity-weighted SM:

{met_conditioned[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

P_missing-conditioned top-5% v3 tail using all luminosity-weighted SM:

{pmissing_conditioned[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

## MET / P_missing / Residual Calibration Summary

{cal[['primary_dataset','sm_pool','source','variable','weighted_mean','q05','q50','q95','q99']].to_markdown(index=False)}

## Interpretation

If the v3 excess remains with all luminosity-weighted SM, full-component SM, reduced-component SM, and HLT-matched SM, then it is not simply caused by mixing trigger streams. However, if the v3 score remains almost perfectly correlated with raw MET/P_missing in real data, and the effect changes under MET/P_missing conditioning, then missing-energy calibration or simulation-modelling mismatch remains a live explanation.

This diagnostic is designed to distinguish a robust N-Frame real-boundary anomaly from a calibration/background mismatch. It does not by itself prove SUSY or bulk-space dynamics.
"""
    (REPORTS / "01_FULL_LUMI_V3_MISMATCH_DIAGNOSTICS_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Full-Luminosity v3 Diagnostics

We reran the N-Frame v3 missing-residual score against the full available luminosity-weighted SM table and compared it with full-component, reduced-component, and HLT-matched SM subsets.

Full luminosity-weighted SM, standard-score-conditioned top-5% v3 tail:

{main_cond[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

MET-conditioned stress test:

{met_conditioned[['primary_dataset','real_observed','expected_shape_normalized','observed_over_expected','Z_signed']].to_markdown(index=False)}

This tests the v3 result against the complete weighted SM shape, not only the HLT-tagged subset. The remaining question is calibration: in real data, `resid_P_missing` is almost perfectly correlated with raw MET/P_missing, so missing-energy modelling is not ruled out by this pass.
"""
    (REPORTS / "02_SHORT_UPDATE_FULL_LUMI_V3_DIAGNOSTICS.md").write_text(short, encoding="utf-8")

    print("FULL-LUMI V3 MISMATCH DIAGNOSTICS COMPLETE")
    print(main_cond[["primary_dataset", "real_observed", "expected_shape_normalized", "observed_over_expected", "Z_signed"]].to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
