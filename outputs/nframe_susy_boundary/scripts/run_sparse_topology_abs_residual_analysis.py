import argparse
import json
import shutil
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "data" / "processed" / "signal_regions_verified_plus_imputed_scored.csv"
OUTDIR = PROJECT / "results" / "sparse_topology_abs_residual"
TABLES = OUTDIR / "tables"
FIGURES = OUTDIR / "figures"
SUMMARY = OUTDIR / "nframe_sparse_topology_abs_residual_summary.md"
ZIP = PROJECT / "nframe_sparse_topology_abs_residual_results.zip"


OUTCOMES = [
    "abs_Z_capped_3",
    "Z_capped_3",
    "abs_Z_conservative",
    "abs_Poisson",
]


def ensure_dirs():
    for path in [OUTDIR, TABLES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def prepare(df):
    df = df.copy()
    df["R_rare"] = (
        df["R_lifetime_verified_imputed"].fillna(0)
        + df["R_displacement_verified_imputed"].fillna(0)
        + df["R_compression_verified_imputed"].fillna(0)
        + df["R_reconstruction_verified_imputed"].fillna(0)
    )
    df["B"] = df["B_access_verified_imputed_z"]
    df["B_x_Rrare"] = df["B"] * df["R_rare"]
    df["abs_Z"] = df["Z"].abs()
    df["abs_Z_capped_3"] = df["Z_capped_3"].abs()
    df["abs_Z_conservative"] = df["Z_conservative"].abs()
    df["abs_Poisson"] = df["Poisson_deviance_residual"].abs()
    df["R_rare_group"] = np.where(df["R_rare"] > 0, "R_rare_high", "R_rare_low")
    df["B_quartile"] = pd.qcut(df["B"].rank(method="first"), q=4, labels=["Q1", "Q2", "Q3", "Q4"])
    return df


def model_formula(outcome, include_analysis=True):
    fixed = "C(experiment)"
    if include_analysis:
        fixed += " + C(analysis)"
    return f"{outcome} ~ B + R_rare + B_x_Rrare + {fixed}"


def reduced_formula(outcome, include_analysis=True):
    fixed = "C(experiment)"
    if include_analysis:
        fixed += " + C(analysis)"
    return f"{outcome} ~ B + R_rare + {fixed}"


def fit_model(df, outcome, dataset, include_analysis=True):
    cols = [outcome, "B", "R_rare", "B_x_Rrare", "experiment", "analysis"]
    data = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(data) < 20 or data["B_x_Rrare"].nunique() < 2:
        fit = None
        try:
            fit = smf.ols(reduced_formula(outcome, include_analysis=include_analysis), data=data).fit() if len(data) >= 20 else None
        except Exception:
            fit = None
        return {
            "dataset": dataset,
            "outcome": outcome,
            "n": len(data),
            "term": "B_x_Rrare",
            "coef": np.nan,
            "p_value": np.nan,
            "cluster_p_value": np.nan,
            "r2": float(fit.rsquared) if fit is not None else np.nan,
            "adj_r2": float(fit.rsquared_adj) if fit is not None else np.nan,
            "note": "B_x_Rrare not estimable; R2/adj_R2 are reduced model without interaction",
        }
    fit = smf.ols(model_formula(outcome, include_analysis=include_analysis), data=data).fit()
    try:
        cluster = fit.get_robustcov_results(cov_type="cluster", groups=data["analysis"])
        names = list(fit.params.index)
        cluster_p = float(cluster.pvalues[names.index("B_x_Rrare")])
        cluster_se = float(cluster.bse[names.index("B_x_Rrare")])
    except Exception:
        cluster_p = np.nan
        cluster_se = np.nan
    return {
        "dataset": dataset,
        "outcome": outcome,
        "n": len(data),
        "n_analyses": int(data["analysis"].nunique()),
        "term": "B_x_Rrare",
        "coef": float(fit.params.get("B_x_Rrare", np.nan)),
        "std_error": float(fit.bse.get("B_x_Rrare", np.nan)),
        "p_value": float(fit.pvalues.get("B_x_Rrare", np.nan)),
        "cluster_std_error": cluster_se,
        "cluster_p_value": cluster_p,
        "r2": float(fit.rsquared),
        "adj_r2": float(fit.rsquared_adj),
        "note": "analysis FE" if include_analysis else "experiment FE only",
    }


def all_model_results(df):
    rows = []
    for outcome in OUTCOMES:
        rows.append(fit_model(df, outcome, "pooled", include_analysis=True))
        rows.append(fit_model(df[df["experiment"] == "ATLAS"], outcome, "ATLAS", include_analysis=True))
        rows.append(fit_model(df[df["experiment"] == "CMS"], outcome, "CMS", include_analysis=True))
    return pd.DataFrame(rows)


def diagnostic_table(df):
    rows = []
    for dataset, sub in [("pooled", df), ("ATLAS", df[df["experiment"] == "ATLAS"]), ("CMS", df[df["experiment"] == "CMS"])]:
        rows.append(
            {
                "dataset": dataset,
                "n": len(sub),
                "n_analyses": int(sub["analysis"].nunique()),
                "R_rare_nonzero_rows": int((sub["R_rare"] != 0).sum()),
                "B_nonzero_rows": int((sub["B"] != 0).sum()),
                "B_x_Rrare_nonzero_rows": int((sub["B_x_Rrare"] != 0).sum()),
                "B_x_Rrare_unique_values": int(sub["B_x_Rrare"].nunique(dropna=True)),
                "mean_B_when_Rrare_nonzero": float(sub.loc[sub["R_rare"] != 0, "B"].mean()) if (sub["R_rare"] != 0).any() else np.nan,
                "interaction_estimable": bool(sub["B_x_Rrare"].nunique(dropna=True) > 1),
            }
        )
    return pd.DataFrame(rows)


def cv_pipeline():
    try:
        onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        onehot = OneHotEncoder(handle_unknown="ignore", sparse=False)
    return Pipeline(
        [
            (
                "pre",
                ColumnTransformer(
                    [
                        ("num", StandardScaler(), ["B", "R_rare", "B_x_Rrare"]),
                        ("cat", onehot, ["experiment", "analysis"]),
                    ]
                ),
            ),
            ("model", LinearRegression()),
        ]
    )


def metrics(y, pred, scheme, n_train=None):
    return {
        "scheme": scheme,
        "n": int(len(y)),
        "n_train": int(n_train) if n_train is not None else np.nan,
        "r2": float(r2_score(y, pred)) if len(y) > 1 else np.nan,
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "corr": float(pd.Series(y).reset_index(drop=True).corr(pd.Series(pred))),
    }


def cross_validate(df, outcome="abs_Z_capped_3"):
    cols = [outcome, "B", "R_rare", "B_x_Rrare", "experiment", "analysis"]
    data = df[cols].replace([np.inf, -np.inf], np.nan).dropna().copy()
    rows = []
    if data["analysis"].nunique() >= 3:
        preds = np.full(len(data), np.nan)
        groups = data["analysis"]
        for train_idx, test_idx in GroupKFold(n_splits=min(5, data["analysis"].nunique())).split(data, data[outcome], groups):
            pipe = cv_pipeline()
            pipe.fit(data.iloc[train_idx][["B", "R_rare", "B_x_Rrare", "experiment", "analysis"]], data.iloc[train_idx][outcome])
            preds[test_idx] = pipe.predict(data.iloc[test_idx][["B", "R_rare", "B_x_Rrare", "experiment", "analysis"]])
        rows.append(metrics(data[outcome], preds, "GroupKFold_by_analysis", n_train=len(data)))
    for train_exp, test_exp in [("ATLAS", "CMS"), ("CMS", "ATLAS")]:
        train = data[data["experiment"] == train_exp]
        test = data[data["experiment"] == test_exp]
        if len(train) >= 20 and len(test) >= 20:
            pipe = cv_pipeline()
            pipe.fit(train[["B", "R_rare", "B_x_Rrare", "experiment", "analysis"]], train[outcome])
            pred = pipe.predict(test[["B", "R_rare", "B_x_Rrare", "experiment", "analysis"]])
            rows.append(metrics(test[outcome], pred, f"{train_exp}_train_{test_exp}_test", n_train=len(train)))
    return pd.DataFrame(rows)


def coefficient_table(df):
    rows = []
    for dataset, sub in [("pooled", df), ("ATLAS", df[df["experiment"] == "ATLAS"]), ("CMS", df[df["experiment"] == "CMS"])]:
        data = sub[["abs_Z_capped_3", "B", "R_rare", "B_x_Rrare", "experiment", "analysis"]].dropna()
        if len(data) < 20:
            continue
        interaction_ok = data["B_x_Rrare"].nunique() > 1
        fit = smf.ols(
            model_formula("abs_Z_capped_3", include_analysis=True) if interaction_ok else reduced_formula("abs_Z_capped_3", include_analysis=True),
            data=data,
        ).fit()
        for term in ["B", "R_rare"]:
            rows.append(
                {
                    "dataset": dataset,
                    "term": term,
                    "coef": float(fit.params.get(term, np.nan)),
                    "ci_low": float(fit.conf_int().loc[term, 0]) if term in fit.params else np.nan,
                    "ci_high": float(fit.conf_int().loc[term, 1]) if term in fit.params else np.nan,
                    "p_value": float(fit.pvalues.get(term, np.nan)),
                }
            )
        rows.append(
            {
                "dataset": dataset,
                "term": "B_x_Rrare",
                "coef": float(fit.params.get("B_x_Rrare", np.nan)),
                "ci_low": float(fit.conf_int().loc["B_x_Rrare", 0]) if "B_x_Rrare" in fit.params else np.nan,
                "ci_high": float(fit.conf_int().loc["B_x_Rrare", 1]) if "B_x_Rrare" in fit.params else np.nan,
                "p_value": float(fit.pvalues.get("B_x_Rrare", np.nan)),
                "note": "" if interaction_ok else "not estimable: zero variance",
            }
        )
    return pd.DataFrame(rows)


def make_plots(df, coef):
    sample = df.sample(min(len(df), 5000), random_state=7)
    plt.figure(figsize=(7, 5))
    colors = np.where(sample["R_rare"] > 0, "#b23b3b", "#2b6cb0")
    plt.scatter(sample["B"], sample["abs_Z_capped_3"], c=colors, s=22, alpha=0.65)
    plt.xlabel("B_access_verified_imputed_z")
    plt.ylabel("abs_Z_capped_3")
    plt.title("Exploratory: abs_Z_capped_3 vs B by R_rare group")
    plt.tight_layout()
    plt.savefig(FIGURES / "abs_z_capped3_vs_B_by_Rrare.png", dpi=180)
    plt.close()

    q = df.groupby(["B_quartile", "R_rare_group"], observed=False)["abs_Z_capped_3"].mean().reset_index()
    piv = q.pivot(index="B_quartile", columns="R_rare_group", values="abs_Z_capped_3")
    piv.plot(kind="bar", figsize=(7, 5))
    plt.ylabel("Mean abs_Z_capped_3")
    plt.tight_layout()
    plt.savefig(FIGURES / "mean_abs_z_capped3_by_B_quartile_Rrare.png", dpi=180)
    plt.close()

    pooled = coef[coef["dataset"] == "pooled"].copy()
    plt.figure(figsize=(7, 4))
    if len(pooled):
        x = np.arange(len(pooled))
        plt.errorbar(pooled["coef"], x, xerr=[pooled["coef"] - pooled["ci_low"], pooled["ci_high"] - pooled["coef"]], fmt="o")
        plt.yticks(x, pooled["term"])
    else:
        plt.text(0.5, 0.5, "B_x_Rrare not estimable:\ninteraction has zero variance", ha="center", va="center")
        plt.yticks([])
    plt.axvline(0, color="black", lw=1)
    plt.xlabel("Coefficient")
    plt.title("Pooled coefficient plot")
    plt.tight_layout()
    plt.savefig(FIGURES / "coefficient_plot_pooled.png", dpi=180)
    plt.close()

    comp = coef[coef["term"] == "B_x_Rrare"].copy()
    plt.figure(figsize=(6, 4))
    if len(comp):
        plt.bar(comp["dataset"], comp["coef"])
    else:
        plt.text(0.5, 0.5, "No estimable B_x_Rrare coefficient", ha="center", va="center")
    plt.axhline(0, color="black", lw=1)
    plt.ylabel("B_x_Rrare coefficient")
    plt.title("ATLAS vs CMS comparison")
    plt.tight_layout()
    plt.savefig(FIGURES / "atlas_vs_cms_BxRrare_comparison.png", dpi=180)
    plt.close()


def write_summary(df, models, cv, coef, diagnostics):
    primary = models[(models["dataset"] == "pooled") & (models["outcome"] == "abs_Z_capped_3")].iloc[0]
    atlas = models[(models["dataset"] == "ATLAS") & (models["outcome"] == "abs_Z_capped_3")].iloc[0]
    cms = models[(models["dataset"] == "CMS") & (models["outcome"] == "abs_Z_capped_3")].iloc[0]
    gkf = cv[cv["scheme"] == "GroupKFold_by_analysis"]
    gkf_r2 = gkf["r2"].iloc[0] if len(gkf) else np.nan
    interaction_estimable = bool(diagnostics.loc[diagnostics["dataset"] == "pooled", "interaction_estimable"].iloc[0])
    if not interaction_estimable:
        verdict = "Key interaction not estimable: `B_x_Rrare` has zero variance because all nonzero `R_rare` rows have `B = 0` in the current verified+imputed table. This prevents testing the stated prediction."
    elif primary["coef"] > 0 and atlas["coef"] > 0 and cms["coef"] > 0 and np.isfinite(gkf_r2) and gkf_r2 > 0:
        verdict = "Exploratory support: the interaction is positive in pooled and split samples and has positive GroupKFold performance."
    elif primary["coef"] > 0 and (not np.isfinite(gkf_r2) or gkf_r2 <= 0):
        verdict = "In-sample exploratory fit only: the pooled interaction is positive but cross-validation does not support robust generalization."
    elif cms["coef"] <= 0 or pd.isna(cms["coef"]):
        verdict = "Not robust: CMS is null/negative or not estimable, so any signal is experiment-specific."
    else:
        verdict = "No robust exploratory support for the rare-topology boundary-stress model."
    text = f"""# Exploratory Sparse-Topology Absolute-Residual Model

## Scope

This is exploratory model development using `signal_regions_verified_plus_imputed_scored.csv`. It is not confirmation of N-Frame, SUSY, hidden symmetry, or a physics discovery.

## Data

- Signal regions: {len(df)}
- Analyses: {df['analysis'].nunique()}
- ATLAS rows: {(df['experiment'] == 'ATLAS').sum()}
- CMS rows: {(df['experiment'] == 'CMS').sum()}
- Nonzero `R_rare` rows: {(df['R_rare'] != 0).sum()}

## Primary Model

`abs_Z_capped_3 ~ B + R_rare + B_x_Rrare + C(experiment) + C(analysis)`

Primary key prediction: `B_x_Rrare > 0`.

Pooled primary result:

- `B_x_Rrare` coefficient: {primary['coef']:.6g}
- p-value: {primary['p_value']:.6g}
- analysis-clustered p-value: {primary['cluster_p_value']:.6g}
- R2: {primary['r2']:.6g}
- adjusted R2: {primary['adj_r2']:.6g}

Split primary coefficients:

- ATLAS `B_x_Rrare`: {atlas['coef']:.6g}, cluster p={atlas['cluster_p_value']:.6g}
- CMS `B_x_Rrare`: {cms['coef']:.6g}, cluster p={cms['cluster_p_value']:.6g}

Cross-validation:

```text
{cv.to_string(index=False)}
```

Interaction diagnostic:

```text
{diagnostics.to_string(index=False)}
```

## Interpretation

{verdict}

The cross-validation numbers are reported for the sparse-topology feature set, but because `B_x_Rrare` is constant zero, they do not validate the key interaction prediction.

Do not claim SUSY discovery. Do not claim N-Frame confirmed. This is exploratory fit development.
"""
    SUMMARY.write_text(text, encoding="utf-8")


def package():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in [OUTDIR, PROJECT / "scripts" / "run_sparse_topology_abs_residual_analysis.py"]:
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(PROJECT))
            elif path.exists():
                zf.write(path, path.relative_to(PROJECT))
    return ZIP


def main():
    parser = argparse.ArgumentParser(description="Run exploratory sparse-topology absolute-residual N-Frame model.")
    parser.add_argument("--input", default=INPUT)
    args = parser.parse_args()
    ensure_dirs()
    df = prepare(pd.read_csv(args.input))
    df.to_csv(TABLES / "sparse_topology_model_dataset.csv", index=False)
    diagnostics = diagnostic_table(df)
    diagnostics.to_csv(TABLES / "sparse_topology_interaction_diagnostics.csv", index=False)
    models = all_model_results(df)
    models.to_csv(TABLES / "sparse_topology_model_results.csv", index=False)
    cv = cross_validate(df, "abs_Z_capped_3")
    cv.to_csv(TABLES / "sparse_topology_cross_validation.csv", index=False)
    coef = coefficient_table(df)
    coef.to_csv(TABLES / "sparse_topology_coefficients.csv", index=False)
    make_plots(df, coef)
    write_summary(df, models, cv, coef, diagnostics)
    package_path = package()
    print(f"Wrote {models.shape[0]} model rows")
    print(f"Wrote {package_path}")
    print(SUMMARY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
