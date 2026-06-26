from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
DATE = "2026-06-09"
WEIGHTS = {
    "B_P_displacement_proxy": 0.3566,
    "B_P_reconstruction": 0.2112,
    "B_P_multiplicity": 0.2019,
    "B_P_btag_structure": 0.0926,
    "B_P_visible_energy": 0.0728,
    "B_P_missing": 0.0595,
    "B_P_compression": 0.0055,
}


def load() -> pd.DataFrame:
    return pd.concat([pd.read_csv(SUSY), pd.read_csv(SM)], ignore_index=True)


def derive_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["score_missing_visible"] = df[["B_P_missing", "B_P_visible_energy"]].mean(axis=1)
    df["score_missing_visible_multiplicity"] = df[["B_P_missing", "B_P_visible_energy", "B_P_multiplicity"]].mean(axis=1)
    for excluded in ["B_P_missing", "B_P_visible_energy", "B_P_multiplicity"]:
        cols = [c for c in WEIGHTS if c != excluded and c in df and df[c].notna().any()]
        score = pd.Series(0.0, index=df.index)
        for c in cols:
            score += WEIGHTS[c] * df[c].fillna(0)
        df[f"B_NF_excluding_{excluded.replace('B_P_', '')}"] = score
    return df


def logistic_auc(pair: pd.DataFrame, features: list[str]) -> float:
    valid = pair[features].notna().all(axis=1)
    if valid.sum() < 20:
        return np.nan
    x = pair.loc[valid, features].to_numpy()
    y = pair.loc[valid, "classification"].eq("signal").astype(int).to_numpy()
    if len(np.unique(y)) < 2:
        return np.nan
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(x, y)
    prob = model.predict_proba(x)[:, 1]
    return float(roc_auc_score(y, prob))


def one_feature_auc(pair: pd.DataFrame, feature: str) -> float:
    valid = pair[feature].notna()
    if valid.sum() < 20:
        return np.nan
    y = pair.loc[valid, "classification"].eq("signal").astype(int)
    if y.nunique() < 2:
        return np.nan
    return float(roc_auc_score(y, pair.loc[valid, feature]))


def main() -> None:
    df = derive_scores(load())
    q95 = float(pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv").query("threshold == 'q95'")["value"].iloc[0])
    features = {
        "B_NF_fitted": "B_NF_fitted_frozen_raw",
        "P_missing_only": "B_P_missing",
        "P_visible_energy_only": "B_P_visible_energy",
        "P_multiplicity_only": "B_P_multiplicity",
        "P_missing_plus_visible": "score_missing_visible",
        "P_missing_plus_visible_plus_multiplicity": "score_missing_visible_multiplicity",
        "B_NF_excluding_missing": "B_NF_excluding_missing",
        "B_NF_excluding_visible_energy": "B_NF_excluding_visible_energy",
        "B_NF_excluding_multiplicity": "B_NF_excluding_multiplicity",
    }
    rows = []
    sms = df[df["sample_id"].eq("sms_t5wg_mg1500_mlsp1_signal")]
    for background_id, b in df[df["classification"].eq("SM_background")].groupby("sample_id"):
        pair = pd.concat([sms, b], ignore_index=True)
        for label, col in features.items():
            rows.append({
                "comparison": f"SMS-T5Wg vs {background_id}",
                "model_or_score": label,
                "feature_column": col,
                "auc": one_feature_auc(pair, col),
                "signal_q95_real_tail_fraction": (sms[col] > q95).mean() if col == "B_NF_fitted_frozen_raw" else np.nan,
                "background_q95_real_tail_fraction": (b[col] > q95).mean() if col == "B_NF_fitted_frozen_raw" else np.nan,
            })
        rows.append({
            "comparison": f"SMS-T5Wg vs {background_id}",
            "model_or_score": "logistic_missing_visible_multiplicity",
            "feature_column": "B_P_missing;B_P_visible_energy;B_P_multiplicity",
            "auc": logistic_auc(pair, ["B_P_missing", "B_P_visible_energy", "B_P_multiplicity"]),
            "signal_q95_real_tail_fraction": np.nan,
            "background_q95_real_tail_fraction": np.nan,
        })
        available_component_cols = [c for c in WEIGHTS if c in pair and pair[c].notna().all()]
        rows.append({
            "comparison": f"SMS-T5Wg vs {background_id}",
            "model_or_score": "logistic_available_components",
            "feature_column": ";".join(available_component_cols),
            "auc": logistic_auc(pair, available_component_cols),
            "signal_q95_real_tail_fraction": np.nan,
            "background_q95_real_tail_fraction": np.nan,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "bnf_vs_met_ht_incremental_tests.csv", index=False)
    best = out.sort_values("auc", ascending=False).groupby("comparison").head(5)
    interp = "The current separation is dominated by missing-energy, visible-energy and multiplicity components if those component AUCs match or exceed B_NF."
    report = ["# B_NF Versus MET/HT Incremental Test Report", "", f"Date: {DATE}", "", "## Results", "", out.to_markdown(index=False), "", "## Best Per Comparison", "", best.to_markdown(index=False), "", "## Interpretation", "", interp]
    (REPORTS / "BNF_VS_MET_HT_INCREMENTAL_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
