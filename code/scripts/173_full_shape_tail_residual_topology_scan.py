from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_full_shape_tail_residual_topology_scan"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
REAL_SAMPLES = [
    ("Run2016G_main_MET", ROOT / "data/processed/nframe_parameter_fit/real_data_with_fitted_nframe_boundary_score.csv"),
    ("Run2016H_independent_MET", ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv"),
    ("Run2016H_expanded_MET", ROOT / "data/processed/expanded_run2016h_miniaod_full/expanded_run2016h_miniaod_with_fitted_nframe_score.csv"),
    ("Run2016H_new_independent_MET", ROOT / "data/processed/new_independent_real_miniaod_validation/full/new_real_events_with_frozen_BNF.csv"),
]

FEATURES = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_btags_medium",
    "N_muons",
    "N_electrons",
    "secondary_vertex_count",
    "packed_candidate_count",
]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = [
    "q000_050",
    "q050_080",
    "q080_090",
    "q090_095",
    "q095_0975",
    "q0975_099",
    "q099_100",
]
BAND_MIDPOINT = {
    "q000_050": 0.25,
    "q050_080": 0.65,
    "q080_090": 0.85,
    "q090_095": 0.925,
    "q095_0975": 0.9625,
    "q0975_099": 0.9825,
    "q099_100": 0.995,
}
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
FINAL_TAIL_BANDS = ["q095_0975", "q0975_099", "q099_100"]
REL_UNC = 0.127


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0 or weights.sum() <= 0:
        return np.nan
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    mean = float(np.average(values[mask], weights=weights[mask]))
    var = float(np.average((values[mask] - mean) ** 2, weights=weights[mask]))
    return mean, np.sqrt(max(var, 1e-12))


def read_sm() -> pd.DataFrame:
    header = pd.read_csv(FULL_WEIGHTED_SM, nrows=0).columns
    use = [c for c in FEATURES + ["event_weight", "process_family_norm", "component_layer"] if c in header]
    sm = pd.read_csv(FULL_WEIGHTED_SM, usecols=use, low_memory=False)
    for col in FEATURES + ["event_weight"]:
        if col not in sm:
            sm[col] = 1.0 if col == "event_weight" else 0.0
        sm[col] = pd.to_numeric(sm[col], errors="coerce")
    sm["event_weight"] = sm["event_weight"].fillna(1.0)
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    sm["primary_dataset"] = "SM"
    return sm


def read_real_met(path: Path, sample_name: str) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0).columns
    use = [c for c in ["primary_dataset", "run", "lumi", "event", "sample_id", "record_id", "source_file"] + FEATURES if c in header]
    frames: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=use, chunksize=200_000, low_memory=False):
        if "primary_dataset" not in chunk:
            continue
        chunk = chunk[chunk["primary_dataset"].astype(str).eq("MET")].copy()
        if chunk.empty:
            continue
        for col in FEATURES + ["run", "lumi", "event"]:
            if col not in chunk:
                chunk[col] = 0.0
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        chunk["real_sample"] = sample_name
        chunk["event_key"] = (
            chunk["run"].astype("Int64").astype(str)
            + ":"
            + chunk["lumi"].astype("Int64").astype(str)
            + ":"
            + chunk["event"].astype("Int64").astype(str)
        )
        frames.append(chunk)
    if not frames:
        return pd.DataFrame()
    real = pd.concat(frames, ignore_index=True)
    real["log1p_MET_pt"] = np.log1p(real["MET_pt"].clip(lower=0))
    real["log1p_HT"] = np.log1p(real["HT"].clip(lower=0))
    return real


