from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, norm
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_realdata_residual_nframe_v2_trace_test"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

BENCHMARK_DATA = ROOT / "outputs_trace_predictive_significance/sources/primary_trace_available_balanced_dataset.csv"
WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
REAL_RUN2016H = ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv"

STANDARD = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
STD_ENG = ["log1p_MET_pt", "log1p_HT", "jet_btag_ratio", "met_ht_ratio"]
NFRAME_COMPONENTS = [
    "B_NF_z",
    "displacement_reconstruction_axis",
    "missing_visible_axis",
    "qcd_like_axis",
    "trace_alignment_score",
    "P_displacement",
    "P_reconstruction",
    "P_missing",
    "P_visible",
    "P_multiplicity",
    "P_btag",
    "P_compression",
]
RESID_COLS = [f"resid_{c}" for c in NFRAME_COMPONENTS]
STANDARD_FEATURES = STANDARD + STD_ENG
NFRAME_V2_FEATURES = STANDARD + STD_ENG + RESID_COLS


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def first_available(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype="float64")
    for col in cols:
        if col in df.columns:
            out = out.combine_first(pd.to_numeric(df[col], errors="coerce"))
    return out


def normalise_schema(df: pd.DataFrame, label: str) -> pd.DataFrame:
    out = df.copy()
    for col in STANDARD + ["N_primary_vertices", "secondary_vertex_count", "packed_candidate_count", "event_weight"]:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["B_NF_z"] = first_available(
        out,
        [
            "B_NF_z",
            "B_NF_fitted_frozen_z_real_scaled",
            "B_NF_fitted_run2016h_z",
            "B_NF_fitted_expanded_run2016h_z",
            "B_NF_fitted_z",
        ],
    )
    out["P_displacement"] = first_available(
        out,
        [
            "P_displacement",
            "B_P_displacement_proxy",
            "run2016h_P_displacement_proxy",
            "expanded_P_displacement_proxy",
            "fitted_P_displacement_proxy",
        ],
    )
    out["P_reconstruction"] = first_available(
        out,
        [
            "P_reconstruction",
            "B_P_reconstruction",
            "run2016h_P_reconstruction",
            "expanded_P_reconstruction",
            "fitted_P_reconstruction",
        ],
    )
    out["P_missing"] = first_available(
        out,
        ["P_missing", "B_P_missing", "run2016h_P_missing", "expanded_P_missing", "fitted_P_missing"],
    )
    out["P_visible"] = first_available(
        out,
        [
            "P_visible",
            "B_P_visible_energy",
            "run2016h_P_visible_energy",
            "expanded_P_visible_energy",
            "fitted_P_visible_energy",
        ],
    )
    out["P_multiplicity"] = first_available(
        out,
        [
            "P_multiplicity",
            "B_P_multiplicity",
            "run2016h_P_multiplicity",
            "expanded_P_multiplicity",
            "fitted_P_multiplicity",
        ],
    )
    out["P_btag"] = first_available(
        out,
        [
            "P_btag",
            "B_P_btag_structure",
            "run2016h_P_btag_structure",
            "expanded_P_btag_structure",
            "fitted_P_btag_structure",
        ],
    )
    out["P_compression"] = first_available(
        out,
        [
            "P_compression",
            "B_P_compression",
            "run2016h_P_compression",
            "expanded_P_compression",
            "fitted_P_compression",
        ],
    )
    out["displacement_reconstruction_axis"] = first_available(out, ["displacement_reconstruction_axis"])
    miss = out["displacement_reconstruction_axis"].isna()
    out.loc[miss, "displacement_reconstruction_axis"] = (
        out.loc[miss, "P_displacement"] + out.loc[miss, "P_reconstruction"]
    )
    out["missing_visible_axis"] = first_available(out, ["missing_visible_axis"])
    miss = out["missing_visible_axis"].isna()
    out.loc[miss, "missing_visible_axis"] = out.loc[miss, "P_missing"] + out.loc[miss, "P_visible"]
    out["qcd_like_axis"] = first_available(out, ["qcd_like_axis"])
    miss = out["qcd_like_axis"].isna()
    out.loc[miss, "qcd_like_axis"] = out.loc[miss, ["P_visible", "P_multiplicity", "P_btag"]].mean(axis=1)
    out["trace_alignment_score"] = first_available(out, ["trace_alignment_score"])
    miss = out["trace_alignment_score"].isna()
    out.loc[miss, "trace_alignment_score"] = (
        out.loc[miss, "B_NF_z"]
        + out.loc[miss, "displacement_reconstruction_axis"]
        - out.loc[miss, "missing_visible_axis"].clip(lower=0)
    )

    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["jet_btag_ratio"] = out["N_btags_medium"] / (out["N_jets_30"].abs() + 1.0)
    out["met_ht_ratio"] = out["MET_pt"] / (out["HT"].abs() + 1.0)
    out["analysis_source"] = label
    if "primary_dataset" not in out.columns:
        out["primary_dataset"] = out.get("process_family_norm", "unknown")
    out["primary_dataset"] = out["primary_dataset"].fillna("unknown").astype(str)
    if "process_label" not in out.columns:
        out["process_label"] = out.get("process_family_norm", "unknown")
    out["process_label"] = out["process_label"].fillna("unknown").astype(str)
    return out


