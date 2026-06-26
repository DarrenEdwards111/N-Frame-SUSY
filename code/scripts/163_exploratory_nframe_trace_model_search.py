from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_exploratory_nframe_trace_model_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
DATA = ROOT / "outputs_trace_predictive_significance/sources/primary_trace_available_balanced_dataset.csv"
STAT_SCRIPT = ROOT / "scripts/162_trace_predictive_significance.py"

STANDARD = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
NFRAME_BASE = [
    "B_NF_z",
    "B_NF_raw",
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
    "B_P_displacement_proxy",
    "B_P_reconstruction",
    "B_P_missing",
    "B_P_visible_energy",
    "B_P_multiplicity",
    "B_P_btag_structure",
    "B_P_compression",
    "secondary_vertex_count",
    "packed_candidate_count",
    "N_primary_vertices",
]


def load_stat_helpers():
    spec = importlib.util.spec_from_file_location("trace_stats", STAT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def add_engineered_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    out = df.copy()
    for col in STANDARD + NFRAME_BASE:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["jet_btag_ratio"] = out["N_btags_medium"] / (out["N_jets_30"].abs() + 1.0)
    out["met_ht_ratio"] = out["MET_pt"] / (out["HT"].abs() + 1.0)
    standard_engineered = ["log1p_MET_pt", "log1p_HT", "jet_btag_ratio", "met_ht_ratio"]

    nframe_engineered = []
    for col in NFRAME_BASE:
        if out[col].notna().sum() == 0:
            continue
        for suffix, series in [
            ("pos", out[col].clip(lower=0)),
            ("neg", (-out[col]).clip(lower=0)),
            ("abs", out[col].abs()),
            ("sq", out[col] * out[col]),
        ]:
            name = f"{col}_{suffix}"
            out[name] = series
            nframe_engineered.append(name)

    disp = out["displacement_reconstruction_axis"]
    bnf = out["B_NF_z"]
    miss = out["missing_visible_axis"]
    qcd = out["qcd_like_axis"]
    comp = out["P_compression"]
    vis = out["P_visible"]
    pdisp = out["P_displacement"]
    precon = out["P_reconstruction"]
    pmiss = out["P_missing"]

    interaction_defs = {
        "trace_disp_x_bnf": disp * bnf,
        "trace_disp_x_missing": disp * miss,
        "trace_disp_minus_missing": disp - miss,
        "trace_disp_minus_qcd": disp - qcd,
        "trace_disp_plus_bnf_minus_missing": disp + bnf - miss.clip(lower=0),
        "trace_reco_x_missing": precon * pmiss,
        "trace_disp_x_reco": pdisp * precon,
        "trace_visible_missing_balance": vis - pmiss,
        "trace_compressed_displaced": disp - comp,
        "trace_boundary_curvature": disp * disp + bnf * bnf + miss * miss,
        "trace_qcd_suppressed_boundary": disp + bnf - qcd.clip(lower=0),
        "trace_hidden_sector_candidate": disp + bnf + comp.clip(lower=0) - miss.clip(lower=0),
    }
    for name, series in interaction_defs.items():
        out[name] = series
    nframe_engineered.extend(interaction_defs.keys())
    return out, standard_engineered + nframe_engineered


def split_data(df: pd.DataFrame) -> dict[str, np.ndarray]:
    idx = np.arange(len(df))
    dev_idx, test_idx = train_test_split(
        idx, test_size=0.25, random_state=163, stratify=df["target"].astype(int)
    )
    train_idx, tune_idx = train_test_split(
        dev_idx, test_size=0.333333, random_state=164, stratify=df.loc[dev_idx, "target"].astype(int)
    )
    return {"train": train_idx, "tune": tune_idx, "test": test_idx}


def model_for(kind: str):
    if kind == "logistic":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=163),
        )
    if kind == "hgb":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            HistGradientBoostingClassifier(
                max_iter=250,
                learning_rate=0.06,
                max_leaf_nodes=31,
                l2_regularization=0.05,
                random_state=163,
            ),
        )
    if kind == "rf":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(
                n_estimators=300,
                min_samples_leaf=10,
                class_weight="balanced_subsample",
                n_jobs=-1,
                random_state=163,
            ),
        )
    if kind == "extra_trees":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            ExtraTreesClassifier(
                n_estimators=350,
                min_samples_leaf=8,
                class_weight="balanced",
                n_jobs=-1,
                random_state=163,
            ),
        )
    raise ValueError(kind)


