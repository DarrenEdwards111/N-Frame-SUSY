import argparse
import json
import re
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV, HuberRegressor, LinearRegression, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "data" / "processed" / "signal_regions_verified_plus_imputed_scored.csv"
OUT = PROJECT / "results" / "iterative_nframe_model_search"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
ZIP = PROJECT / "nframe_iterative_model_search_results.zip"


def ensure_dirs():
    for path in [OUT, TABLES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def zscore(series):
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def max_label_number(row):
    text = " ".join(str(row.get(c, "")) for c in ["signal_region", "source_comment", "source_path", "category_enriched"])
    vals = []
    for raw in re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?(?![A-Za-z])|(?<=[A-Za-z])\d+(?:\.\d+)?", text):
        try:
            val = float(raw)
        except ValueError:
            continue
        # Keep SR/cut-scale numbers but avoid tiny labels like d1/o2 dominating.
        if val >= 10:
            vals.append(val)
    return max(vals) if vals else np.nan


def prepare(df):
    df = df.copy()
    df["R_rare"] = (
        df["R_lifetime_verified_imputed"].fillna(0)
        + df["R_displacement_verified_imputed"].fillna(0)
        + df["R_compression_verified_imputed"].fillna(0)
        + df["R_reconstruction_verified_imputed"].fillna(0)
    )
    df["R_topology"] = df["R_rare"] + df["R_multiplicity_verified_imputed"].fillna(0) + df["R_missing_verified_imputed"].fillna(0)
    df["abs_Z"] = df["Z"].abs()
    df["abs_Z_capped_3"] = df["Z_capped_3"].abs()
    df["abs_Z_conservative"] = df["Z_conservative"].abs()
    df["abs_Poisson"] = df["Poisson_deviance_residual"].abs()
    df["label_max_number"] = df.apply(max_label_number, axis=1)
    df["label_log_intensity"] = np.log1p(df["label_max_number"])
    df["B_current"] = df["B_access_verified_imputed_z"].fillna(0)
    df["B_label"] = zscore(df["label_log_intensity"])
    df["B_label_available"] = df["label_log_intensity"].notna().astype(int)
    core_z = [
        "z_MET_verified_imputed",
        "z_HT_or_meff_verified_imputed",
        "z_N_jets_verified_imputed",
        "z_N_leptons_verified_imputed",
        "z_N_btags_verified_imputed",
    ]
    df["B_core_sum"] = df[core_z].sum(axis=1)
    df["B_core_abs"] = df["B_core_sum"].abs()
    df["B_core_or_label"] = zscore(df["B_core_sum"].where(df["B_core_sum"] != 0).combine_first(df["B_label"]))
    df["B_label_plus_core"] = zscore(df["B_label"].fillna(0) + df["B_core_sum"].fillna(0))
    df["B_metadata_stress"] = zscore(df["imputation_fraction"].fillna(0) - df["metadata_completeness_score"].fillna(0))
    for b in ["B_current", "B_label", "B_core_sum", "B_core_abs", "B_core_or_label", "B_label_plus_core", "B_metadata_stress"]:
        df[f"{b}_x_Rrare"] = df[b].fillna(0) * df["R_rare"].fillna(0)
    return df


FEATURE_SETS = {
    "baseline_metadata": ["imputation_fraction", "metadata_completeness_score"],
    "current_B_rare": ["B_current", "R_rare", "B_current_x_Rrare", "imputation_fraction", "metadata_completeness_score"],
    "label_B_rare": ["B_label", "R_rare", "B_label_x_Rrare", "B_label_available", "imputation_fraction", "metadata_completeness_score"],
    "core_or_label_rare": ["B_core_or_label", "R_rare", "B_core_or_label_x_Rrare", "B_label_available", "imputation_fraction", "metadata_completeness_score"],
    "label_plus_core_rare": ["B_label_plus_core", "R_rare", "B_label_plus_core_x_Rrare", "B_label_available", "imputation_fraction", "metadata_completeness_score"],
    "components_sparse": [
        "B_label_plus_core",
        "B_metadata_stress",
        "R_rare",
        "R_missing_verified_imputed",
        "R_multiplicity_verified_imputed",
        "R_reconstruction_verified_imputed",
        "B_label_plus_core_x_Rrare",
        "imputation_fraction",
        "metadata_completeness_score",
    ],
}


def make_model(kind):
    if kind == "ols":
        return LinearRegression()
    if kind == "ridge":
        return RidgeCV(alphas=np.logspace(-3, 3, 25))
    if kind == "elasticnet":
        return ElasticNetCV(alphas=np.logspace(-3, 1, 20), l1_ratio=[0.1, 0.5, 0.9], max_iter=50000, random_state=7)
    if kind == "huber":
        return HuberRegressor(max_iter=1000)
    if kind == "forest":
        return RandomForestRegressor(n_estimators=500, min_samples_leaf=8, random_state=7)
    raise ValueError(kind)


def make_pipeline(features, kind, include_experiment=True):
    try:
        onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        onehot = OneHotEncoder(handle_unknown="ignore", sparse=False)
    transformers = [("num", StandardScaler(), features)]
    if include_experiment:
        transformers.append(("exp", onehot, ["experiment"]))
    return Pipeline([("pre", ColumnTransformer(transformers)), ("model", make_model(kind))])


def metric_row(y, pred, model, feature_set, scheme, outcome):
    return {
        "outcome": outcome,
        "feature_set": feature_set,
        "model": model,
        "scheme": scheme,
        "n": len(y),
        "r2": float(r2_score(y, pred)) if len(y) > 1 else np.nan,
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "corr": float(pd.Series(y).reset_index(drop=True).corr(pd.Series(pred))),
    }


def evaluate_cv(df, outcome, feature_set, model_kind):
    features = FEATURE_SETS[feature_set]
    cols = [outcome, "analysis", "experiment"] + features
    data = df[cols].replace([np.inf, -np.inf], np.nan).copy()
    data[features] = data[features].fillna(0)
    data = data.dropna(subset=[outcome])
    rows = []
    preds = np.full(len(data), np.nan)
    splitter = GroupKFold(n_splits=min(5, data["analysis"].nunique()))
    for train_idx, test_idx in splitter.split(data, data[outcome], groups=data["analysis"]):
        pipe = make_pipeline(features, model_kind, include_experiment=True)
        pipe.fit(data.iloc[train_idx][features + ["experiment"]], data.iloc[train_idx][outcome])
        preds[test_idx] = pipe.predict(data.iloc[test_idx][features + ["experiment"]])
    rows.append(metric_row(data[outcome], preds, model_kind, feature_set, "GroupKFold_by_analysis", outcome))
    for train_exp, test_exp in [("ATLAS", "CMS"), ("CMS", "ATLAS")]:
        train = data[data["experiment"] == train_exp]
        test = data[data["experiment"] == test_exp]
        if len(train) >= 20 and len(test) >= 20:
            pipe = make_pipeline(features, model_kind, include_experiment=True)
            pipe.fit(train[features + ["experiment"]], train[outcome])
            pred = pipe.predict(test[features + ["experiment"]])
            rows.append(metric_row(test[outcome], pred, model_kind, feature_set, f"{train_exp}_train_{test_exp}_test", outcome))
    return rows


def in_sample_ols(df, outcome="abs_Z_capped_3"):
    rows = []
    for name, features in FEATURE_SETS.items():
        data = df[[outcome, "experiment", "analysis"] + features].replace([np.inf, -np.inf], np.nan).copy()
        data[features] = data[features].fillna(0)
        formula = f"{outcome} ~ " + " + ".join(features) + " + C(experiment) + C(analysis)"
        try:
            fit = smf.ols(formula, data=data).fit()
            rows.append({"feature_set": name, "r2": fit.rsquared, "adj_r2": fit.rsquared_adj, "aic": fit.aic, "bic": fit.bic})
        except Exception as exc:
            rows.append({"feature_set": name, "r2": np.nan, "adj_r2": np.nan, "aic": np.nan, "bic": np.nan, "note": str(exc)})
    return pd.DataFrame(rows)


def run_search(df):
    outcomes = ["abs_Z_capped_3", "abs_Z_conservative", "abs_Poisson", "Z_capped_3"]
    models = ["ols", "ridge", "elasticnet", "huber", "forest"]
    rows = []
    for outcome in outcomes:
        for feature_set in FEATURE_SETS:
            for model in models:
                rows.extend(evaluate_cv(df, outcome, feature_set, model))
    return pd.DataFrame(rows)


def make_plots(df, leaderboard):
    best = leaderboard[(leaderboard["outcome"] == "abs_Z_capped_3") & (leaderboard["scheme"] == "GroupKFold_by_analysis")].sort_values("r2", ascending=False).head(15)
    plt.figure(figsize=(10, 5))
    labels = best["feature_set"] + "/" + best["model"]
    plt.bar(labels, best["r2"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("GroupKFold R2")
    plt.title("Exploratory model search leaderboard")
    plt.tight_layout()
    plt.savefig(FIGURES / "model_search_groupkfold_leaderboard.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 5))
    colors = np.where(df["R_rare"] > 0, "#b23b3b", "#2b6cb0")
    plt.scatter(df["B_label_plus_core"], df["abs_Z_capped_3"], c=colors, s=22, alpha=0.65)
    plt.xlabel("B_label_plus_core")
    plt.ylabel("abs_Z_capped_3")
    plt.title("Best proxy boundary feature vs anomaly magnitude")
    plt.tight_layout()
    plt.savefig(FIGURES / "b_label_plus_core_vs_abs_z.png", dpi=180)
    plt.close()


def write_summary(df, leaderboard, insample):
    gkf = leaderboard[(leaderboard["outcome"] == "abs_Z_capped_3") & (leaderboard["scheme"] == "GroupKFold_by_analysis")].sort_values("r2", ascending=False)
    best = gkf.iloc[0]
    cross = leaderboard[(leaderboard["outcome"] == "abs_Z_capped_3") & (leaderboard["feature_set"] == best["feature_set"]) & (leaderboard["model"] == best["model"]) & (leaderboard["scheme"] != "GroupKFold_by_analysis")]
    overfit = bool(best["r2"] <= 0 or (len(cross) and cross["r2"].mean() <= 0))
    verdict = (
        "Best exploratory model has positive GroupKFold performance, but cross-experiment transfer remains weak/negative; treat as experiment-specific and not robust."
        if not overfit
        else "No robust good fit found under held-out tests; apparent in-sample fit is likely overfit or experiment-specific."
    )
    text = f"""# Iterative Exploratory N-Frame Model Search

## Scope

This is exploratory model development. It intentionally searches candidate feature definitions, so it must not be treated as confirmation.

## Data

- Signal regions: {len(df)}
- Analyses: {df['analysis'].nunique()}
- Nonzero R_rare rows: {(df['R_rare'] != 0).sum()}

## Search Design

Candidate models used defensible variants of the boundary score:

- current verified+imputed B
- label-derived numeric boundary intensity
- core-or-label boundary intensity
- label-plus-core boundary intensity
- metadata-stress controls
- sparse topology interactions

Models were ranked by GroupKFold-by-analysis R2, with ATLAS/CMS transfer reported separately.

## Best Held-Out Model For abs_Z_capped_3

- feature set: `{best['feature_set']}`
- model: `{best['model']}`
- GroupKFold R2: {best['r2']:.6g}
- MAE: {best['mae']:.6g}
- RMSE: {best['rmse']:.6g}
- correlation: {best['corr']:.6g}

Cross-experiment transfer for the same model:

```text
{cross.to_string(index=False)}
```

Top GroupKFold leaderboard:

```text
{gkf.head(12).to_string(index=False)}
```

In-sample fixed-effect fit:

```text
{insample.sort_values('adj_r2', ascending=False).to_string(index=False)}
```

## Interpretation

{verdict}

Do not claim SUSY discovery. Do not claim N-Frame confirmed. If we keep iterating, the next useful improvement is external validation or better verified metadata for the rare-topology rows, not more flexible curve fitting.
"""
    (OUT / "nframe_iterative_model_search_summary.md").write_text(text, encoding="utf-8")


def package():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in [OUT, PROJECT / "scripts" / "run_iterative_nframe_model_search.py"]:
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(PROJECT))
            elif path.exists():
                zf.write(path, path.relative_to(PROJECT))
    return ZIP


def main():
    parser = argparse.ArgumentParser(description="Iterative exploratory N-Frame model search with held-out safeguards.")
    parser.add_argument("--input", default=INPUT)
    args = parser.parse_args()
    ensure_dirs()
    df = prepare(pd.read_csv(args.input))
    df.to_csv(TABLES / "iterative_model_search_dataset.csv", index=False)
    leaderboard = run_search(df)
    leaderboard.to_csv(TABLES / "iterative_model_search_leaderboard.csv", index=False)
    insample = in_sample_ols(df)
    insample.to_csv(TABLES / "iterative_model_search_insample_fixed_effects.csv", index=False)
    make_plots(df, leaderboard)
    write_summary(df, leaderboard, insample)
    zip_path = package()
    print(f"Wrote {zip_path}")
    print((OUT / "nframe_iterative_model_search_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
