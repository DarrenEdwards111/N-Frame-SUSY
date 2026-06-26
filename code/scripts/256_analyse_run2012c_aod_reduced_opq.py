from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "outputs_run2012c_aod_reduced_validation"
OUT = ROOT / "outputs_run2012c_aod_reduced_opq_analysis"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
LEDGER = IN / "tables" / "01_run2012c_aod_reduced_extraction_ledger.csv"
PREV_THREE = ROOT / "outputs_opq_remote_three_sample_statistical_robustness" / "tables" / "01_opq_three_sample_statistics.csv"
MOD = SourceFileLoader("cross_sample", str(ROOT / "scripts" / "226_cross_sample_frozen_trace_validation.py")).load_module()

MICROBANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
WIDTHS = np.asarray([0.05, 0.02, 0.01, 0.01, 0.01], dtype=float)


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
    return pd.concat(frames, ignore_index=True)


def vector(counts: pd.DataFrame, trace: bool) -> np.ndarray:
    if trace:
        hit = counts[counts["primary_dataset"].eq("MET") & counts["jet_bin"].astype(str).eq("0jet")]
    else:
        hit = counts[counts["primary_dataset"].isin(["JetHT", "SingleMuon"])]
    return np.asarray([hit.loc[hit["microband"].eq(band), "n"].sum() for band in MICROBANDS], dtype=int)


def density_ratio(vec: np.ndarray) -> tuple[float, float]:
    shoulder = ((vec[1:4].sum() / vec.sum()) / WIDTHS[1:4].sum()) / ((vec[0] / vec.sum()) / WIDTHS[0])
    q99 = ((vec[4] / vec.sum()) / WIDTHS[4]) / ((vec[1:4].sum() / vec.sum()) / WIDTHS[1:4].sum())
    return float(shoulder), float(q99)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(LEDGER)
    frames = []
    for row in ledger.itertuples(index=False):
        if row.status != "completed":
            continue
        frame = pd.read_csv(row.output_path, low_memory=False)
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(TABLES / "01_run2012c_aod_reduced_raw_combined.csv", index=False)
    quality = raw[MOD.strict_quality(raw)].copy()
    scored = []
    for _dataset, group in quality.groupby("primary_dataset", sort=False):
        scored.append(MOD.add_components_one_dataset(group))
    events = pd.concat(scored, ignore_index=True)
    events["missing_for_decile"] = events["missing_proxy_pt"]
    events = MOD.add_missing_deciles(events)
    events["score_opq"] = opq_score(events)
    events.to_csv(TABLES / "02_run2012c_aod_reduced_scored_events.csv", index=False)

    tagged = tag_microbands(events)
    counts = (
        tagged.groupby(["primary_dataset", "jet_bin", "microband"], observed=False)
        .size()
        .reset_index(name="n")
    )
    counts.to_csv(TABLES / "03_run2012c_aod_reduced_microband_counts.csv", index=False)

    trace = vector(counts, trace=True)
    control = vector(counts, trace=False)
    chi2, p, dof, _expected = chi2_contingency(np.vstack([trace, control]), correction=False)
    shoulder_table = np.asarray([[trace[1:4].sum(), trace[0]], [control[1:4].sum(), control[0]]], dtype=float)
    shoulder_chi2, shoulder_p, _, _ = chi2_contingency(shoulder_table, correction=False)
    trace_shoulder, trace_q99 = density_ratio(trace)
    control_shoulder, control_q99 = density_ratio(control)
    result = pd.DataFrame(
        [
            {
                "sample_validation_id": "Run2012C_AOD_reduced_cross_era",
                "feature_scope": "reduced_AOD_OPQ",
                "trace_total": int(trace.sum()),
                "control_total": int(control.sum()),
                "shape_chi2": float(chi2),
                "shape_dof": int(dof),
                "shape_p": float(p),
                "shape_Z": p_to_z(float(p)),
                "shoulder_chi2": float(shoulder_chi2),
                "shoulder_p": float(shoulder_p),
                "shoulder_Z": p_to_z(float(shoulder_p)),
                "trace_95_99_over_90_95_density_ratio": trace_shoulder,
                "control_95_99_over_90_95_density_ratio": control_shoulder,
                "trace_99_over_95_99_density_ratio": trace_q99,
                "control_99_over_95_99_density_ratio": control_q99,
                "shoulder_above_control": bool(trace_shoulder > control_shoulder),
                "not_full_miniaod_equivalent": True,
            }
        ]
    )
    result.to_csv(TABLES / "04_run2012c_aod_reduced_opq_statistics.csv", index=False)

    combined_rows = []
    if PREV_THREE.exists():
        prev = pd.read_csv(PREV_THREE)
        pvals = [*prev["shape_p"].astype(float).tolist(), float(result["shape_p"].iloc[0])]
        stat, comb_p = combine_pvalues(np.asarray(pvals), method="fisher")
        combined_rows.append(
            {
                "combination": "three_miniaod_like_samples_plus_run2012c_reduced_aod",
                "sample_count": len(pvals),
                "fisher_statistic": float(stat),
                "fisher_p": float(comb_p),
                "fisher_Z": p_to_z(float(comb_p)),
                "reduced_aod_included_as_stress_only": True,
            }
        )
    combined = pd.DataFrame(combined_rows)
    combined.to_csv(TABLES / "05_run2012c_added_cross_era_combination_stress.csv", index=False)

    report = f"""# Run2012C Reduced AOD OPQ Cross-Era Validation

## Purpose

This tests the frozen OPQ boundary-trace score on a genuinely older CMS era:
Run2012C AOD. This is a reduced feature-equivalent validation, not a MiniAOD
equivalent validation. It uses AOD-level PF MET, AK5 PF jets, muons, electrons,
primary vertices, particle-flow candidate count, and trigger flags.

The frozen score remains:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

## Extraction Ledger

{ledger.to_markdown(index=False)}

## Run2012C OPQ Result

{result.to_markdown(index=False, floatfmt='.6g')}

## Optional Cross-Era Combination Stress

{combined.to_markdown(index=False, floatfmt='.6g') if not combined.empty else '_Previous three-sample table unavailable._'}

## Interpretation

This is a useful cross-era stress test because it uses real 2012 CMS collision
data and the same frozen OPQ formula. It is not discovery-grade by itself
because the feature space is reduced relative to 2015/2016 MiniAOD/MiniAOD-like
validation: b-tag and secondary-vertex structure are not yet fully mapped, and
the 2012 detector/reconstruction era differs materially from UL2016 MiniAOD.

The important question is whether the MET 0jet trace shape remains separated
from JetHT/SingleMuon controls. A positive result strengthens the boundary-trace
story; a weak or null result means the current OPQ trace is detector-era or
feature-definition dependent.
"""
    (REPORTS / "01_RUN2012C_AOD_REDUCED_OPQ_CROSS_ERA_VALIDATION.md").write_text(report, encoding="utf-8")
    print(result.to_string(index=False))
    if not combined.empty:
        print(combined.to_string(index=False))
    print(REPORTS / "01_RUN2012C_AOD_REDUCED_OPQ_CROSS_ERA_VALIDATION.md")


if __name__ == "__main__":
    main()