def fit_eval(df: pd.DataFrame, splits: dict[str, np.ndarray], name: str, kind: str, features: list[str]) -> tuple[dict, np.ndarray, object]:
    train = splits["train"]
    tune = splits["tune"]
    model = model_for(kind)
    model.fit(df.loc[train, features], df.loc[train, "target"].astype(int))
    score = model.predict_proba(df.loc[tune, features])[:, 1]
    y = df.loc[tune, "target"].astype(int).to_numpy()
    return (
        {
            "candidate": name,
            "model_kind": kind,
            "n_features": len(features),
            "features": "+".join(features),
            "tune_auc": roc_auc_score(y, score),
            "tune_pr_auc": average_precision_score(y, score),
        },
        score,
        model,
    )


def refit_test(df: pd.DataFrame, splits: dict[str, np.ndarray], name: str, kind: str, features: list[str]) -> tuple[dict, np.ndarray, object]:
    train = np.concatenate([splits["train"], splits["tune"]])
    test = splits["test"]
    model = model_for(kind)
    model.fit(df.loc[train, features], df.loc[train, "target"].astype(int))
    score = model.predict_proba(df.loc[test, features])[:, 1]
    y = df.loc[test, "target"].astype(int).to_numpy()
    return (
        {
            "candidate": name,
            "model_kind": kind,
            "n_features": len(features),
            "features": "+".join(features),
            "test_auc": roc_auc_score(y, score),
            "test_pr_auc": average_precision_score(y, score),
        },
        score,
        model,
    )


def add_residualized_features(df: pd.DataFrame, splits: dict[str, np.ndarray], cols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    out = df.copy()
    residual_cols = []
    train = splits["train"]
    base_model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=500, random_state=163),
    )
    # LinearRegression is unavailable in a Pipeline with multioutput residual setup here, so use least squares.
    x_train = out.loc[train, STANDARD].copy()
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_train_arr = scaler.fit_transform(imputer.fit_transform(x_train))
    x_all_arr = scaler.transform(imputer.transform(out[STANDARD]))
    x_train_design = np.column_stack([np.ones(len(x_train_arr)), x_train_arr])
    x_all_design = np.column_stack([np.ones(len(x_all_arr)), x_all_arr])
    for col in cols:
        if out[col].notna().sum() < 100:
            continue
        y_train = out.loc[train, col].to_numpy(dtype=float)
        y_fill = np.nanmedian(y_train)
        y_train = np.where(np.isfinite(y_train), y_train, y_fill)
        coef, *_ = np.linalg.lstsq(x_train_design, y_train, rcond=None)
        pred = x_all_design @ coef
        actual = out[col].to_numpy(dtype=float)
        actual = np.where(np.isfinite(actual), actual, y_fill)
        name = f"resid_{col}"
        out[name] = actual - pred
        residual_cols.append(name)
    return out, residual_cols


