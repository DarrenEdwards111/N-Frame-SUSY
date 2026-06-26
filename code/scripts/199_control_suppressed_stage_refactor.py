from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_control_suppressed_stage_refactor"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPEC = importlib.util.spec_from_file_location("stage", ROOT / "scripts/198_trigger_stage_boundary_model.py")
stage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stage)

COMPONENTS = stage.COMPONENTS
JET_BINS = stage.JET_BINS


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)


def normalise(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(float(v)) for v in weights.values())
    return {k: float(weights.get(k, 0.0)) / scale if scale else 0.0 for k in COMPONENTS}


def control_suppressed_weights() -> list[dict[str, object]]:
    rows = []
    # Search around the previous best: observer ~= 0.39, physical ~= 0.44,
    # but allow stronger ordinary-QCD and lepton-control suppression.
    obs_vals = [0.30, 0.40, 0.55, 0.70, 0.90]
    phys_vals = [0.20, 0.35, 0.50, 0.70]
    alg_vals = [0.0, 0.10, 0.25]
    qcd_vals = [-1.50, -1.00, -0.70, -0.50, -0.30]
    lep_vals = [-0.50, -0.25, 0.0, 0.25]
    i = 0
    for obs, phys, alg, qcd, lep in product(obs_vals, phys_vals, alg_vals, qcd_vals, lep_vals):
        weights = normalise(
            {
                "observer_projection": obs,
                "physical_projection": phys,
                "algebraic_projection": alg,
                "ordinary_qcd_axis": qcd,
                "leptonic_control_axis": lep,
            }
        )
        rows.append({"candidate": f"control_suppressed_{i:04d}", "source": "control_suppressed_grid", **weights})
        i += 1
    seeds = [
        ("previous_best_plus_qcd", {"observer_projection": 0.39, "physical_projection": 0.44, "ordinary_qcd_axis": -0.70}),
        ("previous_best_plus_strong_qcd", {"observer_projection": 0.39, "physical_projection": 0.44, "ordinary_qcd_axis": -1.20}),
        ("previous_best_plus_lepton_suppressed", {"observer_projection": 0.39, "physical_projection": 0.44, "ordinary_qcd_axis": -0.70, "leptonic_control_axis": -0.30}),
        ("observer_physical_lowqcd", {"observer_projection": 0.70, "physical_projection": 0.50, "ordinary_qcd_axis": -1.00}),
        ("physical_dominant_lowqcd", {"observer_projection": 0.40, "physical_projection": 0.80, "ordinary_qcd_axis": -1.20}),
    ]
    for name, w in seeds:
        rows.append({"candidate": name, "source": "seed", **normalise(w)})

    seen = set()
    dedup = []
    for row in rows:
        key = tuple(round(float(row[c]), 8) for c in COMPONENTS)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def main() -> None:
    ensure_dirs()
    fresh = stage.load_fresh()
    audit = (
        fresh.groupby(["primary_dataset", "split"], as_index=False)
        .agg(events=("event", "count"), runs=("run", "nunique"), lumis=("lumi", "nunique"))
    )
    audit.to_csv(TABLES / "00_fresh_split_audit.csv", index=False)

    candidates = control_suppressed_weights()
    pd.DataFrame(candidates).to_csv(TABLES / "01_control_suppressed_candidate_weights.csv", index=False)

    dev_rows = []
    val_rows = []
    retained = []
    for i, cand in enumerate(candidates, start=1):
        name = str(cand["candidate"])
        weights = {c: float(cand[c]) for c in COMPONENTS}
        score_col = f"score_{i}"
        fresh[score_col] = stage.score(fresh, weights)
        dev_table = stage.stage_tail_table(fresh, score_col, "development", name)
        dev_eval = stage.evaluate_stage_pairs(dev_table, name, "development")
        best_dev = dev_eval.sort_values("selection_score", ascending=False).head(1)
        dev_rows.append(best_dev)
        should_validate = False
        if not best_dev.empty:
            row = best_dev.iloc[0]
            should_validate = bool(
                row["selection_score"] > -3.0
                or (row["signal_stouffer_Z"] > 5.0 and row["max_control_absZ_all_stages"] < 8.0)
                or row["passes_stage_screen"]
            )
        if should_validate:
            val_table = stage.stage_tail_table(fresh, score_col, "validation", name)
            keep_pairs = best_dev[["MET_stage", "HTMHT_stage"]].drop_duplicates()
            val_eval = stage.evaluate_stage_pairs(val_table, name, "validation").merge(keep_pairs, on=["MET_stage", "HTMHT_stage"], how="inner")
            val_rows.append(val_eval)
            retained.extend([dev_table, val_table])
        del fresh[score_col]
        if i % 100 == 0:
            print(f"screened {i}/{len(candidates)} control-suppressed candidates", flush=True)

    dev = pd.concat(dev_rows, ignore_index=True).sort_values("selection_score", ascending=False)
    val = pd.concat(val_rows, ignore_index=True) if val_rows else pd.DataFrame()
    if not val.empty:
        val = val.sort_values(["passes_stage_screen", "selection_score", "signal_stouffer_Z"], ascending=False)
    retained_df = pd.concat(retained, ignore_index=True) if retained else pd.DataFrame()

    dev.to_csv(TABLES / "02_development_control_suppressed_screen.csv", index=False)
    val.to_csv(TABLES / "03_heldout_control_suppressed_validation.csv", index=False)
    retained_df.to_csv(TABLES / "04_retained_control_suppressed_tail_tables.csv", index=False)

    pass_count = int(val["passes_stage_screen"].sum()) if not val.empty else 0
    best = val.head(20)
    best_text = best.to_markdown(index=False) if not best.empty else "No held-out candidates were validated."
    weights = pd.DataFrame(candidates)
    top_weights = weights[weights["candidate"].isin(best["candidate"].tolist())] if not best.empty else pd.DataFrame()
    top_weights_text = top_weights.to_markdown(index=False) if not top_weights.empty else "No held-out candidate weights."

    report = f"""# Control-Suppressed Trigger-Stage Boundary Refactor

## Purpose

The previous trigger-stage scan found strong held-out MET/HTMHT signal-stage behaviour, but it failed because JetHT also lit up. This run searches a stricter N-Frame boundary family with stronger ordinary-QCD and lepton-control suppression.

The target is not a SUSY-particle claim. The target is a cleaner hidden-boundary trace where MET and HTMHT are positive while JetHT and SingleMuon remain quiet across all stages.

## Fresh Split Audit

{audit.to_markdown(index=False)}

## Best Held-Out Rows

{best_text}

## Weights For Best Held-Out Rows

{top_weights_text}

## Strict Pass Count

{pass_count}

## Interpretation

If `pass_count` remains zero, then the project has not yet found a control-clean dynamic trace on this fresh MHT-aware sample. If a high signal Stouffer Z survives but controls exceed `|Z| < 3`, the result is still interesting but background/control limited.
"""
    (REPORTS / "01_CONTROL_SUPPRESSED_STAGE_REFACTOR_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Control-Suppressed Stage Refactor

Strict held-out pass count: {pass_count}

Best held-out rows:

{best_text}
"""
    (REPORTS / "02_SHORT_UPDATE_CONTROL_SUPPRESSED_STAGE.md").write_text(short, encoding="utf-8")

    print("CONTROL-SUPPRESSED STAGE REFACTOR COMPLETE")
    print(best.to_string(index=False) if not best.empty else "No validation rows.")
    print("Strict pass count:", pass_count)
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
