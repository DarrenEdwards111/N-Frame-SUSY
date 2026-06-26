from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, norm


ROOT = Path(__file__).resolve().parents[1]
RUN2016G_EVENTS = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz"
RUN2016H_EVENTS = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv"
OUT = ROOT / "outputs_replicated_transition_observable_scan"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

COMPONENTS = ["observer_projection", "physical_projection", "algebraic_projection", "ordinary_qcd_axis", "leptonic_control_axis"]
MICROBANDS = [
    ("q90_95", 0.90, 0.95),
    ("q95_97", 0.95, 0.97),
    ("q97_98", 0.97, 0.98),
    ("q98_99", 0.98, 0.99),
    ("q99_100", 0.99, 1.00),
]
TRACE = ("MET", "0jet")
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def load_events() -> pd.DataFrame:
    g_cols = [
        "era",
        "primary_dataset",
        "MET_pt",
        "MHT_pt",
        "missing_proxy_pt",
        "jet_bin",
        "strict_quality_clean",
        *COMPONENTS,
        "frozen_boundary_score",
    ]
    g = pd.read_csv(RUN2016G_EVENTS, usecols=lambda c: c in g_cols, low_memory=False)
    g = g[g["strict_quality_clean"].astype(bool)].copy()
    g["run_era"] = "Run2016G"
    g["score_existing_frozen"] = pd.to_numeric(g["frozen_boundary_score"], errors="coerce")
    g = g.drop(columns=["era", "strict_quality_clean", "frozen_boundary_score"], errors="ignore")

    h_cols = [
        "run_era",
        "primary_dataset",
        "MET_pt",
        "MHT_pt",
        "missing_proxy_pt",
        "jet_bin",
        "strict_quality_clean",
        *COMPONENTS,
        "mht_dynamic_boundary_score",
    ]
    h = pd.read_csv(RUN2016H_EVENTS, usecols=lambda c: c in h_cols, low_memory=False)
    h = h[h["strict_quality_clean"].astype(bool)].copy()
    h["run_era"] = "Run2016H"
    h["score_existing_dynamic"] = pd.to_numeric(h["mht_dynamic_boundary_score"], errors="coerce")
    h = h.drop(columns=["strict_quality_clean", "mht_dynamic_boundary_score"], errors="ignore")

    events = pd.concat([g, h], ignore_index=True, sort=False)
    for col in COMPONENTS + ["MET_pt", "MHT_pt", "missing_proxy_pt"]:
        events[col] = pd.to_numeric(events[col], errors="coerce").fillna(0.0)
    events = events[events["primary_dataset"].isin(["MET", "HTMHT", "JetHT", "SingleMuon"])].copy()
    events["jet_bin"] = events["jet_bin"].astype(str)
    # Use dataset-native missing proxy for deciles: MHT for HTMHT, MET proxy for others.
    events["missing_for_decile"] = np.where(events["primary_dataset"].eq("HTMHT"), events["MHT_pt"], events["MET_pt"])
    events["missing_for_decile"] = pd.to_numeric(events["missing_for_decile"], errors="coerce").fillna(events["missing_proxy_pt"])
    return events


def candidate_weights() -> pd.DataFrame:
    rows = []
    # Named baselines.
    named = {
        "existing_frozen_OPQL": [0.31372549, 0.31372549, 0.0, -0.2745098, -0.0980392],
        "observer_only": [1, 0, 0, 0, 0],
        "physical_only": [0, 1, 0, 0, 0],
        "algebraic_only": [0, 0, 1, 0, 0],
        "observer_physical": [0.5, 0.5, 0, 0, 0],
        "observer_physical_minus_qcd": [0.4, 0.4, 0, -0.2, 0],
        "observer_physical_algebraic_minus_qcd": [0.35, 0.35, 0.15, -0.15, 0],
        "observer_physical_minus_qcd_lepton": [0.35, 0.35, 0, -0.2, -0.1],
        "missing_observer_minus_qcd": [0.75, 0, 0, -0.25, 0],
        "physical_minus_qcd": [0, 0.75, 0, -0.25, 0],
    }
    for name, weights in named.items():
        rows.append({"candidate_id": name, **dict(zip(COMPONENTS, weights)), "source": "named"})

    vals_pos = [0.25, 0.5, 0.75]
    vals_alg = [0.0, 0.15]
    vals_q = [0.0, -0.2]
    vals_l = [0.0, -0.1]
    idx = 0
    for o, p, a, q, l in product(vals_pos, vals_pos, vals_alg, vals_q, vals_l):
        if o + p <= 0:
            continue
        norm = abs(o) + abs(p) + abs(a) + abs(q) + abs(l)
        if norm == 0:
            continue
        weights = np.asarray([o, p, a, q, l], dtype=float) / norm
        idx += 1
        rows.append({"candidate_id": f"grid_{idx:04d}", **dict(zip(COMPONENTS, weights)), "source": "grid"})
    out = pd.DataFrame(rows).drop_duplicates(subset=COMPONENTS).reset_index(drop=True)
    return out


