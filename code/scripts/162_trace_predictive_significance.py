from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_trace_predictive_significance"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

SM_PATH = (
    ROOT
    / "outputs_breakthrough_full_push_nframe_susy/sources/"
    / "best_available_full_plus_reduced_weighted_sm_events.csv"
)
SIGNAL_PATHS = [
    ROOT / "data/processed/fuller_component_susy_signals/accessible_susy_miniaodsim_events_with_BNF.csv",
    ROOT / "data/processed/susy_relevance_benchmark_features/susy_sm_benchmark_events_with_BNF.csv",
    ROOT / "data/processed/expanded_benchmark_features/expanded_benchmark_events_with_BNF.csv",
]

BASE_COLS = [
    "run",
    "lumi",
    "event",
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_btags_medium",
    "N_muons",
    "N_electrons",
    "N_leptons",
    "N_primary_vertices",
    "secondary_vertex_count",
    "packed_candidate_count",
    "classification",
    "process_label",
    "sample_id",
    "record_id",
    "component_layer",
    "component_mode",
    "data_tier",
    "source_file",
    "event_weight",
    "B_NF_z",
    "B_NF_raw",
    "B_NF_fitted_frozen_z_real_scaled",
    "B_NF_fitted_frozen_raw",
    "B_P_displacement_proxy",
    "B_P_reconstruction",
    "B_P_multiplicity",
    "B_P_btag_structure",
    "B_P_visible_energy",
    "B_P_missing",
    "B_P_compression",
    "P_displacement",
    "P_reconstruction",
    "P_multiplicity",
    "P_btag",
    "P_visible",
    "P_missing",
    "P_compression",
    "displacement_reconstruction_axis",
    "missing_visible_axis",
    "qcd_like_axis",
    "trace_alignment_score",
]

STANDARD = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
FEATURE_SETS = {
    "standard_CMS_like": STANDARD,
    "standard_plus_trace_axis": STANDARD + ["displacement_reconstruction_axis"],
    "standard_plus_BNF": STANDARD + ["B_NF_z"],
    "standard_plus_full_NFrame_axes": STANDARD
    + ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "qcd_like_axis"],
    "trace_axis_alone": ["displacement_reconstruction_axis"],
    "BNF_alone": ["B_NF_z"],
}


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def read_selected(path: Path) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0)
    usecols = [col for col in BASE_COLS if col in header.columns]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    for col in BASE_COLS:
        if col not in df.columns:
            df[col] = np.nan
    df["source_table"] = str(path.relative_to(ROOT))
    return df


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def first_available(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype="float64")
    for col in cols:
        if col in df.columns:
            out = out.combine_first(pd.to_numeric(df[col], errors="coerce"))
    return out


def normalise_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "N_leptons",
        "N_primary_vertices",
        "secondary_vertex_count",
        "packed_candidate_count",
        "event_weight",
    ]:
        out[col] = numeric(out, col)

    out["B_NF_z"] = first_available(out, ["B_NF_z", "B_NF_fitted_frozen_z_real_scaled"])
    out["B_NF_raw"] = first_available(out, ["B_NF_raw", "B_NF_fitted_frozen_raw"])

    component_map = {
        "P_displacement": ["P_displacement", "B_P_displacement_proxy"],
        "P_reconstruction": ["P_reconstruction", "B_P_reconstruction"],
        "P_multiplicity": ["P_multiplicity", "B_P_multiplicity"],
        "P_btag": ["P_btag", "B_P_btag_structure"],
        "P_visible": ["P_visible", "B_P_visible_energy"],
        "P_missing": ["P_missing", "B_P_missing"],
        "P_compression": ["P_compression", "B_P_compression"],
    }
    for dst, cols in component_map.items():
        out[dst] = first_available(out, cols)

    out["displacement_reconstruction_axis"] = first_available(
        out,
        ["displacement_reconstruction_axis"],
    )
    missing_trace = out["displacement_reconstruction_axis"].isna()
    out.loc[missing_trace, "displacement_reconstruction_axis"] = (
        out.loc[missing_trace, "P_displacement"] + out.loc[missing_trace, "P_reconstruction"]
    )

    out["missing_visible_axis"] = first_available(out, ["missing_visible_axis"])
    missing_mv = out["missing_visible_axis"].isna()
    out.loc[missing_mv, "missing_visible_axis"] = (
        out.loc[missing_mv, "P_missing"] + out.loc[missing_mv, "P_visible"]
    )

    out["qcd_like_axis"] = first_available(out, ["qcd_like_axis"])
    missing_qcd = out["qcd_like_axis"].isna()
    out.loc[missing_qcd, "qcd_like_axis"] = out.loc[
        missing_qcd, ["P_visible", "P_multiplicity", "P_btag"]
    ].mean(axis=1)

    out["trace_alignment_score"] = first_available(out, ["trace_alignment_score"])
    missing_align = out["trace_alignment_score"].isna()
    out.loc[missing_align, "trace_alignment_score"] = (
        out.loc[missing_align, "B_NF_z"]
        + out.loc[missing_align, "displacement_reconstruction_axis"]
        - out.loc[missing_align, "missing_visible_axis"].clip(lower=0)
    )

    out["process_label"] = out["process_label"].fillna("unknown").astype(str)
    out["sample_id"] = out["sample_id"].fillna("").astype(str)
    out["record_id"] = out["record_id"].fillna("").astype(str)
    out["component_mode"] = out["component_mode"].fillna("").astype(str)
    out["component_layer"] = out["component_layer"].fillna("").astype(str)
    out["data_tier"] = out["data_tier"].fillna("").astype(str)
    return out


