from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation" / "tables" / "04_remote_mht_aware_scored_axis_events.csv"
OUT = ROOT / "outputs_opq_remote_three_sample_statistical_robustness"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SAMPLES = [
    "Run2015D_remote_mht_aware_holdout",
    "Run2016H_remote_mht_aware",
    "Run2016G_remote_mht_aware_fresh",
]
MICROBANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
WIDTHS = np.asarray([0.05, 0.02, 0.01, 0.01, 0.01], dtype=float)
N_BOOTSTRAP = 50000
RNG = np.random.default_rng(20260622)


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def opq_score(df: pd.DataFrame) -> np.ndarray:
    return (
        0.344828 * pd.to_numeric(df["observer_projection"], errors="coerce").fillna(0.0).to_numpy(float)
        + 0.517241 * pd.to_numeric(df["physical_projection"], errors="coerce").fillna(0.0).to_numpy(float)
        - 0.137931 * pd.to_numeric(df["ordinary_qcd_axis"], errors="coerce").fillna(0.0).to_numpy(float)
    )


def tag_microbands(events: pd.DataFrame) -> pd.DataFrame:
    tmp = events.copy()
    tmp["score_opq"] = opq_score(tmp)
    frames = []
    for _key, group in tmp.groupby(["sample_validation_id", "primary_dataset", "missing_decile"], observed=False):
        if len(group) < 100:
            continue
        vals = group["score_opq"].to_numpy(float)
        edges = np.quantile(vals, [0.90, 0.95, 0.97, 0.98, 0.99, 1.00])
        edges[-1] = np.inf
        labels = np.full(len(group), None, dtype=object)
        for name, lo, hi in zip(MICROBANDS, edges[:-1], edges[1:]):
            labels[(vals >= lo) & (vals < hi)] = name
        g = group.copy()
        g["microband"] = labels
        frames.append(g[g["microband"].notna()])
    if not frames:
        return pd.DataFrame(columns=list(tmp.columns) + ["microband"])
    return pd.concat(frames, ignore_index=True)


def vector(counts: pd.DataFrame, sample: str, trace: bool) -> np.ndarray:
    if trace:
        hit = counts[
            counts["sample_validation_id"].eq(sample)
            & counts["primary_dataset"].eq("MET")
            & counts["jet_bin"].astype(str).eq("0jet")
        ]
    else:
        hit = counts[
            counts["sample_validation_id"].eq(sample)
            & counts["primary_dataset"].isin(["JetHT", "SingleMuon"])
        ]
    return np.asarray([hit.loc[hit["microband"].eq(band), "n"].sum() for band in MICROBANDS], dtype=int)