def assign_missing_deciles(events: pd.DataFrame) -> pd.DataFrame:
    out = events.copy()
    out["missing_decile"] = -1
    for keys, idx in out.groupby(["run_era", "primary_dataset"], observed=False).groups.items():
        vals = out.loc[idx, "missing_for_decile"].to_numpy(float)
        try:
            bins = pd.qcut(vals, 10, labels=False, duplicates="drop")
        except ValueError:
            bins = np.zeros(len(idx), dtype=int)
        out.loc[idx, "missing_decile"] = np.asarray(bins, dtype=float)
    out["missing_decile"] = out["missing_decile"].astype(int)
    return out


def candidate_score(events: pd.DataFrame, weights: pd.Series) -> np.ndarray:
    score = np.zeros(len(events), dtype=float)
    for col in COMPONENTS:
        score += float(weights[col]) * events[col].to_numpy(float)
    return score


def microband_counts(events: pd.DataFrame, score: np.ndarray) -> pd.DataFrame:
    tmp = events[["run_era", "primary_dataset", "jet_bin", "missing_decile"]].copy()
    tmp["score"] = score
    frames = []
    for _keys, group in tmp.groupby(["run_era", "primary_dataset", "missing_decile"], observed=False):
        if len(group) < 100:
            continue
        vals = group["score"].to_numpy(float)
        qs = np.quantile(vals, [0.90, 0.95, 0.97, 0.98, 0.99, 1.00])
        qs[-1] = np.inf
        labels = np.full(len(group), None, dtype=object)
        for (name, _lo, _hi), lo, hi in zip(MICROBANDS, qs[:-1], qs[1:]):
            labels[(vals >= lo) & (vals < hi)] = name
        g = group.copy()
        g["microband"] = labels
        frames.append(g[g["microband"].notna()])
    if not frames:
        return pd.DataFrame()
    tagged = pd.concat(frames, ignore_index=True)
    return (
        tagged.groupby(["run_era", "primary_dataset", "jet_bin", "microband"], observed=False)
        .size()
        .reset_index(name="observed")
    )


def vec(counts: pd.DataFrame, era: str, dataset: str, jet_bin: str) -> np.ndarray:
    hit = counts[(counts["run_era"].eq(era)) & (counts["primary_dataset"].eq(dataset)) & (counts["jet_bin"].eq(jet_bin))]
    return np.asarray([float(hit.loc[hit["microband"].eq(b), "observed"].sum()) for b, _lo, _hi in MICROBANDS], dtype=float)


def control_vec(counts: pd.DataFrame, era: str) -> np.ndarray:
    out = np.zeros(len(MICROBANDS), dtype=float)
    for dataset in CONTROL_DATASETS:
        for jet_bin in JET_BINS:
            out += vec(counts, era, dataset, jet_bin)
    return out


def shape_result(trace: np.ndarray, control: np.ndarray) -> dict[str, float]:
    if trace.sum() <= 0 or control.sum() <= 0:
        return {"shape_Z": np.nan}
    chi2_stat, p, dof, _ = chi2_contingency(np.vstack([trace, control]), correction=False)
    widths = np.asarray([0.05, 0.02, 0.01, 0.01, 0.01], dtype=float)
    t_density = trace / trace.sum() / (widths / widths.sum())
    c_density = control / control.sum() / (widths / widths.sum())
    t_shoulder = (t_density[1] * 0.02 + t_density[2] * 0.01 + t_density[3] * 0.01) / 0.04
    c_shoulder = (c_density[1] * 0.02 + c_density[2] * 0.01 + c_density[3] * 0.01) / 0.04
    return {
        "shape_chi2": float(chi2_stat),
        "shape_dof": int(dof),
        "shape_p": float(p),
        "shape_Z": p_to_z(float(p)),
        "trace_95_99_over_90_95": float(t_shoulder / t_density[0]) if t_density[0] > 0 else np.nan,
        "control_95_99_over_90_95": float(c_shoulder / c_density[0]) if c_density[0] > 0 else np.nan,
        "trace_99_over_95_99": float(t_density[4] / t_shoulder) if t_shoulder > 0 else np.nan,
        "control_99_over_95_99": float(c_density[4] / c_shoulder) if c_shoulder > 0 else np.nan,
    }


