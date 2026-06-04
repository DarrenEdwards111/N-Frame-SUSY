import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from common import PROCESSED_DIR, TABLES_DIR, ensure_dirs


def fit_ols(df: pd.DataFrame, y_col: str) -> dict:
    x = sm.add_constant(df["B_access_z"])
    model = sm.OLS(df[y_col], x).fit()
    return {
        "alpha": float(model.params["const"]),
        "beta": float(model.params["B_access_z"]),
        "std_error": float(model.bse["B_access_z"]),
        "p_value": float(model.pvalues["B_access_z"]),
        "r2": float(model.rsquared),
    }


def fast_beta(x: np.ndarray, y: np.ndarray) -> float:
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)
    denom = np.sum(x_centered**2)
    if denom == 0:
        return float("nan")
    return float(np.sum(x_centered * y_centered) / denom)


def bootstrap_beta(df: pd.DataFrame, y_col: str, n_resamples: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    betas = np.empty(n_resamples)
    n = len(df)
    x = df["B_access_z"].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    for i in range(n_resamples):
        idx = rng.integers(0, n, n)
        betas[i] = fast_beta(x[idx], y[idx])
    betas = betas[np.isfinite(betas)]
    return {
        "mean": float(np.mean(betas)),
        "ci_low": float(np.percentile(betas, 2.5)),
        "ci_high": float(np.percentile(betas, 97.5)),
        "n_success": int(len(betas)),
    }


def permutation_p(df: pd.DataFrame, y_col: str, observed_beta: float, n_permutations: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    y = df[y_col].to_numpy()
    x = df["B_access_z"].to_numpy(dtype=float)
    perm_betas = np.empty(n_permutations)
    for i in range(n_permutations):
        perm_betas[i] = fast_beta(x, rng.permutation(y))
    return float((np.sum(np.abs(perm_betas) >= abs(observed_beta)) + 1) / (len(perm_betas) + 1))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OLS, Spearman, bootstrap, and permutation tests.")
    parser.add_argument("--input", default=PROCESSED_DIR / "signal_regions_scored.csv")
    parser.add_argument("--output", default=TABLES_DIR / "regression_results.json")
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260603)
    args = parser.parse_args()

    ensure_dirs()
    df = pd.read_csv(args.input).dropna(subset=["B_access_z", "Z", "Delta_N"])
    results = {"n_signal_regions": int(len(df)), "n_analyses": int(df["analysis"].nunique())}

    for y_col in ["Z", "Delta_N"]:
        ols = fit_ols(df, y_col)
        boot = bootstrap_beta(df, y_col, args.bootstrap, args.seed)
        perm_p = permutation_p(df, y_col, ols["beta"], args.permutations, args.seed + 1)
        results[y_col] = {
            "ols": ols,
            "bootstrap": boot,
            "permutation_p_value": perm_p,
        }

    rho, rho_p = stats.spearmanr(df["B_access_z"], df["Z"])
    results["spearman_B_access_z_vs_Z"] = {"rho": float(rho), "p_value": float(rho_p)}

    Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
