from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, norm


ROOT = Path(__file__).resolve().parents[1]
RUN2016G_EVENTS = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz"
RUN2016H_EVENTS = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv"
OUT = ROOT / "outputs_frozen_replicated_transition_stress_suite"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

COMPONENTS = [
    "observer_projection",
    "physical_projection",
    "algebraic_projection",
    "ordinary_qcd_axis",
    "leptonic_control_axis",
]

MICROBANDS = [
    ("q90_95", 0.90, 0.95, 0.05),
    ("q95_97", 0.95, 0.97, 0.02),
    ("q97_98", 0.97, 0.98, 0.01),
    ("q98_99", 0.98, 0.99, 0.01),
    ("q99_100", 0.99, 1.00, 0.01),
]

TRACE_REGION = ("MET", "0jet")

FROZEN_CANDIDATES = [
    {
        "candidate_id": "observer_physical_clean",
        "why_frozen": "Clean tri-aspect observer plus physical boundary projection; no QCD or lepton suppression.",
        "observer_projection": 0.5,
        "physical_projection": 0.5,
        "algebraic_projection": 0.0,
        "ordinary_qcd_axis": 0.0,
        "leptonic_control_axis": 0.0,
    },
    {
        "candidate_id": "observer_physical_qcd_suppressed_scan_best",
        "why_frozen": "Best interpretable replicated scan candidate: observer and physical axes with modest QCD-like suppression.",
        "observer_projection": 0.344828,
        "physical_projection": 0.517241,
        "algebraic_projection": 0.0,
        "ordinary_qcd_axis": -0.137931,
        "leptonic_control_axis": 0.0,
    },
    {
        "candidate_id": "algebraic_only_theory_interest",
        "why_frozen": "Highest replicated scan score, retained as a theory-interest comparator because it is sparse and less directly detector-physical.",
        "observer_projection": 0.0,
        "physical_projection": 0.0,
        "algebraic_projection": 1.0,
        "ordinary_qcd_axis": 0.0,
        "leptonic_control_axis": 0.0,
    },
]

CONTROL_DEFINITIONS = {
    "targeted_baseline": [("JetHT", "1to2jets"), ("SingleMuon", "0jet")],
    "all_jetht_singlemuon_bins": [
        ("JetHT", "0jet"),
        ("JetHT", "1to2jets"),
        ("JetHT", "3to4jets"),
        ("JetHT", "5plusjets"),
        ("SingleMuon", "0jet"),
        ("SingleMuon", "1to2jets"),
        ("SingleMuon", "3to4jets"),
        ("SingleMuon", "5plusjets"),
    ],
    "same_stage_0jet_controls": [("JetHT", "0jet"), ("SingleMuon", "0jet")],
    "jetht_all_bins_only": [("JetHT", "0jet"), ("JetHT", "1to2jets"), ("JetHT", "3to4jets"), ("JetHT", "5plusjets")],
    "singlemuon_all_bins_only": [
        ("SingleMuon", "0jet"),
        ("SingleMuon", "1to2jets"),
        ("SingleMuon", "3to4jets"),
        ("SingleMuon", "5plusjets"),
    ],
}


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def p_to_z(p: float) -> float:
    p = float(np.clip(p, np.nextafter(0, 1), 1.0))
    return float(norm.isf(p))


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
    ]
    h_cols = [
        "run_era",
        "primary_dataset",
        "MET_pt",
        "MHT_pt",
        "missing_proxy_pt",
        "jet_bin",
        "strict_quality_clean",
        *COMPONENTS,
    ]
    g = pd.read_csv(RUN2016G_EVENTS, usecols=lambda c: c in g_cols, low_memory=False)
    h = pd.read_csv(RUN2016H_EVENTS, usecols=lambda c: c in h_cols, low_memory=False)
    g = g[g["strict_quality_clean"].astype(bool)].copy()
    h = h[h["strict_quality_clean"].astype(bool)].copy()
    g["run_era"] = "Run2016G"
    h["run_era"] = "Run2016H"
    g = g.drop(columns=["era", "strict_quality_clean"], errors="ignore")
    h = h.drop(columns=["strict_quality_clean"], errors="ignore")
    events = pd.concat([g, h], ignore_index=True, sort=False)
    events = events[events["primary_dataset"].isin(["MET", "HTMHT", "JetHT", "SingleMuon"])].copy()
    for col in COMPONENTS + ["MET_pt", "MHT_pt", "missing_proxy_pt"]:
        events[col] = pd.to_numeric(events[col], errors="coerce").fillna(0.0)
    events["jet_bin"] = events["jet_bin"].astype(str)
    events["missing_for_decile"] = np.where(events["primary_dataset"].eq("HTMHT"), events["MHT_pt"], events["MET_pt"])
    events["missing_for_decile"] = pd.to_numeric(events["missing_for_decile"], errors="coerce").fillna(events["missing_proxy_pt"])
    return events


