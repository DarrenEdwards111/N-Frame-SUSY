from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
EVENTS = ROOT / "data" / "processed" / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv"
THRESH = TABLES / "bnf_thresholds_real_and_sm.csv"
DATE = "2026-06-09"


def ztest(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if p not in [0, 1] else np.nan
    z = (p1 - p2) / se if se and not np.isnan(se) else np.nan
    pval = float(stats.norm.sf(z)) if pd.notna(z) else np.nan
    log10p = float(stats.norm.logsf(z) / np.log(10)) if pd.notna(z) else np.nan
    return z, pval, log10p


def corrected_z(z, m):
    if pd.isna(z):
        return np.nan
    logp = stats.norm.logsf(z) + np.log(m)
    if logp >= 0:
        return -np.inf
    if logp > np.log(np.finfo(float).tiny):
        return float(stats.norm.isf(np.exp(logp)))
    return float(optimize.brentq(lambda x: stats.norm.logsf(x) - logp, 0, 200))


def main():
    df = pd.read_csv(EVENTS)
    th = pd.read_csv(THRESH)
    tails = []
    for (sample, process, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        for t in th.itertuples(index=False):
            k = int((g["B_NF_fitted_frozen_raw"] > t.value).sum())
            n = len(g)
            tails.append({"sample_id": sample, "process_label": process, "classification": cls, "threshold": t.threshold, "threshold_value": t.value, "n_total": n, "n_above": k, "tail_fraction": k/n, "mean_BNF": g["B_NF_fitted_frozen_raw"].mean()})
    tail = pd.DataFrame(tails)
    tail.to_csv(TABLES / "expanded_benchmark_tail_fractions.csv", index=False)
    sigs = tail[tail["classification"].eq("signal")]
    bgs = tail[tail["classification"].eq("SM_background")]
    rows = []
    for _, s in sigs.iterrows():
        for _, b in bgs[bgs["threshold"].eq(s["threshold"])].iterrows():
            z, p, log10p = ztest(int(s.n_above), int(s.n_total), int(b.n_above), int(b.n_total))
            rows.append({"threshold": s.threshold, "signal_sample": s.sample_id, "signal_process": s.process_label, "background_sample": b.sample_id, "background_process": b.process_label, "signal_count": int(s.n_above), "signal_total": int(s.n_total), "background_count": int(b.n_above), "background_total": int(b.n_total), "p_signal": s.tail_fraction, "p_background": b.tail_fraction, "risk_difference": s.tail_fraction - b.tail_fraction, "risk_ratio": s.tail_fraction / b.tail_fraction if b.tail_fraction else np.inf, "z_one_sided": z, "p_one_sided": p, "log10_p": log10p})
    tests = pd.DataFrame(rows)
    tests.to_csv(TABLES / "expanded_benchmark_sigma_tests.csv", index=False)
    m = len(tests)
    corr = tests.copy()
    corr["bonferroni_family_size"] = m
    corr["bonferroni_z"] = corr["z_one_sided"].apply(lambda z: corrected_z(z, m))
    corr["remains_5sigma_after_bonferroni"] = corr["bonferroni_z"] >= 5
    corr.to_csv(TABLES / "expanded_benchmark_corrected_sigma_tests.csv", index=False)
    key = corr[(corr["signal_sample"].eq("sms_t5wg_mg1500_mlsp1_signal")) & (corr["threshold"].isin(["q95", "q99"]))].sort_values(["threshold", "bonferroni_z"], ascending=[True, False])
    report = ["# Expanded Benchmark Five Sigma Test Report", "", f"Date: {DATE}", "", "The frozen B_NF equation was not refitted. Expanded samples are benchmark/specificity tests only.", "", "## Tail Fractions", "", tail.to_markdown(index=False), "", "## Corrected Sigma Tests", "", corr.to_markdown(index=False), "", "## SMS-T5Wg Key Rows", "", key.to_markdown(index=False)]
    (REPORTS / "EXPANDED_BENCHMARK_FIVE_SIGMA_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(key.to_string(index=False))


if __name__ == "__main__":
    main()
