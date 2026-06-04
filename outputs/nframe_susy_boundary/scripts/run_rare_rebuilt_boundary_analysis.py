import argparse
import re
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "data" / "processed" / "signal_regions_verified_plus_imputed_scored.csv"
OUT = PROJECT / "results" / "rare_rebuilt_boundary"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
ZIP = PROJECT / "nframe_rare_rebuilt_boundary_results.zip"


def ensure_dirs():
    for p in [OUT, TABLES, FIGURES]:
        p.mkdir(parents=True, exist_ok=True)


def zscore(series):
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def label_numbers(row):
    text = " ".join(str(row.get(c, "")) for c in ["signal_region", "source_comment", "source_path", "category_enriched"])
    vals = []
    for raw in re.findall(r"\d+(?:\.\d+)?", text):
        try:
            val = float(raw)
        except ValueError:
            continue
        if val >= 10:
            vals.append(val)
    return vals


def prepare(df):
    df = df.copy()
    df["R_rare"] = (
        df["R_lifetime_verified_imputed"].fillna(0)
        + df["R_displacement_verified_imputed"].fillna(0)
        + df["R_compression_verified_imputed"].fillna(0)
        + df["R_reconstruction_verified_imputed"].fillna(0)
    )
    df["is_rare"] = (df["R_rare"] != 0).astype(int)
    nums = df.apply(label_numbers, axis=1)
    df["rare_label_max_cut_proxy"] = [max(x) if x else np.nan for x in nums]
    df["rare_label_n_numbers"] = [len(x) for x in nums]
    label_text = (
        df["signal_region"].fillna("").astype(str)
        + " "
        + df["source_comment"].fillna("").astype(str)
        + " "
        + df["source_path"].fillna("").astype(str)
    ).str.lower()
    df["rare_label_high"] = label_text.str.contains("high").astype(int)
    df["rare_label_low"] = label_text.str.contains("low").astype(int)
    df["rare_label_bdt"] = label_text.str.contains("bdt").astype(int)
    df["B_original"] = df["B_access_verified_imputed_z"].fillna(0)
    df["B_rare_proxy_raw"] = (
        zscore(np.log1p(df["rare_label_max_cut_proxy"]))
        + 0.5 * zscore(df["rare_label_n_numbers"])
        + 0.5 * df["rare_label_high"]
        + 0.25 * df["rare_label_bdt"]
    )
    df["B_rare_proxy_z"] = zscore(df["B_rare_proxy_raw"])
    df["B_rebuilt_raw"] = df["B_original"]
    rare_has_proxy = (df["is_rare"] == 1) & df["B_rare_proxy_z"].notna()
    df.loc[rare_has_proxy, "B_rebuilt_raw"] = df.loc[rare_has_proxy, "B_rare_proxy_z"]
    df["B_rebuilt"] = zscore(df["B_rebuilt_raw"])
    df["B_rebuilt_x_Rrare"] = df["B_rebuilt"] * df["R_rare"]
    df["B_original_x_Rrare"] = df["B_original"] * df["R_rare"]
    df["abs_Z_capped_3"] = df["Z_capped_3"].abs()
    df["abs_Z_conservative"] = df["Z_conservative"].abs()
    df["abs_Poisson"] = df["Poisson_deviance_residual"].abs()
    return df


def fit(df, outcome, dataset):
    data = df[[outcome, "B_rebuilt", "R_rare", "B_rebuilt_x_Rrare", "experiment", "analysis"]].dropna()
    if len(data) < 30 or data["B_rebuilt_x_Rrare"].nunique() < 2:
        return {"dataset": dataset, "outcome": outcome, "n": len(data), "coef": np.nan, "p_value": np.nan, "cluster_p_value": np.nan, "r2": np.nan, "adj_r2": np.nan, "note": "not estimable"}
    model = smf.ols(f"{outcome} ~ B_rebuilt + R_rare + B_rebuilt_x_Rrare + C(experiment) + C(analysis)", data=data).fit()
    try:
        cluster = model.get_robustcov_results(cov_type="cluster", groups=data["analysis"])
        names = list(model.params.index)
        cp = float(cluster.pvalues[names.index("B_rebuilt_x_Rrare")])
    except Exception:
        cp = np.nan
    return {
        "dataset": dataset,
        "outcome": outcome,
        "n": len(data),
        "n_analyses": data["analysis"].nunique(),
        "coef": float(model.params["B_rebuilt_x_Rrare"]),
        "p_value": float(model.pvalues["B_rebuilt_x_Rrare"]),
        "cluster_p_value": cp,
        "r2": float(model.rsquared),
        "adj_r2": float(model.rsquared_adj),
        "note": "exploratory proxy B for rare rows",
    }