def fit_residualizer(reference: pd.DataFrame) -> dict[str, dict[str, np.ndarray | float]]:
    x = reference[STANDARD].copy()
    imputer = SimpleImputer(strategy="median")
    x_arr = imputer.fit_transform(x)
    mu = x_arr.mean(axis=0)
    sd = x_arr.std(axis=0)
    sd[sd == 0] = 1.0
    z = (x_arr - mu) / sd
    design = np.column_stack([np.ones(len(z)), z])
    params = {"__imputer_statistics__": {"median": imputer.statistics_, "mu": mu, "sd": sd}}
    for col in NFRAME_COMPONENTS:
        y = pd.to_numeric(reference[col], errors="coerce").to_numpy(dtype=float)
        fill = float(np.nanmedian(y))
        y = np.where(np.isfinite(y), y, fill)
        coef, *_ = np.linalg.lstsq(design, y, rcond=None)
        params[col] = {"coef": coef, "fill": fill}
    return params


def apply_residualizer(df: pd.DataFrame, params: dict[str, dict[str, np.ndarray | float]]) -> pd.DataFrame:
    out = df.copy()
    stats = params["__imputer_statistics__"]
    x = out[STANDARD].to_numpy(dtype=float)
    med = np.asarray(stats["median"], dtype=float)
    inds = np.where(~np.isfinite(x))
    if len(inds[0]):
        x[inds] = np.take(med, inds[1])
    z = (x - np.asarray(stats["mu"], dtype=float)) / np.asarray(stats["sd"], dtype=float)
    design = np.column_stack([np.ones(len(z)), z])
    for col in NFRAME_COMPONENTS:
        coef = np.asarray(params[col]["coef"], dtype=float)
        fill = float(params[col]["fill"])
        actual = pd.to_numeric(out[col], errors="coerce").to_numpy(dtype=float)
        actual = np.where(np.isfinite(actual), actual, fill)
        out[f"resid_{col}"] = actual - design @ coef
    return out


def model() -> object:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        HistGradientBoostingClassifier(
            max_iter=250,
            learning_rate=0.06,
            max_leaf_nodes=31,
            l2_regularization=0.05,
            random_state=164,
        ),
    )


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / np.sum(weights)
    return float(np.interp(quantile, cdf, values))


def one_sided_count_z(observed: int, total: int, expected_fraction: float) -> tuple[float, float, float]:
    expected_fraction = float(np.clip(expected_fraction, 1e-12, 1 - 1e-12))
    expected = total * expected_fraction
    variance = total * expected_fraction * (1 - expected_fraction)
    z = (observed - expected) / np.sqrt(max(variance, 1e-12))
    p = float(binom.sf(observed - 1, total, expected_fraction)) if observed >= expected else float(1.0)
    return expected, p, float(norm.isf(p)) if p > 0 else float("inf")


def score_frame(df: pd.DataFrame, std_model: object, nf_model: object) -> pd.DataFrame:
    out = df.copy()
    out["standard_score"] = std_model.predict_proba(out[STANDARD_FEATURES])[:, 1]
    out["nframe_v2_trace_score"] = nf_model.predict_proba(out[NFRAME_V2_FEATURES])[:, 1]
    out["nframe_v2_over_standard"] = out["nframe_v2_trace_score"] - out["standard_score"]
    return out


