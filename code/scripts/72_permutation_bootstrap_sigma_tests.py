from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
DATE = "2026-06-09"
COMPARISONS = [
    ("sms_t5wg_mg1500_mlsp1_signal", "ttjets_nanoaodsim_pilot"),
    ("sms_t5wg_mg1500_mlsp1_signal", "qcd_ht700to1000_nanoaodsim_pilot"),
    ("sms_t5wg_mg1500_mlsp1_signal", "pooled_sm_background"),
]


def load_events() -> pd.DataFrame:
    return pd.concat([pd.read_csv(SUSY), pd.read_csv(SM)], ignore_index=True)


def pooled_z(k1, n1, k2, n2) -> float:
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if p not in [0, 1] else np.nan
    return (p1 - p2) / se if se and not np.isnan(se) else np.nan


def boot_ci(signal_scores, background_scores, threshold, reps=1000, seed=7):
    rng = np.random.default_rng(seed)
    s = np.asarray(signal_scores)
    b = np.asarray(background_scores)
    rows = []
    for _ in range(reps):
        sb = rng.choice(s, len(s), replace=True)
        bb = rng.choice(b, len(b), replace=True)
        sf = (sb > threshold).mean()
        bf = (bb > threshold).mean()
        rows.append([sf - bf, sf / bf if bf else np.inf, sb.mean() - bb.mean(), np.median(sb) - np.median(bb)])
    arr = np.asarray(rows)
    return np.quantile(arr, [0.025, 0.5, 0.975], axis=0)


def permutation_p(signal_scores, background_scores, threshold, reps=10_000, seed=11):
    rng = np.random.default_rng(seed)
    s = np.asarray(signal_scores)
    b = np.asarray(background_scores)
    obs = (s > threshold).mean() - (b > threshold).mean()
    pooled = np.concatenate([s, b])
    n_s = len(s)
    exceed = 0
    for _ in range(reps):
        idx = rng.permutation(len(pooled))
        ps = pooled[idx[:n_s]]
        pb = pooled[idx[n_s:]]
        diff = (ps > threshold).mean() - (pb > threshold).mean()
        if diff >= obs:
            exceed += 1
    p = (exceed + 1) / (reps + 1)
    return obs, p, float(stats.norm.isf(p))


def equal_size(signal_scores, background_scores, threshold, reps=1000, seed=23):
    rng = np.random.default_rng(seed)
    s = np.asarray(signal_scores)
    b = np.asarray(background_scores)
    n = min(len(s), len(b))
    rows = []
    for _ in range(reps):
        ss = rng.choice(s, n, replace=False if len(s) >= n else True)
        bb = rng.choice(b, n, replace=False if len(b) >= n else True)
        k1, k2 = int((ss > threshold).sum()), int((bb > threshold).sum())
        rows.append([k1 / n - k2 / n, pooled_z(k1, n, k2, n)])
    arr = np.asarray(rows)
    return np.quantile(arr, [0.025, 0.5, 0.975], axis=0)


def get_background(df: pd.DataFrame, background_id: str) -> pd.Series:
    if background_id == "pooled_sm_background":
        return df[df["classification"].eq("SM_background")]["B_NF_fitted_frozen_raw"].dropna()
    return df[df["sample_id"].eq(background_id)]["B_NF_fitted_frozen_raw"].dropna()


def main() -> None:
    df = load_events()
    th = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    thresholds = th[th["threshold"].isin(["q90", "q95", "q99"])]
    boot_rows, perm_rows, eq_rows = [], [], []
    for signal_id, background_id in COMPARISONS:
        s = df[df["sample_id"].eq(signal_id)]["B_NF_fitted_frozen_raw"].dropna()
        b = get_background(df, background_id)
        for t in thresholds.itertuples(index=False):
            q = float(t.value)
            ci = boot_ci(s, b, q)
            boot_rows.append({
                "signal_sample": signal_id,
                "background_sample": background_id,
                "threshold": t.threshold,
                "tail_diff_ci95_low": ci[0, 0],
                "tail_diff_median": ci[1, 0],
                "tail_diff_ci95_high": ci[2, 0],
                "tail_ratio_ci95_low": ci[0, 1],
                "tail_ratio_median": ci[1, 1],
                "tail_ratio_ci95_high": ci[2, 1],
                "mean_BNF_diff_ci95_low": ci[0, 2],
                "mean_BNF_diff_median": ci[1, 2],
                "mean_BNF_diff_ci95_high": ci[2, 2],
                "median_BNF_diff_ci95_low": ci[0, 3],
                "median_BNF_diff_median": ci[1, 3],
                "median_BNF_diff_ci95_high": ci[2, 3],
            })
            obs, p, z = permutation_p(s, b, q)
            perm_rows.append({"signal_sample": signal_id, "background_sample": background_id, "threshold": t.threshold, "observed_tail_difference": obs, "permutation_p_one_sided": p, "permutation_z_equivalent": z, "permutations": 10_000})
            eq = equal_size(s, b, q)
            eq_rows.append({"signal_sample": signal_id, "background_sample": background_id, "threshold": t.threshold, "tail_diff_ci95_low": eq[0, 0], "tail_diff_median": eq[1, 0], "tail_diff_ci95_high": eq[2, 0], "z_ci95_low": eq[0, 1], "z_median": eq[1, 1], "z_ci95_high": eq[2, 1]})
    boot = pd.DataFrame(boot_rows)
    perm = pd.DataFrame(perm_rows)
    eq = pd.DataFrame(eq_rows)
    boot.to_csv(TABLES / "bootstrap_sigma_robustness.csv", index=False)
    perm.to_csv(TABLES / "permutation_sigma_robustness.csv", index=False)
    eq.to_csv(TABLES / "equal_size_subsample_sigma_robustness.csv", index=False)
    report = ["# Permutation Bootstrap Sigma Robustness Report", "", f"Date: {DATE}", "", "## Bootstrap", "", boot.to_markdown(index=False), "", "## Permutation", "", perm.to_markdown(index=False), "", "## Equal-Size Subsampling", "", eq.to_markdown(index=False)]
    (REPORTS / "PERMUTATION_BOOTSTRAP_SIGMA_ROBUSTNESS_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(perm.to_string(index=False))


if __name__ == "__main__":
    main()
