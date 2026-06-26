from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import optimize, stats


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"


def finite_p(row):
    p = row["p_two_proportion_one_sided"]
    if pd.notna(p) and p > 0:
        return p
    return 0.0 if pd.notna(row["z_two_proportion_one_sided"]) else np.nan


def corrected_z_from_row(row, family_size: int) -> float:
    z = row["z_two_proportion_one_sided"]
    if pd.isna(z):
        return np.nan
    logp = stats.norm.logsf(z) + np.log(family_size)
    if logp >= 0:
        return -np.inf
    if logp > np.log(np.finfo(float).tiny):
        return float(stats.norm.isf(np.exp(logp)))
    return float(optimize.brentq(lambda x: stats.norm.logsf(x) - logp, 0, 200))


def bh(pvals: np.ndarray) -> np.ndarray:
    order = np.argsort(pvals)
    ranked = pvals[order]
    m = len(pvals)
    adjusted = np.empty(m)
    prev = 1.0
    for i in range(m - 1, -1, -1):
        val = min(prev, ranked[i] * m / (i + 1))
        adjusted[i] = val
        prev = val
    out = np.empty(m)
    out[order] = adjusted
    return out


def main() -> None:
    tests = pd.read_csv(TABLES / "two_proportion_sigma_tests.csv")
    target = tests[tests["signal_sample"].eq("sms_t5wg_mg1500_mlsp1_signal")].copy()
    target["raw_p_for_correction"] = target.apply(finite_p, axis=1)
    m = len(target)
    target["bonferroni_family_size"] = m
    target["bonferroni_p"] = np.minimum(1, target["raw_p_for_correction"] * m)
    target["bonferroni_z"] = target.apply(lambda r: corrected_z_from_row(r, m), axis=1)
    valid = target["raw_p_for_correction"].fillna(1).to_numpy()
    target["bh_fdr_p"] = bh(valid)
    target["bh_fdr_z"] = target["bh_fdr_p"].apply(lambda p: float(stats.norm.isf(p)) if pd.notna(p) and p > 0 else (np.inf if p == 0 else np.nan))
    target["remains_5sigma_after_bonferroni"] = target["bonferroni_z"].apply(lambda z: bool(pd.notna(z) and z >= 5))
    target.to_csv(TABLES / "look_elsewhere_corrected_sigma_tests.csv", index=False)
    strongest = target.sort_values("bonferroni_z", ascending=False).head(1)
    report = ["# Look-Elsewhere Correction Report", "", f"Date: {DATE}", "", "Correction family: SMS-T5Wg comparisons across q90/q95/q99/q999 and TTJets/QCD/pooled SM backgrounds.", "", "## Corrected Tests", "", target.to_markdown(index=False), "", "## Strongest Corrected Result", "", strongest.to_markdown(index=False)]
    (REPORTS / "LOOK_ELSEWHERE_CORRECTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(target.to_string(index=False))


if __name__ == "__main__":
    main()
