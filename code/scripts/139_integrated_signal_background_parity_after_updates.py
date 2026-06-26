from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
from scipy import optimize, stats

from susy_signal_common import DATE, REPORTS, ROOT, TABLES


FILES = [
    ROOT / "data" / "processed" / "fuller_component_susy_signals" / "accessible_susy_miniaodsim_events_with_BNF.csv",
    ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_events_with_BNF.csv",
    ROOT / "data" / "processed" / "expanded_sm_after_signal_parity" / "expanded_sm_backgrounds_with_BNF.csv",
]


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


def fdr_bh(pvals: pd.Series) -> pd.Series:
    p = pvals.fillna(1.0).to_numpy(float)
    order = np.argsort(p)
    q = np.empty_like(p)
    prev = 1.0
    n = len(p)
    for rank, idx in enumerate(order[::-1], start=1):
        i = n - rank + 1
        val = min(prev, p[idx] * n / i)
        q[idx] = val
        prev = val
    return pd.Series(q, index=pvals.index)


def main() -> None:
    frames = [pd.read_csv(p, low_memory=False) for p in FILES if p.exists()]
    df = pd.concat(frames, ignore_index=True, sort=False)
    thresholds = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    tails = []
    for (sample, process, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        for t in thresholds.itertuples(index=False):
            k = int((g["B_NF_fitted_frozen_raw"] > t.value).sum())
            tails.append({
                "sample_id": sample, "process_label": process, "classification": cls,
                "threshold": t.threshold, "threshold_value": t.value, "n_total": len(g),
                "n_above": k, "tail_fraction": k / len(g), "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
                "component_mode": ";".join(sorted(g.get("component_mode", pd.Series(["full-component"])).dropna().astype(str).unique())),
            })
    tails = pd.DataFrame(tails)
    tails.to_csv(TABLES / "integrated_signal_background_tail_fractions_after_updates.csv", index=False)
    rows = []
    for _, s in tails[tails["classification"].eq("signal")].iterrows():
        for _, b in tails[(tails["classification"].eq("SM_background")) & (tails["threshold"].eq(s["threshold"]))].iterrows():
            k1, n1, k2, n2 = int(s.n_above), int(s.n_total), int(b.n_above), int(b.n_total)
            z, p = ztest(k1, n1, k2, n2)
            odds, fisher = stats.fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")
            rows.append({
                "threshold": s.threshold, "signal_sample": s.sample_id, "signal_process": s.process_label,
                "background_sample": b.sample_id, "background_process": b.process_label,
                "n_signal": n1, "signal_count": k1, "signal_tail_fraction": s.tail_fraction,
                "n_background": n2, "background_count": k2, "background_tail_fraction": b.tail_fraction,
                "risk_difference": s.tail_fraction - b.tail_fraction,
                "risk_ratio": s.tail_fraction / b.tail_fraction if b.tail_fraction else np.inf,
                "odds_ratio": odds, "z_one_sided": z, "p_one_sided": p, "fisher_exact_p_greater": fisher,
            })
    tests = pd.DataFrame(rows)
    tests.to_csv(TABLES / "integrated_signal_background_sigma_after_updates.csv", index=False)
    corrected = tests.copy()
    m = len(corrected) if len(corrected) else 1
    corrected["bonferroni_family_size"] = m
    corrected["bonferroni_z"] = corrected["z_one_sided"].apply(lambda x: corrected_z(x, m))
    corrected["remains_5sigma_after_bonferroni"] = corrected["bonferroni_z"] >= 5
    corrected["fdr_bh_q"] = fdr_bh(corrected["p_one_sided"])
    corrected["fdr_significant_0p05"] = corrected["fdr_bh_q"] < 0.05
    corrected.to_csv(TABLES / "integrated_signal_background_corrected_after_updates.csv", index=False)
    q95 = corrected[corrected["threshold"].eq("q95")].sort_values("risk_difference", ascending=False)
    report = [
        "# Integrated Signal/Background Parity After Updates Report",
        "",
        f"Date: {DATE}",
        "",
        "Primary comparisons use full-component MiniAODSIM-derived samples only. Newly added SM controls include provenance-caveated diboson-query matches where noted in the SM expansion report.",
        "",
        "## q95 Comparisons",
        "",
        q95.to_markdown(index=False),
        "",
        "## All Corrected Tests",
        "",
        corrected.to_markdown(index=False),
    ]
    (REPORTS / "INTEGRATED_SIGNAL_BACKGROUND_PARITY_AFTER_UPDATES_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(q95.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