def mean_tests(df):
    rows = []
    for outcome in ["abs_Z_capped_3", "abs_Z_conservative", "abs_Poisson", "Z_capped_3"]:
        rare = df.loc[df["is_rare"] == 1, outcome].dropna()
        non = df.loc[df["is_rare"] == 0, outcome].dropna()
        test = stats.ttest_ind(rare, non, equal_var=False)
        rows.append(
            {
                "outcome": outcome,
                "rare_mean": rare.mean(),
                "nonrare_mean": non.mean(),
                "difference": rare.mean() - non.mean(),
                "welch_p": test.pvalue,
                "rare_n": len(rare),
                "nonrare_n": len(non),
            }
        )
    return pd.DataFrame(rows)


def cv(df, outcome="abs_Z_capped_3"):
    cols = [outcome, "B_rebuilt", "R_rare", "B_rebuilt_x_Rrare", "experiment", "analysis"]
    data = df[cols].dropna()
    try:
        onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        onehot = OneHotEncoder(handle_unknown="ignore", sparse=False)
    pipe = Pipeline(
        [
            ("pre", ColumnTransformer([("num", StandardScaler(), ["B_rebuilt", "R_rare", "B_rebuilt_x_Rrare"]), ("exp", onehot, ["experiment"])])),
            ("model", RidgeCV(alphas=np.logspace(-3, 3, 25))),
        ]
    )
    rows = []
    pred = np.full(len(data), np.nan)
    for train_idx, test_idx in GroupKFold(n_splits=min(5, data["analysis"].nunique())).split(data, data[outcome], groups=data["analysis"]):
        pipe.fit(data.iloc[train_idx][["B_rebuilt", "R_rare", "B_rebuilt_x_Rrare", "experiment"]], data.iloc[train_idx][outcome])
        pred[test_idx] = pipe.predict(data.iloc[test_idx][["B_rebuilt", "R_rare", "B_rebuilt_x_Rrare", "experiment"]])
    rows.append(metrics(data[outcome], pred, "GroupKFold_by_analysis", len(data)))
    for train_exp, test_exp in [("ATLAS", "CMS"), ("CMS", "ATLAS")]:
        train = data[data["experiment"] == train_exp]
        test = data[data["experiment"] == test_exp]
        if len(train) and len(test):
            pipe.fit(train[["B_rebuilt", "R_rare", "B_rebuilt_x_Rrare", "experiment"]], train[outcome])
            p = pipe.predict(test[["B_rebuilt", "R_rare", "B_rebuilt_x_Rrare", "experiment"]])
            rows.append(metrics(test[outcome], p, f"{train_exp}_train_{test_exp}_test", len(train)))
    return pd.DataFrame(rows)


def metrics(y, pred, scheme, n_train):
    return {
        "scheme": scheme,
        "n": len(y),
        "n_train": n_train,
        "r2": r2_score(y, pred),
        "mae": mean_absolute_error(y, pred),
        "rmse": np.sqrt(mean_squared_error(y, pred)),
        "corr": pd.Series(y).reset_index(drop=True).corr(pd.Series(pred)),
    }


