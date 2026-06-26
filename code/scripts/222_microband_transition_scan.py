from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN2016G_EVENTS = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz"
RUN2016H_EVENTS = ROOT / "outputs_control_calibrated_cross_sample_validation" / "tables" / "00_run2016h_recomputed_frozen_score_tagged_events.csv.gz"
OUT = ROOT / "outputs_microband_transition_scan"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

MICROBANDS = [
    ("q90_95", 0.90, 0.95, 0.05),
    ("q95_97", 0.95, 0.97, 0.02),
    ("q97_98", 0.97, 0.98, 0.01),
    ("q98_99", 0.98, 0.99, 0.01),
    ("q99_100", 0.99, 1.00, 0.01),
]
TARGET_ROWS = [
    ("MET", "0jet", "trace"),
    ("HTMHT", "1to2jets", "support"),
    ("JetHT", "1to2jets", "control"),
    ("SingleMuon", "0jet", "control"),
]
ALL_CONTROL_ROWS = [(d, j, "control") for d in ["JetHT", "SingleMuon"] for j in ["0jet", "1to2jets", "3to4jets", "5plusjets"]]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def load_real_events() -> pd.DataFrame:
    g_cols = ["era", "primary_dataset", "run", "lumi", "event", "missing_proxy_pt", "jet_bin", "frozen_boundary_score", "strict_quality_clean"]
    g = pd.read_csv(RUN2016G_EVENTS, usecols=lambda c: c in g_cols, low_memory=False)
    if "strict_quality_clean" in g:
        g = g[g["strict_quality_clean"].astype(bool)].copy()
    g["run_era"] = "Run2016G"
    g["score"] = pd.to_numeric(g["frozen_boundary_score"], errors="coerce")
    g["missing_proxy_pt"] = pd.to_numeric(g["missing_proxy_pt"], errors="coerce")
    g["missing_bin"] = -1
    for dataset, sub_idx in g.groupby("primary_dataset").groups.items():
        idx = list(sub_idx)
        vals = g.loc[idx, "missing_proxy_pt"].to_numpy(float)
        try:
            bins = pd.qcut(vals, 10, labels=False, duplicates="drop")
        except ValueError:
            bins = np.zeros(len(idx), dtype=int)
        g.loc[idx, "missing_bin"] = np.asarray(bins, dtype=float)
    g = g[["run_era", "primary_dataset", "jet_bin", "missing_bin", "missing_proxy_pt", "score"]]

    h = pd.read_csv(RUN2016H_EVENTS, low_memory=False)
    h["run_era"] = "Run2016H"
    h["score"] = pd.to_numeric(h["frozen_boundary_score_recomputed"], errors="coerce")
    h["missing_proxy_pt"] = pd.to_numeric(h["missing_proxy_pt"], errors="coerce")
    h["missing_bin"] = pd.to_numeric(h["missing_bin"], errors="coerce")
    h = h[["run_era", "primary_dataset", "jet_bin", "missing_bin", "missing_proxy_pt", "score"]]

    out = pd.concat([g, h], ignore_index=True)
    out = out.dropna(subset=["score", "missing_bin", "jet_bin", "primary_dataset", "run_era"]).copy()
    out["missing_bin"] = out["missing_bin"].astype(int)
    return out


