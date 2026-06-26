from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
EVENTS = ROOT / "data" / "processed" / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv"
DATE = "2026-06-09"

FEATURES = {
    "B_NF_fitted": "B_NF_fitted_frozen_raw",
    "P_missing_only": "B_P_missing",
    "P_visible_energy_only": "B_P_visible_energy",
    "P_multiplicity_only": "B_P_multiplicity",
}


def auc(pair, col):
    valid = pair[col].notna()
    if valid.sum() < 20:
        return np.nan
    y = pair.loc[valid, "classification"].eq("signal").astype(int)
    if y.nunique() < 2:
        return np.nan
    return float(roc_auc_score(y, pair.loc[valid, col]))


def main():
    df = pd.read_csv(EVENTS)
    df["missing_plus_visible"] = df[["B_P_missing", "B_P_visible_energy"]].mean(axis=1)
    df["missing_visible_multiplicity"] = df[["B_P_missing", "B_P_visible_energy", "B_P_multiplicity"]].mean(axis=1)
    FEATURES["P_missing_plus_visible"] = "missing_plus_visible"
    FEATURES["P_missing_plus_visible_plus_multiplicity"] = "missing_visible_multiplicity"
    q95 = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv").query("threshold == 'q95'")["value"].iloc[0]
    rows = []
    signals = df[df["classification"].eq("signal")]
    backgrounds = df[df["classification"].eq("SM_background")]
    for sid, s in signals.groupby("sample_id"):
        for bid, b in backgrounds.groupby("sample_id"):
            pair = pd.concat([s, b], ignore_index=True, sort=False)
            for label, col in FEATURES.items():
                rows.append({"signal_sample": sid, "background_sample": bid, "model_or_score": label, "auc": auc(pair, col), "signal_q95_tail_fraction": (s[col] > q95).mean() if col == "B_NF_fitted_frozen_raw" else np.nan, "background_q95_tail_fraction": (b[col] > q95).mean() if col == "B_NF_fitted_frozen_raw" else np.nan})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "expanded_bnf_vs_met_ht_incremental_tests.csv", index=False)
    report = ["# Expanded B_NF Versus MET/HT Incremental Test Report", "", f"Date: {DATE}", "", out.to_markdown(index=False), "", "If component-only scores exceed B_NF AUC, the benchmark separation is mainly missing-energy/visible-energy/multiplicity rather than a unique N-Frame composite effect."]
    (REPORTS / "EXPANDED_BNF_VS_MET_HT_INCREMENTAL_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.groupby("model_or_score")["auc"].median().reset_index().to_string(index=False))


if __name__ == "__main__":
    main()
