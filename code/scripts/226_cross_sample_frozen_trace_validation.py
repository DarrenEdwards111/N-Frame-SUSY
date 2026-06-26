from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_cross_sample_frozen_trace_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SAMPLES = [
    {
        "sample_id": "Run2016G_reference",
        "path": ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz",
        "component_mode": "existing",
        "era_label": "Run2016G",
    },
    {
        "sample_id": "Run2016H_fresh_mht",
        "path": ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv",
        "component_mode": "existing",
        "era_label": "Run2016H",
    },
    {
        "sample_id": "Run2016H_expanded_miniaod",
        "path": ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_event_features_combined.csv",
        "component_mode": "recompute",
        "era_label": "Run2016H_expanded",
    },
    {
        "sample_id": "Run2015D_pilot",
        "path": ROOT / "outputs_run2015d_frozen_q99_pilot" / "sources" / "run2015d_all_selected_real_events_scored.csv",
        "component_mode": "recompute",
        "era_label": "Run2015D",
    },
]

COMPONENTS = [
    "observer_projection",
    "physical_projection",
    "algebraic_projection",
    "ordinary_qcd_axis",
    "leptonic_control_axis",
]

FROZEN_CANDIDATES = [
    {
        "candidate_id": "observer_physical_clean",
        "observer_projection": 0.5,
        "physical_projection": 0.5,
        "algebraic_projection": 0.0,
        "ordinary_qcd_axis": 0.0,
        "leptonic_control_axis": 0.0,
    },
    {
        "candidate_id": "observer_physical_qcd_suppressed_scan_best",
        "observer_projection": 0.344828,
        "physical_projection": 0.517241,
        "algebraic_projection": 0.0,
        "ordinary_qcd_axis": -0.137931,
        "leptonic_control_axis": 0.0,
    },
]

MICROBANDS = [
    ("q90_95", 0.90, 0.95, 0.05),
    ("q95_97", 0.95, 0.97, 0.02),
    ("q97_98", 0.97, 0.98, 0.01),
    ("q98_99", 0.98, 0.99, 0.01),
    ("q99_100", 0.99, 1.00, 0.01),
]

JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]
TRACE_REGION = ("MET", "0jet")
CONTROL_REGIONS = [(dataset, jet_bin) for dataset in ["JetHT", "SingleMuon"] for jet_bin in JET_BINS]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def numeric(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def zscore(values: pd.Series, ref_mask: pd.Series | np.ndarray | None = None) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    ref = x if ref_mask is None else x.loc[ref_mask]
    mean = float(ref.mean()) if len(ref) else 0.0
    sd = float(ref.std(ddof=0)) if len(ref) else 1.0
    if not np.isfinite(sd) or sd <= 1e-9:
        sd = 1.0
    return (x - mean) / sd


def jet_bin(n_jets: pd.Series) -> pd.Series:
    n = pd.to_numeric(n_jets, errors="coerce").fillna(0).astype(float)
    bins = np.select(
        [n <= 0, (n >= 1) & (n <= 2), (n >= 3) & (n <= 4), n >= 5],
        ["0jet", "1to2jets", "3to4jets", "5plusjets"],
        default="unknown",
    )
    return pd.Series(pd.Categorical(bins, categories=JET_BINS), index=n.index)


def strict_quality(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for col in QUALITY_FILTERS:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            mask &= vals.eq(1)
    return mask


def add_components_one_dataset(group: pd.DataFrame) -> pd.DataFrame:
    g = group.copy()
    dataset = str(g["primary_dataset"].iloc[0])
    g["MET_pt"] = numeric(g, "MET_pt")
    g["HT"] = numeric(g, "HT")
    g["N_jets_30"] = numeric(g, "N_jets_30", np.nan).fillna(numeric(g, "N_jets", 0.0))
    g["N_btags_medium"] = numeric(g, "N_btags_medium")
    g["N_muons"] = numeric(g, "N_muons")
    g["N_electrons"] = numeric(g, "N_electrons")
    g["secondary_vertex_count"] = numeric(g, "secondary_vertex_count")
    g["packed_candidate_count"] = numeric(g, "packed_candidate_count")
    g["missing_proxy_kind"] = "MHT_pt" if dataset == "HTMHT" and "MHT_pt" in g.columns else "MET_pt"
    g["missing_proxy_pt"] = numeric(g, "MHT_pt" if g["missing_proxy_kind"].iloc[0] == "MHT_pt" else "MET_pt")
    g["log1p_missing_proxy"] = np.log1p(np.clip(g["missing_proxy_pt"], 0, None))
    g["log1p_MET_pt"] = np.log1p(np.clip(g["MET_pt"], 0, None))
    g["log1p_HT"] = np.log1p(np.clip(g["HT"], 0, None))
    g["MHT_over_HT"] = numeric(g, "MHT_over_HT")
    g["MET_minus_MHT"] = numeric(g, "MET_minus_MHT")
    g["jet_bin"] = jet_bin(g["N_jets_30"])

    lower_mask = g["log1p_missing_proxy"] <= g["log1p_missing_proxy"].quantile(0.95)
    x_cols = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
    x = g.loc[lower_mask, x_cols].to_numpy(float)
    y = g.loc[lower_mask, "log1p_missing_proxy"].to_numpy(float)
    if len(g.loc[lower_mask]) >= len(x_cols) + 5:
        design = np.column_stack([np.ones(len(x)), x])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        pred = np.column_stack([np.ones(len(g)), g[x_cols].to_numpy(float)]) @ beta
    else:
        pred = np.full(len(g), float(g.loc[lower_mask, "log1p_missing_proxy"].mean()))
    g["missing_visible_residual_raw"] = g["log1p_missing_proxy"].to_numpy(float) - pred
    g["observer_projection"] = zscore(g["missing_visible_residual_raw"], lower_mask)

    disp_raw = np.log1p(np.clip(g["secondary_vertex_count"], 0, None)) + 0.05 * zscore(
        np.log1p(np.clip(g["packed_candidate_count"], 0, None))
    )
    g["physical_projection"] = (
        0.65 * zscore(g["log1p_missing_proxy"], lower_mask)
        + 0.20 * zscore(g["log1p_HT"], lower_mask)
        + 0.15 * zscore(disp_raw, lower_mask)
    )

    pca_cols = [
        "log1p_missing_proxy",
        "log1p_HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "MHT_over_HT",
        "MET_minus_MHT",
    ]
    x_all = g[pca_cols].to_numpy(float)
    ref = g.loc[lower_mask, pca_cols].to_numpy(float)
    mean = ref.mean(axis=0)
    sd = np.where(ref.std(axis=0) <= 1e-9, 1.0, ref.std(axis=0))
    z_ref = (ref - mean) / sd
    z_all = (x_all - mean) / sd
    if len(ref) >= len(pca_cols) + 5:
        _, _, vt = np.linalg.svd(z_ref, full_matrices=False)
        basis = vt[: min(3, vt.shape[0])].T
        recon = (z_all @ basis) @ basis.T
        resid = np.sqrt(np.mean((z_all - recon) ** 2, axis=1))
    else:
        resid = np.zeros(len(g), dtype=float)
    g["algebraic_projection"] = zscore(pd.Series(resid, index=g.index), lower_mask)
    g["ordinary_qcd_axis"] = 0.70 * zscore(g["N_jets_30"], lower_mask) + 0.30 * zscore(g["N_btags_medium"], lower_mask)
    g["leptonic_control_axis"] = -zscore(g["N_muons"] + g["N_electrons"], lower_mask)
    return g


def load_sample(config: dict[str, object]) -> pd.DataFrame:
    path = Path(config["path"])
    usecols = None
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    if "run_era" not in df.columns:
        df["run_era"] = str(config["era_label"])
    df["sample_validation_id"] = str(config["sample_id"])
    df = df[df["primary_dataset"].isin(["MET", "HTMHT", "JetHT", "SingleMuon"])].copy()
    df = df[strict_quality(df)].copy()
    if str(config["component_mode"]) == "existing" and set(COMPONENTS).issubset(df.columns):
        for col in COMPONENTS:
            df[col] = numeric(df, col)
        if "jet_bin" not in df.columns:
            df["jet_bin"] = jet_bin(numeric(df, "N_jets_30", np.nan).fillna(numeric(df, "N_jets", 0.0)))
        df["missing_for_decile"] = numeric(df, "MET_pt")
        return df
    frames = [add_components_one_dataset(group) for _, group in df.groupby("primary_dataset", sort=False)]
    out = pd.concat(frames, ignore_index=True)
    out["missing_for_decile"] = out["missing_proxy_pt"]
    return out


def p_to_z(p_value: float) -> float:
    return float(norm.isf(float(np.clip(p_value, np.nextafter(0, 1), 1.0))))


def add_missing_deciles(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["missing_decile"] = -1
    for _keys, idx in out.groupby(["sample_validation_id", "primary_dataset"], observed=False).groups.items():
        vals = pd.to_numeric(out.loc[idx, "missing_for_decile"], errors="coerce").fillna(0.0).to_numpy(float)
        if len(vals) < 10 or len(np.unique(vals)) < 2:
            bins = np.zeros(len(vals), dtype=int)
        else:
            bins = pd.qcut(vals, 10, labels=False, duplicates="drop")
        out.loc[idx, "missing_decile"] = np.asarray(bins, dtype=float)
    out["missing_decile"] = out["missing_decile"].astype(int)
    return out


def score_candidate(df: pd.DataFrame, candidate: dict[str, float]) -> np.ndarray:
    score = np.zeros(len(df), dtype=float)
    for col in COMPONENTS:
        score += float(candidate[col]) * pd.to_numeric(df[col], errors="coerce").fillna(0.0).to_numpy(float)
    return score


def tag_microbands(df: pd.DataFrame, score: np.ndarray) -> pd.DataFrame:
    tmp = df[["sample_validation_id", "run_era", "primary_dataset", "jet_bin", "missing_decile"]].copy()
    tmp["score"] = score
    frames = []
    for _keys, group in tmp.groupby(["sample_validation_id", "primary_dataset", "missing_decile"], observed=False):
        if len(group) < 100:
            continue
        vals = group["score"].to_numpy(float)
        edges = np.quantile(vals, [0.90, 0.95, 0.97, 0.98, 0.99, 1.00])
        edges[-1] = np.inf
        labels = np.full(len(group), None, dtype=object)
        for (name, _lo, _hi, _width), lo_edge, hi_edge in zip(MICROBANDS, edges[:-1], edges[1:]):
            labels[(vals >= lo_edge) & (vals < hi_edge)] = name
        g = group.copy()
        g["microband"] = labels
        frames.append(g[g["microband"].notna()])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def vector(counts: pd.DataFrame, sample_id: str, regions: list[tuple[str, str]]) -> np.ndarray:
    vals = np.zeros(len(MICROBANDS), dtype=float)
    for dataset, jet in regions:
        sub = counts[
            counts["sample_validation_id"].eq(sample_id)
            & counts["primary_dataset"].eq(dataset)
            & counts["jet_bin"].astype(str).eq(jet)
        ]
        vals += np.asarray([sub.loc[sub["microband"].eq(band), "observed"].sum() for band, *_ in MICROBANDS], dtype=float)
    return vals


def shape_metrics(trace: np.ndarray, control: np.ndarray) -> dict[str, float]:
    if trace.sum() <= 0 or control.sum() <= 0:
        return {
            "shape_Z": np.nan,
            "shape_p": np.nan,
            "trace_total": float(trace.sum()),
            "control_total": float(control.sum()),
        }
    chi2_stat, p_value, dof, _ = chi2_contingency(np.vstack([trace, control]), correction=False)
    widths = np.asarray([width for *_unused, width in MICROBANDS], dtype=float)
    trace_density = trace / trace.sum() / widths
    control_density = control / control.sum() / widths
    trace_shoulder = (trace[1:4].sum() / trace.sum()) / widths[1:4].sum()
    control_shoulder = (control[1:4].sum() / control.sum()) / widths[1:4].sum()
    shoulder_table = np.asarray([[trace[1:4].sum(), trace[0]], [control[1:4].sum(), control[0]]], dtype=float)
    shoulder_chi2, shoulder_p, _sdof, _sexp = chi2_contingency(shoulder_table, correction=False)
    return {
        "trace_total": float(trace.sum()),
        "control_total": float(control.sum()),
        "shape_chi2": float(chi2_stat),
        "shape_dof": int(dof),
        "shape_p": float(p_value),
        "shape_Z": p_to_z(float(p_value)),
        "shoulder_p": float(shoulder_p),
        "shoulder_Z": p_to_z(float(shoulder_p)),
        "trace_95_99_over_90_95_density_ratio": float(trace_shoulder / trace_density[0]) if trace_density[0] > 0 else np.nan,
        "control_95_99_over_90_95_density_ratio": float(control_shoulder / control_density[0]) if control_density[0] > 0 else np.nan,
        "trace_99_over_95_99_density_ratio": float(trace_density[4] / trace_shoulder) if trace_shoulder > 0 else np.nan,
        "control_99_over_95_99_density_ratio": float(control_density[4] / control_shoulder) if control_shoulder > 0 else np.nan,
    }


def evaluate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    audit = (
        df.groupby(["sample_validation_id", "primary_dataset", "jet_bin"], observed=False)
        .size()
        .reset_index(name="events_after_quality")
    )
    rows = []
    vectors = []
    for candidate in FROZEN_CANDIDATES:
        tagged = tag_microbands(df, score_candidate(df, candidate))
        counts = (
            tagged.groupby(["sample_validation_id", "run_era", "primary_dataset", "jet_bin", "microband"], observed=False)
            .size()
            .reset_index(name="observed")
        )
        counts["candidate_id"] = candidate["candidate_id"]
        for sample_id in sorted(df["sample_validation_id"].unique()):
            trace = vector(counts, sample_id, [TRACE_REGION])
            control = vector(counts, sample_id, CONTROL_REGIONS)
            metrics = shape_metrics(trace, control)
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "sample_validation_id": sample_id,
                    **{col: candidate[col] for col in COMPONENTS},
                    **metrics,
                    "shoulder_above_control": bool(
                        metrics.get("trace_95_99_over_90_95_density_ratio", -np.inf)
                        > metrics.get("control_95_99_over_90_95_density_ratio", np.inf)
                    ),
                }
            )
            for band, t, c in zip([band for band, *_ in MICROBANDS], trace, control):
                vectors.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "sample_validation_id": sample_id,
                        "microband": band,
                        "trace_count": float(t),
                        "control_count": float(c),
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(vectors), audit


def combined_readiness(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate_id, group in summary.groupby("candidate_id", observed=False):
        pvals = group["shape_p"].dropna().to_numpy(float)
        if len(pvals):
            _stat, combined_p = combine_pvalues(pvals, method="fisher")
            combined_z = p_to_z(float(combined_p))
        else:
            combined_p = np.nan
            combined_z = np.nan
        rows.append(
            {
                "candidate_id": candidate_id,
                "samples_tested": int(len(group)),
                "samples_shape_Z_ge_5": int((group["shape_Z"] >= 5).sum()),
                "samples_shoulder_above_control": int(group["shoulder_above_control"].sum()),
                "min_shape_Z": float(group["shape_Z"].min(skipna=True)),
                "median_shape_Z": float(group["shape_Z"].median(skipna=True)),
                "fisher_combined_shape_p": float(combined_p),
                "fisher_combined_shape_Z": float(combined_z),
                "strict_replicated_pass_all_samples": bool((group["shape_Z"] >= 5).all() and group["shoulder_above_control"].all()),
            }
        )
    return pd.DataFrame(rows).sort_values("fisher_combined_shape_Z", ascending=False)


def write_report(summary: pd.DataFrame, ready: pd.DataFrame, audit: pd.DataFrame) -> None:
    report = f"""# Cross-Sample Frozen N-Frame Trace Validation

## Purpose

This run keeps the new N-Frame trace scores frozen and tests them on every suitable local real-CMS sample currently available without downloading new data. The target remains Darren's hidden-boundary trace question: a repeatable MET high-boundary transition shape, not direct SUSY particle detection.

## Samples Used

{audit.groupby(["sample_validation_id", "primary_dataset"], observed=False)["events_after_quality"].sum().reset_index().to_markdown(index=False)}

## Frozen Scores

- `observer_physical_clean`: $B = 0.5O + 0.5P$
- `observer_physical_qcd_suppressed_scan_best`: $B = 0.344828O + 0.517241P - 0.137931Q$

where $O$ is the observer/reconstruction residual projection, $P$ is the physical visible/missing/displacement-reconstruction projection, and $Q$ is the ordinary-QCD axis.

## Sample-by-Sample Results

{summary[["candidate_id", "sample_validation_id", "trace_total", "control_total", "shape_Z", "shoulder_Z", "trace_95_99_over_90_95_density_ratio", "control_95_99_over_90_95_density_ratio", "shoulder_above_control"]].to_markdown(index=False, floatfmt=".6g")}

## Combined Readiness

{ready.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The key publication-level question is whether the frozen trace repeats outside the two samples used in the previous candidate scan. A fully convincing result would pass in all additional samples with the same shoulder direction and no retuning.

If a sample fails, that does not automatically kill the N-Frame interpretation, but it means the claim must become conditional: the trace depends on era, trigger/sample composition, feature availability, or detector/reconstruction conditions. That would require a dynamical-boundary model rather than a single universal score.
"""
    (REPORTS / "01_CROSS_SAMPLE_FROZEN_TRACE_VALIDATION.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = []
    audit_rows = []
    for config in SAMPLES:
        path = Path(config["path"])
        if not path.exists():
            audit_rows.append({"sample_validation_id": config["sample_id"], "status": "missing", "path": str(path)})
            continue
        sample = load_sample(config)
        sample = add_missing_deciles(sample)
        frames.append(sample)
        audit_rows.append(
            {
                "sample_validation_id": config["sample_id"],
                "status": "loaded",
                "path": str(path),
                "events_after_quality": len(sample),
                "component_mode": config["component_mode"],
            }
        )
    if not frames:
        raise RuntimeError("No validation samples were available.")
    events = pd.concat(frames, ignore_index=True, sort=False)
    summary, vectors, region_audit = evaluate(events)
    ready = combined_readiness(summary)
    pd.DataFrame(audit_rows).to_csv(TABLES / "00_source_sample_audit.csv", index=False)
    region_audit.to_csv(TABLES / "01_region_event_audit.csv", index=False)
    summary.to_csv(TABLES / "02_cross_sample_frozen_trace_summary.csv", index=False)
    vectors.to_csv(TABLES / "03_cross_sample_microband_vectors.csv", index=False)
    ready.to_csv(TABLES / "04_cross_sample_combined_readiness.csv", index=False)
    write_report(summary, ready, region_audit)
    print(REPORTS / "01_CROSS_SAMPLE_FROZEN_TRACE_VALIDATION.md")
    print(ready.to_string(index=False))


if __name__ == "__main__":
    main()
