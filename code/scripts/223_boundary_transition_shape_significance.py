from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2, chi2_contingency, norm


ROOT = Path(__file__).resolve().parents[1]
COUNTS = ROOT / "outputs_microband_transition_scan" / "tables" / "02_target_microband_counts.csv"
BROAD = ROOT / "outputs_microband_transition_scan" / "tables" / "01_all_microband_counts.csv"
OUT = ROOT / "outputs_boundary_transition_shape_significance"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

MICROBANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
WIDTHS = {"q90_95": 0.05, "q95_97": 0.02, "q97_98": 0.01, "q98_99": 0.01, "q99_100": 0.01}
TRACE = ("MET", "0jet")
TARGET_CONTROLS = [("JetHT", "1to2jets"), ("SingleMuon", "0jet")]
ALL_CONTROL_DATASETS = ["JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def load_counts() -> tuple[pd.DataFrame, pd.DataFrame]:
    target = pd.read_csv(COUNTS)
    broad = pd.read_csv(BROAD)
    for df in [target, broad]:
        df["observed"] = pd.to_numeric(df["observed"], errors="coerce").fillna(0.0)
        df["nominal_width"] = df["microband"].map(WIDTHS)
    return target, broad


def vector(df: pd.DataFrame, run_era: str, dataset: str, jet_bin: str) -> np.ndarray:
    hit = df[(df["run_era"].eq(run_era)) & (df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet_bin))]
    vals = []
    for band in MICROBANDS:
        sub = hit[hit["microband"].eq(band)]
        vals.append(float(sub["observed"].sum()) if not sub.empty else 0.0)
    return np.asarray(vals, dtype=float)


def control_vector_target(df: pd.DataFrame, run_era: str) -> np.ndarray:
    out = np.zeros(len(MICROBANDS), dtype=float)
    for dataset, jet_bin in TARGET_CONTROLS:
        out += vector(df, run_era, dataset, jet_bin)
    return out


def control_vector_all(broad: pd.DataFrame, run_era: str) -> np.ndarray:
    out = np.zeros(len(MICROBANDS), dtype=float)
    for dataset in ALL_CONTROL_DATASETS:
        for jet_bin in JET_BINS:
            out += vector(broad, run_era, dataset, jet_bin)
    return out


def density(v: np.ndarray) -> np.ndarray:
    widths = np.asarray([WIDTHS[b] for b in MICROBANDS], dtype=float)
    total = v.sum()
    if total <= 0:
        return np.full_like(v, np.nan)
    return v / total / (widths / widths.sum())


def chi_square_shape(trace: np.ndarray, control: np.ndarray) -> dict[str, float]:
    table = np.vstack([trace, control])
    chi2_stat, p, dof, _expected = chi2_contingency(table, correction=False)
    return {"shape_chi2": float(chi2_stat), "shape_dof": int(dof), "shape_p": float(p), "shape_Z": p_to_z(float(p))}


def shoulder_test(trace: np.ndarray, control: np.ndarray) -> dict[str, float]:
    # Collapse into low shoulder 90-95, high shoulder 95-99, endpoint 99-100.
    t = np.asarray([trace[0], trace[1:4].sum(), trace[4]], dtype=float)
    c = np.asarray([control[0], control[1:4].sum(), control[4]], dtype=float)
    table = np.vstack([t, c])
    chi2_stat, p, dof, _expected = chi2_contingency(table, correction=False)
    t_density = t / t.sum() / np.asarray([0.05, 0.04, 0.01])
    c_density = c / c.sum() / np.asarray([0.05, 0.04, 0.01])
    return {
        "shoulder_chi2": float(chi2_stat),
        "shoulder_dof": int(dof),
        "shoulder_p": float(p),
        "shoulder_Z": p_to_z(float(p)),
        "trace_95_99_over_90_95": float(t_density[1] / t_density[0]) if t_density[0] > 0 else np.nan,
        "control_95_99_over_90_95": float(c_density[1] / c_density[0]) if c_density[0] > 0 else np.nan,
        "trace_99_100_over_95_99": float(t_density[2] / t_density[1]) if t_density[1] > 0 else np.nan,
        "control_99_100_over_95_99": float(c_density[2] / c_density[1]) if c_density[1] > 0 else np.nan,
    }


