import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from common import TABLES_DIR, ensure_dirs
from run_regression import fast_beta


def ols_summary(df: pd.DataFrame, y_col: str = "Z") -> dict:
    x = sm.add_constant(df["B_access_z"])
    model = sm.OLS(df[y_col], x).fit()
    rho, rho_p = stats.spearmanr(df["B_access_z"], df[y_col])
    return {
        "n": int(len(df)),
        "n_analyses": int(df["analysis"].nunique()),
        "beta": float(model.params["B_access_z"]),
        "se": float(model.bse["B_access_z"]),
        "p": float(model.pvalues["B_access_z"]),
        "r2": float(model.rsquared),
        "spearman_rho": float(rho),
        "spearman_p": float(rho_p),
    }


def bootstrap_ci(df: pd.DataFrame, y_col: str, n_resamples: int, seed: int, by_analysis: bool) -> dict:
    rng = np.random.default_rng(seed)
    betas = []
    if by_analysis:
        groups = {k: g for k, g in df.groupby("analysis")}
        keys = np.array(list(groups.keys()))
        for _ in range(n_resamples):
            sampled = [groups[k] for k in rng.choice(keys, size=len(keys), replace=True)]
            sample = pd.concat(sampled, ignore_index=True)
            betas.append(fast_beta(sample["B_access_z"].to_numpy(), sample[y_col].to_numpy()))
    else:
        x = df["B_access_z"].to_numpy()
        y = df[y_col].to_numpy()
        n = len(df)
        for _ in range(n_resamples):
            idx = rng.integers(0, n, n)
            betas.append(fast_beta(x[idx], y[idx]))
    betas = np.asarray(betas)
    betas = betas[np.isfinite(betas)]
    return {
        "ci_low": float(np.percentile(betas, 2.5)),
        "ci_high": float(np.percentile(betas, 97.5)),
        "mean": float(np.mean(betas)),
        "n_success": int(len(betas)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run robustness checks for the expanded N-Frame SR analysis.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=TABLES_DIR / "real_full_robustness_results.json")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260604)
    args = parser.parse_args()

    ensure_dirs()
    df = pd.read_csv(args.input).dropna(subset=["B_access_z", "Z", "Delta_N"])
    checks = {
        "pooled_Z": ols_summary(df, "Z"),
        "pooled_Delta_N": ols_summary(df, "Delta_N"),
        "row_bootstrap_Z": bootstrap_ci(df, "Z", args.bootstrap, args.seed, by_analysis=False),
        "analysis_cluster_bootstrap_Z": bootstrap_ci(df, "Z", args.bootstrap, args.seed + 1, by_analysis=True),
        "experiments_Z": {},
        "trimmed_Z": {},
        "categories_Z": {},
    }

    for exp, sub in df.groupby("experiment"):
        if len(sub) >= 10:
            checks["experiments_Z"][exp] = ols_summary(sub, "Z")

    for threshold in [3, 5, 10]:
        sub = df[df["Z"].abs() <= threshold]
        checks["trimmed_Z"][f"abs_Z_le_{threshold}"] = ols_summary(sub, "Z")

    category_terms = ["compressed", "disappearing_track", "long_lived", "displaced", "high_MET", "high_multiplicity"]
    for term in category_terms:
        mask = df["category"].fillna("").str.contains(term, regex=False)
        if mask.sum() >= 10:
            checks["categories_Z"][term] = ols_summary(df[mask], "Z")

    Path(args.output).write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
