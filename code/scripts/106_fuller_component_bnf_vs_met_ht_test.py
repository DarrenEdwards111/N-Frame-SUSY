from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from fuller_component_common import DATE, OUT, REPORTS, TABLES


def auc(pair: pd.DataFrame, col: str) -> float:
    valid = pair[col].notna()
    if valid.sum() < 20:
        return np.nan
    y = pair.loc[valid, "classification"].eq("signal").astype(int)
    if y.nunique() < 2:
        return np.nan
    return float(roc_auc_score(y, pair.loc[valid, col]))


def main() -> None:
    fuller = pd.read_csv(OUT / "fuller_component_benchmark_events_with_BNF.csv", low_memory=False)
    prior = pd.read_csv(OUT.parents[0] / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv", low_memory=False)
    df = pd.concat([prior[prior["classification"].eq("signal")], fuller], ignore_index=True, sort=False)
    df["missing_plus_visible"] = df[["B_P_missing", "B_P_visible_energy"]].mean(axis=1)
    df["missing_visible_multiplicity"] = df[["B_P_missing", "B_P_visible_energy", "B_P_multiplicity"]].mean(axis=1)
    df["displacement_reconstruction"] = df[["B_P_displacement_proxy", "B_P_reconstruction"]].mean(axis=1)
    df["bnf_without_missing"] = df["B_NF_fitted_frozen_raw"] - 0.0595 * df["B_P_missing"].fillna(0)
    df["bnf_without_disp_reco"] = df["B_NF_fitted_frozen_raw"] - 0.3566 * df["B_P_displacement_proxy"].fillna(0) - 0.2112 * df["B_P_reconstruction"].fillna(0)
    features = {
        "B_NF_fitted": "B_NF_fitted_frozen_raw",
        "P_missing_only": "B_P_missing",
        "P_visible_energy_only": "B_P_visible_energy",
        "P_multiplicity_only": "B_P_multiplicity",
        "P_missing_plus_visible": "missing_plus_visible",
        "P_missing_plus_visible_plus_multiplicity": "missing_visible_multiplicity",
        "P_displacement_plus_reconstruction": "displacement_reconstruction",
        "B_NF_without_missing": "bnf_without_missing",
        "B_NF_without_displacement_reconstruction": "bnf_without_disp_reco",
    }
    rows = []
    for sid, signal in df[df["classification"].eq("signal")].groupby("sample_id"):
        for bid, background in df[df["classification"].eq("SM_background")].groupby("sample_id"):
            pair = pd.concat([signal, background], ignore_index=True, sort=False)
            for label, col in features.items():
                rows.append({
                    "signal_sample": sid,
                    "background_sample": bid,
                    "score": label,
                    "auc": auc(pair, col),
                    "signal_mean": signal[col].mean(),
                    "background_mean": background[col].mean(),
                    "mean_difference": signal[col].mean() - background[col].mean(),
                })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "fuller_component_bnf_vs_met_ht_incremental_tests.csv", index=False)
    med = out.groupby("score", as_index=False)["auc"].median().sort_values("auc", ascending=False)
    (REPORTS / "FULLER_COMPONENT_BNF_VS_MET_HT_INCREMENTAL_TEST_REPORT.md").write_text(
        "# Fuller Component B_NF Versus MET/HT Incremental Test Report\n\n"
        f"Date: {DATE}\n\n"
        "This checks whether the fitted N-Frame score adds separation beyond simpler MET/visible-energy/multiplicity components.\n\n"
        + out.to_markdown(index=False)
        + "\n\n## Median AUC By Score\n\n"
        + med.to_markdown(index=False),
        encoding="utf-8",
    )
    print(med.to_string(index=False))


if __name__ == "__main__":
    main()
