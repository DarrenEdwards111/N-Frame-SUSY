from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_local_control_clean_refinement"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPEC = importlib.util.spec_from_file_location("stage", ROOT / "scripts/198_trigger_stage_boundary_model.py")
stage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stage)

COMPONENTS = stage.COMPONENTS


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)


def normalise(w: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(float(v)) for v in w.values())
    return {k: float(w.get(k, 0.0)) / scale if scale else 0.0 for k in COMPONENTS}


def local_weights() -> list[dict[str, object]]:
    rows = []
    # Focused neighbourhood between the best quiet-control and best near-control candidates.
    obs_vals = [0.20, 0.23, 0.26, 0.29, 0.32]
    phys_vals = [0.29, 0.32, 0.35, 0.38]
    qcd_vals = [-0.40, -0.36, -0.32, -0.28]
    lep_vals = [-0.28, -0.22, -0.16, -0.10]
    alg_vals = [0.0]
    i = 0
    for obs, phys, qcd, lep, alg in product(obs_vals, phys_vals, qcd_vals, lep_vals, alg_vals):
        raw = {
            "observer_projection": float(obs),
            "physical_projection": float(phys),
            "algebraic_projection": float(alg),
            "ordinary_qcd_axis": float(qcd),
            "leptonic_control_axis": float(lep),
        }
        rows.append({"candidate": f"local_refine_{i:05d}", "source": "local_control_clean_refinement", **normalise(raw)})
        i += 1
    return rows


def main() -> None:
    ensure_dirs()
    fresh = stage.load_fresh()
    candidates = local_weights()
    pd.DataFrame(candidates).to_csv(TABLES / "01_local_refinement_candidate_weights.csv", index=False)

    dev_rows = []
    val_rows = []
    retained = []
    target_pair = pd.DataFrame([{"MET_stage": "0jet", "HTMHT_stage": "1to2jets"}])
    for i, cand in enumerate(candidates, start=1):
        name = str(cand["candidate"])
        weights = {c: float(cand[c]) for c in COMPONENTS}
        score_col = f"score_{i}"
        fresh[score_col] = stage.score(fresh, weights)
        dev_table = stage.stage_tail_table(fresh, score_col, "development", name)
        dev_eval = stage.evaluate_stage_pairs(dev_table, name, "development").merge(target_pair, on=["MET_stage", "HTMHT_stage"], how="inner")
        dev_rows.append(dev_eval)
        if not dev_eval.empty:
            d = dev_eval.iloc[0]
            should_validate = bool(
                d["min_signal_Z"] >= 2.0
                or d["signal_stouffer_Z"] >= 4.0
                or d["max_control_absZ_all_stages"] < 3.2
            )
        else:
            should_validate = False
        if should_validate:
            val_table = stage.stage_tail_table(fresh, score_col, "validation", name)
            val_eval = stage.evaluate_stage_pairs(val_table, name, "validation").merge(target_pair, on=["MET_stage", "HTMHT_stage"], how="inner")
            val_rows.append(val_eval)
            retained.extend([dev_table, val_table])
        del fresh[score_col]
        if i % 500 == 0:
            print(f"screened {i}/{len(candidates)} local candidates", flush=True)

    dev = pd.concat(dev_rows, ignore_index=True) if dev_rows else pd.DataFrame()
    val = pd.concat(val_rows, ignore_index=True) if val_rows else pd.DataFrame()
    if not dev.empty:
        dev = dev.sort_values("selection_score", ascending=False)
    if not val.empty:
        val = val.sort_values(["passes_stage_screen", "selection_score", "signal_stouffer_Z"], ascending=False)
    retained_df = pd.concat(retained, ignore_index=True) if retained else pd.DataFrame()

    dev.to_csv(TABLES / "02_development_local_refinement.csv", index=False)
    val.to_csv(TABLES / "03_heldout_local_refinement.csv", index=False)
    retained_df.to_csv(TABLES / "04_retained_local_refinement_tail_tables.csv", index=False)

    pass_count = int(val["passes_stage_screen"].sum()) if not val.empty else 0
    best = val.head(30)
    weights = pd.DataFrame(candidates)
    top_weights = weights[weights["candidate"].isin(best["candidate"].tolist())] if not best.empty else pd.DataFrame()
    best_text = best.to_markdown(index=False) if not best.empty else "No held-out candidates were validated."
    weights_text = top_weights.to_markdown(index=False) if not top_weights.empty else "No held-out weights."

    report = f"""# Local Control-Clean Boundary Refinement

## Purpose

This run performs a focused local refinement between the two best control-suppressed candidates:

- quiet-control candidate: signal Stouffer `Z = 4.28`, controls under `|Z| < 3`;
- stronger near-miss candidate: signal Stouffer `Z = 6.07`, but SingleMuon 0-jet `Z = 3.36`.

The target region is fixed to the stage pair selected by the previous scans:

- MET: 0-jet
- HTMHT: 1-2 jets

## Held-Out Results

{best_text}

## Weights For Best Held-Out Results

{weights_text}

## Strict Pass Count

{pass_count}

## Interpretation

This is the most focused attempt to keep the strong missing-boundary trace while suppressing JetHT and SingleMuon controls. A strict pass requires both signal stages to exceed `Z >= 3`, combined Stouffer `Z >= 5`, and every JetHT/SingleMuon stage to stay below `|Z| < 3`.
"""
    (REPORTS / "01_LOCAL_CONTROL_CLEAN_REFINEMENT_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Local Control-Clean Refinement

Strict held-out pass count: {pass_count}

Best held-out rows:

{best_text}
"""
    (REPORTS / "02_SHORT_UPDATE_LOCAL_CONTROL_CLEAN.md").write_text(short, encoding="utf-8")

    print("LOCAL CONTROL-CLEAN REFINEMENT COMPLETE")
    print(best.to_string(index=False) if not best.empty else "No validation rows.")
    print("Strict pass count:", pass_count)
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
