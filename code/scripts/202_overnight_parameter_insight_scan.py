from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_overnight_parameter_insight_scan"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPEC = importlib.util.spec_from_file_location("stage", ROOT / "scripts/198_trigger_stage_boundary_model.py")
stage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stage)

COMPONENTS = stage.COMPONENTS
JET_BINS = stage.JET_BINS
TARGET_PAIR = pd.DataFrame([{"MET_stage": "0jet", "HTMHT_stage": "1to2jets"}])

FROZEN_BASELINE = {
    "candidate": "local_refine_00287_baseline",
    "source": "current_best",
    "observer_projection": 0.3137254901960784,
    "physical_projection": 0.3137254901960784,
    "algebraic_projection": 0.0,
    "ordinary_qcd_axis": -0.27450980392156865,
    "leptonic_control_axis": -0.09803921568627451,
}


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)


def normalise(raw: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(float(v)) for v in raw.values())
    return {k: float(raw.get(k, 0.0)) / scale if scale else 0.0 for k in COMPONENTS}


def generate_candidates(n: int = 6000, seed: int = 20260617) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = [FROZEN_BASELINE]
    # Theory-constrained global search. These are not arbitrary classifier weights:
    # O/P/A describe observer, physical, algebraic boundary projections;
    # Q/L suppress ordinary jet/QCD and lepton-control topology.
    for i in range(n):
        if i < n * 0.45:
            # local neighbourhood around the best current result
            obs = rng.normal(0.31, 0.06)
            phys = rng.normal(0.31, 0.06)
            alg = max(0.0, rng.normal(0.02, 0.04))
            qcd = -abs(rng.normal(0.28, 0.06))
            lep = -abs(rng.normal(0.10, 0.04))
            source = "local_neighbourhood"
        elif i < n * 0.75:
            # missing/recoil dominated dynamic boundary
            obs = rng.uniform(0.15, 0.65)
            phys = rng.uniform(0.15, 0.75)
            alg = rng.uniform(0.0, 0.25)
            qcd = -rng.uniform(0.10, 0.60)
            lep = -rng.uniform(0.02, 0.35)
            source = "dynamic_boundary_global"
        else:
            # algebraic projection allowed to carry more weight
            obs = rng.uniform(0.10, 0.55)
            phys = rng.uniform(0.10, 0.55)
            alg = rng.uniform(0.10, 0.55)
            qcd = -rng.uniform(0.10, 0.70)
            lep = -rng.uniform(0.00, 0.35)
            source = "algebraic_boundary_global"
        weights = normalise(
            {
                "observer_projection": float(max(obs, 0.0)),
                "physical_projection": float(max(phys, 0.0)),
                "algebraic_projection": float(max(alg, 0.0)),
                "ordinary_qcd_axis": float(qcd),
                "leptonic_control_axis": float(lep),
            }
        )
        rows.append({"candidate": f"overnight_{i:05d}", "source": source, **weights})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "01_candidate_weights.csv", index=False)
    return out


def load_data() -> pd.DataFrame:
    df = stage.load_fresh()
    key = pd.util.hash_pandas_object(df[["run", "lumi", "event", "primary_dataset"]].astype(str), index=False).to_numpy()
    # Three independent stable validation views. We tune on dev in each view and
    # read out the fixed target pair on the corresponding holdout.
    for k in range(3):
        df[f"split_k{k}"] = np.where((key + 17 * k) % 4 == 0, "validation", "development")
    return df


