from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_tri_aspect_dynamic_boundary_model"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPEC = importlib.util.spec_from_file_location("bb", ROOT / "scripts/189_breakthrough_or_bust_nframe_boundary_search.py")
bb = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bb)
v4 = bb.v4

SIGNAL_DATASETS = ["MET", "HTMHT"]
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def add_algebraic_projection(sm: pd.DataFrame, real: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = [
        "log1p_MET_pt",
        "log1p_HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "packed_candidate_count",
        "secondary_vertex_count",
        "met_ht_ratio",
        "jet_btag_ratio",
    ]
    w = sm["event_weight"].to_numpy(float)
    x_sm = sm[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(float)
    mean = np.average(x_sm, axis=0, weights=w)
    sd = np.sqrt(np.average((x_sm - mean) ** 2, axis=0, weights=w))
    sd = np.where(sd <= 1e-9, 1.0, sd)
    z_sm = (x_sm - mean) / sd
    # Weighted PCA basis from SM: first three components are treated as ordinary low-dimensional event manifold.
    zw = z_sm * np.sqrt(np.clip(w, 1e-12, np.inf))[:, None]
    _, _, vt = np.linalg.svd(zw, full_matrices=False)
    basis = vt[:3].T

    def project(df: pd.DataFrame) -> pd.Series:
        x = df[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(float)
        z = (x - mean) / sd
        recon = (z @ basis) @ basis.T
        resid = np.sqrt(np.mean((z - recon) ** 2, axis=1))
        return pd.Series(resid, index=df.index)

    sm = sm.copy()
    real = real.copy()
    sm["algebraic_manifold_residual_raw"] = project(sm)
    real["algebraic_manifold_residual_raw"] = project(real)
    m = np.average(sm["algebraic_manifold_residual_raw"], weights=w)
    s = np.sqrt(np.average((sm["algebraic_manifold_residual_raw"] - m) ** 2, weights=w))
    s = max(float(s), 1e-9)
    sm["algebraic_projection"] = (sm["algebraic_manifold_residual_raw"] - m) / s
    real["algebraic_projection"] = (real["algebraic_manifold_residual_raw"] - m) / s
    return sm, real


def add_tri_aspect_components(sm: pd.DataFrame, real: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sm, real = add_algebraic_projection(sm, real)
    for df in [sm, real]:
        df["physical_projection"] = 0.65 * df["z_log1p_MET_pt"] + 0.20 * df["visible_energy"] + 0.15 * df["disp_reco"]
        df["observer_projection"] = df["missing_resid"]
        df["ordinary_qcd_axis"] = 0.70 * df["multiplicity"] + 0.30 * df["btag_structure"]
        df["leptonic_control_axis"] = -df["lepton_suppression"]
    return sm, real


def normalise(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(v) for v in weights.values())
    return {k: float(v / scale) for k, v in weights.items()} if scale else weights


def candidate_grid() -> list[dict[str, object]]:
    # Hand-built candidate family for a first pass. These are deliberately interpretable:
    # MET remains close to the artefact-clean v5 missing-residual trace, while HTMHT is
    # allowed to pick up physical recoil and algebraic manifold-residual structure.
    met_family = [
        normalise({"observer_projection": 0.80, "ordinary_qcd_axis": -0.20}),
        normalise({"observer_projection": 0.70, "algebraic_projection": 0.15, "ordinary_qcd_axis": -0.15}),
        normalise({"observer_projection": 0.65, "physical_projection": 0.15, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.10}),
    ]
    htmht_family = [
        normalise({"observer_projection": 0.60, "physical_projection": 0.25, "ordinary_qcd_axis": -0.15}),
        normalise({"observer_projection": 0.50, "physical_projection": 0.25, "algebraic_projection": 0.15, "ordinary_qcd_axis": -0.10}),
        normalise({"observer_projection": 0.45, "physical_projection": 0.35, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.10}),
        normalise({"observer_projection": 0.55, "algebraic_projection": 0.30, "ordinary_qcd_axis": -0.15}),
    ]
    control_mixtures = {
        "JetHT": normalise({"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.35}),
        "SingleMuon": normalise({"observer_projection": 0.55, "algebraic_projection": 0.10, "ordinary_qcd_axis": -0.20, "leptonic_control_axis": -0.15}),
    }
    rows = []
    idx = 0
    for met_w in met_family:
        for htmht_w in htmht_family:
            rows.append(
                {
                    "candidate": f"tri_dynamic_{idx:02d}",
                    "MET": met_w,
                    "HTMHT": htmht_w,
                    "JetHT": control_mixtures["JetHT"],
                    "SingleMuon": control_mixtures["SingleMuon"],
                }
            )
            idx += 1
    return rows


def apply_dynamic_score(df: pd.DataFrame, model: dict[str, object]) -> pd.DataFrame:
    out = df.copy()
    score = np.zeros(len(out), dtype=float)
    for dataset in ["MET", "HTMHT", "JetHT", "SingleMuon"]:
        weights = model[dataset]
        mask = out["primary_dataset"].astype(str).eq(dataset).to_numpy()
        s = np.zeros(mask.sum(), dtype=float)
        for col, weight in weights.items():
            s += weight * out.loc[mask, col].to_numpy(float)
        score[mask] = s
    out["dynamic_score"] = score
    return out


def assign_dynamic_bands(real: pd.DataFrame, sm: pd.DataFrame, model: dict[str, object]) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    real_scored = apply_dynamic_score(real, model)
    sm_by_dataset = {}
    for dataset in ["MET", "HTMHT", "JetHT", "SingleMuon"]:
        sm_tmp = sm.copy()
        sm_tmp["primary_dataset"] = dataset
        sm_tmp = apply_dynamic_score(sm_tmp, model)
        met_edges, score_edges = v4.define_edges(sm_tmp, "dynamic_score")
        sm_by_dataset[dataset] = v4.assign_bands(sm_tmp, "dynamic_score", met_edges, score_edges)
        mask = real_scored["primary_dataset"].astype(str).eq(dataset)
        if mask.any():
            assigned = v4.assign_bands(real_scored.loc[mask].copy(), "dynamic_score", met_edges, score_edges)
            real_scored.loc[assigned.index, "met_bin_v4"] = assigned["met_bin_v4"]
            real_scored.loc[assigned.index, "score_band_v4"] = assigned["score_band_v4"]
    real_scored = real_scored[real_scored["score_band_v4"].notna()].copy()
    return real_scored, sm_by_dataset


def counts_for_dynamic(real: pd.DataFrame, sm_by_dataset: dict[str, pd.DataFrame], split: str, candidate: str) -> pd.DataFrame:
    frames = []
    for dataset, sm_d in sm_by_dataset.items():
        real_d = real[(real["split"].eq(split)) & (real["primary_dataset"].astype(str).eq(dataset))]
        if real_d.empty:
            continue
        frames.append(bb.score_counts_fast(real_d, sm_d, split, candidate))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def evaluate(summary: pd.DataFrame, candidate: str, split: str, signal_jet_bin: str) -> dict:
    return bb.evaluate_region(summary, candidate, split, signal_jet_bin)


def best_development_region(summary: pd.DataFrame, candidate: str) -> dict:
    rows = [evaluate(summary, candidate, "development", jb) for jb in JET_BINS]
    return max(rows, key=lambda r: -np.inf if not np.isfinite(r["selection_score"]) else r["selection_score"])


def main() -> None:
    ensure_dirs()
    sm_raw = v4.add_base_transforms(v4.read_sm())
    ref = v4.fit_reference(sm_raw)
    sm = v4.apply_reference(sm_raw, ref)
    real = v4.split_files(v4.apply_reference(v4.read_real(), ref))
    sm, real = add_tri_aspect_components(sm, real)

    split_audit = (
        real.groupby(["era", "primary_dataset", "split"], observed=False)
        .agg(source_files=("source_file", "nunique"), events=("source_file", "size"))
        .reset_index()
    )
    split_audit.to_csv(TABLES / "01_split_audit.csv", index=False)

    models = candidate_grid()
    dev_rows = []
    shortlisted = []
    for i, model in enumerate(models):
        real_b, sm_by_dataset = assign_dynamic_bands(real, sm, model)
        counts = counts_for_dynamic(real_b, sm_by_dataset, "development", model["candidate"])
        summary = v4.summarize_counts(counts)
        row = best_development_region(summary, model["candidate"])
        dev_rows.append(row)
        if np.isfinite(row["selection_score"]) and (row["selection_score"] > 0.5 or row["signal_stouffer_Z"] > 5):
            shortlisted.append(model)
        if (i + 1) % 100 == 0:
            print(f"screened {i + 1} / {len(models)} dynamic models", flush=True)

    dev_df = pd.DataFrame(dev_rows).sort_values(["selection_score", "signal_stouffer_Z"], ascending=False)
    dev_df.to_csv(TABLES / "02_dynamic_development_screen.csv", index=False)

    # Keep validation bounded and include the best development models even if the cutoff is too strict.
    best_names = set(dev_df.head(12)["candidate"].tolist())
    shortlisted = [m for m in shortlisted if m["candidate"] in best_names] + [m for m in models if m["candidate"] in best_names]
    seen = set()
    unique_shortlist = []
    for m in shortlisted:
        if m["candidate"] not in seen:
            unique_shortlist.append(m)
            seen.add(m["candidate"])

    val_rows = []
    model_rows = []
    for model in unique_shortlist:
        real_b, sm_by_dataset = assign_dynamic_bands(real, sm, model)
        counts = counts_for_dynamic(real_b, sm_by_dataset, "validation", model["candidate"])
        summary = v4.summarize_counts(counts)
        signal_bin = dev_df.loc[dev_df["candidate"].eq(model["candidate"]), "signal_jet_bin"].iloc[0]
        val_rows.append(evaluate(summary, model["candidate"], "validation", signal_bin))
        for dataset in ["MET", "HTMHT", "JetHT", "SingleMuon"]:
            row = {"candidate": model["candidate"], "dataset_context": dataset}
            row.update(model[dataset])
            model_rows.append(row)

    val_df = pd.DataFrame(val_rows)
    if not val_df.empty:
        val_df = val_df.sort_values(["selection_score", "signal_stouffer_Z", "min_signal_Z"], ascending=False)
    weights_df = pd.DataFrame(model_rows).fillna(0.0)
    val_df.to_csv(TABLES / "03_dynamic_heldout_validation.csv", index=False)
    weights_df.to_csv(TABLES / "04_dynamic_context_weights.csv", index=False)

    best = val_df.iloc[0] if not val_df.empty else pd.Series(dtype=object)
    best_weights = weights_df[weights_df["candidate"].eq(best.get("candidate", ""))] if not val_df.empty else pd.DataFrame()
    pass_count = int(val_df["passes_trace_breakthrough_screen"].sum()) if not val_df.empty else 0
    report = f"""# Tri-Aspect Dynamic Boundary Model

## Purpose

Darren's tri-aspect note suggests that the collision boundary should be dynamic rather than a single static observer surface. This run translates that into a testable toy model:

\\[
\\Omega_0 \\rightarrow \\Omega_1 \\rightarrow \\Omega_2 \\rightarrow \\Omega_T
\\]

with three projected aspects:

1. physical projection: missing energy, visible energy, and detector/reconstruction stress;
2. observer projection: missing-energy residual after visible reconstructed structure is modelled;
3. algebraic projection: distance from the low-dimensional SM event manifold fitted by weighted PCA.

The model is dynamic because the MET, HTMHT, JetHT, and SingleMuon contexts are allowed to use different mixtures of the same tri-aspect components. Candidate mixtures are selected on development files and tested on held-out files.

## Split Audit

{split_audit.to_markdown(index=False)}

## Best Held-Out Dynamic Boundary Results

{val_df.head(20).to_markdown(index=False) if not val_df.empty else "No dynamic candidates validated."}

## Best Dynamic Candidate Weights

{best_weights.to_markdown(index=False) if not best_weights.empty else "No best candidate."}

## Readout

- Dynamic models screened: {len(models)}
- Dynamic models held out for validation: {len(unique_shortlist)}
- Strict trace-breakthrough pass count: {pass_count}

## Interpretation

This is a more faithful implementation of Darren's dynamical-boundary idea than the static v5 score. It allows the same underlying N-Frame aspects to reweight by detector/reconstruction context.

If the best dynamic model improves HTMHT transfer while keeping JetHT and SingleMuon controls quiet, that supports the dynamical-boundary direction. If it does not, the bottleneck is still cross-dataset transfer and SM/control robustness rather than lack of boundary flexibility.
"""
    (REPORTS / "01_TRI_ASPECT_DYNAMIC_BOUNDARY_MODEL_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Tri-Aspect Dynamic Boundary

Best held-out dynamic result:

{val_df.head(8).to_markdown(index=False) if not val_df.empty else "No dynamic candidates validated."}

Strict pass count: {pass_count}
"""
    (REPORTS / "02_SHORT_UPDATE_TRI_ASPECT_DYNAMIC_BOUNDARY.md").write_text(short, encoding="utf-8")
    print("TRI-ASPECT DYNAMIC BOUNDARY MODEL COMPLETE")
    print(val_df.head(10).to_string(index=False) if not val_df.empty else "No validation rows")
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
