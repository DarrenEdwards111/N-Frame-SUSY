from __future__ import annotations

"""Record-level held-out test of N-Frame predictive incrementality.

Unlike the earlier event-randomised benchmark test, no source record is allowed
to contribute events to both model fitting and evaluation.
"""

from importlib.machinery import SourceFileLoader
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_grouped_record_holdout_predictive_test"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
LEGACY = SourceFileLoader("trace_legacy", str(ROOT / "scripts" / "162_trace_predictive_significance.py")).load_module()

SEED = 278
MAX_EVENTS_PER_RECORD = 3_000
STANDARD = LEGACY.STANDARD
FEATURE_SETS = {
    "standard_CMS_like": STANDARD,
    "standard_plus_trace_axis": STANDARD + ["displacement_reconstruction_axis"],
    "standard_plus_BNF": STANDARD + ["B_NF_z"],
    "standard_plus_full_NFrame_axes": STANDARD
    + ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "qcd_like_axis"],
}


def sample_records(frame: pd.DataFrame, target: int) -> pd.DataFrame:
    parts = []
    for record_id, group in frame.groupby("record_id", sort=True):
        n = min(len(group), MAX_EVENTS_PER_RECORD)
        parts.append(group.sample(n=n, random_state=SEED + int(float(record_id))))
    out = pd.concat(parts, ignore_index=True)
    out["target"] = target
    return out


def assign_folds(signal: pd.DataFrame, sm: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, dict[str, list[str]]]]:
    signal_ids = sorted(signal["record_id"].astype(str).unique())
    sm_ids = sorted(sm["record_id"].astype(str).unique())
    n_folds = len(signal_ids)
    mapping: dict[int, dict[str, list[str]]] = {i: {"signal": [rid], "sm": []} for i, rid in enumerate(signal_ids)}
    for i, rid in enumerate(sm_ids):
        mapping[i % n_folds]["sm"].append(rid)

    signal = signal.copy()
    sm = sm.copy()
    signal["fold"] = signal["record_id"].astype(str).map({rid: i for i, rid in enumerate(signal_ids)})
    sm_fold = {rid: i % n_folds for i, rid in enumerate(sm_ids)}
    sm["fold"] = sm["record_id"].astype(str).map(sm_fold)
    return pd.concat([signal, sm], ignore_index=True), mapping


def exact_sign_flip_p(deltas: np.ndarray) -> tuple[float, float]:
    """Exact one-sided cluster-level sign-flip p for the mean AUC increment."""
    observed = float(np.mean(deltas))
    null = []
    for signs in product([-1.0, 1.0], repeat=len(deltas)):
        null.append(float(np.mean(np.asarray(signs) * deltas)))
    null = np.asarray(null)
    p = float((np.sum(null >= observed) + 1) / (len(null) + 1))
    return p, float(norm.isf(p))


def main() -> None:
    for path in [TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)

    sm = LEGACY.load_sm()
    signal = LEGACY.load_signal()
    needed = sorted(set(sum(FEATURE_SETS.values(), []) + ["record_id"]))
    signal = signal[signal["record_id"].astype(str).str.fullmatch(r"\d+(?:\.0+)?", na=False)].copy()
    sm = sm[sm["record_id"].astype(str).str.fullmatch(r"\d+(?:\.0+)?", na=False)].copy()
    signal = sample_records(signal, 1)
    sm = sample_records(sm, 0)
    data, fold_map = assign_folds(signal, sm)

    predictions = []
    metrics = []
    for fold in sorted(data["fold"].unique()):
        train = data[data["fold"].ne(fold)].copy()
        test = data[data["fold"].eq(fold)].copy()
        if train["target"].nunique() != 2 or test["target"].nunique() != 2:
            raise RuntimeError(f"Fold {fold} lacks both classes")
        pred = test[["target", "record_id", "process_label", "fold"]].copy()
        for name, cols in FEATURE_SETS.items():
            model = LEGACY.make_pipeline_model()
            model.fit(train[cols], train["target"].astype(int))
            score = model.predict_proba(test[cols])[:, 1]
            pred[name] = score
            metrics.append(
                {
                    "fold": int(fold),
                    "model": name,
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    "heldout_signal_records": ";".join(fold_map[int(fold)]["signal"]),
                    "heldout_sm_records": ";".join(fold_map[int(fold)]["sm"]),
                    "auc": float(roc_auc_score(test["target"], score)),
                }
            )
        predictions.append(pred)

    pred = pd.concat(predictions, ignore_index=True)
    metric = pd.DataFrame(metrics)
    base = metric[metric["model"].eq("standard_CMS_like")][["fold", "auc"]].rename(columns={"auc": "base_auc"})
    comparisons = []
    for name in FEATURE_SETS:
        if name == "standard_CMS_like":
            continue
        rows = metric[metric["model"].eq(name)][["fold", "auc"]].merge(base, on="fold")
        rows["delta_auc"] = rows["auc"] - rows["base_auc"]
        p, z = exact_sign_flip_p(rows["delta_auc"].to_numpy(float))
        comparisons.append(
            {
                "tested_model": name,
                "mean_delta_auc": float(rows["delta_auc"].mean()),
                "median_delta_auc": float(rows["delta_auc"].median()),
                "folds_positive": int((rows["delta_auc"] > 0).sum()),
                "fold_count": int(len(rows)),
                "cluster_sign_flip_p_one_sided": p,
                "cluster_sign_flip_Z_one_sided": z,
            }
        )
        rows.insert(1, "tested_model", name)
        rows.to_csv(TABLES / f"03_fold_auc_{name}.csv", index=False)

    audit = (
        data.groupby(["target", "fold", "record_id", "process_label"], as_index=False)
        .size()
        .rename(columns={"size": "sampled_events"})
    )
    audit.to_csv(TABLES / "01_record_holdout_fold_manifest.csv", index=False)
    metric.to_csv(TABLES / "02_grouped_holdout_auc_by_fold.csv", index=False)
    pd.DataFrame(comparisons).to_csv(TABLES / "04_grouped_holdout_incrementality_summary.csv", index=False)
    pred.to_csv(TABLES / "05_grouped_holdout_predictions.csv", index=False)

    summary = pd.DataFrame(comparisons)
    report = f"""# Grouped Record-Holdout Predictive Test

## Purpose

This replaces the earlier event-randomised benchmark split. Every fold holds out
one complete signal benchmark record and a disjoint set of SM records. No
source record appears in both model fitting and evaluation.

## Record-fold manifest

{audit.to_markdown(index=False)}

## Fold AUCs

{metric.to_markdown(index=False, floatfmt='.6f')}

## Incrementality summary

{summary.to_markdown(index=False, floatfmt='.6f')}

## Interpretation rule

This is a benchmark-method generalisation test, not a collision-data anomaly
test and not a SUSY discovery. The cluster sign-flip statistic is deliberately
conservative because there are only five independent signal benchmark records.
Only a consistent positive increment across held-out records supports a claim
that the N-Frame features generalise beyond standard CMS-like variables.
"""
    (REPORTS / "01_GROUPED_RECORD_HOLDOUT_PREDICTIVE_TEST.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(REPORTS / "01_GROUPED_RECORD_HOLDOUT_PREDICTIVE_TEST.md")


if __name__ == "__main__":
    main()
