from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_overnight_followon_stability"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

PARAM_TABLE = ROOT / "outputs_overnight_parameter_insight_scan" / "tables" / "03_validation_stability_summary.csv"

SPEC = importlib.util.spec_from_file_location("stage", ROOT / "scripts/198_trigger_stage_boundary_model.py")
stage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stage)

COMPONENTS = stage.COMPONENTS
TARGET_PAIR = pd.DataFrame([{"MET_stage": "0jet", "HTMHT_stage": "1to2jets"}])

BASELINE = {
    "candidate": "local_refine_00287_baseline",
    "observer_projection": 0.3137254901960784,
    "physical_projection": 0.3137254901960784,
    "algebraic_projection": 0.0,
    "ordinary_qcd_axis": -0.27450980392156865,
    "leptonic_control_axis": -0.09803921568627451,
}


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)


def wait_for_parameter_scan() -> pd.DataFrame:
    ensure_dirs()
    while True:
        if PARAM_TABLE.exists():
            try:
                table = pd.read_csv(PARAM_TABLE)
                if not table.empty and "validation_mean_signal_Z" in table:
                    print(f"[wait] parameter scan table ready: {PARAM_TABLE}", flush=True)
                    return table
            except Exception as exc:
                print(f"[wait] table exists but is not ready: {exc}", flush=True)
        print("[wait] parameter scan not finished yet; sleeping 5 min", flush=True)
        time.sleep(300)


def weights_from_row(row: pd.Series) -> dict[str, float]:
    return {c: float(row.get(c, 0.0)) for c in COMPONENTS}


def choose_candidates(param: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not param.empty:
        top = param.sort_values(["validation_pass_folds", "selection_score", "validation_mean_signal_Z"], ascending=False).head(8)
        rows.append(top)
    base = pd.DataFrame([BASELINE])
    out = pd.concat(rows + [base], ignore_index=True).drop_duplicates("candidate", keep="first")
    out.to_csv(TABLES / "00_followon_candidate_set.csv", index=False)
    return out


def evaluate_one(df: pd.DataFrame, weights: dict[str, float], candidate: str, split_col: str, split: str) -> pd.DataFrame:
    tmp = df.copy()
    tmp["split"] = tmp[split_col]
    tmp["score"] = stage.score(tmp, weights)
    table = stage.stage_tail_table(tmp, "score", split, candidate)
    return stage.evaluate_stage_pairs(table, candidate, split).merge(TARGET_PAIR, on=["MET_stage", "HTMHT_stage"], how="inner")


def stability_splits(df: pd.DataFrame, candidates: pd.DataFrame, n_splits: int = 24) -> pd.DataFrame:
    key = pd.util.hash_pandas_object(df[["run", "lumi", "event", "primary_dataset"]].astype(str), index=False).to_numpy()
    rows = []
    for i in range(n_splits):
        split_col = f"followon_split_{i}"
        df[split_col] = np.where((key + 7919 * i) % 5 == 0, "validation", "development")
        for _, cand in candidates.iterrows():
            candidate = str(cand["candidate"])
            weights = weights_from_row(cand)
            res = evaluate_one(df, weights, candidate, split_col, "validation")
            if not res.empty:
                row = res.iloc[0].to_dict()
                row["repeat_split"] = i
                rows.append(row)
        del df[split_col]
        if (i + 1) % 4 == 0:
            print(f"[stability] completed {i + 1}/{n_splits} repeated splits", flush=True)
            pd.DataFrame(rows).to_csv(TABLES / "01_repeated_split_stability_running.csv", index=False)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "01_repeated_split_stability.csv", index=False)
    return out