def bootstrap_ratios(trace: np.ndarray, control: np.ndarray, n_boot: int = 20_000, seed: int = 20260617) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    widths = np.asarray([0.05, 0.04, 0.01], dtype=float)

    def collapse(v: np.ndarray) -> np.ndarray:
        return np.asarray([v[0], v[1:4].sum(), v[4]], dtype=float)

    def shoulder_ratio(v: np.ndarray) -> float:
        c = collapse(v)
        d = c / max(c.sum(), 1.0) / widths
        return float(d[1] / d[0]) if d[0] > 0 else np.nan

    t_prob = trace / trace.sum()
    c_prob = control / control.sum()
    t_n = int(trace.sum())
    c_n = int(control.sum())
    deltas = np.empty(n_boot)
    for i in range(n_boot):
        tb = rng.multinomial(t_n, t_prob)
        cb = rng.multinomial(c_n, c_prob)
        deltas[i] = shoulder_ratio(tb) - shoulder_ratio(cb)
    obs_delta = shoulder_ratio(trace) - shoulder_ratio(control)
    two_sided_p = float(np.mean(np.abs(deltas - np.mean(deltas)) >= abs(obs_delta)))
    # Also record one-sided probability that the trace shoulder is no stronger.
    one_sided_p = float(np.mean(deltas <= 0.0))
    return {
        "bootstrap_delta_95_99_over_90_95": float(obs_delta),
        "bootstrap_delta_ci_low": float(np.quantile(deltas, 0.025)),
        "bootstrap_delta_ci_high": float(np.quantile(deltas, 0.975)),
        "bootstrap_one_sided_p_trace_not_gt_control": max(one_sided_p, 1.0 / n_boot if one_sided_p == 0 else one_sided_p),
        "bootstrap_one_sided_Z": p_to_z(max(one_sided_p, 1.0 / n_boot if one_sided_p == 0 else one_sided_p)),
    }


def build_results(target: pd.DataFrame, broad: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    vectors = []
    for era in ["Run2016G", "Run2016H"]:
        trace = vector(target, era, TRACE[0], TRACE[1])
        controls = {
            "targeted_controls": control_vector_target(target, era),
            "all_jetht_singlemuon_controls": control_vector_all(broad, era),
        }
        for control_name, control in controls.items():
            if trace.sum() <= 0 or control.sum() <= 0:
                continue
            shape = chi_square_shape(trace, control)
            shoulder = shoulder_test(trace, control)
            boot = bootstrap_ratios(trace, control, seed=20260617 + (0 if era == "Run2016G" else 1))
            rows.append(
                {
                    "run_era": era,
                    "control_reference": control_name,
                    "trace_total_top10": float(trace.sum()),
                    "control_total_top10": float(control.sum()),
                    **shape,
                    **shoulder,
                    **boot,
                    "passes_shape_difference_screen": bool(shape["shape_Z"] >= 5.0),
                    "passes_shoulder_enrichment_screen": bool(boot["bootstrap_one_sided_Z"] >= 5.0 and boot["bootstrap_delta_95_99_over_90_95"] > 0),
                }
            )
            for band, t, c, td, cd in zip(MICROBANDS, trace, control, density(trace), density(control)):
                vectors.append(
                    {
                        "run_era": era,
                        "control_reference": control_name,
                        "microband": band,
                        "trace_count": float(t),
                        "control_count": float(c),
                        "trace_width_normalised_density": float(td),
                        "control_width_normalised_density": float(cd),
                        "trace_over_control_density": float(td / cd) if cd > 0 else np.nan,
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(vectors)


def main() -> None:
    ensure_dirs()
    target, broad = load_counts()
    summary, vectors = build_results(target, broad)
    summary.to_csv(TABLES / "01_boundary_transition_shape_significance.csv", index=False)
    vectors.to_csv(TABLES / "02_boundary_transition_shape_vectors.csv", index=False)

    best = summary.sort_values(["passes_shape_difference_screen", "shape_Z"], ascending=[False, False])
    report = f"""# Boundary-Transition Shape Significance

## Purpose

This stage stops asking whether Q99 alone spikes. Instead it asks whether the full `90-100%` N-Frame score-tail shape in MET 0-jet differs from JetHT/SingleMuon controls.

This is closer to the boundary-trace question: is there a broad high-boundary transition in MET-like data, not just a single endpoint excess?

## Tests

1. Five-bin shape test across `90-95`, `95-97`, `97-98`, `98-99`, `99-100`.
2. Collapsed shoulder test: `90-95` vs `95-99` vs `99-100`.
3. Bootstrap check for whether the `95-99 / 90-95` shoulder ratio is stronger in MET than in controls.

## Summary

{summary.to_markdown(index=False, floatfmt=".6g")}

## Microband Shape Vectors

{vectors.to_markdown(index=False, floatfmt=".6g")}

## Best Rows

{best.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

A strong result here would show that MET has a statistically distinct high-boundary transition shape relative to JetHT/SingleMuon controls, replicated in both Run2016G and Run2016H. A weak result would mean the broad shoulder exists but is not cleanly separable from ordinary control-tail behaviour.
"""
    (REPORTS / "01_BOUNDARY_TRANSITION_SHAPE_SIGNIFICANCE.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_BOUNDARY_TRANSITION_SHAPE_SIGNIFICANCE.md")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
