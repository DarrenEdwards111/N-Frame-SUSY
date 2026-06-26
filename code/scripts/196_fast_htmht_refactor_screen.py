from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_fast_htmht_refactor_screen"
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
TARGET_JET_BIN = "1to2jets"
COMPONENTS = ["observer_projection", "physical_projection", "algebraic_projection", "ordinary_qcd_axis"]
REL_UNC = 0.30


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def normalise(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(float(v)) for v in weights.values())
    return {k: (float(weights.get(k, 0.0)) / scale if scale else 0.0) for k in COMPONENTS}


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0:
        return np.nan
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def strict_quality(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in QUALITY_FILTERS:
        if col not in out:
            out[col] = 1
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(-999)
    return out[(out[QUALITY_FILTERS] == 1).all(axis=1)].copy()


def read_fresh_real(ref: dict) -> pd.DataFrame:
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
    return v4.apply_reference(fresh, ref)


def read_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    sm_raw = v4.add_base_transforms(v4.read_sm())
    ref = v4.fit_reference(sm_raw)
    sm = v4.apply_reference(sm_raw, ref)
    prior = v4.split_files(v4.apply_reference(v4.read_real(), ref))
    fresh = read_fresh_real(ref)
    real = pd.concat([prior, fresh], ignore_index=True)
    sm, real = tri.add_tri_aspect_components(sm, real)
    return sm, real


def weight_grid() -> list[dict[str, float]]:
    rows = []
    observer = [0.35, 0.55, 0.75]
    physical = [0.20, 0.45]
    algebraic = [0.0, 0.30]
    qcd = [-0.30, -0.15]
    for vals in product(observer, physical, algebraic, qcd):
        rows.append(normalise(dict(zip(COMPONENTS, vals))))
    seeds = [
        {"observer_projection": 0.80, "physical_projection": 0.0, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.20},
        {"observer_projection": 0.45, "physical_projection": 0.35, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.10},
        {"observer_projection": 0.60, "physical_projection": 0.25, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.15},
        {"observer_projection": 0.35, "physical_projection": 0.60, "algebraic_projection": 0.25, "ordinary_qcd_axis": -0.30},
        {"observer_projection": 0.25, "physical_projection": 0.70, "algebraic_projection": 0.25, "ordinary_qcd_axis": -0.30},
    ]
    rows.extend(normalise(s) for s in seeds)
    dedup = []
    seen = set()
    for row in rows:
        key = tuple(round(row[c], 8) for c in COMPONENTS)
        if key not in seen:
            dedup.append(row)
            seen.add(key)
    return dedup


def score(df: pd.DataFrame, weights: dict[str, float]) -> np.ndarray:
    out = np.zeros(len(df), dtype=float)
    for col, weight in weights.items():
        out += weight * df[col].to_numpy(float)
    return out


def fast_q99_summary(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, weights: dict[str, float], candidate: str, mode: str) -> pd.DataFrame:
    sm_d = sm.copy()
    sm_d["score"] = score(sm_d, weights)
    w = sm_d["event_weight"].to_numpy(float)
    met = sm_d["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, w, q) for q in np.linspace(0, 1, v4.MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    thresholds = []
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        mask = (met >= lo) & (met < hi)
        thresholds.append(weighted_quantile(sm_d.loc[mask, "score"].to_numpy(float), w[mask], 0.99))

    real_d = real[real["primary_dataset"].astype(str).eq(dataset)].copy()
    if real_d.empty:
        return pd.DataFrame()
    real_d["score"] = score(real_d, weights)
    real_d["met_bin_fast"] = pd.cut(real_d["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    thresh = pd.Series(thresholds, index=range(len(thresholds)))
    real_d["q99_tail"] = real_d["score"] >= real_d["met_bin_fast"].map(thresh).astype(float)

    rows = []
    for keys, group in real_d.groupby(["era", "split", "jet_bin"], dropna=False):
        era, split, jet_bin = keys
        obs = int(group["q99_tail"].sum())
        exp = 0.01 * len(group)
        z = (obs - exp) / np.sqrt(exp + (REL_UNC * exp) ** 2) if exp > 0 else np.nan
        rows.append(
            {
                "candidate": candidate,
                "mode": mode,
                "era": era,
                "split": split,
                "primary_dataset": dataset,
                "jet_bin": jet_bin,
                "q99_observed": obs,
                "q99_expected_fast": exp,
                "q99_obs_exp_fast": obs / exp if exp > 0 else np.nan,
                "q99_fast_Z": z,
            }
        )
    return pd.DataFrame(rows)


def get_z(summary: pd.DataFrame, era: str, dataset: str, split: str, jet_bin: str = TARGET_JET_BIN) -> float:
    row = summary[
        summary["era"].astype(str).eq(era)
        & summary["primary_dataset"].astype(str).eq(dataset)
        & summary["split"].astype(str).eq(split)
        & summary["jet_bin"].astype(str).eq(jet_bin)
    ]
    return float(row["q99_fast_Z"].iloc[0]) if not row.empty else np.nan


def get_oe(summary: pd.DataFrame, era: str, dataset: str, split: str, jet_bin: str = TARGET_JET_BIN) -> float:
    row = summary[
        summary["era"].astype(str).eq(era)
        & summary["primary_dataset"].astype(str).eq(dataset)
        & summary["split"].astype(str).eq(split)
        & summary["jet_bin"].astype(str).eq(jet_bin)
    ]
    return float(row["q99_obs_exp_fast"].iloc[0]) if not row.empty else np.nan


def evaluate(summary: pd.DataFrame, candidate: str, mode: str) -> dict[str, object]:
    signal = [
        ("Run2016", "MET", "validation"),
        ("Run2015D", "MET", "validation"),
        ("Run2015D", "HTMHT", "validation"),
        ("Run2016H_fresh", "MET", "fresh_seen_exploratory"),
        ("Run2016H_fresh", "HTMHT", "fresh_seen_exploratory"),
    ]
    controls = [
        ("Run2015D", "JetHT", "validation"),
        ("Run2015D", "SingleMuon", "validation"),
        ("Run2016H_fresh", "JetHT", "fresh_seen_exploratory"),
        ("Run2016H_fresh", "SingleMuon", "fresh_seen_exploratory"),
    ]
    zvals = {f"{era}_{dataset}_Z": get_z(summary, era, dataset, split) for era, dataset, split in signal + controls}
    oe = {f"{era}_{dataset}_obs_exp": get_oe(summary, era, dataset, split) for era, dataset, split in signal}
    sig = np.array([zvals[f"{era}_{dataset}_Z"] for era, dataset, split in signal], dtype=float)
    ctrl = np.array([zvals[f"{era}_{dataset}_Z"] for era, dataset, split in controls], dtype=float)
    htmht = np.array([zvals["Run2015D_HTMHT_Z"], zvals["Run2016H_fresh_HTMHT_Z"]], dtype=float)
    sig = sig[np.isfinite(sig)]
    ctrl = ctrl[np.isfinite(ctrl)]
    htmht = htmht[np.isfinite(htmht)]
    combined = float(sig.sum() / np.sqrt(len(sig))) if len(sig) else np.nan
    min_signal = float(sig.min()) if len(sig) else np.nan
    min_htmht = float(htmht.min()) if len(htmht) else np.nan
    max_control = float(np.abs(ctrl).max()) if len(ctrl) else np.nan
    selection = min_htmht + 0.10 * combined - max(0.0, max_control - 3.0)
    return {
        "candidate": candidate,
        "mode": mode,
        **zvals,
        **oe,
        "combined_signal_Z": combined,
        "min_signal_Z": min_signal,
        "min_HTMHT_Z": min_htmht,
        "max_control_absZ": max_control,
        "selection_score": selection,
        "passes_fast_refactor_screen": bool(
            np.isfinite(min_htmht)
            and min_htmht >= 3
            and np.isfinite(combined)
            and combined >= 5
            and np.isfinite(max_control)
            and max_control < 3
        ),
    }


def make_models() -> tuple[list[dict[str, object]], pd.DataFrame]:
    grid = weight_grid()
    met_base = normalise({"observer_projection": 0.80, "physical_projection": 0.0, "algebraic_projection": 0.0, "ordinary_qcd_axis": -0.20})
    control_jetht = normalise({"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.35, "physical_projection": 0.0})
    control_single = normalise({"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.20, "physical_projection": 0.0})
    models = []
    weights = []
    for i, w in enumerate(grid):
        for mode, met_w, htmht_w in [
            ("shared_MET_HTMHT", w, w),
            ("dynamic_HTMHT_only", met_base, w),
        ]:
            candidate = f"{mode}_{i:04d}"
            model = {
                "candidate": candidate,
                "mode": mode,
                "MET": met_w,
                "HTMHT": htmht_w,
                "JetHT": control_jetht,
                "SingleMuon": control_single,
            }
            models.append(model)
            for dataset in DATASETS:
                weights.append({"candidate": candidate, "mode": mode, "dataset_context": dataset, **model[dataset]})
    return models, pd.DataFrame(weights)


def main() -> None:
    ensure_dirs()
    print("reading inputs", flush=True)
    sm, real = read_inputs()
    audit = (
        real.groupby(["era", "primary_dataset", "split"], dropna=False)
        .agg(events=("source_file", "size"), files=("source_file", "nunique"))
        .reset_index()
    )
    audit.to_csv(TABLES / "01_input_audit.csv", index=False)

    models, weights = make_models()
    weights.to_csv(TABLES / "03_fast_candidate_weights.csv", index=False)
    eval_rows = []
    retained_summaries = []
    for i, model in enumerate(models, start=1):
        pieces = []
        for dataset in DATASETS:
            pieces.append(fast_q99_summary(real, sm, dataset, model[dataset], model["candidate"], model["mode"]))
        summary = pd.concat(pieces, ignore_index=True)
        row = evaluate(summary, model["candidate"], model["mode"])
        eval_rows.append(row)
        if row["selection_score"] >= 2.0 or row["passes_fast_refactor_screen"]:
            retained_summaries.append(summary)
        if i % 50 == 0:
            print(f"screened {i}/{len(models)}", flush=True)
    eval_df = pd.DataFrame(eval_rows).sort_values(["passes_fast_refactor_screen", "selection_score", "min_HTMHT_Z", "combined_signal_Z"], ascending=False)
    eval_df.to_csv(TABLES / "02_fast_refactor_screen.csv", index=False)
    retained = pd.concat(retained_summaries, ignore_index=True) if retained_summaries else pd.DataFrame()
    retained.to_csv(TABLES / "04_retained_fast_q99_summaries.csv", index=False)

    top_candidates = eval_df.head(8)["candidate"].tolist()
    top_weights = weights[weights["candidate"].isin(top_candidates)]
    pass_count = int(eval_df["passes_fast_refactor_screen"].sum())
    best = eval_df.head(20)

    report = f"""# Fast Exploratory HTMHT Boundary Refactor Screen

## Purpose

This is a fast model-development screen asking whether N-Frame weights can be adjusted so HTMHT improves across datasets. It uses a direct Q99 tail estimate rather than the slower sideband-profile fit, so the result is for ranking candidates, not for claiming discovery.

## Inputs

{audit.to_markdown(index=False)}

## Method

For each candidate boundary, the Standard Model reference defines the 99th percentile score threshold inside each MET bin. Real CMS events above that threshold are counted in the 1-2 jet tail. Expected counts are approximated as 1% of the matched real events in that bin, with 30% relative background-shape uncertainty.

Two families were screened:

- `shared_MET_HTMHT`: MET and HTMHT use the same weights.
- `dynamic_HTMHT_only`: MET keeps the previously successful missing-residual form, while HTMHT is refactored.

This is not a frozen validation. Any promising row must be frozen and tested on new files.

## Best Fast-Screen Rows

{best.to_markdown(index=False)}

## Top Candidate Weights

{top_weights.to_markdown(index=False)}

## Strict Fast-Screen Pass Count

{pass_count}

## Interpretation

A pass here would mean there is at least a plausible parameter direction where HTMHT can be brought into line without immediately lighting up JetHT/SingleMuon. A failure here means simple weight adjustment is probably not enough, and the next step should be trigger-aware HTMHT/MET modelling or a different boundary construction.
"""
    (REPORTS / "01_FAST_EXPLORATORY_HTMHT_REFACTOR_SCREEN.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Fast HTMHT Refactor Screen

Strict fast-screen pass count: {pass_count}

Best rows:

{best.head(10).to_markdown(index=False)}

Top candidate weights:

{top_weights.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_FAST_HTMHT_REFACTOR.md").write_text(short, encoding="utf-8")
    print("FAST HTMHT REFACTOR SCREEN COMPLETE")
    print(best.head(10).to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