def assign_microbands(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    edge_rows = []
    for keys, group in events.groupby(["run_era", "primary_dataset", "missing_bin"], observed=False):
        g = group.copy()
        scores = g["score"].to_numpy(float)
        if len(g) < 100:
            continue
        qs = np.quantile(scores, [0.90, 0.95, 0.97, 0.98, 0.99, 1.00])
        qs[-1] = np.inf
        labels = np.full(len(g), None, dtype=object)
        for name, _, _, _width in MICROBANDS:
            pass
        for (name, _loq, _hiq, _width), lo, hi in zip(MICROBANDS, qs[:-1], qs[1:]):
            labels[(scores >= lo) & (scores < hi)] = name
            edge_rows.append(
                {
                    "run_era": keys[0],
                    "primary_dataset": keys[1],
                    "missing_bin": keys[2],
                    "microband": name,
                    "score_low_edge": float(lo),
                    "score_high_edge": float(hi) if np.isfinite(hi) else np.inf,
                    "events_in_cell": len(g),
                }
            )
        g["microband"] = labels
        frames.append(g[g["microband"].notna()])
    return pd.concat(frames, ignore_index=True), pd.DataFrame(edge_rows)


def microband_counts(tagged: pd.DataFrame) -> pd.DataFrame:
    base = (
        tagged.groupby(["run_era", "primary_dataset", "jet_bin"], observed=False)
        .size()
        .reset_index(name="n_top10_total")
    )
    counts = (
        tagged.groupby(["run_era", "primary_dataset", "jet_bin", "microband"], observed=False)
        .size()
        .reset_index(name="observed")
    )
    widths = pd.DataFrame([{"microband": name, "nominal_width": width} for name, _lo, _hi, width in MICROBANDS])
    out = counts.merge(base, on=["run_era", "primary_dataset", "jet_bin"], how="left").merge(widths, on="microband", how="left")
    # Density per 1% score width, normalised to the whole 90-100% band.
    out["density_per_percent_of_top10"] = out["observed"] / out["n_top10_total"].replace(0, np.nan) / (100.0 * out["nominal_width"])
    return out


def select_rows(counts: pd.DataFrame, rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    selected = []
    for dataset, jet_bin, role in rows:
        hit = counts[(counts["primary_dataset"].eq(dataset)) & (counts["jet_bin"].eq(jet_bin))].copy()
        hit["role"] = role
        selected.append(hit)
    return pd.concat(selected, ignore_index=True)


def transition_metrics(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in selected.groupby(["run_era", "primary_dataset", "jet_bin", "role"], observed=False):
        pivot = group.set_index("microband")
        def val(band: str, col: str = "density_per_percent_of_top10") -> float:
            return float(pivot.loc[band, col]) if band in pivot.index else np.nan
        q99_density = val("q99_100")
        q95_99_density = np.nansum([
            val("q95_97") * 0.02,
            val("q97_98") * 0.01,
            val("q98_99") * 0.01,
        ]) / 0.04
        q90_95_density = val("q90_95")
        rows.append(
            {
                "run_era": keys[0],
                "primary_dataset": keys[1],
                "jet_bin": keys[2],
                "role": keys[3],
                "q90_95_density": q90_95_density,
                "q95_99_density": q95_99_density,
                "q99_100_density": q99_density,
                "q99_over_q95_99_density": q99_density / q95_99_density if q95_99_density > 0 else np.nan,
                "q95_99_over_q90_95_density": q95_99_density / q90_95_density if q90_95_density > 0 else np.nan,
                "q99_count": val("q99_100", "observed"),
                "top10_total": float(group["n_top10_total"].iloc[0]) if not group.empty else np.nan,
            }
        )
    metrics = pd.DataFrame(rows)
    control_ref = (
        metrics[metrics["role"].eq("control")]
        .groupby("run_era", as_index=False)
        .agg(
            control_mean_q99_over_q95_99=("q99_over_q95_99_density", "mean"),
            control_max_q99_over_q95_99=("q99_over_q95_99_density", "max"),
            control_mean_q95_99_over_q90_95=("q95_99_over_q90_95_density", "mean"),
        )
    )
    metrics = metrics.merge(control_ref, on="run_era", how="left")
    metrics["trace_vs_control_mean_q99_jump"] = metrics["q99_over_q95_99_density"] / metrics["control_mean_q99_over_q95_99"]
    return metrics


def monotonic_prediction(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Fit log-density as a function of band midpoint using only 90-95 and 95-97,
    # excluding 97-99 as the suspected transition shoulder, then predict 99-100.
    mids = {"q90_95": 92.5, "q95_97": 96.0, "q97_98": 97.5, "q98_99": 98.5, "q99_100": 99.5}
    for keys, group in selected.groupby(["run_era", "primary_dataset", "jet_bin", "role"], observed=False):
        g = group.copy()
        g["mid"] = g["microband"].map(mids)
        fit = g[g["microband"].isin(["q90_95", "q95_97"])].dropna(subset=["density_per_percent_of_top10", "mid"])
        obs = g[g["microband"].eq("q99_100")]
        if len(fit) < 2 or obs.empty:
            continue
        y = np.log(np.maximum(fit["density_per_percent_of_top10"].to_numpy(float), 1e-12))
        x = fit["mid"].to_numpy(float)
        slope, intercept = np.polyfit(x, y, 1)
        pred_density = float(np.exp(intercept + slope * 99.5))
        total = float(obs["n_top10_total"].iloc[0])
        pred_count = pred_density * total * 100.0 * 0.01
        observed = float(obs["observed"].iloc[0])
        # Simple binomial/Poisson-style diagnostic, not a discovery likelihood.
        sigma = np.sqrt(max(pred_count, 1.0))
        rows.append(
            {
                "run_era": keys[0],
                "primary_dataset": keys[1],
                "jet_bin": keys[2],
                "role": keys[3],
                "fit_log_density_slope": slope,
                "predicted_q99_count_from_90_97": pred_count,
                "observed_q99_count": observed,
                "obs_minus_pred": observed - pred_count,
                "simple_count_Z": (observed - pred_count) / sigma,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    events = load_real_events()
    tagged, edges = assign_microbands(events)
    counts = microband_counts(tagged)
    selected = select_rows(counts, TARGET_ROWS)
    all_controls = select_rows(counts, [("MET", "0jet", "trace"), *ALL_CONTROL_ROWS])
    metrics = transition_metrics(selected)
    broad_metrics = transition_metrics(all_controls)
    mono = monotonic_prediction(selected)

    edges.to_csv(TABLES / "00_microband_score_edges.csv", index=False)
    counts.to_csv(TABLES / "01_all_microband_counts.csv", index=False)
    selected.to_csv(TABLES / "02_target_microband_counts.csv", index=False)
    metrics.to_csv(TABLES / "03_target_transition_metrics.csv", index=False)
    broad_metrics.to_csv(TABLES / "04_broad_control_transition_metrics.csv", index=False)
    mono.to_csv(TABLES / "05_monotonic_extrapolation_check.csv", index=False)

    met_metrics = metrics[(metrics["primary_dataset"].eq("MET")) & (metrics["jet_bin"].eq("0jet"))]
    control_metrics = metrics[metrics["role"].eq("control")]
    met_mono = mono[(mono["primary_dataset"].eq("MET")) & (mono["jet_bin"].eq("0jet"))]

    report = f"""# Microband Transition Scan Across the N-Frame Tail

## Purpose

This stage tests whether the `95-99%` band is a clean background sideband or already part of the N-Frame boundary transition. No weights are refit and no new data are downloaded.

The score tail is split within each era, dataset and missing-energy decile:

- `90-95%`
- `95-97%`
- `97-98%`
- `98-99%`
- `99-100%`

The main diagnostic is the per-width density of events in each microband. If `95-99%` is already elevated in MET, then using it as a background sideband will subtract away the Q99 trace.

## MET 0-Jet Transition Metrics

{met_metrics.to_markdown(index=False, floatfmt=".6g")}

## Target/Control Transition Metrics

{metrics.to_markdown(index=False, floatfmt=".6g")}

## Monotonic Extrapolation Check

This fits a simple log-density trend using `90-95%` and `95-97%`, deliberately excluding the suspected `97-99%` shoulder, then predicts `99-100%`.

{mono.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

If MET has a larger `q95_99_over_q90_95_density` than JetHT/SingleMuon controls, then `95-99%` is not a clean sideband for the trace. If the monotonic extrapolation still predicts far below the observed Q99 count, then the boundary transition begins before Q99 and adjacent-sideband subtraction is too aggressive.
"""
    (REPORTS / "01_MICROBAND_TRANSITION_SCAN.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_MICROBAND_TRANSITION_SCAN.md")
    print(met_metrics.to_string(index=False))
    print(met_mono.to_string(index=False))


if __name__ == "__main__":
    main()