def global_tail_test(real: pd.DataFrame, sm: pd.DataFrame) -> pd.DataFrame:
    weights = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=float)
    rows = []
    for score_col in ["standard_score", "nframe_v2_trace_score", "nframe_v2_over_standard"]:
        sm_score = pd.to_numeric(sm[score_col], errors="coerce").to_numpy(dtype=float)
        real_score = pd.to_numeric(real[score_col], errors="coerce").to_numpy(dtype=float)
        for frac in [0.10, 0.05, 0.01, 0.005, 0.001]:
            threshold = weighted_quantile(sm_score, weights, 1.0 - frac)
            sm_tail_w = float(weights[sm_score >= threshold].sum())
            expected_fraction = sm_tail_w / float(weights.sum())
            observed = int((real_score >= threshold).sum())
            expected, p, z = one_sided_count_z(observed, len(real_score), expected_fraction)
            rows.append(
                {
                    "score": score_col,
                    "tail_label": f"SM_weighted_top_{frac:g}",
                    "tail_threshold": threshold,
                    "sm_expected_fraction": expected_fraction,
                    "real_observed": observed,
                    "real_total": len(real_score),
                    "expected_if_sm_shape": expected,
                    "observed_over_expected": observed / expected if expected > 0 else np.inf,
                    "one_sided_p_upward": p,
                    "one_sided_Z_upward": z,
                }
            )
    return pd.DataFrame(rows)


def conditional_tail_test(real: pd.DataFrame, sm: pd.DataFrame, n_bins: int = 10, tail_frac: float = 0.05) -> pd.DataFrame:
    weights = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=float)
    standard_sm = pd.to_numeric(sm["standard_score"], errors="coerce").to_numpy(dtype=float)
    edges = [weighted_quantile(standard_sm, weights, q) for q in np.linspace(0, 1, n_bins + 1)]
    edges[0] = -np.inf
    edges[-1] = np.inf
    rows = []
    total_obs = 0
    total_exp = 0.0
    total_var = 0.0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        sm_bin = (sm["standard_score"] >= lo) & (sm["standard_score"] < hi)
        real_bin = (real["standard_score"] >= lo) & (real["standard_score"] < hi)
        if sm_bin.sum() < 20 or real_bin.sum() == 0:
            continue
        sm_scores = sm.loc[sm_bin, "nframe_v2_over_standard"].to_numpy(dtype=float)
        sm_w = pd.to_numeric(sm.loc[sm_bin, "event_weight"], errors="coerce").fillna(1.0).to_numpy(dtype=float)
        threshold = weighted_quantile(sm_scores, sm_w, 1.0 - tail_frac)
        expected_fraction = float(sm_w[sm_scores >= threshold].sum() / sm_w.sum())
        real_scores = real.loc[real_bin, "nframe_v2_over_standard"].to_numpy(dtype=float)
        obs = int((real_scores >= threshold).sum())
        n = int(real_bin.sum())
        expected, p, z = one_sided_count_z(obs, n, expected_fraction)
        total_obs += obs
        total_exp += expected
        total_var += n * expected_fraction * (1 - expected_fraction)
        rows.append(
            {
                "standard_score_bin": i,
                "standard_score_low": lo,
                "standard_score_high": hi,
                "real_bin_n": n,
                "tail_threshold_on_residual_trace": threshold,
                "sm_expected_fraction_in_bin": expected_fraction,
                "real_observed_tail": obs,
                "expected_tail_if_sm_shape": expected,
                "observed_over_expected": obs / expected if expected > 0 else np.inf,
                "one_sided_Z_upward": z,
            }
        )
    combined_z = (total_obs - total_exp) / np.sqrt(max(total_var, 1e-12))
    rows.append(
        {
            "standard_score_bin": "combined",
            "standard_score_low": np.nan,
            "standard_score_high": np.nan,
            "real_bin_n": int(len(real)),
            "tail_threshold_on_residual_trace": np.nan,
            "sm_expected_fraction_in_bin": np.nan,
            "real_observed_tail": int(total_obs),
            "expected_tail_if_sm_shape": float(total_exp),
            "observed_over_expected": float(total_obs / total_exp) if total_exp > 0 else np.inf,
            "one_sided_Z_upward": float(combined_z),
        }
    )
    return pd.DataFrame(rows)


