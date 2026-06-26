from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

from fuller_component_common import DATE, OUT, REPORTS, TABLES


ROOT = Path(__file__).resolve().parents[1]


def ztest(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float]:
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else np.nan
    z = (p1 - p2) / se if se and not np.isnan(se) else np.nan
    pval = float(stats.norm.sf(z)) if pd.notna(z) else np.nan
    log10p = float(stats.norm.logsf(z) / np.log(10)) if pd.notna(z) else np.nan
    return z, pval, log10p


def corrected_z(z: float, m: int) -> float:
    if pd.isna(z):
        return np.nan
    logp = stats.norm.logsf(z) + np.log(m)
    if logp >= 0:
        return -np.inf
    if logp > np.log(np.finfo(float).tiny):
        return float(stats.norm.isf(np.exp(logp)))
    return float(optimize.brentq(lambda x: stats.norm.logsf(x) - logp, 0, 200))


def main() -> None:
    fuller = pd.read_csv(OUT / "fuller_component_benchmark_events_with_BNF.csv", low_memory=False)
    prior = pd.read_csv(ROOT / "data" / "processed" / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv", low_memory=False)
    events = pd.concat([prior[prior["classification"].eq("signal")], fuller], ignore_index=True, sort=False)
    th = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    tail_rows = []
    for (sample, process, cls), g in events.groupby(["sample_id", "process_label", "classification"]):
        for t in th.itertuples(index=False):
            k = int((g["B_NF_fitted_frozen_raw"] > t.value).sum())
            tail_rows.append({
                "sample_id": sample,
                "process_label": process,
                "classification": cls,
                "threshold": t.threshold,
                "threshold_value": t.value,
                "n_total": len(g),
                "n_above": k,
                "tail_fraction": k / len(g),
                "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
            })
    tails = pd.DataFrame(tail_rows)
    tails.to_csv(TABLES / "fuller_component_tail_fractions.csv", index=False)
    rows = []
    sigs = tails[tails["classification"].eq("signal")]
    bgs = tails[tails["classification"].eq("SM_background")]
    for _, s in sigs.iterrows():
        for _, b in bgs[bgs["threshold"].eq(s["threshold"])].iterrows():
            z, p, log10p = ztest(int(s.n_above), int(s.n_total), int(b.n_above), int(b.n_total))
            rows.append({
                "threshold": s.threshold,
                "signal_sample": s.sample_id,
                "signal_process": s.process_label,
                "background_sample": b.sample_id,
                "background_process": b.process_label,
                "signal_count": int(s.n_above),
                "signal_total": int(s.n_total),
                "background_count": int(b.n_above),
                "background_total": int(b.n_total),
                "p_signal": s.tail_fraction,
                "p_background": b.tail_fraction,
                "risk_difference": s.tail_fraction - b.tail_fraction,
                "risk_ratio": s.tail_fraction / b.tail_fraction if b.tail_fraction else np.inf,
                "z_one_sided": z,
                "p_one_sided": p,
                "log10_p": log10p,
            })
    tests = pd.DataFrame(rows)
    m = len(tests) if len(tests) else 1
    tests["bonferroni_family_size"] = m
    tests["bonferroni_z"] = tests["z_one_sided"].apply(lambda x: corrected_z(x, m))
    tests["remains_5sigma_after_bonferroni"] = tests["bonferroni_z"] >= 5
    tests.to_csv(TABLES / "fuller_component_sigma_tests.csv", index=False)
    key = tests[tests["signal_sample"].astype(str).str.contains("t5wg", case=False, na=False) & tests["threshold"].isin(["q95", "q99"])]
    report = [
        "# Fuller Component Five Sigma Benchmark Test Report",
        "",
        f"Date: {DATE}",
        "",
        "Signals are benchmark simulations only. Backgrounds here are the selected fuller-component MiniAODSIM files. This is not a discovery test and not a SUSY classifier.",
        "",
        "## Tail Fractions",
        "",
        tails.to_markdown(index=False),
        "",
        "## Corrected Tests",
        "",
        tests.to_markdown(index=False),
        "",
        "## SMS-T5Wg Rows",
        "",
        key.to_markdown(index=False) if not key.empty else "No SMS-T5Wg rows were available.",
    ]
    (REPORTS / "FULLER_COMPONENT_FIVE_SIGMA_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(key.to_string(index=False) if not key.empty else tests.to_string(index=False))


if __name__ == "__main__":
    main()