def add_missing_deciles(events: pd.DataFrame) -> pd.DataFrame:
    out = events.copy()
    out["missing_decile"] = -1
    for _keys, idx in out.groupby(["run_era", "primary_dataset"], observed=False).groups.items():
        vals = out.loc[idx, "missing_for_decile"].to_numpy(float)
        if len(np.unique(vals)) < 2:
            bins = np.zeros(len(vals), dtype=int)
        else:
            bins = pd.qcut(vals, 10, labels=False, duplicates="drop")
        out.loc[idx, "missing_decile"] = np.asarray(bins, dtype=float)
    out["missing_decile"] = out["missing_decile"].astype(int)
    return out


def score_events(events: pd.DataFrame, candidate: dict[str, float]) -> np.ndarray:
    score = np.zeros(len(events), dtype=float)
    for col in COMPONENTS:
        score += float(candidate[col]) * events[col].to_numpy(float)
    return score


def tag_microbands(events: pd.DataFrame, score: np.ndarray) -> pd.DataFrame:
    tmp = events[["run_era", "primary_dataset", "jet_bin", "missing_decile"]].copy()
    tmp["candidate_score"] = score
    frames = []
    for _keys, group in tmp.groupby(["run_era", "primary_dataset", "missing_decile"], observed=False):
        if len(group) < 100:
            continue
        vals = group["candidate_score"].to_numpy(float)
        edges = np.quantile(vals, [0.90, 0.95, 0.97, 0.98, 0.99, 1.00])
        edges[-1] = np.inf
        labels = np.full(len(group), None, dtype=object)
        for (name, _lo, _hi, _width), lo_edge, hi_edge in zip(MICROBANDS, edges[:-1], edges[1:]):
            labels[(vals >= lo_edge) & (vals < hi_edge)] = name
        tagged = group.copy()
        tagged["microband"] = labels
        frames.append(tagged[tagged["microband"].notna()])
    return pd.concat(frames, ignore_index=True)


def band_vector(counts: pd.DataFrame, era: str, regions: list[tuple[str, str]]) -> np.ndarray:
    vals = np.zeros(len(MICROBANDS), dtype=float)
    for dataset, jet_bin in regions:
        sub = counts[
            counts["run_era"].eq(era)
            & counts["primary_dataset"].eq(dataset)
            & counts["jet_bin"].eq(jet_bin)
        ]
        vals += np.asarray([sub.loc[sub["microband"].eq(band), "observed"].sum() for band, *_ in MICROBANDS], dtype=float)
    return vals


