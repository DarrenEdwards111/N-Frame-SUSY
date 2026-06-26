from __future__ import annotations

from math import log10, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
PAIRS = [
    ("sms_t5wg_mg1500_mlsp1_signal", "ttjets_nanoaodsim_pilot"),
    ("sms_t5wg_mg1500_mlsp1_signal", "qcd_ht700to1000_nanoaodsim_pilot"),
    ("sms_t5wg_mg1500_mlsp1_signal", "pooled_sm_background"),
    ("susy_htoaa4b_m12_signal", "ttjets_nanoaodsim_pilot"),
    ("susy_htoaa4b_m12_signal", "qcd_ht700to1000_nanoaodsim_pilot"),
]


def wilson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return max(0, centre - half), min(1, centre + half)


def log10_norm_sf(z: float) -> float:
    return float(stats.norm.logsf(z) / np.log(10))


def p_to_z(p: float, z_fallback: float | None = None) -> float:
    if p > 0:
        return float(stats.norm.isf(p))
    return float(z_fallback) if z_fallback is not None else np.inf


def pooled_rows(counts: pd.DataFrame) -> pd.DataFrame:
    sm = counts[counts["classification"].eq("SM_background")]
    rows = []
    for threshold, group in sm.groupby("threshold"):
        n = int(group["n_total"].sum())
        k = int(group["n_above_threshold"].sum())
        rows.append({
            "sample_id": "pooled_sm_background",
            "process_label": "Pooled TTJets + QCD",
            "classification": "SM_background",
            "threshold": threshold,
            "threshold_value": group["threshold_value"].iloc[0],
            "n_total": n,
            "n_above_threshold": k,
            "n_below_threshold": n - k,
            "tail_fraction": k / n,
            "mean_BNF": np.nan,
            "median_BNF": np.nan,
            "component_mode": "pooled reduced-component SM background",
        })
    return pd.DataFrame(rows)


def test_pair(signal, background) -> dict:
    k1, n1 = int(signal.n_above_threshold), int(signal.n_total)
    k2, n2 = int(background.n_above_threshold), int(background.n_total)
    p1, p2 = k1 / n1, k2 / n2
    pooled = (k1 + k2) / (n1 + n2)
    se = sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2)) if pooled not in [0, 1] else np.nan
    z = (p1 - p2) / se if se and not np.isnan(se) else np.nan
    p_one = float(stats.norm.sf(z)) if not np.isnan(z) else np.nan
    log10p = log10_norm_sf(z) if not np.isnan(z) else np.nan
    table = [[k1, n1 - k1], [k2, n2 - k2]]
    try:
        fisher = stats.fisher_exact(table, alternative="greater")
        fisher_p = float(fisher.pvalue)
        odds_ratio = float(fisher.statistic)
    except Exception:
        fisher_p, odds_ratio = np.nan, np.nan
    rr = np.inf if p2 == 0 and p1 > 0 else (p1 / p2 if p2 else np.nan)
    rd = p1 - p2
    ci1 = wilson(k1, n1)
    ci2 = wilson(k2, n2)
    se_rd = sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    rd_ci = (rd - 1.96 * se_rd, rd + 1.96 * se_rd)
    rr_ci = (np.nan, np.nan)
    if k1 > 0 and k2 > 0:
        se_log_rr = sqrt((1 / k1) - (1 / n1) + (1 / k2) - (1 / n2))
        rr_ci = (float(np.exp(np.log(rr) - 1.96 * se_log_rr)), float(np.exp(np.log(rr) + 1.96 * se_log_rr)))
    return {
        "threshold": signal.threshold,
        "threshold_value": signal.threshold_value,
        "signal_sample": signal.sample_id,
        "background_sample": background.sample_id,
        "signal_count": k1,
        "signal_total": n1,
        "background_count": k2,
        "background_total": n2,
        "p_signal": p1,
        "p_background": p2,
        "risk_difference": rd,
        "risk_difference_ci95_low": rd_ci[0],
        "risk_difference_ci95_high": rd_ci[1],
        "risk_ratio": rr,
        "risk_ratio_ci95_low": rr_ci[0],
        "risk_ratio_ci95_high": rr_ci[1],
        "odds_ratio": odds_ratio,
        "signal_fraction_ci95_low": ci1[0],
        "signal_fraction_ci95_high": ci1[1],
        "background_fraction_ci95_low": ci2[0],
        "background_fraction_ci95_high": ci2[1],
        "z_two_proportion_one_sided": z,
        "p_two_proportion_one_sided": p_one,
        "log10_p_two_proportion_one_sided": log10p,
        "fisher_exact_p_one_sided": fisher_p,
        "fisher_exact_z_equivalent": p_to_z(fisher_p, z),
        "exceeds_5sigma_two_prop": bool(z >= 5) if not np.isnan(z) else False,
    }


def main() -> None:
    counts = pd.read_csv(TABLES / "sigma_tail_counts_by_sample.csv")
    counts = pd.concat([counts, pooled_rows(counts)], ignore_index=True)
    rows = []
    for signal_id, background_id in PAIRS:
        for threshold in ["q90", "q95", "q99", "q999"]:
            s = counts[(counts["sample_id"].eq(signal_id)) & (counts["threshold"].eq(threshold))]
            b = counts[(counts["sample_id"].eq(background_id)) & (counts["threshold"].eq(threshold))]
            if s.empty or b.empty:
                continue
            rows.append(test_pair(s.iloc[0], b.iloc[0]))
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "two_proportion_sigma_tests.csv", index=False)
    report = [
        "# Two-Proportion Sigma Test Report",
        "",
        f"Date: {DATE}",
        "",
        "H0: p_signal <= p_SM. H1: p_signal > p_SM. The frozen B_NF equation was not refitted.",
        "",
        out.to_markdown(index=False),
    ]
    (REPORTS / "TWO_PROPORTION_SIGMA_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