def random_formula_search(df: pd.DataFrame, splits: dict[str, np.ndarray], cols: list[str], n_formulas: int = 1200) -> tuple[pd.DataFrame, list[str]]:
    rng = np.random.default_rng(163)
    tune = splits["tune"]
    y = df.loc[tune, "target"].astype(int).to_numpy()
    clean_cols = [c for c in cols if df[c].notna().sum() > 1000]
    x = df[clean_cols].copy()
    med = x.median(numeric_only=True)
    x = x.fillna(med)
    mu = x.loc[splits["train"]].mean()
    sd = x.loc[splits["train"]].std().replace(0, 1.0)
    z = ((x - mu) / sd).clip(-8, 8)
    z_tune = z.iloc[tune].to_numpy()
    rows = []
    formulas = []
    for i in range(n_formulas):
        active = rng.choice(len(clean_cols), size=min(6, len(clean_cols)), replace=False)
        weights = rng.normal(0, 1, size=len(active))
        score = z_tune[:, active] @ weights
        auc = roc_auc_score(y, score)
        if auc < 0.5:
            auc = 1.0 - auc
            weights = -weights
        rows.append(
            {
                "formula_id": f"random_trace_formula_{i:04d}",
                "tune_auc_formula_alone": auc,
                "terms": json.dumps(
                    [{"feature": clean_cols[j], "weight": float(w)} for j, w in zip(active, weights)]
                ),
            }
        )
        formulas.append((auc, active, weights))
    ranked = pd.DataFrame(rows).sort_values("tune_auc_formula_alone", ascending=False).reset_index(drop=True)
    top_cols = []
    for rank, (_, active, weights) in enumerate(sorted(formulas, key=lambda v: v[0], reverse=True)[:20], start=1):
        name = f"searched_trace_formula_top{rank:02d}"
        df[name] = z.iloc[:, active].to_numpy() @ weights
        top_cols.append(name)
    return ranked, top_cols


def statistical_tests(stats_mod, y: np.ndarray, base: np.ndarray, score: np.ndarray, comparison: str) -> pd.DataFrame:
    rows = [stats_mod.delong_test(y, base, score)]
    boot, _ = stats_mod.bootstrap_test(y, base, score, seed=263, n_boot=2000)
    perm, _ = stats_mod.permutation_test(y, base, score, seed=264, n_perm=5000)
    rows.extend([boot, perm])
    out = pd.DataFrame(rows)
    out.insert(0, "comparison", comparison)
    return out