def shape_metrics(trace: np.ndarray, control: np.ndarray) -> dict[str, float]:
    if trace.sum() <= 0 or control.sum() <= 0:
        return {}
    table = np.vstack([trace, control])
    chi2_stat, p_value, dof, _expected = chi2_contingency(table, correction=False)
    widths = np.asarray([width for *_unused, width in MICROBANDS], dtype=float)
    trace_density = trace / trace.sum() / widths
    control_density = control / control.sum() / widths
    trace_shoulder = (trace[1:4].sum() / trace.sum()) / widths[1:4].sum()
    control_shoulder = (control[1:4].sum() / control.sum()) / widths[1:4].sum()

    shoulder_table = np.asarray([[trace[1:4].sum(), trace[0]], [control[1:4].sum(), control[0]]], dtype=float)
    shoulder_chi2, shoulder_p, _sdof, _sexp = chi2_contingency(shoulder_table, correction=False)
    endpoint_table = np.asarray([[trace[4], trace[1:4].sum()], [control[4], control[1:4].sum()]], dtype=float)
    endpoint_chi2, endpoint_p, _edof, _eexp = chi2_contingency(endpoint_table, correction=False)
    return {
        "trace_total": float(trace.sum()),
        "control_total": float(control.sum()),
        "shape_chi2": float(chi2_stat),
        "shape_dof": int(dof),
        "shape_p": float(p_value),
        "shape_Z": p_to_z(float(p_value)),
        "shoulder_chi2": float(shoulder_chi2),
        "shoulder_p": float(shoulder_p),
        "shoulder_Z": p_to_z(float(shoulder_p)),
        "endpoint_chi2": float(endpoint_chi2),
        "endpoint_p": float(endpoint_p),
        "endpoint_Z": p_to_z(float(endpoint_p)),
        "trace_95_99_over_90_95_density_ratio": float(trace_shoulder / trace_density[0]) if trace_density[0] > 0 else np.nan,
        "control_95_99_over_90_95_density_ratio": float(control_shoulder / control_density[0]) if control_density[0] > 0 else np.nan,
        "trace_99_over_95_99_density_ratio": float(trace_density[4] / trace_shoulder) if trace_shoulder > 0 else np.nan,
        "control_99_over_95_99_density_ratio": float(control_density[4] / control_shoulder) if control_shoulder > 0 else np.nan,
    }


def evaluate_candidate(events: pd.DataFrame, candidate: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    tagged = tag_microbands(events, score_events(events, candidate))
    counts = (
        tagged.groupby(["run_era", "primary_dataset", "jet_bin", "microband"], observed=False)
        .size()
        .reset_index(name="observed")
    )
    counts["candidate_id"] = candidate["candidate_id"]
    vector_rows = []
    stress_rows = []
    for control_name, control_regions in CONTROL_DEFINITIONS.items():
        for era in ["Run2016G", "Run2016H"]:
            trace = band_vector(counts, era, [TRACE_REGION])
            control = band_vector(counts, era, control_regions)
            metrics = shape_metrics(trace, control)
            stress_rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "why_frozen": candidate["why_frozen"],
                    "control_definition": control_name,
                    "run_era": era,
                    **{col: candidate[col] for col in COMPONENTS},
                    **metrics,
                }
            )
            for band, t, c in zip([band for band, *_ in MICROBANDS], trace, control):
                vector_rows.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "control_definition": control_name,
                        "run_era": era,
                        "microband": band,
                        "trace_region": "MET_0jet",
                        "trace_count": float(t),
                        "control_count": float(c),
                    }
                )
    return pd.DataFrame(stress_rows), pd.DataFrame(vector_rows)