def plots(df):
    plt.figure(figsize=(7, 5))
    colors = np.where(df["is_rare"] == 1, "#b23b3b", "#2b6cb0")
    plt.scatter(df["B_rebuilt"], df["abs_Z_capped_3"], c=colors, s=22, alpha=0.6)
    plt.xlabel("B_rebuilt")
    plt.ylabel("abs_Z_capped_3")
    plt.tight_layout()
    plt.savefig(FIGURES / "abs_z_capped3_vs_B_rebuilt.png", dpi=180)
    plt.close()

    rare = df[df["is_rare"] == 1].copy()
    if len(rare):
        rare["B_rebuilt_quartile"] = pd.qcut(rare["B_rebuilt"].rank(method="first"), q=min(4, len(rare)), labels=False)
        q = rare.groupby("B_rebuilt_quartile")["abs_Z_capped_3"].mean()
        plt.figure(figsize=(6, 4))
        q.plot(kind="bar")
        plt.ylabel("Mean abs_Z_capped_3")
        plt.xlabel("Rare-row B_rebuilt quartile")
        plt.tight_layout()
        plt.savefig(FIGURES / "rare_rows_mean_abs_z_by_B_rebuilt_quartile.png", dpi=180)
        plt.close()


def summary(results, tests, cvres, df):
    primary = results[(results["dataset"] == "pooled") & (results["outcome"] == "abs_Z_capped_3")].iloc[0]
    if primary["coef"] > 0 and primary["cluster_p_value"] < 0.05 and cvres.loc[cvres["scheme"] == "GroupKFold_by_analysis", "r2"].iloc[0] > 0:
        verdict = "Exploratory proxy support: rebuilt rare-row B makes the interaction estimable and positive in pooled data, but it remains proxy-derived and must be externally validated."
    elif primary["coef"] > 0:
        verdict = "Weak exploratory signal: interaction is positive after rebuilding rare-row B, but robustness/CV is insufficient."
    else:
        verdict = "No support for a positive rebuilt-B rare interaction; the rare-vs-nonrare magnitude effect remains the cleaner exploratory finding."
    text = f"""# Rare-Row Rebuilt Boundary Analysis

## Scope

This is exploratory model development. `B_rebuilt` uses label-derived cut-scale proxies for rare rows whose verified+imputed `B` collapsed to zero. These proxy values are not verified cut metadata.

## Key Data Facts

- Signal regions: {len(df)}
- Rare rows: {int(df['is_rare'].sum())}
- Rare rows with proxy cut numbers: {int(((df['is_rare'] == 1) & df['rare_label_max_cut_proxy'].notna()).sum())}
- Nonzero rebuilt interaction rows: {int((df['B_rebuilt_x_Rrare'] != 0).sum())}

## Rare vs Nonrare Magnitude Tests

```text
{tests.to_string(index=False)}
```

## Interaction Models

```text
{results.to_string(index=False)}
```

## Cross-Validation

```text
{cvres.to_string(index=False)}
```

## Interpretation

{verdict}

Do not claim SUSY discovery. Do not claim N-Frame confirmed. The stable result remains that rare/reconstruction-stressed topologies have larger residual magnitudes; the boundary interaction now depends on proxy label reconstruction and needs real HEPData/paper cut metadata.
"""
    (OUT / "nframe_rare_rebuilt_boundary_summary.md").write_text(text, encoding="utf-8")


def package():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in [OUT, PROJECT / "scripts" / "run_rare_rebuilt_boundary_analysis.py"]:
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(PROJECT))
            elif path.exists():
                zf.write(path, path.relative_to(PROJECT))
    return ZIP


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=INPUT)
    args = parser.parse_args()
    ensure_dirs()
    df = prepare(pd.read_csv(args.input))
    df.to_csv(TABLES / "rare_rebuilt_boundary_dataset.csv", index=False)
    tests = mean_tests(df)
    tests.to_csv(TABLES / "rare_vs_nonrare_magnitude_tests.csv", index=False)
    rows = []
    for outcome in ["abs_Z_capped_3", "Z_capped_3", "abs_Z_conservative", "abs_Poisson"]:
        rows.append(fit(df, outcome, "pooled"))
        rows.append(fit(df[df["experiment"] == "ATLAS"], outcome, "ATLAS"))
        rows.append(fit(df[df["experiment"] == "CMS"], outcome, "CMS"))
    results = pd.DataFrame(rows)
    results.to_csv(TABLES / "rare_rebuilt_boundary_model_results.csv", index=False)
    cvres = cv(df)
    cvres.to_csv(TABLES / "rare_rebuilt_boundary_cross_validation.csv", index=False)
    plots(df)
    summary(results, tests, cvres, df)
    zip_path = package()
    print(f"Wrote {zip_path}")
    print((OUT / "nframe_rare_rebuilt_boundary_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
