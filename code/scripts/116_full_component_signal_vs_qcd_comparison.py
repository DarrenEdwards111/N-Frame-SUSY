from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
from scipy import optimize, stats

from susy_signal_common import DATE, REPORTS, ROOT, TABLES


BG = ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_events_with_BNF.csv"
SIG = ROOT / "data" / "processed" / "fuller_component_susy_signals" / "accessible_susy_miniaodsim_events_with_BNF.csv"


def ztest(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else np.nan
    z = (p1 - p2) / se if se and not np.isnan(se) else np.nan
    return z, float(stats.norm.sf(z)) if pd.notna(z) else np.nan


def corrected_z(z: float, m: int) -> float:
    if pd.isna(z):
        return np.nan
    logp = stats.norm.logsf(z) + np.log(m)
    if logp >= 0:
        return -np.inf
    if logp > np.log(np.finfo(float).tiny):
        return float(stats.norm.isf(np.exp(logp)))
    return float(optimize.brentq(lambda x: stats.norm.logsf(x) - logp, 0, 200))


def bootstrap_ci(sig_tail: np.ndarray, bg_tail: np.ndarray, seed: int = 7, draws: int = 1000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(draws):
        s = rng.choice(sig_tail, size=len(sig_tail), replace=True).mean()
        b = rng.choice(bg_tail, size=len(bg_tail), replace=True).mean()
        diffs.append(s - b)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)


def main() -> None:
    df = pd.concat([pd.read_csv(SIG, low_memory=False), pd.read_csv(BG, low_memory=False)], ignore_index=True, sort=False)
    thresholds = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    tails = []
    for (sample, process, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        for t in thresholds.itertuples(index=False):
            k = int((g["B_NF_fitted_frozen_raw"] > t.value).sum())
            tails.append({
                "sample_id": sample, "process_label": process, "classification": cls,
                "threshold": t.threshold, "threshold_value": t.value, "n_total": len(g),
                "n_above": k, "tail_fraction": k / len(g), "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
            })
    tails = pd.DataFrame(tails)
    tails.to_csv(TABLES / "full_component_signal_vs_background_tail_fractions.csv", index=False)
    rows = []
    for _, sig in tails[tails["classification"].eq("signal")].iterrows():
        for _, bg in tails[(tails["classification"].eq("SM_background")) & (tails["threshold"].eq(sig["threshold"]))].iterrows():
            k1, n1, k2, n2 = int(sig.n_above), int(sig.n_total), int(bg.n_above), int(bg.n_total)
            z, p = ztest(k1, n1, k2, n2)
            odds_ratio, fisher_p = stats.fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")
            sig_tail = np.r_[np.ones(k1), np.zeros(n1 - k1)]
            bg_tail = np.r_[np.ones(k2), np.zeros(n2 - k2)]
            ci_lo, ci_hi = bootstrap_ci(sig_tail, bg_tail)
            rows.append({
                "threshold": sig.threshold,
                "signal_sample": sig.sample_id,
                "signal_process": sig.process_label,
                "background_sample": bg.sample_id,
                "background_process": bg.process_label,
                "n_signal": n1,
                "signal_count": k1,
                "signal_tail_fraction": sig.tail_fraction,
                "n_background": n2,
                "background_count": k2,
                "background_tail_fraction": bg.tail_fraction,
                "risk_difference": sig.tail_fraction - bg.tail_fraction,
                "risk_ratio": sig.tail_fraction / bg.tail_fraction if bg.tail_fraction else np.inf,
                "odds_ratio": odds_ratio,
                "z_one_sided": z,
                "p_one_sided": p,
                "fisher_exact_p_greater": fisher_p,
                "bootstrap_risk_difference_ci95_low": ci_lo,
                "bootstrap_risk_difference_ci95_high": ci_hi,
            })
    tests = pd.DataFrame(rows)
    tests.to_csv(TABLES / "full_component_signal_vs_background_sigma_tests.csv", index=False)
    corrected = tests.copy()
    m = len(corrected) if len(corrected) else 1
    corrected["bonferroni_family_size"] = m
    corrected["bonferroni_z"] = corrected["z_one_sided"].apply(lambda x: corrected_z(x, m))
    corrected["remains_5sigma_after_bonferroni"] = corrected["bonferroni_z"] >= 5
    corrected.to_csv(TABLES / "full_component_signal_vs_background_corrected_tests.csv", index=False)
    q95 = corrected[corrected["threshold"].eq("q95")].sort_values("risk_difference", ascending=False)
    report = [
        "# Full Component Signal Versus QCD/WJets Comparison Report",
        "",
        f"Date: {DATE}",
        "",
        "All samples in this comparison have MiniAODSIM-derived reconstruction/displacement components. B_NF remains frozen.",
        "",
        "## q95 Core Comparisons",
        "",
        q95.to_markdown(index=False),
        "",
        "## All Corrected Tests",
        "",
        corrected.to_markdown(index=False),
    ]
    (REPORTS / "FULL_COMPONENT_SIGNAL_VS_QCD_COMPARISON_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(q95.to_string(index=False))


if __name__ == "__main__":
    main()