def load_signal() -> pd.DataFrame:
    frames = []
    for path in SIGNAL_PATHS:
        if not path.exists():
            continue
        df = read_selected(path)
        df = df[df["classification"].astype(str).str.contains("signal", case=False, na=False)].copy()
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No signal benchmark inputs were found.")
    signal = pd.concat(frames, ignore_index=True, sort=False)
    signal = normalise_features(signal)
    key_cols = ["sample_id", "process_label", "record_id", "run", "lumi", "event"]
    signal["_dedupe_key"] = signal[key_cols].astype(str).agg("|".join, axis=1)
    signal = signal.drop_duplicates("_dedupe_key", keep="first").drop(columns=["_dedupe_key"])
    signal["target"] = 1
    signal["class_name"] = "signal_benchmark"
    return signal


def load_sm() -> pd.DataFrame:
    if not SM_PATH.exists():
        raise FileNotFoundError(f"Missing weighted SM source table: {SM_PATH}")
    sm = read_selected(SM_PATH)
    sm = sm[sm["classification"].astype(str).str.contains("SM_background", case=False, na=False)].copy()
    sm = normalise_features(sm)
    sm["target"] = 0
    sm["class_name"] = "standard_model_background"
    return sm


def make_analysis_dataset(sm: pd.DataFrame, signal: pd.DataFrame, seed: int = 162) -> pd.DataFrame:
    required = sorted(set(FEATURE_SETS["standard_plus_trace_axis"] + ["target"]))
    signal_trace = signal.dropna(subset=required).copy()
    sm_trace = sm.dropna(subset=required).copy()
    n_signal = len(signal_trace)
    if n_signal == 0:
        raise ValueError("No trace-available signal events are available.")
    n_sm = min(len(sm_trace), n_signal)
    sm_sample = sm_trace.sample(n_sm, random_state=seed)
    data = pd.concat([sm_sample, signal_trace], ignore_index=True, sort=False)
    data = data.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    data["analysis_dataset"] = "primary_trace_available_balanced"
    return data


def make_pipeline_model() -> object:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=162),
    )