def dataset_composition(real: pd.DataFrame) -> pd.DataFrame:
    rows = []
    thresholds = {
        "top10": real["nframe_v2_over_standard"].quantile(0.90),
        "top05": real["nframe_v2_over_standard"].quantile(0.95),
        "top01": real["nframe_v2_over_standard"].quantile(0.99),
    }
    for label, thr in thresholds.items():
        tail = real[real["nframe_v2_over_standard"] >= thr]
        counts = tail["primary_dataset"].value_counts()
        base = real["primary_dataset"].value_counts()
        for ds in sorted(base.index):
            rows.append(
                {
                    "tail_label": label,
                    "primary_dataset": ds,
                    "tail_count": int(counts.get(ds, 0)),
                    "tail_fraction": float(counts.get(ds, 0) / max(len(tail), 1)),
                    "overall_count": int(base.get(ds, 0)),
                    "overall_fraction": float(base.get(ds, 0) / len(real)),
                    "enrichment_vs_overall": float((counts.get(ds, 0) / max(len(tail), 1)) / (base.get(ds, 0) / len(real))),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    benchmark = normalise_schema(pd.read_csv(BENCHMARK_DATA, low_memory=False), "benchmark_training")
    benchmark["target"] = pd.to_numeric(benchmark["target"], errors="coerce").astype(int)
    residualizer = fit_residualizer(benchmark)
    benchmark = apply_residualizer(benchmark, residualizer)

    std_model = model()
    nf_model = model()
    std_model.fit(benchmark[STANDARD_FEATURES], benchmark["target"])
    nf_model.fit(benchmark[NFRAME_V2_FEATURES], benchmark["target"])

    sm = normalise_schema(pd.read_csv(WEIGHTED_SM, low_memory=False), "weighted_sm")
    sm = sm[sm["event_weight"].notna()].copy()
    sm = apply_residualizer(sm, residualizer)
    sm_scored = score_frame(sm, std_model, nf_model)

    real = normalise_schema(pd.read_csv(REAL_RUN2016H, low_memory=False), "run2016h_real_miniaod")
    real = apply_residualizer(real, residualizer)
    real_scored = score_frame(real, std_model, nf_model)

    keep_cols = [
        "primary_dataset",
        "sample_id",
        "record_id",
        "run",
        "lumi",
        "event",
        "source_file",
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "secondary_vertex_count",
        "packed_candidate_count",
        "standard_score",
        "nframe_v2_trace_score",
        "nframe_v2_over_standard",
    ] + RESID_COLS
    real_scored[keep_cols].to_csv(SOURCES / "run2016h_real_miniaod_scored_with_residual_nframe_v2.csv", index=False)
    sm_scored.sample(min(len(sm_scored), 100000), random_state=164).to_csv(
        SOURCES / "weighted_sm_scored_with_residual_nframe_v2_sample.csv", index=False
    )

    audit = pd.DataFrame(
        [
            {"item": "benchmark_training_rows", "value": len(benchmark), "source": str(BENCHMARK_DATA.relative_to(ROOT))},
            {"item": "weighted_sm_rows", "value": len(sm_scored), "source": str(WEIGHTED_SM.relative_to(ROOT))},
            {"item": "real_run2016h_rows", "value": len(real_scored), "source": str(REAL_RUN2016H.relative_to(ROOT))},
            {"item": "real_jetht_rows", "value": int((real_scored["primary_dataset"] == "JetHT").sum()), "source": ""},
            {"item": "real_met_rows", "value": int((real_scored["primary_dataset"] == "MET").sum()), "source": ""},
            {"item": "real_singlemuon_rows", "value": int((real_scored["primary_dataset"] == "SingleMuon").sum()), "source": ""},
        ]
    )
    global_tests = global_tail_test(real_scored, sm_scored)
    conditional_tests = conditional_tail_test(real_scored, sm_scored, n_bins=10, tail_frac=0.05)
    comp = dataset_composition(real_scored)
    top_candidates = real_scored.sort_values("nframe_v2_over_standard", ascending=False).head(200)[keep_cols]

    audit.to_csv(TABLES / "00_realdata_v2_trace_audit.csv", index=False)
    global_tests.to_csv(TABLES / "01_real_vs_weighted_sm_global_tail_tests.csv", index=False)
    conditional_tests.to_csv(TABLES / "02_standard_score_conditioned_residual_trace_tail_test.csv", index=False)
    comp.to_csv(TABLES / "03_real_high_trace_tail_primary_dataset_composition.csv", index=False)
    top_candidates.to_csv(TABLES / "04_top_real_residual_nframe_v2_candidates.csv", index=False)

    best_global = global_tests[
        global_tests["score"].eq("nframe_v2_over_standard") & global_tests["tail_label"].eq("SM_weighted_top_0.01")
    ].iloc[0]
    combined = conditional_tests[conditional_tests["standard_score_bin"].astype(str).eq("combined")].iloc[0]

    report = f"""# Residual N-Frame v2 Real-Data Trace Test

## Question

Does the improved residual N-Frame v2 trace model point to an excess-like high-trace population in real CMS Run2016H MiniAOD data, compared with the best available weighted SM simulation shape?

This is still exploratory. It is a real-data trace test, not a SUSY particle-discovery claim.

## Data used

{audit.to_markdown(index=False)}

## Main result

Global weighted-SM top-1% residual-trace threshold:

- Real observed high residual-trace events: {int(best_global['real_observed'])}
- Expected if weighted-SM shape held after total-count normalization: {float(best_global['expected_if_sm_shape']):.2f}
- Observed / expected: {float(best_global['observed_over_expected']):.3f}
- Upward Z: {float(best_global['one_sided_Z_upward']):.3f} sigma

Standard-score-conditioned residual trace tail test:

- Real observed conditioned high residual-trace events: {int(combined['real_observed_tail'])}
- Expected if SM residual-trace shape held inside standard-score bins: {float(combined['expected_tail_if_sm_shape']):.2f}
- Observed / expected: {float(combined['observed_over_expected']):.3f}
- Combined upward Z: {float(combined['one_sided_Z_upward']):.3f} sigma

## Interpretation

If this Z is positive and large, it means real CMS data contains more high residual-N-Frame trace events than the weighted SM shape predicts, even after conditioning on the standard CMS-like score. If it is small or negative, the improved model is strong in benchmark discrimination but has not yet produced real-data trace evidence.

This test is a bridge between the benchmark trace-pattern result and the stronger claim Darren wants. It does not by itself prove particles are hidden in bulk space.

## Global tail tests

{global_tests.to_markdown(index=False)}

## Standard-score-conditioned test

{conditional_tests.to_markdown(index=False)}

## Real high-trace primary-dataset composition

{comp.to_markdown(index=False)}
"""
    (REPORTS / "01_RESIDUAL_NFRAME_V2_REALDATA_TRACE_TEST_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Residual N-Frame v2 Real-Data Trace Test

We trained the exploratory residual N-Frame v2 model from the benchmark layer and applied it to independent real CMS Run2016H MiniAOD data.

The key real-data check was the residual N-Frame trace tail after comparing with weighted SM simulation and after conditioning on the standard CMS-like score.

Results:

- Global top-1% residual-trace tail: observed {int(best_global['real_observed'])}, expected {float(best_global['expected_if_sm_shape']):.2f}, Z = {float(best_global['one_sided_Z_upward']):.3f} sigma.
- Standard-score-conditioned residual-trace tail: observed {int(combined['real_observed_tail'])}, expected {float(combined['expected_tail_if_sm_shape']):.2f}, Z = {float(combined['one_sided_Z_upward']):.3f} sigma.

Interpretation: this is the first direct bridge test asking whether the improved N-Frame trace appears in real CMS boundary data, not just benchmark simulation.
"""
    (REPORTS / "02_SHORT_UPDATE_RESIDUAL_NFRAME_V2_REALDATA_TRACE_TEST.md").write_text(short, encoding="utf-8")

    print("RESIDUAL N-FRAME V2 REAL-DATA TRACE TEST COMPLETE")
    print(audit.to_string(index=False))
    print(global_tests[global_tests["score"].eq("nframe_v2_over_standard")].to_string(index=False))
    print(conditional_tests.tail(1).to_string(index=False))
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