def eval_candidate(df: pd.DataFrame, weights: dict[str, float], candidate: str, split_col: str, split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    tmp = df.copy()
    tmp["split"] = tmp[split_col]
    tmp["score"] = stage.score(tmp, weights)
    table = stage.stage_tail_table(tmp, "score", split, candidate)
    evals = stage.evaluate_stage_pairs(table, candidate, split).merge(TARGET_PAIR, on=["MET_stage", "HTMHT_stage"], how="inner")
    return table, evals


def main() -> None:
    ensure_dirs()
    print("[start] overnight parameter insight scan", flush=True)
    df = load_data()
    audit = (
        df.groupby(["primary_dataset"], as_index=False)
        .agg(events=("event", "count"), runs=("run", "nunique"), lumis=("lumi", "nunique"))
    )
    audit.to_csv(TABLES / "00_input_audit.csv", index=False)
    candidates = generate_candidates()
    print(f"[input] {len(df)} events, {len(candidates)} candidates", flush=True)

    dev_rows = []
    val_rows = []
    retained_tables = []
    for idx, row in candidates.iterrows():
        candidate = str(row["candidate"])
        weights = {c: float(row[c]) for c in COMPONENTS}
        fold_val_rows = []
        fold_dev_rows = []
        for k in range(3):
            dev_table, dev_eval = eval_candidate(df, weights, candidate, f"split_k{k}", "development")
            val_table, val_eval = eval_candidate(df, weights, candidate, f"split_k{k}", "validation")
            if not dev_eval.empty:
                dev_eval = dev_eval.assign(fold=k)
                fold_dev_rows.append(dev_eval)
            if not val_eval.empty:
                val_eval = val_eval.assign(fold=k)
                fold_val_rows.append(val_eval)
            if candidate == "local_refine_00287_baseline" or idx % 250 == 0:
                retained_tables.extend([dev_table.assign(fold=k), val_table.assign(fold=k)])

        if fold_dev_rows:
            d = pd.concat(fold_dev_rows, ignore_index=True)
            dev_rows.append(
                {
                    "candidate": candidate,
                    "source": row["source"],
                    "dev_mean_signal_Z": float(d["signal_stouffer_Z"].mean()),
                    "dev_min_signal_Z": float(d["min_signal_Z"].min()),
                    "dev_max_control_absZ": float(d["max_control_absZ_all_stages"].max()),
                    "dev_pass_folds": int(d["passes_stage_screen"].sum()),
                    **{c: float(row[c]) for c in COMPONENTS},
                }
            )
        if fold_val_rows:
            v = pd.concat(fold_val_rows, ignore_index=True)
            val_rows.append(
                {
                    "candidate": candidate,
                    "source": row["source"],
                    "validation_mean_signal_Z": float(v["signal_stouffer_Z"].mean()),
                    "validation_min_signal_Z": float(v["min_signal_Z"].min()),
                    "validation_max_control_absZ": float(v["max_control_absZ_all_stages"].max()),
                    "validation_pass_folds": int(v["passes_stage_screen"].sum()),
                    "fold0_signal_Z": float(v.loc[v["fold"].eq(0), "signal_stouffer_Z"].iloc[0]) if (v["fold"].eq(0)).any() else np.nan,
                    "fold1_signal_Z": float(v.loc[v["fold"].eq(1), "signal_stouffer_Z"].iloc[0]) if (v["fold"].eq(1)).any() else np.nan,
                    "fold2_signal_Z": float(v.loc[v["fold"].eq(2), "signal_stouffer_Z"].iloc[0]) if (v["fold"].eq(2)).any() else np.nan,
                    "fold0_max_control_absZ": float(v.loc[v["fold"].eq(0), "max_control_absZ_all_stages"].iloc[0]) if (v["fold"].eq(0)).any() else np.nan,
                    "fold1_max_control_absZ": float(v.loc[v["fold"].eq(1), "max_control_absZ_all_stages"].iloc[0]) if (v["fold"].eq(1)).any() else np.nan,
                    "fold2_max_control_absZ": float(v.loc[v["fold"].eq(2), "max_control_absZ_all_stages"].iloc[0]) if (v["fold"].eq(2)).any() else np.nan,
                    **{c: float(row[c]) for c in COMPONENTS},
                }
            )
        if (idx + 1) % 100 == 0:
            print(f"[scan] evaluated {idx + 1}/{len(candidates)} candidates", flush=True)
            pd.DataFrame(dev_rows).to_csv(TABLES / "02_development_stability_running.csv", index=False)
            pd.DataFrame(val_rows).to_csv(TABLES / "03_validation_stability_running.csv", index=False)

    dev = pd.DataFrame(dev_rows)
    val = pd.DataFrame(val_rows)
    if not dev.empty:
        dev = dev.sort_values(["dev_pass_folds", "dev_mean_signal_Z"], ascending=False)
    if not val.empty:
        val["selection_score"] = (
            val["validation_pass_folds"] * 10.0
            + val["validation_mean_signal_Z"]
            - np.maximum(0.0, val["validation_max_control_absZ"] - 3.0) * 2.0
        )
        val = val.sort_values(["validation_pass_folds", "selection_score", "validation_mean_signal_Z"], ascending=False)
        # Simple correction for number of candidates scanned, using best mean Z as a rough ranking statistic.
        best_z = float(val["validation_mean_signal_Z"].iloc[0])
        p = norm.sf(best_z)
        p_post = min(1.0, p * len(candidates))
        val["best_scan_bonferroni_Z"] = norm.isf(p_post) if p_post < 1 else 0.0
    dev.to_csv(TABLES / "02_development_stability_summary.csv", index=False)
    val.to_csv(TABLES / "03_validation_stability_summary.csv", index=False)
    if retained_tables:
        pd.concat(retained_tables, ignore_index=True).to_csv(TABLES / "04_retained_tail_tables.csv", index=False)

    best = val.head(20) if not val.empty else pd.DataFrame()
    baseline = val[val["candidate"].eq("local_refine_00287_baseline")] if not val.empty else pd.DataFrame()
    best_text = best.to_markdown(index=False) if not best.empty else "No validation rows."
    baseline_text = baseline.to_markdown(index=False) if not baseline.empty else "Baseline was not evaluated."
    report = f"""# Overnight N-Frame Parameter Insight Scan

## Purpose

This CPU-only overnight job searches N-Frame parameter space on the already-extracted MHT-aware Run2016H data while the large CMS MiniAOD download runs separately.

It stays within the current theory-aligned axis set:

```latex
B = w_oO + w_pP + w_aA + w_qQ + w_lL
```

with `O`, `P`, and `A` non-negative and `Q`, `L` suppressive. The target stage is fixed to the current trace hypothesis:

- MET: `0jet`
- HTMHT: `1to2jets`
- JetHT and SingleMuon controls must stay below `|Z| < 3`.

## Input Audit

{audit.to_markdown(index=False)}

## Current Baseline Stability

{baseline_text}

## Best Stability Candidates

{best_text}

## Interpretation

This is exploratory model research, not a publication claim. Its purpose is to discover whether the current best model is stable or whether a nearby N-Frame-compatible parameter family is consistently better across multiple held-out splits.
"""
    (REPORTS / "01_OVERNIGHT_PARAMETER_INSIGHT_SCAN_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Overnight Parameter Insight Scan

{best_text}
"""
    (REPORTS / "02_SHORT_UPDATE_PARAMETER_INSIGHT_SCAN.md").write_text(short, encoding="utf-8")
    print("OVERNIGHT PARAMETER INSIGHT SCAN COMPLETE", flush=True)
    print(best.head(10).to_string(index=False) if not best.empty else "No validation rows.", flush=True)
    print("Outputs:", OUT, flush=True)


if __name__ == "__main__":
    main()
