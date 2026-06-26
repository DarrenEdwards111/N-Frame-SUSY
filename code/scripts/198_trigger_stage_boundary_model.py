from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_trigger_stage_boundary_model"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

FRESH_SCORED = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv"
PREVIOUS_V4_SUMMARY = ROOT / "outputs_quality_aware_nframe_v4_cross_era_search" / "tables" / "03_candidate_profile_summary.csv"
PREVIOUS_V5_READOUT = ROOT / "outputs_artifact_clean_hidden_trace_boundary_v5" / "tables" / "01_artifact_clean_v5_candidate_readout.csv"

SIGNAL_DATASETS = ["MET", "HTMHT"]
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
COMPONENTS = [
    "observer_projection",
    "physical_projection",
    "algebraic_projection",
    "ordinary_qcd_axis",
    "leptonic_control_axis",
]
REL_UNC = 0.30


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def normalise(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(float(v)) for v in weights.values())
    return {k: float(weights.get(k, 0.0)) / scale if scale else 0.0 for k in COMPONENTS}


def candidate_weights() -> list[dict[str, object]]:
    seeds = [
        ("mht_tri_dynamic", {"observer_projection": 0.45, "physical_projection": 0.35, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.10}),
        ("met_missing_low_qcd", {"observer_projection": 0.80, "ordinary_qcd_axis": -0.20}),
        ("observer_only", {"observer_projection": 1.0}),
        ("observer_physical", {"observer_projection": 0.60, "physical_projection": 0.25, "ordinary_qcd_axis": -0.15}),
        ("observer_algebraic", {"observer_projection": 0.55, "algebraic_projection": 0.30, "ordinary_qcd_axis": -0.15}),
        ("physical_algebraic", {"physical_projection": 0.55, "algebraic_projection": 0.25, "ordinary_qcd_axis": -0.20}),
        ("lepton_veto_trace", {"observer_projection": 0.60, "physical_projection": 0.20, "leptonic_control_axis": 0.20}),
        ("anti_lepton_low_qcd", {"observer_projection": 0.60, "ordinary_qcd_axis": -0.25, "leptonic_control_axis": 0.15}),
    ]
    rows = [{"candidate": name, "source": "seed", **normalise(w)} for name, w in seeds]

    obs_vals = [0.35, 0.55, 0.75, 1.00]
    phys_vals = [0.0, 0.20, 0.40]
    alg_vals = [0.0, 0.20, 0.40]
    qcd_vals = [-0.35, -0.15, 0.0]
    lep_vals = [-0.20, 0.0, 0.20]
    i = 0
    for obs, phys, alg, qcd, lep in product(obs_vals, phys_vals, alg_vals, qcd_vals, lep_vals):
        if obs == phys == alg == qcd == lep == 0:
            continue
        weights = normalise(
            {
                "observer_projection": obs,
                "physical_projection": phys,
                "algebraic_projection": alg,
                "ordinary_qcd_axis": qcd,
                "leptonic_control_axis": lep,
            }
        )
        rows.append({"candidate": f"stage_grid_{i:04d}", "source": "stage_grid", **weights})
        i += 1

    seen = set()
    dedup = []
    for row in rows:
        key = tuple(round(row[c], 8) for c in COMPONENTS)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def load_fresh() -> pd.DataFrame:
    if not FRESH_SCORED.exists():
        raise FileNotFoundError(FRESH_SCORED)
    cols = [
        "run",
        "lumi",
        "event",
        "primary_dataset",
        "jet_bin",
        "missing_proxy_pt",
        "missing_proxy_kind",
        *COMPONENTS,
    ]
    header = pd.read_csv(FRESH_SCORED, nrows=0).columns
    usecols = [c for c in cols if c in header]
    df = pd.read_csv(FRESH_SCORED, usecols=usecols, low_memory=False)
    for col in ["run", "lumi", "event", "missing_proxy_pt", *COMPONENTS]:
        if col not in df:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["primary_dataset"] = df["primary_dataset"].astype(str)
    df["jet_bin"] = df["jet_bin"].astype(str)
    df["missing_proxy_kind"] = df["missing_proxy_kind"].astype(str)
    key = pd.util.hash_pandas_object(df[["run", "lumi", "event", "primary_dataset"]].astype(str), index=False).to_numpy()
    df["split"] = np.where(key % 3 == 0, "validation", "development")
    return df


def score(df: pd.DataFrame, weights: dict[str, float]) -> np.ndarray:
    out = np.zeros(len(df), dtype=float)
    for col in COMPONENTS:
        out += float(weights.get(col, 0.0)) * df[col].to_numpy(float)
    return out