def fit_visible_residual(sm: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    weights = sm["event_weight"].to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), weights)
    sm = sm.copy()
    sm["common_missing_z"] = (sm["log1p_MET_pt"] - mean_met) / sd_met
    x = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = x.median().to_numpy(float)
    x = x.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
    y = sm["common_missing_z"].to_numpy(float)
    sw = np.sqrt(np.clip(weights, 1e-12, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    sm["common_missing_resid_visible_only"] = y - design @ coef
    return {"mean_logmet": mean_met, "sd_logmet": sd_met, "visible_median": med, "coef": coef}, sm


def apply_visible_residual(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    out["common_missing_z"] = (out["log1p_MET_pt"] - params["mean_logmet"]) / params["sd_logmet"]
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["visible_median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["common_missing_resid_visible_only"] = out["common_missing_z"].to_numpy(float) - design @ params["coef"]
    return out


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    weights = sm["event_weight"].to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, weights, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score_edges: dict[int, list[float]] = {}
    score = sm["common_missing_resid_visible_only"].to_numpy(float)
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        mask = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[mask], weights[mask], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_bands(df: pd.DataFrame, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["met_bin"] = pd.cut(out["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(out), None, dtype=object)
    score = out["common_missing_resid_visible_only"].to_numpy(float)
    met_bins = out["met_bin"].to_numpy()
    for i in range(MET_BINS):
        mask = met_bins == i
        edges = score_edges[i]
        for band_name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = band_name
    out["score_band"] = band
    return out[out["score_band"].notna()].copy()


def add_topology_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["topology_all"] = "all_MET"
    out["topology_lepton_veto"] = np.where((out["N_muons"].fillna(0) + out["N_electrons"].fillna(0)) == 0, "lepton_veto", "has_lepton")
    out["topology_jet_bin"] = pd.cut(
        out["N_jets_30"].fillna(0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    out["topology_btag"] = np.where(out["N_btags_medium"].fillna(0) > 0, "btag", "no_btag")
    out["topology_ht"] = np.where(out["HT"].fillna(0) >= 300, "HT_ge_300", "HT_lt_300")
    out["topology_sv"] = np.where(out["secondary_vertex_count"].fillna(0) > 0, "sv_proxy_gt0", "sv_proxy_0")
    out["topology_lowvisible"] = np.where((out["HT"].fillna(0) < 100) & (out["N_jets_30"].fillna(0) <= 1), "low_visible", "not_low_visible")
    return out


def make_counts(
    real: pd.DataFrame,
    sm: pd.DataFrame,
    sample_name: str,
    topology_column: str,
    topology_value: str,
) -> pd.DataFrame:
    real_sub = real[real[topology_column].astype(str).eq(topology_value)]
    sm_sub = sm[sm[topology_column].astype(str).eq(topology_value)]
    rows = []
    if len(real_sub) < 500 or sm_sub["event_weight"].sum() <= 0:
        return pd.DataFrame()
    for met_bin, band in product(range(MET_BINS), SCORE_BANDS):
        r_bin = real_sub[real_sub["met_bin"].eq(met_bin)]
        s_bin = sm_sub[sm_sub["met_bin"].eq(met_bin)]
        r_total = len(r_bin)
        s_total = float(s_bin["event_weight"].sum())
        if r_total < 20 or s_total <= 0:
            continue
        r_obs = int((r_bin["score_band"].eq(band)).sum())
        s_band = float(s_bin.loc[s_bin["score_band"].eq(band), "event_weight"].sum())
        frac = s_band / s_total if s_total > 0 else 0.0
        exp = r_total * frac
        rows.append(
            {
                "real_sample": sample_name,
                "topology_column": topology_column,
                "topology_value": topology_value,
                "met_bin": met_bin,
                "score_band": band,
                "band_midpoint": BAND_MIDPOINT[band],
                "real_met_topology_bin_n": r_total,
                "observed": r_obs,
                "sm_fraction": frac,
                "expected_official_shape": exp,
            }
        )
    return pd.DataFrame(rows)


def fit_sideband_shape(counts: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    fit_rows = counts[counts["score_band"].isin(SIDEBAND_FIT_BANDS)].copy()
    if len(fit_rows) < 6:
        return pd.DataFrame(), {}
    oe = (fit_rows["observed"].to_numpy(float) + 0.5) / (fit_rows["expected_official_shape"].to_numpy(float) + 0.5)
    x = fit_rows["band_midpoint"].to_numpy(float)
    y = np.log(np.clip(oe, 1e-6, np.inf))
    weights = np.sqrt(np.clip(fit_rows["observed"].to_numpy(float), 1.0, np.inf))
    x0 = x - 0.90
    design = np.column_stack([np.ones(len(x0)), x0])
    coef, *_ = np.linalg.lstsq(design * weights[:, None], y * weights, rcond=None)
    pred_log = design @ coef
    residual = y - pred_log
    sideband_rms = float(np.sqrt(np.average(residual**2, weights=weights)))

    for _, row in counts.iterrows():
        mid = float(row["band_midpoint"])
        corr = float(np.exp(np.array([1.0, mid - 0.90]) @ coef))
        exp_shape = float(row["expected_official_shape"]) * corr
        rows.append({**row.to_dict(), "sideband_shape_correction": corr, "expected_sideband_shape_extrapolated": exp_shape})

    out = pd.DataFrame(rows)
    summary = summarize_tail(out, sideband_rms)
    summary.update({"sideband_log_rms": sideband_rms, "sideband_intercept": float(coef[0]), "sideband_slope": float(coef[1])})
    return out, summary


def summarize_tail(pred: pd.DataFrame, sideband_rms: float) -> dict:
    def region_stats(label: str, bands: list[str], expected_col: str) -> dict:
        sub = pred[pred["score_band"].isin(bands)]
        obs = float(sub["observed"].sum())
        exp = float(sub[expected_col].sum())
        z_stat = (obs - exp) / np.sqrt(max(exp, 1e-12))
        rel_shape_unc = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
        z_unc = (obs - exp) / np.sqrt(max(exp + (rel_shape_unc * exp) ** 2, 1e-12))
        return {
            f"{label}_observed": obs,
            f"{label}_expected": exp,
            f"{label}_observed_over_expected": obs / exp if exp > 0 else np.inf,
            f"{label}_Z_stat_only": z_stat,
            f"{label}_Z_with_shape_uncertainty": z_unc,
            f"{label}_rel_shape_uncertainty_used": rel_shape_unc,
        }

    summary = {}
    summary.update(region_stats("sideband_80_95", ["q080_090", "q090_095"], "expected_official_shape"))
    summary.update(region_stats("tail_95_100_official", FINAL_TAIL_BANDS, "expected_official_shape"))
    summary.update(region_stats("tail_95_100_shape_extrapolated", FINAL_TAIL_BANDS, "expected_sideband_shape_extrapolated"))
    summary.update(region_stats("tail_99_100_shape_extrapolated", ["q099_100"], "expected_sideband_shape_extrapolated"))
    return summary


def one_sided_trial_adjusted_z(z: float, n_trials: int) -> float:
    if not np.isfinite(z):
        return np.nan
    p = norm.sf(z)
    p_global = min(1.0, p * max(n_trials, 1))
    return float(norm.isf(p_global)) if p_global < 1 else 0.0


def main() -> None:
    ensure_dirs()
    sm = read_sm()
    params, sm = fit_visible_residual(sm)
    met_edges, score_edges = define_bins(sm)
    sm = add_topology_flags(assign_bands(sm, met_edges, score_edges))

    topology_columns = [
        "topology_all",
        "topology_lepton_veto",
        "topology_jet_bin",
        "topology_btag",
        "topology_ht",
        "topology_sv",
        "topology_lowvisible",
    ]
    topology_values = {col: sorted(sm[col].dropna().astype(str).unique()) for col in topology_columns}

    all_counts = []
    all_predictions = []
    summaries = []
    audit_rows = []
    for sample_name, path in REAL_SAMPLES:
        real = read_real_met(path, sample_name)
        if real.empty:
            continue
        real = add_topology_flags(assign_bands(apply_visible_residual(real, params), met_edges, score_edges))
        audit_rows.append({"real_sample": sample_name, "path": str(path.relative_to(ROOT)), "met_events": len(real)})
        for col in topology_columns:
            real_values = sorted(real[col].dropna().astype(str).unique())
            for value in sorted(set(real_values) & set(topology_values[col])):
                counts = make_counts(real, sm, sample_name, col, value)
                if counts.empty:
                    continue
                pred, summary = fit_sideband_shape(counts)
                if pred.empty:
                    continue
                summary.update({"real_sample": sample_name, "topology_column": col, "topology_value": value, "real_events_in_topology": int((real[col].astype(str) == value).sum())})
                all_counts.append(counts)
                all_predictions.append(pred)
                summaries.append(summary)

    counts_df = pd.concat(all_counts, ignore_index=True)
    pred_df = pd.concat(all_predictions, ignore_index=True)
    summary_df = pd.DataFrame(summaries)
    summary_df["shape_tail_minus_sideband_ratio"] = (
        summary_df["tail_95_100_shape_extrapolated_observed_over_expected"]
        / summary_df["sideband_80_95_observed_over_expected"].replace(0, np.nan)
    )
    n_trials = len(summary_df)
    summary_df["tail_95_100_shape_extrapolated_Z_global_trial_adjusted"] = summary_df[
        "tail_95_100_shape_extrapolated_Z_with_shape_uncertainty"
    ].map(lambda z: one_sided_trial_adjusted_z(float(z), n_trials))

    # Rank useful candidate slices: top-tail survives sideband shape, sideband is not wildly open, and enough events exist.
    candidates = summary_df[
        (summary_df["real_events_in_topology"] >= 1000)
        & (summary_df["tail_95_100_shape_extrapolated_Z_with_shape_uncertainty"] > 0)
    ].copy()
    candidates["rank_score"] = (
        candidates["tail_95_100_shape_extrapolated_Z_global_trial_adjusted"]
        + np.minimum(candidates["shape_tail_minus_sideband_ratio"].fillna(0), 3)
        - abs(np.log(candidates["sideband_80_95_observed_over_expected"].clip(lower=1e-6)))
    )
    candidates = candidates.sort_values("rank_score", ascending=False)

    audit = pd.DataFrame(audit_rows)
    audit.to_csv(TABLES / "00_met_sample_audit.csv", index=False)
    counts_df.to_csv(TABLES / "01_fine_score_band_counts.csv", index=False)
    pred_df.to_csv(TABLES / "02_sideband_shape_extrapolated_predictions.csv", index=False)
    summary_df.to_csv(TABLES / "03_full_shape_tail_residual_summary.csv", index=False)
    candidates.head(80).to_csv(TABLES / "04_ranked_topology_tail_residual_candidates.csv", index=False)

    main_cols = [
        "real_sample",
        "topology_column",
        "topology_value",
        "real_events_in_topology",
        "sideband_80_95_observed_over_expected",
        "tail_95_100_official_observed_over_expected",
        "tail_95_100_shape_extrapolated_observed_over_expected",
        "tail_95_100_shape_extrapolated_Z_with_shape_uncertainty",
        "tail_95_100_shape_extrapolated_Z_global_trial_adjusted",
        "tail_99_100_shape_extrapolated_observed_over_expected",
        "tail_99_100_shape_extrapolated_Z_with_shape_uncertainty",
        "shape_tail_minus_sideband_ratio",
        "sideband_log_rms",
    ]
    all_met = summary_df[summary_df["topology_column"].eq("topology_all")].copy()
    report = f"""# Full Shape Tail-Residual and Topology Scan

## Question

Can the broad N-Frame sideband mismatch explain the final MET boundary tail, or does the final tail remain unusually high after fitting the shape below 95%?

## Method

- Score: `common_missing_resid_visible_only`
- Conditioning: 10 raw `MET_pt` bins
- Fine N-Frame score bands: 0-50, 50-80, 80-90, 90-95, 95-97.5, 97.5-99, 99-100%
- Sideband-shape fit: log observed/expected trend fitted on 50-95%
- Signal test: extrapolate that fitted sideband trend into 95-100% and 99-100%
- Topology scan: simple pre-defined slices using leptons, jet count, b-tags, HT, secondary-vertex proxy and low-visible topology
- Uncertainty: combines previous 12.7% replication uncertainty with the sideband-fit residual scatter

This asks a stricter question than the earlier top-5% test: not merely whether the high tail is elevated, but whether it is elevated above the broad sideband distortion.

## Samples

{audit.to_markdown(index=False)}

## All-MET Shape Residual

{all_met[main_cols].to_markdown(index=False)}

## Best Topology Candidates

{candidates.head(25)[main_cols + ["rank_score"]].to_markdown(index=False)}

## Interpretation

If the shape-extrapolated 95-100% Z remains high, the final tail is sharper than the broad sideband mismatch. If it collapses, then the current observation is better described as a broad Standard Model shape mismatch.

The topology table is exploratory. It should be used to define a smaller follow-up region, then retested independently rather than quoted as a final discovery claim.
"""
    (REPORTS / "01_FULL_SHAPE_TAIL_RESIDUAL_TOPOLOGY_SCAN_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Full-Shape Tail Residual Scan

We fitted the broad N-Frame score mismatch below the top tail, then extrapolated into the 95-100% MET boundary region.

All-MET result:

{all_met[main_cols].to_markdown(index=False)}

Best exploratory topology candidates:

{candidates.head(10)[main_cols + ["rank_score"]].to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_FULL_SHAPE_TAIL_RESIDUAL_SCAN.md").write_text(short, encoding="utf-8")

    print("FULL SHAPE TAIL-RESIDUAL TOPOLOGY SCAN COMPLETE")
    print("All-MET result:")
    print(all_met[main_cols].to_string(index=False))
    print("Top candidates:")
    print(candidates.head(15)[main_cols + ["rank_score"]].to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