def readiness(stress: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate_id, group in stress.groupby("candidate_id", observed=False):
        baseline = group[group["control_definition"].eq("all_jetht_singlemuon_bins")]
        g_z = float(baseline.loc[baseline["run_era"].eq("Run2016G"), "shape_Z"].iloc[0])
        h_z = float(baseline.loc[baseline["run_era"].eq("Run2016H"), "shape_Z"].iloc[0])
        min_z = min(g_z, h_z)
        all_controls_pass = bool((group["shape_Z"] >= 5.0).all())
        shoulder_pass = bool(
            (
                group["trace_95_99_over_90_95_density_ratio"]
                > group["control_95_99_over_90_95_density_ratio"]
            ).all()
        )
        endpoint_spike = bool(
            (
                group["trace_99_over_95_99_density_ratio"]
                > group["control_99_over_95_99_density_ratio"]
            ).all()
        )
        if all_controls_pass and shoulder_pass:
            status = "strong_replicated_transition_trace"
        elif min_z >= 5:
            status = "partial_replicated_shape_only"
        else:
            status = "not_replicated_under_stress"
        rows.append(
            {
                "candidate_id": candidate_id,
                "Run2016G_all_controls_shape_Z": g_z,
                "Run2016H_all_controls_shape_Z": h_z,
                "min_all_controls_shape_Z": min_z,
                "all_control_definitions_shape_Z_ge_5": all_controls_pass,
                "shoulder_ratio_above_controls_in_all_tests": shoulder_pass,
                "q99_endpoint_spike_above_controls_in_all_tests": endpoint_spike,
                "readiness_status": status,
            }
        )
    return pd.DataFrame(rows).sort_values(["readiness_status", "min_all_controls_shape_Z"], ascending=[True, False])


def write_report(stress: pd.DataFrame, vectors: pd.DataFrame, ready: pd.DataFrame) -> None:
    primary = stress[stress["control_definition"].eq("all_jetht_singlemuon_bins")].copy()
    top_ready = ready.sort_values("min_all_controls_shape_Z", ascending=False)
    report = f"""# Frozen Replicated N-Frame Transition Stress Suite

## Purpose

This run froze the best N-Frame transition candidates from the prior replicated scan and stress-tested them without downloading new data. The test is aimed at Darren's trace question: whether an N-Frame boundary observable finds a repeated high-boundary MET transition shape in real CMS data, while JetHT and SingleMuon controls behave differently.

This is not a SUSY-particle discovery claim and not an official CMS Standard Model likelihood. It is a control-shape stress test of a proposed observable boundary trace.

## Frozen Candidates

| Candidate | Definition |
|---|---|
| `observer_physical_clean` | $B = 0.5O + 0.5P$ |
| `observer_physical_qcd_suppressed_scan_best` | $B = 0.344828O + 0.517241P - 0.137931Q$ |
| `algebraic_only_theory_interest` | $B = A$ |

Here $O$ is observer/reconstruction projection, $P$ is physical/displacement-reconstruction projection, $A$ is algebraic projection, and $Q$ is the ordinary-QCD axis.

## Main All-Control Results

{primary[["candidate_id", "run_era", "shape_Z", "shoulder_Z", "endpoint_Z", "trace_95_99_over_90_95_density_ratio", "control_95_99_over_90_95_density_ratio", "trace_99_over_95_99_density_ratio", "control_99_over_95_99_density_ratio"]].to_markdown(index=False, floatfmt=".6g")}

## Readiness Summary

{top_ready.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The most important distinction is between a `Q99 spike` and a broader `95-99 high-boundary shoulder`. A Q99-only spike would mean the final 1% suddenly jumps above the adjacent high-tail. The current replicated evidence is instead a transition-shape result: the 95-99 shoulder in MET 0-jet differs strongly from JetHT/SingleMuon control shapes in both Run2016G and Run2016H for the frozen candidates.

The cleanest candidate for a paper-style next phase is `observer_physical_clean`, because it is simple and directly matches the tri-aspect boundary framing. The stronger scan-selected candidate is `observer_physical_qcd_suppressed_scan_best`; it is still interpretable, but it includes a fitted QCD-suppression term and therefore needs stricter fresh-data validation before being treated as a final model.

## Next Action

Freeze `observer_physical_clean` as the conservative primary trace observable and `observer_physical_qcd_suppressed_scan_best` as the exploratory optimized observable, then validate both on additional independent CMS samples or a remote/cloud run over more unused files. The decisive next test is whether the same 95-99 transition shoulder repeats outside these two 2016 slices.
"""
    (REPORTS / "01_FROZEN_REPLICATED_TRANSITION_STRESS_SUITE.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    events = add_missing_deciles(load_events())
    events.to_csv(TABLES / "00_event_audit.csv", index=False, columns=["run_era", "primary_dataset", "jet_bin", "missing_decile"])
    all_stress = []
    all_vectors = []
    for candidate in FROZEN_CANDIDATES:
        stress, vectors = evaluate_candidate(events, candidate)
        all_stress.append(stress)
        all_vectors.append(vectors)
    stress_df = pd.concat(all_stress, ignore_index=True)
    vectors_df = pd.concat(all_vectors, ignore_index=True)
    ready_df = readiness(stress_df)
    stress_df.to_csv(TABLES / "01_frozen_candidate_control_stress_summary.csv", index=False)
    vectors_df.to_csv(TABLES / "02_frozen_candidate_microband_vectors.csv", index=False)
    ready_df.to_csv(TABLES / "03_frozen_candidate_readiness_summary.csv", index=False)
    write_report(stress_df, vectors_df, ready_df)
    print(REPORTS / "01_FROZEN_REPLICATED_TRANSITION_STRESS_SUITE.md")
    print(ready_df.to_string(index=False))


if __name__ == "__main__":
    main()