def evaluate_candidate(events: pd.DataFrame, weights: pd.Series) -> tuple[dict, pd.DataFrame]:
    counts = microband_counts(events, candidate_score(events, weights))
    rows = []
    vector_rows = []
    for era in ["Run2016G", "Run2016H"]:
        trace = vec(counts, era, TRACE[0], TRACE[1])
        control = control_vec(counts, era)
        res = shape_result(trace, control)
        rows.append({f"{era}_{k}": v for k, v in res.items()})
        for band, t, c in zip([b[0] for b in MICROBANDS], trace, control):
            vector_rows.append(
                {
                    "candidate_id": weights["candidate_id"],
                    "run_era": era,
                    "microband": band,
                    "trace_count": t,
                    "control_count": c,
                }
            )
    flat = {"candidate_id": weights["candidate_id"], "source": weights["source"]}
    for col in COMPONENTS:
        flat[col] = float(weights[col])
    for row in rows:
        flat.update(row)
    z_g = flat.get("Run2016G_shape_Z", np.nan)
    z_h = flat.get("Run2016H_shape_Z", np.nan)
    flat["min_replicated_shape_Z"] = float(np.nanmin([z_g, z_h]))
    flat["stouffer_shape_Z"] = float(np.nansum([z_g, z_h]) / np.sqrt(np.isfinite([z_g, z_h]).sum()))
    flat["replicated_screen_pass"] = bool(
        flat["min_replicated_shape_Z"] >= 5
        and flat.get("Run2016G_trace_95_99_over_90_95", 0) > flat.get("Run2016G_control_95_99_over_90_95", np.inf)
        and flat.get("Run2016H_trace_95_99_over_90_95", 0) > flat.get("Run2016H_control_95_99_over_90_95", np.inf)
    )
    return flat, pd.DataFrame(vector_rows)


def main() -> None:
    ensure_dirs()
    events = assign_missing_deciles(load_events())
    candidates = candidate_weights()
    candidates.to_csv(TABLES / "00_candidate_weight_grid.csv", index=False)

    result_rows = []
    vector_frames = []
    for i, row in candidates.iterrows():
        res, vectors = evaluate_candidate(events, row)
        result_rows.append(res)
        if i < 20 or res["replicated_screen_pass"]:
            vector_frames.append(vectors)
        if (i + 1) % 100 == 0:
            print(f"scanned {i + 1}/{len(candidates)}", flush=True)

    results = pd.DataFrame(result_rows).sort_values(
        ["replicated_screen_pass", "min_replicated_shape_Z", "stouffer_shape_Z"],
        ascending=[False, False, False],
    )
    results.to_csv(TABLES / "01_replicated_transition_observable_scan.csv", index=False)
    if vector_frames:
        pd.concat(vector_frames, ignore_index=True).to_csv(TABLES / "02_saved_candidate_microband_vectors.csv", index=False)

    top = results.head(25)
    passes = results[results["replicated_screen_pass"]]
    report = f"""# Replicated N-Frame Transition Observable Scan

## Purpose

This is an exploratory scan for a more stable N-Frame boundary-transition observable. It does not download new data and does not claim discovery. It asks whether any Darren/N-Frame-style combination of observer, physical, algebraic, QCD and lepton axes produces a MET high-boundary transition shape that replicates in both Run2016G and Run2016H.

## Replication Rule

A candidate passes only if:

- Run2016G MET 0-jet shape differs from all JetHT/SingleMuon controls at >= 5 sigma.
- Run2016H MET 0-jet shape differs from all JetHT/SingleMuon controls at >= 5 sigma.
- The `95-99 / 90-95` shoulder ratio is larger in MET than controls in both eras.

## Passing Candidates

{passes.to_markdown(index=False, floatfmt=".6g") if not passes.empty else "_No candidate passed the strict replicated screen._"}

## Top Candidates

{top.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

If no candidate passes, the current data support a promising but not discovery-grade boundary-trace programme. The next move would be either more independent data or a better physically constrained N-Frame observable, not claiming the existing trace as discovery-level.
"""
    (REPORTS / "01_REPLICATED_TRANSITION_OBSERVABLE_SCAN.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_REPLICATED_TRANSITION_OBSERVABLE_SCAN.md")
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