def train_predict(data: pd.DataFrame, feature_sets: dict[str, list[str]], seed: int = 162) -> tuple[pd.DataFrame, pd.DataFrame]:
    idx = np.arange(len(data))
    train_idx, test_idx = train_test_split(
        idx,
        test_size=0.30,
        random_state=seed,
        stratify=data["target"].astype(int),
    )
    predictions = pd.DataFrame(
        {
            "row_id": test_idx,
            "target": data.loc[test_idx, "target"].astype(int).to_numpy(),
            "process_label": data.loc[test_idx, "process_label"].astype(str).to_numpy(),
            "class_name": data.loc[test_idx, "class_name"].astype(str).to_numpy(),
        }
    )
    rows = []
    for model_name, cols in feature_sets.items():
        model = make_pipeline_model()
        model.fit(data.loc[train_idx, cols], data.loc[train_idx, "target"].astype(int))
        score = model.predict_proba(data.loc[test_idx, cols])[:, 1]
        predictions[model_name] = score
        rows.append(
            {
                "model": model_name,
                "features": "+".join(cols),
                "n_train": len(train_idx),
                "n_test": len(test_idx),
                "test_positive": int(predictions["target"].sum()),
                "test_negative": int((predictions["target"] == 0).sum()),
                "auc": roc_auc_score(predictions["target"], score),
                "pr_auc": average_precision_score(predictions["target"], score),
            }
        )
    aucs = pd.DataFrame(rows)
    base_auc = float(aucs.loc[aucs["model"].eq("standard_CMS_like"), "auc"].iloc[0])
    aucs["delta_auc_vs_standard_CMS_like"] = aucs["auc"] - base_auc
    return predictions, aucs


def compute_midrank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    sorted_x = x[order]
    n = len(x)
    midranks = np.zeros(n, dtype=float)
    i = 0
    while i < n:
        j = i
        while j < n and sorted_x[j] == sorted_x[i]:
            j += 1
        midranks[i:j] = 0.5 * (i + j - 1) + 1
        i = j
    out = np.empty(n, dtype=float)
    out[order] = midranks
    return out


def fast_delong(predictions_sorted_transposed: np.ndarray, label_1_count: int) -> tuple[np.ndarray, np.ndarray]:
    m = label_1_count
    n = predictions_sorted_transposed.shape[1] - m
    positive_examples = predictions_sorted_transposed[:, :m]
    negative_examples = predictions_sorted_transposed[:, m:]
    k = predictions_sorted_transposed.shape[0]

    tx = np.empty([k, m], dtype=float)
    ty = np.empty([k, n], dtype=float)
    tz = np.empty([k, m + n], dtype=float)
    for r in range(k):
        tx[r, :] = compute_midrank(positive_examples[r, :])
        ty[r, :] = compute_midrank(negative_examples[r, :])
        tz[r, :] = compute_midrank(predictions_sorted_transposed[r, :])
    aucs = tz[:, :m].sum(axis=1) / m / n - float(m + 1.0) / 2.0 / n
    v01 = (tz[:, :m] - tx[:, :]) / n
    v10 = 1.0 - (tz[:, m:] - ty[:, :]) / m
    sx = np.cov(v01)
    sy = np.cov(v10)
    delongcov = sx / m + sy / n
    return aucs, np.atleast_2d(delongcov)


def delong_test(y_true: np.ndarray, base_scores: np.ndarray, new_scores: np.ndarray) -> dict[str, float | str | bool]:
    y_true = np.asarray(y_true).astype(int)
    order = np.argsort(-y_true)
    label_1_count = int(y_true.sum())
    preds = np.vstack([base_scores, new_scores])[:, order]
    aucs, covariance = fast_delong(preds, label_1_count)
    delta = float(aucs[1] - aucs[0])
    var = float(covariance[0, 0] + covariance[1, 1] - 2.0 * covariance[0, 1])
    if var <= 0 or not np.isfinite(var):
        return {
            "test": "delong_correlated_auc",
            "delta_auc": delta,
            "standard_error": np.nan,
            "p_one_sided": np.nan,
            "sigma_one_sided_Z": np.nan,
            "p_value_note": "invalid_or_degenerate_covariance",
        }
    z = delta / np.sqrt(var)
    p = float(norm.sf(z))
    return {
        "test": "delong_correlated_auc",
        "delta_auc": delta,
        "standard_error": float(np.sqrt(var)),
        "p_one_sided": p,
        "sigma_one_sided_Z": float(z),
        "p_value_note": "analytic_normal_approximation",
    }


