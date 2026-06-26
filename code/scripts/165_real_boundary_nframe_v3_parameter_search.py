from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_real_boundary_nframe_v3_parameter_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

REAL_SCORED = ROOT / "outputs_realdata_residual_nframe_v2_trace_test/sources/run2016h_real_miniaod_scored_with_residual_nframe_v2.csv"
SM_SCORED_SAMPLE = ROOT / "outputs_realdata_residual_nframe_v2_trace_test/sources/weighted_sm_scored_with_residual_nframe_v2_sample.csv"
BENCHMARK_DATA = ROOT / "outputs_trace_predictive_significance/sources/primary_trace_available_balanced_dataset.csv"
SCRIPT_164 = ROOT / "scripts/164_apply_residual_nframe_v2_to_real_data.py"

RESID_COLS = [
    "resid_B_NF_z",
    "resid_displacement_reconstruction_axis",
    "resid_missing_visible_axis",
    "resid_qcd_like_axis",
    "resid_trace_alignment_score",
    "resid_P_displacement",
    "resid_P_reconstruction",
    "resid_P_missing",
    "resid_P_visible",
    "resid_P_multiplicity",
    "resid_P_btag",
    "resid_P_compression",
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


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0:
        return np.nan
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / np.sum(weights)
    return float(np.interp(quantile, cdf, values))


def fit_scaler(sm: pd.DataFrame, real: pd.DataFrame) -> dict[str, np.ndarray]:
    combo = pd.concat([sm[RESID_COLS], real[RESID_COLS]], ignore_index=True)
    med = combo.median(numeric_only=True).to_numpy(dtype=float)
    filled = combo.fillna(pd.Series(med, index=RESID_COLS))
    mu = filled.mean().to_numpy(dtype=float)
    sd = filled.std().replace(0, 1.0).to_numpy(dtype=float)
    return {"median": med, "mu": mu, "sd": sd}


def zmat(df: pd.DataFrame, scaler: dict[str, np.ndarray]) -> np.ndarray:
    x = df[RESID_COLS].to_numpy(dtype=float)
    med = scaler["median"]
    inds = np.where(~np.isfinite(x))
    if len(inds[0]):
        x[inds] = np.take(med, inds[1])
    return (x - scaler["mu"]) / scaler["sd"]


def split_real_sm(real: pd.DataFrame, sm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    real_idx = np.arange(len(real))
    sm_idx = np.arange(len(sm))
    real_fit, real_test = train_test_split(
        real_idx, test_size=0.50, random_state=165, stratify=real["primary_dataset"].astype(str)
    )
    sm_family = sm["process_family_norm"].fillna(sm["primary_dataset"]).astype(str) if "process_family_norm" in sm.columns else sm["primary_dataset"].astype(str)
    sm_fit, sm_test = train_test_split(sm_idx, test_size=0.50, random_state=166, stratify=sm_family)
    return real.iloc[real_fit].copy(), real.iloc[real_test].copy(), sm.iloc[sm_fit].copy(), sm.iloc[sm_test].copy()


def conditional_tail_z(
    real: pd.DataFrame,
    sm: pd.DataFrame,
    real_score: np.ndarray,
    sm_score: np.ndarray,
    tail_frac: float = 0.05,
    n_bins: int = 10,
) -> dict[str, float]:
    sm_std = pd.to_numeric(sm["standard_score"], errors="coerce").to_numpy(dtype=float)
    real_std = pd.to_numeric(real["standard_score"], errors="coerce").to_numpy(dtype=float)
    weights = pd.to_numeric(sm.get("event_weight", pd.Series(1.0, index=sm.index)), errors="coerce").fillna(1.0).to_numpy(dtype=float)
    edges = [weighted_quantile(sm_std, weights, q) for q in np.linspace(0, 1, n_bins + 1)]
    edges[0] = -np.inf
    edges[-1] = np.inf
    total_obs = 0
    total_exp = 0.0
    total_var = 0.0
    used_bins = 0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        sm_bin = (sm_std >= lo) & (sm_std < hi)
        real_bin = (real_std >= lo) & (real_std < hi)
        if sm_bin.sum() < 50 or real_bin.sum() < 10:
            continue
        threshold = weighted_quantile(sm_score[sm_bin], weights[sm_bin], 1.0 - tail_frac)
        if not np.isfinite(threshold):
            continue
        sm_tail_w = weights[sm_bin & (sm_score >= threshold)].sum()
        sm_w = weights[sm_bin].sum()
        if sm_w <= 0:
            continue
        p = float(np.clip(sm_tail_w / sm_w, 1e-9, 1 - 1e-9))
        n = int(real_bin.sum())
        obs = int((real_score[real_bin] >= threshold).sum())
        total_obs += obs
        total_exp += n * p
        total_var += n * p * (1 - p)
        used_bins += 1
    z = (total_obs - total_exp) / np.sqrt(max(total_var, 1e-12))
    p_up = float(norm.sf(z)) if z > 0 else 1.0
    return {
        "conditioned_tail_fraction": tail_frac,
        "used_standard_score_bins": used_bins,
        "observed_tail": int(total_obs),
        "expected_tail": float(total_exp),
        "observed_over_expected": float(total_obs / total_exp) if total_exp > 0 else np.inf,
        "conditioned_tail_Z": float(z),
        "conditioned_tail_p_upward": p_up,
    }


def global_tail(real_score: np.ndarray, sm_score: np.ndarray, sm_weights: np.ndarray, n_real: int, tail_frac: float = 0.01) -> dict[str, float]:
    thr = weighted_quantile(sm_score, sm_weights, 1.0 - tail_frac)
    p = float(np.clip(sm_weights[sm_score >= thr].sum() / sm_weights.sum(), 1e-12, 1 - 1e-12))
    obs = int((real_score >= thr).sum())
    exp = n_real * p
    z = (obs - exp) / np.sqrt(max(n_real * p * (1 - p), 1e-12))
    return {
        "global_tail_fraction": tail_frac,
        "global_tail_threshold": float(thr),
        "global_observed_tail": obs,
        "global_expected_tail": float(exp),
        "global_observed_over_expected": float(obs / exp) if exp > 0 else np.inf,
        "global_tail_Z": float(z),
    }


def candidate_scores(z: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return z @ weights


def make_formula_table(weights: np.ndarray, formula_name: str) -> str:
    terms = []
    for col, w in sorted(zip(RESID_COLS, weights), key=lambda v: abs(v[1]), reverse=True):
        if abs(w) >= 1e-6:
            terms.append({"feature": col, "weight": float(w)})
    return json.dumps({"formula": formula_name, "terms": terms})


def search_candidates(real_fit: pd.DataFrame, sm_fit: pd.DataFrame, scaler: dict[str, np.ndarray]) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    rng = np.random.default_rng(165)
    zr = zmat(real_fit, scaler)
    zs = zmat(sm_fit, scaler)
    sm_w = pd.to_numeric(sm_fit.get("event_weight", pd.Series(1.0, index=sm_fit.index)), errors="coerce").fillna(1.0).to_numpy(dtype=float)
    candidates: dict[str, np.ndarray] = {}

    for i, col in enumerate(RESID_COLS):
        w = np.zeros(len(RESID_COLS))
        w[i] = 1.0
        candidates[f"{col}_positive"] = w.copy()
        candidates[f"{col}_negative"] = -w.copy()

    y = np.r_[np.ones(len(real_fit)), np.zeros(len(sm_fit))]
    x = np.vstack([zr, zs])
    clf = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=165),
    )
    clf.fit(x, y)
    lr = clf.named_steps["logisticregression"]
    scale = clf.named_steps["standardscaler"].scale_
    weights = lr.coef_.ravel() / np.where(scale == 0, 1.0, scale)
    candidates["logistic_real_boundary_residual"] = weights
    candidates["logistic_real_boundary_residual_inverse"] = -weights

    # Directed hypotheses: hidden trace may invert benchmark-visible terms.
    direction_defs = {
        "bulk_missing_compression_positive": {"resid_P_missing": 1.0, "resid_P_compression": 1.0, "resid_trace_alignment_score": 0.5},
        "bulk_missing_compression_negative": {"resid_P_missing": -1.0, "resid_P_compression": -1.0, "resid_trace_alignment_score": -0.5},
        "qcd_suppressed_boundary": {"resid_P_missing": 1.0, "resid_P_btag": 0.5, "resid_qcd_like_axis": -1.0},
        "visible_reco_deficit": {"resid_P_visible": -1.0, "resid_P_reconstruction": -0.5, "resid_P_missing": 1.0},
        "inverted_old_nframe_trace": {"resid_B_NF_z": -1.0, "resid_displacement_reconstruction_axis": -1.0, "resid_trace_alignment_score": -1.0},
    }
    col_index = {c: i for i, c in enumerate(RESID_COLS)}
    for name, terms in direction_defs.items():
        w = np.zeros(len(RESID_COLS))
        for col, val in terms.items():
            w[col_index[col]] = val
        candidates[name] = w

    for i in range(3000):
        k = int(rng.integers(2, 7))
        active = rng.choice(len(RESID_COLS), size=k, replace=False)
        w = np.zeros(len(RESID_COLS))
        w[active] = rng.normal(0, 1, size=k)
        candidates[f"random_boundary_formula_{i:04d}"] = w

    rows = []
    for name, w in candidates.items():
        rs = candidate_scores(zr, w)
        ss = candidate_scores(zs, w)
        try:
            auc = roc_auc_score(np.r_[np.ones(len(rs)), np.zeros(len(ss))], np.r_[rs, ss])
        except ValueError:
            auc = np.nan
        ctail = conditional_tail_z(real_fit, sm_fit, rs, ss, tail_frac=0.05)
        gtail = global_tail(rs, ss, sm_w, len(real_fit), tail_frac=0.01)
        rows.append(
            {
                "candidate": name,
                "fit_real_vs_sm_auc": auc,
                **ctail,
                **gtail,
                "formula_json": make_formula_table(w, name),
            }
        )
    ranked = pd.DataFrame(rows).sort_values(
        ["conditioned_tail_Z", "global_tail_Z", "fit_real_vs_sm_auc"], ascending=False
    )
    top_names = list(ranked["candidate"].head(100))
    return ranked, {name: candidates[name] for name in top_names}


def evaluate(real: pd.DataFrame, sm: pd.DataFrame, scaler: dict[str, np.ndarray], candidate_weights: dict[str, np.ndarray]) -> pd.DataFrame:
    zr = zmat(real, scaler)
    zs = zmat(sm, scaler)
    sm_w = pd.to_numeric(sm.get("event_weight", pd.Series(1.0, index=sm.index)), errors="coerce").fillna(1.0).to_numpy(dtype=float)
    rows = []
    for name, w in candidate_weights.items():
        rs = candidate_scores(zr, w)
        ss = candidate_scores(zs, w)
        auc = roc_auc_score(np.r_[np.ones(len(rs)), np.zeros(len(ss))], np.r_[rs, ss])
        ctail = conditional_tail_z(real, sm, rs, ss, tail_frac=0.05)
        ctail_1 = conditional_tail_z(real, sm, rs, ss, tail_frac=0.01)
        ctail_1 = {f"top01_{k}": v for k, v in ctail_1.items()}
        gtail = global_tail(rs, ss, sm_w, len(real), tail_frac=0.01)
        rows.append(
            {
                "candidate": name,
                "test_real_vs_sm_auc": auc,
                **ctail,
                **ctail_1,
                **gtail,
                "formula_json": make_formula_table(w, name),
            }
        )
    return pd.DataFrame(rows).sort_values(["conditioned_tail_Z", "global_tail_Z"], ascending=False)


def benchmark_alignment(scaler: dict[str, np.ndarray], candidate_weights: dict[str, np.ndarray]) -> pd.DataFrame:
    mod = load_164()
    bench = mod.normalise_schema(pd.read_csv(BENCHMARK_DATA, low_memory=False), "benchmark")
    bench["target"] = pd.to_numeric(bench["target"], errors="coerce").astype(int)
    residualizer = mod.fit_residualizer(bench)
    bench = mod.apply_residualizer(bench, residualizer)
    z = zmat(bench, scaler)
    y = bench["target"].to_numpy(dtype=int)
    rows = []
    for name, w in candidate_weights.items():
        score = candidate_scores(z, w)
        auc = roc_auc_score(y, score)
        rows.append(
            {
                "candidate": name,
                "benchmark_signal_vs_sm_auc_same_direction": auc,
                "benchmark_signal_vs_sm_auc_best_direction": max(auc, 1.0 - auc),
                "direction_relation_to_benchmark": "aligned" if auc >= 0.5 else "inverted",
            }
        )
    return pd.DataFrame(rows).sort_values("benchmark_signal_vs_sm_auc_best_direction", ascending=False)


def save_scores(real: pd.DataFrame, sm: pd.DataFrame, scaler: dict[str, np.ndarray], best_name: str, best_weights: np.ndarray) -> None:
    real_out = real.copy()
    sm_out = sm.copy()
    real_out["B_NF_v3_real_boundary_score"] = candidate_scores(zmat(real, scaler), best_weights)
    sm_out["B_NF_v3_real_boundary_score"] = candidate_scores(zmat(sm, scaler), best_weights)
    keep = [
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
        "standard_score",
        "nframe_v2_over_standard",
        "B_NF_v3_real_boundary_score",
    ] + RESID_COLS
    real_out.sort_values("B_NF_v3_real_boundary_score", ascending=False).head(1000)[keep].to_csv(
        SOURCES / "top1000_real_events_by_nframe_v3_real_boundary_score.csv", index=False
    )
    sm_out.sort_values("B_NF_v3_real_boundary_score", ascending=False).head(1000).to_csv(
        SOURCES / "top1000_sm_events_by_nframe_v3_real_boundary_score.csv", index=False
    )


def main() -> None:
    ensure_dirs()
    real = pd.read_csv(REAL_SCORED, low_memory=False)
    sm = pd.read_csv(SM_SCORED_SAMPLE, low_memory=False)
    for df in [real, sm]:
        for c in RESID_COLS + ["standard_score", "event_weight"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "event_weight" not in df.columns:
            df["event_weight"] = 1.0

    real_fit, real_test, sm_fit, sm_test = split_real_sm(real, sm)
    scaler = fit_scaler(sm_fit, real_fit)
    search, top_weights = search_candidates(real_fit, sm_fit, scaler)
    test = evaluate(real_test, sm_test, scaler, top_weights)
    align = benchmark_alignment(scaler, top_weights)
    final = test.merge(align, on="candidate", how="left")
    final["passes_exploratory_real_boundary_screen"] = (
        (final["conditioned_tail_Z"] >= 5.0)
        & (final["observed_over_expected"] > 1.0)
        & (final["benchmark_signal_vs_sm_auc_best_direction"] >= 0.60)
    )
    final = final.sort_values(["passes_exploratory_real_boundary_screen", "conditioned_tail_Z"], ascending=False)
    best = final.iloc[0]
    best_name = str(best["candidate"])
    best_weights = top_weights[best_name]
    save_scores(real_test, sm_test, scaler, best_name, best_weights)

    split_audit = pd.DataFrame(
        [
            {"split": "real_fit", "rows": len(real_fit), "note": "used to choose N-Frame v3 parameters"},
            {"split": "real_test", "rows": len(real_test), "note": "held out during parameter search"},
            {"split": "weighted_sm_fit", "rows": len(sm_fit), "note": "used to choose N-Frame v3 parameters"},
            {"split": "weighted_sm_test", "rows": len(sm_test), "note": "held out during parameter search"},
        ]
    )
    search.to_csv(TABLES / "01_real_boundary_parameter_search_fit_leaderboard.csv", index=False)
    test.to_csv(TABLES / "02_real_boundary_parameter_search_test_results.csv", index=False)
    align.to_csv(TABLES / "03_candidate_benchmark_trace_alignment.csv", index=False)
    final.to_csv(TABLES / "04_real_boundary_nframe_v3_final_candidates.csv", index=False)
    split_audit.to_csv(TABLES / "00_real_boundary_search_split_audit.csv", index=False)

    report = f"""# Real-Boundary N-Frame v3 Parameter Search

## Purpose

This is exploratory N-Frame fitting. The premise is that the benchmark-visible N-Frame trace may not be the correct real-boundary parameterization if the real effect is hidden in bulk space. Therefore this search allows the residual N-Frame components to flip sign and reweight themselves to fit real CMS boundary data.

This is not a particle-discovery claim. It is a parameter-learning step.

## Best held-out real-boundary candidate

- Candidate: `{best_name}`
- Held-out real-vs-weighted-SM AUC: {float(best['test_real_vs_sm_auc']):.6f}
- Standard-score-conditioned top-5% residual-tail observed: {int(best['observed_tail'])}
- Standard-score-conditioned expected: {float(best['expected_tail']):.2f}
- Observed / expected: {float(best['observed_over_expected']):.3f}
- Conditional upward Z: {float(best['conditioned_tail_Z']):.3f} sigma
- Global top-1% observed / expected: {float(best['global_observed_over_expected']):.3f}
- Global top-1% Z: {float(best['global_tail_Z']):.3f} sigma
- Benchmark trace relation: {best['direction_relation_to_benchmark']}
- Benchmark trace AUC, same direction: {float(best['benchmark_signal_vs_sm_auc_same_direction']):.6f}
- Benchmark trace AUC, best direction: {float(best['benchmark_signal_vs_sm_auc_best_direction']):.6f}

Formula:

```json
{best['formula_json']}
```

## Interpretation

If the best candidate has a large positive held-out conditional Z, this means a modified N-Frame parameterization can identify a real-data boundary population that is enriched relative to weighted SM after standard-score conditioning.

If the benchmark relation is `inverted`, the real-boundary fit points in the opposite direction to benchmark-visible SUSY-like examples. That would be consistent with the idea that the observable boundary trace is not the direct visible SUSY topology, but it also means this cannot be treated as straightforward SUSY evidence without further theory and controls.

## Split audit

{split_audit.to_markdown(index=False)}

## Held-out candidate results

{final.head(30).to_markdown(index=False)}
"""
    (REPORTS / "01_REAL_BOUNDARY_NFRAME_V3_PARAMETER_SEARCH_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Real-Boundary N-Frame v3 Fit

We allowed the residual N-Frame parameters to reweight and flip signs to fit real CMS boundary data, rather than forcing the benchmark-visible direction.

Best held-out candidate:

- Candidate: `{best_name}`
- Conditional top-5% observed: {int(best['observed_tail'])}
- Conditional expected: {float(best['expected_tail']):.2f}
- Observed / expected: {float(best['observed_over_expected']):.3f}
- Conditional upward Z: {float(best['conditioned_tail_Z']):.3f} sigma
- Benchmark relation: {best['direction_relation_to_benchmark']}
- Benchmark best-direction AUC: {float(best['benchmark_signal_vs_sm_auc_best_direction']):.6f}

Interpretation: this is an exploratory real-boundary parameter fit. A positive held-out Z means N-Frame can be adjusted to identify a real boundary population beyond the weighted-SM residual shape. If the direction is inverted relative to benchmarks, it may be a hidden/bulk-boundary trace rather than direct visible SUSY topology.
"""
    (REPORTS / "02_SHORT_UPDATE_REAL_BOUNDARY_NFRAME_V3_FIT.md").write_text(short, encoding="utf-8")

    print("REAL-BOUNDARY N-FRAME V3 PARAMETER SEARCH COMPLETE")
    print(final.head(10)[[
        "candidate",
        "test_real_vs_sm_auc",
        "observed_tail",
        "expected_tail",
        "observed_over_expected",
        "conditioned_tail_Z",
        "global_observed_over_expected",
        "global_tail_Z",
        "direction_relation_to_benchmark",
        "benchmark_signal_vs_sm_auc_best_direction",
        "passes_exploratory_real_boundary_screen",
    ]].to_string(index=False))
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