def stage_tail_table(df: pd.DataFrame, score_col: str, split: str, candidate: str) -> pd.DataFrame:
    rows = []
    sub = df[df["split"].eq(split)].copy()
    if sub.empty:
        return pd.DataFrame()
    for dataset, group in sub.groupby("primary_dataset", sort=False):
        g = group.copy()
        q = np.linspace(0, 1, 11)
        edges = np.unique(g["missing_proxy_pt"].quantile(q).to_numpy(float))
        if len(edges) < 3:
            edges = np.array([-np.inf, np.inf])
        else:
            edges[0], edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=edges, labels=False, include_lowest=True)
        thresholds = g.groupby("missing_bin", observed=False)[score_col].quantile(0.99)
        g["q99_tail"] = g[score_col] >= g["missing_bin"].map(thresholds).astype(float)
        expected_frac = g.groupby("missing_bin", observed=False)["q99_tail"].mean().rename("expected_tail_fraction")
        for jet_bin, j in g.groupby("jet_bin", observed=False):
            if str(jet_bin) not in JET_BINS or j.empty:
                continue
            expected = float(j["missing_bin"].map(expected_frac).astype(float).sum())
            observed = int(j["q99_tail"].sum())
            z = (observed - expected) / np.sqrt(expected + (REL_UNC * expected) ** 2) if expected > 0 else np.nan
            rows.append(
                {
                    "candidate": candidate,
                    "split": split,
                    "primary_dataset": dataset,
                    "jet_bin": str(jet_bin),
                    "events": len(j),
                    "q99_observed": observed,
                    "q99_expected_internal": expected,
                    "q99_obs_exp_internal": observed / expected if expected > 0 else np.nan,
                    "q99_internal_Z_relunc30": z,
                }
            )
    return pd.DataFrame(rows)


def value(table: pd.DataFrame, dataset: str, jet_bin: str, col: str = "q99_internal_Z_relunc30") -> float:
    row = table[(table["primary_dataset"].eq(dataset)) & (table["jet_bin"].eq(jet_bin))]
    return float(row[col].iloc[0]) if not row.empty else np.nan


def evaluate_stage_pairs(table: pd.DataFrame, candidate: str, split: str) -> pd.DataFrame:
    rows = []
    for met_stage, htmht_stage in product(JET_BINS, JET_BINS):
        met_z = value(table, "MET", met_stage)
        htmht_z = value(table, "HTMHT", htmht_stage)
        signals = np.array([met_z, htmht_z], dtype=float)
        finite = signals[np.isfinite(signals)]
        combined = float(finite.sum() / np.sqrt(len(finite))) if len(finite) else np.nan
        min_signal = float(np.min(finite)) if len(finite) else np.nan
        control_z = []
        for dataset in CONTROL_DATASETS:
            for jet_bin in JET_BINS:
                z = value(table, dataset, jet_bin)
                if np.isfinite(z):
                    control_z.append(z)
        max_control_abs = float(np.max(np.abs(control_z))) if control_z else np.nan
        penalty = max(0.0, max_control_abs - 3.0) if np.isfinite(max_control_abs) else 0.0
        score_val = min_signal + 0.15 * combined - penalty
        rows.append(
            {
                "candidate": candidate,
                "split": split,
                "MET_stage": met_stage,
                "HTMHT_stage": htmht_stage,
                "MET_stage_Z": met_z,
                "HTMHT_stage_Z": htmht_z,
                "signal_stouffer_Z": combined,
                "min_signal_Z": min_signal,
                "max_control_absZ_all_stages": max_control_abs,
                "selection_score": score_val,
                "passes_stage_screen": bool(
                    np.isfinite(min_signal)
                    and min_signal >= 3.0
                    and np.isfinite(combined)
                    and combined >= 5.0
                    and np.isfinite(max_control_abs)
                    and max_control_abs < 3.0
                ),
            }
        )
    return pd.DataFrame(rows)


def previous_context() -> tuple[pd.DataFrame, pd.DataFrame]:
    v4 = pd.read_csv(PREVIOUS_V4_SUMMARY) if PREVIOUS_V4_SUMMARY.exists() else pd.DataFrame()
    v5 = pd.read_csv(PREVIOUS_V5_READOUT) if PREVIOUS_V5_READOUT.exists() else pd.DataFrame()
    return v4, v5