def bootstrap_delta(trace: np.ndarray, control: np.ndarray) -> tuple[float, float, float, float]:
    trace_probs = trace / trace.sum()
    control_probs = control / control.sum()
    t = RNG.multinomial(int(trace.sum()), trace_probs, size=N_BOOTSTRAP)
    c = RNG.multinomial(int(control.sum()), control_probs, size=N_BOOTSTRAP)
    t_ratio = ((t[:, 1:4].sum(axis=1) / t.sum(axis=1)) / WIDTHS[1:4].sum()) / (
        (t[:, 0] / t.sum(axis=1)) / WIDTHS[0]
    )
    c_ratio = ((c[:, 1:4].sum(axis=1) / c.sum(axis=1)) / WIDTHS[1:4].sum()) / (
        (c[:, 0] / c.sum(axis=1)) / WIDTHS[0]
    )
    delta = t_ratio - c_ratio
    lower, upper = np.quantile(delta, [0.025, 0.975])
    one_sided_p = (np.count_nonzero(delta <= 0) + 1) / (N_BOOTSTRAP + 1)
    return float(np.median(delta)), float(lower), float(upper), float(one_sided_p)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    events = pd.read_csv(INPUT, low_memory=False)
    events = events[events["sample_validation_id"].isin(SAMPLES)].copy()
    available = sorted(events["sample_validation_id"].dropna().unique().tolist())
    missing = [sample for sample in SAMPLES if sample not in available]
    if missing:
        raise RuntimeError(f"Missing required validation samples: {missing}")

    tagged = tag_microbands(events)
    counts = (
        tagged.groupby(["sample_validation_id", "primary_dataset", "jet_bin", "microband"], observed=False)
        .size()
        .reset_index(name="n")
    )
    rows = []
    vector_rows = []
    for sample in SAMPLES:
        trace = vector(counts, sample, trace=True)
        control = vector(counts, sample, trace=False)
        if trace.sum() == 0 or control.sum() == 0:
            raise RuntimeError(f"Zero trace/control vector for {sample}: trace={trace}, control={control}")
        chi2, p, dof, _expected = chi2_contingency(np.vstack([trace, control]), correction=False)
        shoulder_table = np.asarray([[trace[1:4].sum(), trace[0]], [control[1:4].sum(), control[0]]], dtype=float)
        shoulder_chi2, shoulder_p, _, _ = chi2_contingency(shoulder_table, correction=False)
        median, low, high, boot_p = bootstrap_delta(trace, control)
        rows.append(
            {
                "candidate_id": "observer_physical_qcd_suppressed_scan_best",
                "sample_validation_id": sample,
                "trace_total": int(trace.sum()),
                "control_total": int(control.sum()),
                "shape_chi2": float(chi2),
                "shape_dof": int(dof),
                "shape_p": float(p),
                "shape_Z": p_to_z(float(p)),
                "shoulder_chi2": float(shoulder_chi2),
                "shoulder_p": float(shoulder_p),
                "shoulder_Z": p_to_z(float(shoulder_p)),
                "bootstrap_shoulder_delta_median": median,
                "bootstrap_shoulder_delta_ci95_low": low,
                "bootstrap_shoulder_delta_ci95_high": high,
                "bootstrap_one_sided_p_delta_not_positive": boot_p,
                "bootstrap_one_sided_Z": p_to_z(boot_p),
                "passes_shape_Z5": bool(p_to_z(float(p)) >= 5),
                "passes_positive_bootstrap_ci": bool(low > 0),
            }
        )
        for band, trace_count, control_count in zip(MICROBANDS, trace, control):
            vector_rows.append(
                {
                    "sample_validation_id": sample,
                    "microband": band,
                    "trace_count": int(trace_count),
                    "control_count": int(control_count),
                }
            )

    summary = pd.DataFrame(rows)
    shape_stat, shape_fisher_p = combine_pvalues(summary["shape_p"].to_numpy(float), method="fisher")
    shoulder_stat, shoulder_fisher_p = combine_pvalues(summary["shoulder_p"].to_numpy(float), method="fisher")
    combined = pd.DataFrame(
        [
            {
                "candidate_id": "observer_physical_qcd_suppressed_scan_best",
                "validation_samples": ";".join(SAMPLES),
                "sample_count": len(SAMPLES),
                "fisher_shape_statistic": float(shape_stat),
                "fisher_shape_p": float(shape_fisher_p),
                "fisher_shape_Z": p_to_z(float(shape_fisher_p)),
                "fisher_shoulder_statistic": float(shoulder_stat),
                "fisher_shoulder_p": float(shoulder_fisher_p),
                "fisher_shoulder_Z": p_to_z(float(shoulder_fisher_p)),
                "min_sample_shape_Z": float(summary["shape_Z"].min()),
                "samples_shape_Z_ge_5": int((summary["shape_Z"] >= 5).sum()),
                "samples_positive_bootstrap_ci": int(summary["passes_positive_bootstrap_ci"].sum()),
            }
        ]
    )

    summary.to_csv(TABLES / "01_opq_three_sample_statistics.csv", index=False)
    pd.DataFrame(vector_rows).to_csv(TABLES / "02_opq_three_sample_microband_vectors.csv", index=False)
    combined.to_csv(TABLES / "03_opq_three_sample_combined_statistics.csv", index=False)
    counts.to_csv(TABLES / "04_opq_three_sample_raw_microband_counts.csv", index=False)

    report = f"""# OPQ Frozen Three-Sample Remote Statistical Robustness

## Purpose

This extends the frozen OPQ boundary-trace check to three remote real-CMS
validation samples:

- `Run2015D_remote_mht_aware_holdout`
- `Run2016H_remote_mht_aware`
- `Run2016G_remote_mht_aware_fresh`

The score was not retuned:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

The trace region is MET 0jet. Controls are JetHT and SingleMuon in the same
microband construction.

## Per-Sample Results

{summary.to_markdown(index=False, floatfmt='.6g')}

## Combined Result

{combined.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

The added Run2016G sample preserves the same sign of the MET-vs-control
boundary-trace effect, but it is weaker than the earlier Run2015D and Run2016H
held-out samples. This strengthens the repeatability argument because the
pattern now appears in a third real-CMS remote sample, but it also qualifies the
claim because the weakest individual sample is below 5 sigma in the asymptotic
shape screen.

This remains evidence for a repeatable N-Frame boundary-trace pattern, not
direct SUSY-particle detection and not yet an official CMS discovery
significance.
"""
    (REPORTS / "01_OPQ_FROZEN_THREE_SAMPLE_STATISTICAL_ROBUSTNESS.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_OPQ_FROZEN_THREE_SAMPLE_STATISTICAL_ROBUSTNESS.md")
    print(summary.to_string(index=False))
    print(combined.to_string(index=False))


if __name__ == "__main__":
    main()