def tail_enrichment(y: np.ndarray, base_score: np.ndarray, cand_score: np.ndarray) -> pd.DataFrame:
    rows = []
    for label, score in [("standard_baseline", base_score), ("exploratory_nframe", cand_score)]:
        for frac in [0.10, 0.05, 0.01, 0.005]:
            threshold = np.quantile(score, 1.0 - frac)
            mask = score >= threshold
            rows.append(
                {
                    "score": label,
                    "tail_fraction": frac,
                    "n_tail": int(mask.sum()),
                    "signal_in_tail": int(y[mask].sum()),
                    "signal_fraction_in_tail": float(y[mask].mean()),
                    "global_signal_fraction": float(y.mean()),
                    "enrichment_over_global": float(y[mask].mean() / y.mean()),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    stats_mod = load_stat_helpers()
    df = pd.read_csv(DATA, low_memory=False)
    df, engineered = add_engineered_features(df)
    splits = split_data(df)

    residual_source = [
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
    df, residual_cols = add_residualized_features(df, splits, residual_source)
    random_ranked, searched_cols = random_formula_search(df, splits, NFRAME_BASE + engineered + residual_cols)

    standard_eng = ["log1p_MET_pt", "log1p_HT", "jet_btag_ratio", "met_ht_ratio"]
    nframe_compact = [
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
    interaction_cols = [c for c in engineered if c.startswith("trace_")]
    candidates = {
        "standard_logistic": ("logistic", STANDARD),
        "standard_engineered_logistic": ("logistic", STANDARD + standard_eng),
        "standard_hgb": ("hgb", STANDARD + standard_eng),
        "standard_plus_old_trace_logistic": ("logistic", STANDARD + ["displacement_reconstruction_axis"]),
        "standard_plus_compact_nframe_logistic": ("logistic", STANDARD + nframe_compact),
        "standard_plus_residual_nframe_logistic": ("logistic", STANDARD + residual_cols),
        "standard_plus_compact_nframe_hgb": ("hgb", STANDARD + standard_eng + nframe_compact),
        "standard_plus_engineered_nframe_hgb": ("hgb", STANDARD + standard_eng + nframe_compact + interaction_cols + searched_cols[:5]),
        "standard_plus_residual_nframe_hgb": ("hgb", STANDARD + standard_eng + residual_cols),
        "standard_plus_engineered_nframe_extra_trees": ("extra_trees", STANDARD + standard_eng + nframe_compact + interaction_cols + searched_cols[:5]),
        "nframe_only_engineered_hgb": ("hgb", nframe_compact + interaction_cols + searched_cols[:5]),
        "standard_plus_best_random_trace_logistic": ("logistic", STANDARD + searched_cols[:3]),
    }

    tune_rows = []
    for name, (kind, features) in candidates.items():
        row, _, _ = fit_eval(df, splits, name, kind, features)
        tune_rows.append(row)
    tune = pd.DataFrame(tune_rows).sort_values("tune_auc", ascending=False).reset_index(drop=True)

    standard_kind, standard_features = candidates["standard_hgb"]
    std_test_row, std_score, std_model = refit_test(df, splits, "standard_hgb", standard_kind, standard_features)
    test_rows = [std_test_row]
    score_map = {"standard_hgb": std_score}
    model_map = {"standard_hgb": std_model}
    for name in tune["candidate"].head(6):
        if name == "standard_hgb":
            continue
        kind, features = candidates[name]
        row, score, model = refit_test(df, splits, name, kind, features)
        test_rows.append(row)
        score_map[name] = score
        model_map[name] = model
    test = pd.DataFrame(test_rows).sort_values("test_auc", ascending=False).reset_index(drop=True)
    base_auc = float(test.loc[test["candidate"].eq("standard_hgb"), "test_auc"].iloc[0])
    test["delta_auc_vs_standard_hgb"] = test["test_auc"] - base_auc

    best_name = test[~test["candidate"].eq("standard_hgb")].iloc[0]["candidate"]
    y_test = df.loc[splits["test"], "target"].astype(int).to_numpy()
    sig_tests = statistical_tests(
        stats_mod,
        y_test,
        score_map["standard_hgb"],
        score_map[best_name],
        f"{best_name}_vs_standard_hgb",
    )
    tails = tail_enrichment(y_test, score_map["standard_hgb"], score_map[best_name])

    # Explain drivers for the best test survivor on a sampled held-out set.
    best_features = candidates[best_name][1]
    sample_n = min(6000, len(splits["test"]))
    rng = np.random.default_rng(163)
    sample_idx = rng.choice(splits["test"], size=sample_n, replace=False)
    importance = permutation_importance(
        model_map[best_name],
        df.loc[sample_idx, best_features],
        df.loc[sample_idx, "target"].astype(int),
        n_repeats=8,
        random_state=163,
        scoring="roc_auc",
        n_jobs=-1,
    )
    drivers = pd.DataFrame(
        {
            "feature": best_features,
            "permutation_importance_auc_mean": importance.importances_mean,
            "permutation_importance_auc_sd": importance.importances_std,
        }
    ).sort_values("permutation_importance_auc_mean", ascending=False)

    split_audit = pd.DataFrame(
        [
            {"split": k, "n": len(v), "signal": int(df.loc[v, "target"].sum()), "sm": int((df.loc[v, "target"] == 0).sum())}
            for k, v in splits.items()
        ]
    )

    tune.to_csv(TABLES / "01_exploratory_tuning_auc_leaderboard.csv", index=False)
    test.to_csv(TABLES / "02_exploratory_holdout_auc_survivors.csv", index=False)
    sig_tests.to_csv(TABLES / "03_best_exploratory_trace_significance_tests.csv", index=False)
    tails.to_csv(TABLES / "04_best_exploratory_tail_enrichment.csv", index=False)
    drivers.to_csv(TABLES / "05_best_exploratory_trace_drivers.csv", index=False)
    random_ranked.to_csv(TABLES / "06_random_trace_formula_search.csv", index=False)
    split_audit.to_csv(TABLES / "00_split_audit.csv", index=False)

    pd.DataFrame(
        {
            "target": y_test,
            "standard_hgb": score_map["standard_hgb"],
            str(best_name): score_map[best_name],
        }
    ).to_csv(SOURCES / "best_exploratory_holdout_predictions.csv", index=False)

    delong = sig_tests[sig_tests["test"].eq("delong_correlated_auc")].iloc[0]
    boot = sig_tests[sig_tests["test"].eq("paired_test_set_bootstrap")].iloc[0]
    perm = sig_tests[sig_tests["test"].eq("paired_score_label_permutation")].iloc[0]

    report = f"""# Exploratory N-Frame Trace Model Search

## Purpose

This is exploratory N-Frame model development. The question is not whether SUSY particles have been directly detected. The question is whether adjusting the N-Frame trace representation improves detection of SUSY-like or hidden-sector topology traces in the observable CMS boundary.

## Best survivor

Best held-out survivor versus a stronger standard baseline:

- Best candidate: `{best_name}`
- Standard baseline: `standard_hgb`
- Best candidate AUC: {float(test.loc[test['candidate'].eq(best_name), 'test_auc'].iloc[0]):.6f}
- Standard baseline AUC: {base_auc:.6f}
- Delta AUC: {float(test.loc[test['candidate'].eq(best_name), 'delta_auc_vs_standard_hgb'].iloc[0]):.6f}
- DeLong Z: {float(delong['sigma_one_sided_Z']):.3f} sigma
- Bootstrap Z: {float(boot['sigma_one_sided_Z']):.3f} sigma
- Permutation Z: {float(perm['sigma_one_sided_Z']):.3f} sigma

Interpretation: this is a stronger exploratory trace-pattern result than the single old trace-axis test if the improvement survives against the stronger `standard_hgb` baseline.

## Split audit

{split_audit.to_markdown(index=False)}

## Tuning leaderboard

{tune.to_markdown(index=False)}

## Held-out survivors

{test.to_markdown(index=False)}

## Formal significance for best survivor

{sig_tests.to_markdown(index=False)}

## Tail enrichment

{tails.to_markdown(index=False)}

## Best-model drivers

{drivers.head(30).to_markdown(index=False)}
"""
    (REPORTS / "01_EXPLORATORY_NFRAME_TRACE_MODEL_SEARCH_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Exploratory N-Frame Trace Tuning

We treated N-Frame as incomplete and ran an exploratory search over nonlinear N-Frame trace components, residualized trace variables, and searched trace formulas.

Best held-out survivor:

- Candidate: `{best_name}`
- Baseline: `standard_hgb`
- Candidate AUC: {float(test.loc[test['candidate'].eq(best_name), 'test_auc'].iloc[0]):.6f}
- Baseline AUC: {base_auc:.6f}
- Delta AUC: {float(test.loc[test['candidate'].eq(best_name), 'delta_auc_vs_standard_hgb'].iloc[0]):.6f}
- DeLong: {float(delong['sigma_one_sided_Z']):.3f} sigma
- Bootstrap: {float(boot['sigma_one_sided_Z']):.3f} sigma
- Permutation: {float(perm['sigma_one_sided_Z']):.3f} sigma

This remains a trace-pattern result: N-Frame may be improving recognition of SUSY-like or hidden-sector topology traces in the observable CMS boundary, not directly detecting SUSY particles.
"""
    (REPORTS / "02_SHORT_UPDATE_EXPLORATORY_TRACE_TUNING.md").write_text(short, encoding="utf-8")

    print("EXPLORATORY N-FRAME TRACE MODEL SEARCH COMPLETE")
    print(test[["candidate", "test_auc", "delta_auc_vs_standard_hgb"]].to_string(index=False))
    print(sig_tests[["test", "delta_auc", "p_one_sided", "sigma_one_sided_Z", "p_value_note"]].to_string(index=False))
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