def main() -> None:
    ensure_dirs()
    fresh = load_fresh()
    audit = (
        fresh.groupby(["primary_dataset", "split"], as_index=False)
        .agg(events=("event", "count"), runs=("run", "nunique"), lumis=("lumi", "nunique"))
    )
    audit.to_csv(TABLES / "00_fresh_split_audit.csv", index=False)

    candidates = candidate_weights()
    pd.DataFrame(candidates).to_csv(TABLES / "01_stage_candidate_weights.csv", index=False)

    dev_rows = []
    validation_rows = []
    retained_tables = []
    for i, cand in enumerate(candidates, start=1):
        name = str(cand["candidate"])
        weights = {c: float(cand[c]) for c in COMPONENTS}
        score_col = f"score_{i}"
        fresh[score_col] = score(fresh, weights)
        dev_table = stage_tail_table(fresh, score_col, "development", name)
        dev_eval = evaluate_stage_pairs(dev_table, name, "development")
        best_dev = dev_eval.sort_values("selection_score", ascending=False).head(1)
        dev_rows.append(best_dev)

        should_validate = False
        if not best_dev.empty:
            row = best_dev.iloc[0]
            should_validate = bool(
                row["selection_score"] > -2.0
                or row["signal_stouffer_Z"] > 4.0
                or name in {"mht_tri_dynamic", "met_missing_low_qcd", "observer_only"}
            )
        if should_validate:
            val_table = stage_tail_table(fresh, score_col, "validation", name)
            val_eval = evaluate_stage_pairs(val_table, name, "validation")
            keep_pairs = best_dev[["MET_stage", "HTMHT_stage"]].drop_duplicates()
            val_eval = val_eval.merge(keep_pairs, on=["MET_stage", "HTMHT_stage"], how="inner")
            validation_rows.append(val_eval)
            retained_tables.extend([dev_table, val_table])
        del fresh[score_col]
        if i % 50 == 0:
            print(f"screened {i}/{len(candidates)} stage-aware candidates", flush=True)

    dev = pd.concat(dev_rows, ignore_index=True).sort_values("selection_score", ascending=False)
    val = pd.concat(validation_rows, ignore_index=True) if validation_rows else pd.DataFrame()
    if not val.empty:
        val = val.sort_values(["passes_stage_screen", "selection_score", "signal_stouffer_Z"], ascending=False)
    retained = pd.concat(retained_tables, ignore_index=True) if retained_tables else pd.DataFrame()
    dev.to_csv(TABLES / "02_development_stage_pair_screen.csv", index=False)
    val.to_csv(TABLES / "03_heldout_stage_pair_validation.csv", index=False)
    retained.to_csv(TABLES / "04_retained_stage_tail_tables.csv", index=False)

    v4, v5 = previous_context()
    if not v4.empty:
        v4_focus = v4[
            (v4["split"].eq("validation"))
            & (v4["primary_dataset"].isin(["MET", "HTMHT", "JetHT", "SingleMuon"]))
            & (v4["jet_bin"].isin(JET_BINS))
        ].copy()
        v4_focus.to_csv(TABLES / "05_previous_v4_validation_stage_context.csv", index=False)
    if not v5.empty:
        v5.to_csv(TABLES / "06_previous_v5_artifact_clean_context.csv", index=False)

    best = val.head(12) if not val.empty else pd.DataFrame()
    pass_count = int(val["passes_stage_screen"].sum()) if not val.empty and "passes_stage_screen" in val else 0
    best_text = best.to_markdown(index=False) if not best.empty else "No held-out candidates were validated."
    dev_text = dev.head(12).to_markdown(index=False) if not dev.empty else "No development candidates were produced."

    report = f"""# Trigger-Stage N-Frame Boundary Model

## Purpose

The previous MHT-aware validation showed that the frozen 1-2 jet readout is probably too rigid. This script tests a trigger-stage model: MET and HTMHT are allowed to occupy different jet-stage boundaries, but JetHT and SingleMuon must remain quiet across all jet stages.

This is still a trace-finding test, not a direct SUSY-particle search.

## Data

Fresh CMS Run2016H MiniAOD, re-extracted with MHT-aware columns:

{audit.to_markdown(index=False)}

## Method

For each candidate score:

```latex
B = w_oO + w_pP + w_aA + w_qQ + w_lL
```

where `O` is the missing-visible residual, `P` is the physical/recoil projection, `A` is the algebraic manifold residual, `Q` is the ordinary jet/b-tag axis, and `L` is the lepton-control axis.

Events are split by a stable hash of `(run,lumi,event,primary_dataset)`. Candidate scores and signal stage pairs are selected on the development split, then tested on the held-out validation split. The score must keep all JetHT and SingleMuon stages below `|Z| < 3` to pass.

## Best Development Stage Pairs

{dev_text}

## Held-Out Validation Readout

{best_text}

## Strict Pass Count

{pass_count}

## Interpretation

If the pass count is zero, then the trigger-stage readout did not produce a clean breakthrough-level trace under this strict control rule. A positive MET or HTMHT stage by itself is not enough: the control streams must not produce comparable stage-local excesses.

The important information from this run is whether the earlier strong MET result can be turned into a controlled dynamic-boundary pattern once HTMHT and controls are treated in their own stages.
"""
    (REPORTS / "01_TRIGGER_STAGE_BOUNDARY_MODEL_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Trigger-Stage Boundary Model

Strict held-out pass count: {pass_count}

Best held-out rows:

{best_text}
"""
    (REPORTS / "02_SHORT_UPDATE_TRIGGER_STAGE_BOUNDARY.md").write_text(short, encoding="utf-8")

    print("TRIGGER-STAGE BOUNDARY MODEL COMPLETE")
    print(best.to_string(index=False) if not best.empty else "No validation rows.")
    print("Strict pass count:", pass_count)
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