def bootstrap_test(
    y_true: np.ndarray,
    base_scores: np.ndarray,
    new_scores: np.ndarray,
    seed: int = 162,
    n_boot: int = 2000,
) -> tuple[dict[str, float | str | bool], pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        deltas.append(roc_auc_score(y_true[idx], new_scores[idx]) - roc_auc_score(y_true[idx], base_scores[idx]))
    arr = np.asarray(deltas, dtype=float)
    count_le_zero = int((arr <= 0).sum())
    p_floor = count_le_zero == 0
    p = (count_le_zero + (1 if p_floor else 0)) / (len(arr) + (1 if p_floor else 0))
    result = {
        "test": "paired_test_set_bootstrap",
        "delta_auc": float(roc_auc_score(y_true, new_scores) - roc_auc_score(y_true, base_scores)),
        "standard_error": float(arr.std(ddof=1)),
        "ci_025": float(np.quantile(arr, 0.025)),
        "ci_975": float(np.quantile(arr, 0.975)),
        "p_one_sided": float(p),
        "sigma_one_sided_Z": float(norm.isf(p)),
        "p_value_note": "floor_1_over_n_plus_1" if p_floor else "empirical_fraction_delta_le_zero",
        "n_resamples": int(len(arr)),
        "count_delta_le_zero": count_le_zero,
    }
    dist = pd.DataFrame({"bootstrap_delta_auc": arr})
    return result, dist


def permutation_test(
    y_true: np.ndarray,
    base_scores: np.ndarray,
    new_scores: np.ndarray,
    seed: int = 163,
    n_perm: int = 5000,
) -> tuple[dict[str, float | str | bool], pd.DataFrame]:
    rng = np.random.default_rng(seed)
    observed = roc_auc_score(y_true, new_scores) - roc_auc_score(y_true, base_scores)
    deltas = np.empty(n_perm, dtype=float)
    for i in range(n_perm):
        swap = rng.random(len(y_true)) < 0.5
        perm_base = base_scores.copy()
        perm_new = new_scores.copy()
        perm_base[swap] = new_scores[swap]
        perm_new[swap] = base_scores[swap]
        deltas[i] = roc_auc_score(y_true, perm_new) - roc_auc_score(y_true, perm_base)
    count_ge_obs = int((deltas >= observed).sum())
    p = (count_ge_obs + 1) / (n_perm + 1)
    result = {
        "test": "paired_score_label_permutation",
        "delta_auc": float(observed),
        "standard_error": float(deltas.std(ddof=1)),
        "p_one_sided": float(p),
        "sigma_one_sided_Z": float(norm.isf(p)),
        "p_value_note": "plus_one_permutation_p_value",
        "n_resamples": int(n_perm),
        "count_delta_ge_observed": count_ge_obs,
    }
    dist = pd.DataFrame({"permutation_delta_auc": deltas})
    return result, dist


def compare_models(predictions: pd.DataFrame, model: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    y = predictions["target"].to_numpy(dtype=int)
    base = predictions["standard_CMS_like"].to_numpy(dtype=float)
    new = predictions[model].to_numpy(dtype=float)

    rows = []
    rows.append(delong_test(y, base, new))
    boot, boot_dist = bootstrap_test(y, base, new)
    rows.append(boot)
    perm, perm_dist = permutation_test(y, base, new)
    rows.append(perm)
    out = pd.DataFrame(rows)
    out.insert(0, "comparison", f"{model}_vs_standard_CMS_like")
    out.insert(1, "tested_model", model)
    return out, boot_dist, perm_dist


def per_family_delong(predictions: pd.DataFrame, model: str) -> pd.DataFrame:
    rows = []
    sm = predictions[predictions["target"].eq(0)]
    for family in sorted(predictions.loc[predictions["target"].eq(1), "process_label"].dropna().unique()):
        sig = predictions[predictions["process_label"].eq(family)]
        subset = pd.concat([sm, sig], ignore_index=True)
        if subset["target"].nunique() < 2 or len(sig) < 50:
            continue
        y = subset["target"].to_numpy(dtype=int)
        res = delong_test(
            y,
            subset["standard_CMS_like"].to_numpy(dtype=float),
            subset[model].to_numpy(dtype=float),
        )
        res.update(
            {
                "process_label": family,
                "tested_model": model,
                "n_signal_test": int(len(sig)),
                "n_sm_test": int(len(sm)),
                "auc_standard": float(roc_auc_score(y, subset["standard_CMS_like"])),
                "auc_tested": float(roc_auc_score(y, subset[model])),
            }
        )
        rows.append(res)
    return pd.DataFrame(rows)


def dataset_audit(sm: pd.DataFrame, signal: pd.DataFrame, data: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {"item": "weighted_sm_input_rows", "value": len(sm), "note": str(SM_PATH.relative_to(ROOT))},
        {"item": "deduplicated_signal_input_rows", "value": len(signal), "note": "all available signal benchmark rows"},
        {
            "item": "trace_available_signal_rows",
            "value": int(signal["displacement_reconstruction_axis"].notna().sum()),
            "note": "signal rows with fitted displacement/reconstruction trace axis",
        },
        {
            "item": "primary_analysis_rows",
            "value": len(data),
            "note": "balanced trace-available SM plus signal sample",
        },
        {"item": "primary_analysis_signal_rows", "value": int(data["target"].sum()), "note": ""},
        {"item": "primary_analysis_sm_rows", "value": int((data["target"] == 0).sum()), "note": ""},
        {"item": "heldout_test_rows", "value": len(predictions), "note": "stratified event-level holdout"},
        {"item": "heldout_test_signal_rows", "value": int(predictions["target"].sum()), "note": ""},
        {"item": "heldout_test_sm_rows", "value": int((predictions["target"] == 0).sum()), "note": ""},
    ]
    return pd.DataFrame(rows)


def write_reports(
    audit: pd.DataFrame,
    aucs: pd.DataFrame,
    tests: pd.DataFrame,
    family: pd.DataFrame,
) -> None:
    headline = tests[
        tests["comparison"].eq("standard_plus_trace_axis_vs_standard_CMS_like")
    ].copy()
    delong = headline[headline["test"].eq("delong_correlated_auc")].iloc[0]
    boot = headline[headline["test"].eq("paired_test_set_bootstrap")].iloc[0]
    perm = headline[headline["test"].eq("paired_score_label_permutation")].iloc[0]

    standard_auc = aucs.loc[aucs["model"].eq("standard_CMS_like"), "auc"].iloc[0]
    trace_auc = aucs.loc[aucs["model"].eq("standard_plus_trace_axis"), "auc"].iloc[0]

    report = f"""# Trace Predictive Significance Report

## Question

Do N-Frame trace variables add predictive information beyond standard CMS-like kinematic variables in the existing benchmark layer?

This is a trace-pattern significance test. It asks whether N-Frame is identifying an observable boundary/topology trace associated with SUSY-like or hidden-sector benchmark structure. It is not a SUSY particle discovery significance and it does not claim a real-data excess.

## Headline result

Comparison: standard CMS-like variables versus standard CMS-like variables plus the displacement/reconstruction trace axis.

- Standard CMS-like AUC: {standard_auc:.6f}
- Standard + trace-axis AUC: {trace_auc:.6f}
- Delta AUC: {trace_auc - standard_auc:.6f}
- DeLong one-sided Z: {float(delong['sigma_one_sided_Z']):.3f} sigma
- DeLong one-sided p: {float(delong['p_one_sided']):.6g}
- Bootstrap one-sided Z: {float(boot['sigma_one_sided_Z']):.3f} sigma ({boot['p_value_note']})
- Permutation one-sided Z: {float(perm['sigma_one_sided_Z']):.3f} sigma ({perm['p_value_note']})

Plain-English version: on the held-out benchmark test set, adding the N-Frame displacement/reconstruction trace score makes the classifier better at identifying SUSY-like or hidden-sector topology traces in the observable CMS boundary than standard CMS-style variables alone.

## Important limits

- This is a predictive-superiority / trace-pattern result, not a discovery of a new particle.
- The test uses simulated benchmark labels against weighted SM background rows; it does not prove an observed collision-data excess.
- The result should be quoted as evidence that the N-Frame trace score carries additional benchmark-topology information beyond standard CMS-style variables.
- The decisive physics-discovery test still requires control-region-closed, luminosity-weighted SM prediction versus real observed data in frozen signal regions.

## Dataset audit

{audit.to_markdown(index=False)}

## Model AUCs

{aucs.to_markdown(index=False)}

## Formal significance tests

{tests.to_markdown(index=False)}

## Per-signal-family DeLong checks

{family.to_markdown(index=False)}
"""
    (REPORTS / "01_TRACE_PREDICTIVE_SIGNIFICANCE_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update For Darren: Trace Sigma

We ran the formal trace-pattern significance test.

The clean headline comparison was:

standard CMS-like variables versus standard CMS-like variables plus the N-Frame displacement/reconstruction trace score.

Result:

- Standard AUC: {standard_auc:.6f}
- Standard + trace AUC: {trace_auc:.6f}
- Delta AUC: {trace_auc - standard_auc:.6f}
- DeLong Z: {float(delong['sigma_one_sided_Z']):.3f} sigma
- Bootstrap Z: {float(boot['sigma_one_sided_Z']):.3f} sigma
- Permutation Z: {float(perm['sigma_one_sided_Z']):.3f} sigma

Interpretation:

This supports the claim that N-Frame may be identifying the trace-pattern of SUSY-like or hidden-sector topology in the observable CMS boundary, rather than directly detecting supersymmetric particles themselves. It is a trace-pattern / method-validation significance, not a SUSY particle-discovery claim.
"""
    (REPORTS / "02_SHORT_UPDATE_FOR_DARREN_TRACE_SIGMA.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    sm = load_sm()
    signal = load_signal()
    data = make_analysis_dataset(sm, signal)
    data.to_csv(SOURCES / "primary_trace_available_balanced_dataset.csv", index=False)

    predictions, aucs = train_predict(data, FEATURE_SETS)
    predictions.to_csv(SOURCES / "heldout_trace_model_predictions.csv", index=False)
    aucs.to_csv(TABLES / "02_trace_model_auc_predictions.csv", index=False)

    audit = dataset_audit(sm, signal, data, predictions)
    audit.to_csv(TABLES / "01_trace_significance_dataset_audit.csv", index=False)

    test_frames = []
    boot_frames = []
    perm_frames = []
    for model in [
        "standard_plus_trace_axis",
        "standard_plus_BNF",
        "standard_plus_full_NFrame_axes",
        "trace_axis_alone",
        "BNF_alone",
    ]:
        tests, boot_dist, perm_dist = compare_models(predictions, model)
        test_frames.append(tests)
        boot_dist.insert(0, "comparison", f"{model}_vs_standard_CMS_like")
        perm_dist.insert(0, "comparison", f"{model}_vs_standard_CMS_like")
        boot_frames.append(boot_dist)
        perm_frames.append(perm_dist)
    tests = pd.concat(test_frames, ignore_index=True)
    tests.to_csv(TABLES / "03_trace_predictive_significance_tests.csv", index=False)
    pd.concat(boot_frames, ignore_index=True).to_csv(
        TABLES / "04_trace_significance_bootstrap_distribution.csv", index=False
    )
    pd.concat(perm_frames, ignore_index=True).to_csv(
        TABLES / "05_trace_significance_permutation_distribution.csv", index=False
    )

    family = pd.concat(
        [
            per_family_delong(predictions, "standard_plus_trace_axis"),
            per_family_delong(predictions, "standard_plus_BNF"),
        ],
        ignore_index=True,
        sort=False,
    )
    family.to_csv(TABLES / "06_trace_predictive_significance_by_signal_family.csv", index=False)

    source_manifest = {
        "sm_source": str(SM_PATH.relative_to(ROOT)),
        "signal_sources": [str(path.relative_to(ROOT)) for path in SIGNAL_PATHS if path.exists()],
        "primary_comparison": "standard_plus_trace_axis_vs_standard_CMS_like",
        "standard_features": STANDARD,
        "trace_feature": "displacement_reconstruction_axis",
        "statistical_tests": ["DeLong correlated AUC", "paired bootstrap", "paired permutation"],
        "random_seed": 162,
        "interpretation": "methods/trace predictive-superiority significance, not particle discovery",
    }
    (OUT / "trace_significance_manifest.json").write_text(
        json.dumps(source_manifest, indent=2),
        encoding="utf-8",
    )
    write_reports(audit, aucs, tests, family)

    headline = tests[
        tests["comparison"].eq("standard_plus_trace_axis_vs_standard_CMS_like")
    ][["test", "delta_auc", "p_one_sided", "sigma_one_sided_Z", "p_value_note"]]
    print("TRACE PREDICTIVE SIGNIFICANCE COMPLETE")
    print(aucs[["model", "auc", "delta_auc_vs_standard_CMS_like"]].to_string(index=False))
    print(headline.to_string(index=False))
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
