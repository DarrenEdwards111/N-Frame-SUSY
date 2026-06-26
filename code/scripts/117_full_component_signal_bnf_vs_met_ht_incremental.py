from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from susy_signal_common import DATE, REPORTS, ROOT, TABLES


def auc(pair: pd.DataFrame, col: str) -> float:
    valid = pair[col].notna()
    if valid.sum() < 20:
        return np.nan
    y = pair.loc[valid, "classification"].eq("signal").astype(int)
    if y.nunique() < 2:
        return np.nan
    return float(roc_auc_score(y, pair.loc[valid, col]))


def main() -> None:
    sig = pd.read_csv(ROOT / "data" / "processed" / "fuller_component_susy_signals" / "accessible_susy_miniaodsim_events_with_BNF.csv", low_memory=False)
    bg = pd.read_csv(ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_events_with_BNF.csv", low_memory=False)
    df = pd.concat([sig, bg], ignore_index=True, sort=False)
    df["missing_plus_visible"] = df[["B_P_missing", "B_P_visible_energy"]].mean(axis=1)
    df["missing_visible_multiplicity"] = df[["B_P_missing", "B_P_visible_energy", "B_P_multiplicity"]].mean(axis=1)
    df["displacement_reconstruction"] = df[["B_P_displacement_proxy", "B_P_reconstruction"]].mean(axis=1)
    df["bnf_without_missing"] = df["B_NF_fitted_frozen_raw"] - 0.0595 * df["B_P_missing"].fillna(0)
    df["bnf_without_disp_reco"] = df["B_NF_fitted_frozen_raw"] - 0.3566 * df["B_P_displacement_proxy"].fillna(0) - 0.2112 * df["B_P_reconstruction"].fillna(0)
    sig = df[df["classification"].eq("signal")]
    bg = df[df["classification"].eq("SM_background")]
    features = {
        "B_NF_fitted": "B_NF_fitted_frozen_raw",
        "P_missing_only": "B_P_missing",
        "P_visible_energy_only": "B_P_visible_energy",
        "P_multiplicity_only": "B_P_multiplicity",
        "P_missing_plus_visible": "missing_plus_visible",
        "P_missing_plus_visible_plus_multiplicity": "missing_visible_multiplicity",
        "P_displacement_proxy_plus_reconstruction": "displacement_reconstruction",
        "B_NF_without_missing": "bnf_without_missing",
        "B_NF_without_displacement_reconstruction": "bnf_without_disp_reco",
    }
    q95 = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv").query("threshold == 'q95'")["value"].iloc[0]
    rows = []
    for sid, s in sig.groupby("sample_id"):
        for bid, b in bg.groupby("sample_id"):
            pair = pd.concat([s, b], ignore_index=True, sort=False)
            for label, col in features.items():
                rows.append({
                    "signal_sample": sid,
                    "background_sample": bid,
                    "score": label,
                    "auc": auc(pair, col),
                    "signal_mean": s[col].mean(),
                    "background_mean": b[col].mean(),
                    "mean_difference": s[col].mean() - b[col].mean(),
                    "signal_q95_enrichment": float((s["B_NF_fitted_frozen_raw"] > q95).mean()),
                    "background_q95_enrichment": float((b["B_NF_fitted_frozen_raw"] > q95).mean()),
                })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "full_component_signal_bnf_vs_met_ht_incremental.csv", index=False)
    med = out.groupby("score", as_index=False)["auc"].median().sort_values("auc", ascending=False)
    (REPORTS / "FULL_COMPONENT_SIGNAL_BNF_VS_MET_HT_INCREMENTAL_REPORT.md").write_text(
        "# Full Component Signal B_NF Versus MET/HT Incremental Report\n\n"
        f"Date: {DATE}\n\n"
        "This tests whether the full fitted B_NF adds beyond missing energy, visible recoil and multiplicity when both signal and background have full MiniAODSIM components.\n\n"
        + out.to_markdown(index=False)
        + "\n\n## Median AUC\n\n"
        + med.to_markdown(index=False),
        encoding="utf-8",
    )
    print(med.to_string(index=False))


if __name__ == "__main__":
    main()