def summarize_stability(stability: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    if stability.empty:
        return pd.DataFrame()
    summary = (
        stability.groupby("candidate", as_index=False)
        .agg(
            repeats=("repeat_split", "count"),
            mean_signal_Z=("signal_stouffer_Z", "mean"),
            min_signal_Z=("min_signal_Z", "min"),
            median_signal_Z=("signal_stouffer_Z", "median"),
            mean_max_control_absZ=("max_control_absZ_all_stages", "mean"),
            max_control_absZ=("max_control_absZ_all_stages", "max"),
            pass_rate=("passes_stage_screen", "mean"),
            pass_count=("passes_stage_screen", "sum"),
        )
        .merge(candidates[["candidate", *COMPONENTS]], on="candidate", how="left")
    )
    summary = summary.sort_values(["pass_count", "mean_signal_Z", "max_control_absZ"], ascending=[False, False, True])
    summary.to_csv(TABLES / "02_repeated_split_stability_summary.csv", index=False)
    return summary


def renormalize(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(v) for v in weights.values())
    return {k: (v / scale if scale else 0.0) for k, v in weights.items()}


def component_ablation(df: pd.DataFrame, best: pd.Series) -> pd.DataFrame:
    key = pd.util.hash_pandas_object(df[["run", "lumi", "event", "primary_dataset"]].astype(str), index=False).to_numpy()
    df["ablation_split"] = np.where(key % 5 == 0, "validation", "development")
    base_weights = weights_from_row(best)
    rows = []
    variants = [("full", base_weights)]
    for col in COMPONENTS:
        w = dict(base_weights)
        w[col] = 0.0
        variants.append((f"drop_{col}", renormalize(w)))
    for name, weights in variants:
        res = evaluate_one(df, weights, name, "ablation_split", "validation")
        if not res.empty:
            row = res.iloc[0].to_dict()
            row["variant"] = name
            rows.append(row)
    del df["ablation_split"]
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "03_component_ablation.csv", index=False)
    return out


def main() -> None:
    ensure_dirs()
    print("[start] overnight follow-on stability queue", flush=True)
    param = wait_for_parameter_scan()
    candidates = choose_candidates(param)
    print(f"[load] selected {len(candidates)} candidates for deeper stability", flush=True)
    df = stage.load_fresh()
    print(f"[load] loaded {len(df)} already-extracted events", flush=True)
    stability = stability_splits(df, candidates)
    summary = summarize_stability(stability, candidates)
    best = summary.iloc[0] if not summary.empty else pd.Series(BASELINE)
    ablation = component_ablation(df, best)

    summary_text = summary.head(20).to_markdown(index=False) if not summary.empty else "No stability summary produced."
    ablation_text = ablation.to_markdown(index=False) if not ablation.empty else "No ablation table produced."
    report = f"""# Overnight Follow-On Stability Checks

## Purpose

This job waits for the broad overnight parameter scan, then performs deeper robustness checks on the best candidates and the current `local_refine_00287` baseline.

It does not use the new downloaded ROOT files; it uses the already-extracted 404k Run2016H MHT-aware events so the machine keeps doing useful work while the large validation download runs separately.

## Repeated Split Stability

{summary_text}

## Component Ablation

{ablation_text}

## Interpretation

High pass-rate candidates are the parameter regions worth freezing for external validation. If the baseline remains near the top, then the best current insight is that the previous `local_refine_00287` boundary is not a fluke of one split. If another candidate is clearly stronger, it should still be treated as exploratory until validated on the new downloaded MiniAOD samples.
"""
    (REPORTS / "01_OVERNIGHT_FOLLOWON_STABILITY_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Overnight Follow-On Stability

{summary.head(10).to_markdown(index=False) if not summary.empty else "No stability summary produced."}
"""
    (REPORTS / "02_SHORT_UPDATE_FOLLOWON_STABILITY.md").write_text(short, encoding="utf-8")
    print("OVERNIGHT FOLLOW-ON STABILITY COMPLETE", flush=True)
    print(summary.head(10).to_string(index=False) if not summary.empty else "No summary.", flush=True)
    print("Outputs:", OUT, flush=True)


if __name__ == "__main__":
    main()
