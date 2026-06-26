from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"


def beta_binomial_tail(k_obs: int, n_sig: int, k_bg: int, n_bg: int, draws: int = 200_000, seed: int = 33) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    p = rng.beta(k_bg + 1, n_bg - k_bg + 1, size=draws)
    probs = stats.binom.sf(k_obs - 1, n_sig, p)
    p_mean = float(np.mean(probs))
    return p_mean, float(stats.norm.isf(p_mean)) if p_mean > 0 else np.inf


def main() -> None:
    counts = pd.read_csv(TABLES / "sigma_tail_counts_by_sample.csv")
    sm = counts[counts["classification"].eq("SM_background")]
    pooled = sm.groupby("threshold", as_index=False).agg(n_total=("n_total", "sum"), n_above_threshold=("n_above_threshold", "sum"), threshold_value=("threshold_value", "first"))
    pooled["sample_id"] = "pooled_sm_background"
    rows = []
    sms = counts[counts["sample_id"].eq("sms_t5wg_mg1500_mlsp1_signal")]
    backgrounds = pd.concat([counts[counts["sample_id"].isin(["ttjets_nanoaodsim_pilot", "qcd_ht700to1000_nanoaodsim_pilot"])], pooled], ignore_index=True)
    for threshold in ["q95", "q99"]:
        s = sms[sms["threshold"].eq(threshold)].iloc[0]
        for _, b in backgrounds[backgrounds["threshold"].eq(threshold)].iterrows():
            n_sig = int(s.n_total)
            k_obs = int(s.n_above_threshold)
            n_bg = int(b.n_total)
            k_bg = int(b.n_above_threshold)
            p_bg = k_bg / n_bg
            expected = p_bg * n_sig
            p_binom = float(stats.binom.sf(k_obs - 1, n_sig, p_bg))
            z_binom = float(stats.norm.isf(p_binom)) if p_binom > 0 else np.inf
            log10_p = float(stats.binom.logsf(k_obs - 1, n_sig, p_bg) / np.log(10))
            excess = max(0, k_obs - expected)
            asimov = np.sqrt(2 * ((excess + expected) * np.log((excess + expected) / expected) - excess)) if expected > 0 and excess > 0 else 0
            p_beta, z_beta = beta_binomial_tail(k_obs, n_sig, k_bg, n_bg)
            rows.append({
                "threshold": threshold,
                "background_model": b.sample_id,
                "sms_total": n_sig,
                "sms_observed_tail_count": k_obs,
                "background_total": n_bg,
                "background_tail_count": k_bg,
                "background_tail_probability": p_bg,
                "expected_background_count_in_sms_n": expected,
                "binomial_tail_p": p_binom,
                "binomial_tail_log10p": log10_p,
                "binomial_z": z_binom,
                "asimov_style_z": asimov,
                "beta_binomial_tail_p_mean": p_beta,
                "beta_binomial_z_mean": z_beta,
            })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "likelihood_counting_sigma.csv", index=False)
    report = ["# Likelihood Counting Sigma Report", "", f"Date: {DATE}", "", "This treats high-B_NF occupancy as a benchmark counting model, not a particle-discovery counting experiment.", "", out.to_markdown(index=False)]
    (REPORTS / "LIKELIHOOD_COUNTING_SIGMA_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
