from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_exploratory_htmht_refactor_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
FRESH_COMBINED = ROOT / "outputs_fresh_run2016h_tri_dynamic_validation" / "sources" / "fresh_run2016h_combined_event_features.csv"

SPEC_TRI = importlib.util.spec_from_file_location("tri", ROOT / "scripts/192_tri_aspect_dynamic_boundary_model.py")
tri = importlib.util.module_from_spec(SPEC_TRI)
assert SPEC_TRI.loader is not None
SPEC_TRI.loader.exec_module(tri)
v4 = tri.v4

QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]
DATASETS = ["MET", "HTMHT", "JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
TARGET_JET_BIN = "1to2jets"
COMPONENTS = ["observer_projection", "physical_projection", "algebraic_projection", "ordinary_qcd_axis"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def normalise(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(float(v)) for v in weights.values())
    if scale <= 0:
        return {k: 0.0 for k in COMPONENTS}
    return {k: float(v) / scale for k, v in weights.items()}


def strict_quality(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in QUALITY_FILTERS:
        if col not in out:
            out[col] = 1
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(-999)
    return out[(out[QUALITY_FILTERS] == 1).all(axis=1)].copy()


def read_fresh_real() -> pd.DataFrame:
    fresh = pd.read_csv(FRESH_COMBINED, low_memory=False)
    fresh = strict_quality(fresh)
    for col in v4.BASE_FEATURES:
        if col not in fresh:
            fresh[col] = 0.0
        fresh[col] = pd.to_numeric(fresh[col], errors="coerce").fillna(0.0)
    fresh["primary_dataset"] = fresh["primary_dataset"].astype(str)
    fresh["source_file"] = fresh["source_file"].astype(str)
    fresh["era"] = "Run2016H_fresh"
    fresh["event_weight"] = 1.0
    fresh["split"] = "fresh_seen_exploratory"
    return fresh


def read_all_real(ref: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sm_raw = v4.add_base_transforms(v4.read_sm())
    sm = v4.apply_reference(sm_raw, ref)
    prior = v4.split_files(v4.apply_reference(v4.read_real(), ref))
    fresh = v4.apply_reference(read_fresh_real(), ref)
    real = pd.concat([prior, fresh], ignore_index=True)
    return sm, prior, real


def weight_grid() -> list[dict[str, float]]:
    rows = []
    # Keep the first pass small and interpretable. The full Cartesian grid is too
    # slow over the current multi-era feature table, so this starts with the
    # physically motivated directions that can plausibly help HTMHT transfer.
    observer = [0.35, 0.50, 0.65, 0.80]
    physical = [0.0, 0.25, 0.45]
    algebraic = [0.0, 0.20, 0.40]
    qcd = [-0.35, -0.15]
    for vals in product(observer, physical, algebraic, qcd):
        w = dict(zip(COMPONENTS, vals))
        rows.append(normalise(w))
    # Include earlier fixed models exactly.
    rows.extend(
        [
            normalise({"observer_projection": 0.80, "physical_projection": 0.0, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.20}),
            normalise({"observer_projection": 0.45, "physical_projection": 0.35, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.10}),
            normalise({"observer_projection": 0.60, "physical_projection": 0.25, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.15}),
            normalise({"observer_projection": 0.55, "physical_projection": 0.0, "algebraic_projection": 0.30, "ordinary_qcd_axis": -0.15}),
        ]
    )
    dedup = []
    seen = set()
    for w in rows:
        key = tuple(round(w.get(c, 0.0), 8) for c in COMPONENTS)
        if key not in seen:
            dedup.append({c: w.get(c, 0.0) for c in COMPONENTS})
            seen.add(key)
    return dedup


def model_from_weights(candidate: str, met_w: dict[str, float], htmht_w: dict[str, float], mode: str) -> dict[str, object]:
    control_jetht = normalise({"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.35, "physical_projection": 0.0})
    control_single = normalise({"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.20, "physical_projection": 0.0})
    return {
        "candidate": candidate,
        "mode": mode,
        "MET": met_w,
        "HTMHT": htmht_w,
        "JetHT": control_jetht,
        "SingleMuon": control_single,
    }


def apply_model_score(df: pd.DataFrame, model: dict[str, object]) -> pd.DataFrame:
    out = df.copy()
    score = np.zeros(len(out), dtype=float)
    for dataset in DATASETS:
        mask = out["primary_dataset"].astype(str).eq(dataset).to_numpy()
        if not mask.any():
            continue
        weights = model[dataset]
        s = np.zeros(mask.sum(), dtype=float)
        for col, weight in weights.items():
            if col not in out:
                continue
            s += float(weight) * out.loc[mask, col].to_numpy(float)
        score[mask] = s
    out["dynamic_score"] = score
    return out


def assign_bands(real: pd.DataFrame, sm: pd.DataFrame, model: dict[str, object]) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    real_scored = apply_model_score(real, model)
    sm_by_dataset = {}
    pieces = []
    for dataset in DATASETS:
        sm_tmp = sm.copy()
        sm_tmp["primary_dataset"] = dataset
        sm_tmp = apply_model_score(sm_tmp, model)
        met_edges, score_edges = v4.define_edges(sm_tmp, "dynamic_score")
        sm_by_dataset[dataset] = v4.assign_bands(sm_tmp, "dynamic_score", met_edges, score_edges)
        real_d = real_scored[real_scored["primary_dataset"].astype(str).eq(dataset)]
        if not real_d.empty:
            pieces.append(v4.assign_bands(real_d.copy(), "dynamic_score", met_edges, score_edges))
    return (pd.concat(pieces, ignore_index=True) if pieces else real_scored.iloc[0:0].copy()), sm_by_dataset


def counts_for_all(real_b: pd.DataFrame, sm_by_dataset: dict[str, pd.DataFrame], model: dict[str, object]) -> pd.DataFrame:
    frames = []
    for dataset, sm_d in sm_by_dataset.items():
        real_d = real_b[real_b["primary_dataset"].astype(str).eq(dataset)]
        if real_d.empty:
            continue
        for split in sorted(real_d["split"].dropna().unique()):
            frames.append(tri.counts_for_dynamic(real_d, {dataset: sm_d}, split, model["candidate"]))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def q99_summary(counts: pd.DataFrame) -> pd.DataFrame:
    if counts.empty:
        return pd.DataFrame()
    return v4.summarize_counts(counts)


def get_z(summary: pd.DataFrame, era: str, dataset: str, split: str, jet_bin: str = TARGET_JET_BIN) -> float:
    row = summary[
        summary["era"].astype(str).eq(era)
        & summary["primary_dataset"].astype(str).eq(dataset)
        & summary["split"].astype(str).eq(split)
        & summary["jet_bin"].astype(str).eq(jet_bin)
    ]
    if row.empty:
        return np.nan
    return float(row["q99_profile_Z"].iloc[0])


def get_oe(summary: pd.DataFrame, era: str, dataset: str, split: str, jet_bin: str = TARGET_JET_BIN) -> float:
    row = summary[
        summary["era"].astype(str).eq(era)
        & summary["primary_dataset"].astype(str).eq(dataset)
        & summary["split"].astype(str).eq(split)
        & summary["jet_bin"].astype(str).eq(jet_bin)
    ]
    if row.empty:
        return np.nan
    return float(row["q99_obs_exp_profile"].iloc[0])


def evaluate(summary: pd.DataFrame, model: dict[str, object]) -> dict[str, object]:
    signal_cells = [
        ("Run2016", "MET", "validation"),
        ("Run2015D", "MET", "validation"),
        ("Run2015D", "HTMHT", "validation"),
        ("Run2016H_fresh", "MET", "fresh_seen_exploratory"),
        ("Run2016H_fresh", "HTMHT", "fresh_seen_exploratory"),
    ]
    control_cells = [
        ("Run2015D", "JetHT", "validation"),
        ("Run2015D", "SingleMuon", "validation"),
        ("Run2016H_fresh", "JetHT", "fresh_seen_exploratory"),
        ("Run2016H_fresh", "SingleMuon", "fresh_seen_exploratory"),
    ]
    zvals = {f"{era}_{dataset}_Z": get_z(summary, era, dataset, split) for era, dataset, split in signal_cells + control_cells}
    oevals = {f"{era}_{dataset}_obs_exp": get_oe(summary, era, dataset, split) for era, dataset, split in signal_cells}
    signals = np.array([zvals[f"{era}_{dataset}_Z"] for era, dataset, split in signal_cells], dtype=float)
    controls = np.array([zvals[f"{era}_{dataset}_Z"] for era, dataset, split in control_cells], dtype=float)
    finite_signal = signals[np.isfinite(signals)]
    finite_control = controls[np.isfinite(controls)]
    htmht_pair = np.array([zvals["Run2015D_HTMHT_Z"], zvals["Run2016H_fresh_HTMHT_Z"]], dtype=float)
    finite_htmht = htmht_pair[np.isfinite(htmht_pair)]
    combined = float(finite_signal.sum() / np.sqrt(len(finite_signal))) if len(finite_signal) else np.nan
    min_signal = float(np.min(finite_signal)) if len(finite_signal) else np.nan
    min_htmht = float(np.min(finite_htmht)) if len(finite_htmht) else np.nan
    max_control = float(np.max(np.abs(finite_control))) if len(finite_control) else np.nan
    # Selection score rewards cross-dataset HTMHT support first, then combined signal, and penalises controls.
    selection = min_htmht + 0.15 * combined - max(0.0, max_control - 3.0)
    return {
        "candidate": model["candidate"],
        "mode": model["mode"],
        **zvals,
        **oevals,
        "combined_signal_Z": combined,
        "min_signal_Z": min_signal,
        "min_HTMHT_Z": min_htmht,
        "max_control_absZ": max_control,
        "selection_score": selection,
        "passes_strict_refactor_screen": bool(
            np.isfinite(min_htmht)
            and min_htmht >= 3.0
            and np.isfinite(combined)
            and combined >= 5.0
            and np.isfinite(max_control)
            and max_control < 3.0
        ),
    }


def main() -> None:
    ensure_dirs()
    sm_raw = v4.add_base_transforms(v4.read_sm())
    ref = v4.fit_reference(sm_raw)
    sm, prior, real = read_all_real(ref)
    sm, real = tri.add_tri_aspect_components(sm, real)

    audit = (
        real.groupby(["era", "primary_dataset", "split"], dropna=False)
        .agg(events=("source_file", "size"), files=("source_file", "nunique"))
        .reset_index()
    )
    audit.to_csv(TABLES / "01_input_audit.csv", index=False)

    grid = weight_grid()
    base_met = normalise({"observer_projection": 0.80, "physical_projection": 0.0, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.20})

    models = []
    for i, w in enumerate(grid):
        models.append(model_from_weights(f"shared_{i:04d}", w, w, "shared_MET_HTMHT"))
        models.append(model_from_weights(f"dynamic_htmht_{i:04d}", base_met, w, "dynamic_HTMHT_only"))

    eval_rows = []
    weight_rows = []
    retained_summaries = []
    for i, model in enumerate(models, start=1):
        print(f"screening {i}/{len(models)} {model['candidate']} {model['mode']}", flush=True)
        real_b, sm_by_dataset = assign_bands(real, sm, model)
        counts = counts_for_all(real_b, sm_by_dataset, model)
        summary = q99_summary(counts)
        row = evaluate(summary, model)
        eval_rows.append(row)
        if row["selection_score"] >= 2.0 or row["passes_strict_refactor_screen"]:
            retained_summaries.append(summary.assign(model_mode=model["mode"]))
        for dataset in DATASETS:
            weight_rows.append({"candidate": model["candidate"], "mode": model["mode"], "dataset_context": dataset, **model[dataset]})
        if i % 100 == 0:
            print(f"screened {i}/{len(models)} refactor candidates", flush=True)

    eval_df = pd.DataFrame(eval_rows).sort_values(["passes_strict_refactor_screen", "selection_score", "min_HTMHT_Z", "combined_signal_Z"], ascending=False)
    weights_df = pd.DataFrame(weight_rows).fillna(0.0)
    retained = pd.concat(retained_summaries, ignore_index=True) if retained_summaries else pd.DataFrame()

    eval_df.to_csv(TABLES / "02_refactor_candidate_screen.csv", index=False)
    weights_df.to_csv(TABLES / "03_refactor_candidate_weights.csv", index=False)
    retained.to_csv(TABLES / "04_retained_candidate_sideband_summaries.csv", index=False)

    best = eval_df.head(20)
    pass_count = int(eval_df["passes_strict_refactor_screen"].sum())
    best_candidate = str(eval_df.iloc[0]["candidate"]) if not eval_df.empty else "none"
    best_weights = weights_df[weights_df["candidate"].eq(best_candidate)]
    report = f"""# Exploratory HTMHT Boundary Refactor Search

## Purpose

This run asks whether the N-Frame boundary parameters can be adjusted so that HTMHT improves across datasets while MET remains positive and JetHT/SingleMuon controls do not also light up.

This is explicitly a model-development/refactor search. It is not a frozen validation and it is not a discovery claim. Because the fresh Run2016H result is now known, any candidate found here must be frozen and tested on new, unused data.

## Inputs

{audit.to_markdown(index=False)}

## Search Design

Two model families were tested:

1. Shared MET/HTMHT boundary: the same weights are used for MET and HTMHT.
2. Dynamic HTMHT boundary: MET keeps the previous successful missing-residual form, while HTMHT is allowed to use a different mixture of observer, physical, algebraic, and QCD-suppression axes.

The target readout is the Q99 1-2 jet tail. The screen requires:

- Run2016 MET positive.
- Run2015D MET positive.
- Run2015D HTMHT positive.
- Fresh Run2016H MET positive.
- Fresh Run2016H HTMHT positive.
- JetHT and SingleMuon controls below |Z| = 3.

## Best Candidates

{best.to_markdown(index=False)}

## Best Candidate Weights

{best_weights.to_markdown(index=False)}

## Strict Pass Count

{pass_count}

## Interpretation

If the best candidates improve fresh HTMHT only in the dynamic family, that supports the idea that HTMHT and MET require different boundary projections. If no candidate passes the strict screen, then parameter adjustment alone has not yet produced the solid cross-dataset result; the next step should focus on trigger-path and background modelling differences between MET and HTMHT, then freeze a revised rule for fresh validation.
"""
    (REPORTS / "01_EXPLORATORY_HTMHT_BOUNDARY_REFACTOR_SEARCH.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Exploratory HTMHT Boundary Refactor

Strict pass count: {pass_count}

Best rows:

{best.head(10).to_markdown(index=False)}

Best weights:

{best_weights.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_EXPLORATORY_HTMHT_REFACTOR.md").write_text(short, encoding="utf-8")
    print("EXPLORATORY HTMHT REFACTOR SEARCH COMPLETE")
    print(best.head(10).to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
