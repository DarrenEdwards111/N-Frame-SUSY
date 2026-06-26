from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
FILES = {
    "Run2016G": OUT / "run2016g_real_with_trace_direction.csv",
    "Run2016H": OUT / "run2016h_real_with_trace_direction.csv",
    "combined": OUT / "combined_real_with_trace_direction.csv",
}


def z_mean(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    res = stats.ttest_ind(a.dropna(), b.dropna(), equal_var=False, alternative="greater")
    return float(res.statistic), float(res.pvalue)


def boot_ci(a: pd.Series, b: pd.Series, reps=1000, seed=99):
    rng = np.random.default_rng(seed)
    av = a.dropna().to_numpy()
    bv = b.dropna().to_numpy()
    vals = []
    for _ in range(reps):
        vals.append(rng.choice(av, len(av), replace=True).mean() - rng.choice(bv, len(bv), replace=True).mean())
    return np.quantile(vals, [0.025, 0.5, 0.975])


def main() -> None:
    rows = []
    for dataset, path in FILES.items():
        df = pd.read_csv(path)
        score = "B_NF_trace_base"
        trace = "Trace_sms_vs_pooledSM"
        for label, q in [("top10", .90), ("top05", .95), ("top01", .99), ("top001", .999)]:
            thr = df[score].quantile(q)
            high = df[df[score] >= thr]
            rest = df[df[score] < thr]
            z, p = z_mean(high[trace], rest[trace])
            ci = boot_ci(high[trace], rest[trace])
            trace_q90 = df[trace].quantile(.90)
            k1, n1 = int((high[trace] >= trace_q90).sum()), len(high)
            k2, n2 = int((rest[trace] >= trace_q90).sum()), len(rest)
            p1, p2 = k1/n1, k2/n2
            pooled = (k1+k2)/(n1+n2)
            se = sqrt(pooled*(1-pooled)*(1/n1+1/n2)) if pooled not in [0,1] else np.nan
            z_prop = (p1-p2)/se if se and not np.isnan(se) else np.nan
            p_prop = float(stats.norm.sf(z_prop)) if not np.isnan(z_prop) else np.nan
            rows.append({
                "dataset": dataset, "bnf_tail": label, "bnf_threshold": thr, "high_events": n1, "rest_events": n2,
                "mean_trace_high": high[trace].mean(), "mean_trace_rest": rest[trace].mean(),
                "median_trace_high": high[trace].median(), "median_trace_rest": rest[trace].median(),
                "mean_diff": high[trace].mean()-rest[trace].mean(),
                "mean_diff_ci95_low": ci[0], "mean_diff_ci95_median": ci[1], "mean_diff_ci95_high": ci[2],
                "welch_z_proxy_t": z, "welch_p_one_sided": p, "welch_gaussian_z": float(stats.norm.isf(p)) if p > 0 else np.inf,
                "fraction_high_above_trace_q90": p1, "fraction_rest_above_trace_q90": p2,
                "trace_q90_enrichment_ratio": p1/p2 if p2 else np.inf,
                "trace_q90_prop_z": z_prop, "trace_q90_prop_p": p_prop,
            })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "real_high_bnf_trace_alignment_summary.csv", index=False)
    out.to_csv(TABLES / "real_trace_alignment_significance_tests.csv", index=False)
    report = ["# Real High-BNF Trace Alignment Test Report", "", f"Date: {DATE}", "", out.to_markdown(index=False), "", "Positive values mean real high-B_NF events have stronger SMS-like trace projection than ordinary real events in the same dataset."]
    (REPORTS / "REAL_HIGH_BNF_TRACE_ALIGNMENT_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
