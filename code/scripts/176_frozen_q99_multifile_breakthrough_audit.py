from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_frozen_q99_multifile_breakthrough_audit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

FULL_WEIGHTED_SM = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
REAL_INPUTS = [
    ("Run2016G_main_MET", ROOT / "data/processed/nframe_parameter_fit/real_data_with_fitted_nframe_boundary_score.csv"),
    ("Run2016H_independent_MET", ROOT / "data/processed/independent_validation_miniaod_full/run2016h_miniaod_with_fitted_nframe_score.csv"),
    ("Run2016H_expanded_MET", ROOT / "data/processed/expanded_run2016h_miniaod_full/expanded_run2016h_miniaod_with_fitted_nframe_score.csv"),
    ("Run2016H_new_independent_MET", ROOT / "data/processed/new_independent_real_miniaod_validation/full/new_real_events_with_frozen_BNF.csv"),
    ("Run2016H_fresh_frozen_MET", ROOT / "outputs_frozen_q99_1to2jet_fresh_validation/sources/frozen_q99_fresh_run2016h_met_17CF0768-2FEC-D640-BCE3-C11CF4D52B69_event_features.csv"),
]
FEATURES = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "secondary_vertex_count", "packed_candidate_count"]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = ["q000_050", "q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099", "q099_100"]
MIDPOINTS = {"q000_050": 0.25, "q050_080": 0.65, "q080_090": 0.85, "q090_095": 0.925, "q095_0975": 0.9625, "q0975_099": 0.9825, "q099_100": 0.995}
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
SIDE_REPORT_BANDS = ["q080_090", "q090_095"]
SIGNAL_BAND = "q099_100"
REL_UNC = 0.127


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS, SOURCES]:
        p.mkdir(parents=True, exist_ok=True)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
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
    use = [c for c in FEATURES + ["event_weight"] if c in header]
    sm = pd.read_csv(FULL_WEIGHTED_SM, usecols=use, low_memory=False)
    for c in FEATURES + ["event_weight"]:
        if c not in sm:
            sm[c] = 1.0 if c == "event_weight" else 0.0
        sm[c] = pd.to_numeric(sm[c], errors="coerce")
    sm["event_weight"] = sm["event_weight"].fillna(1.0)
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    return sm


def fit_visible_residual(sm: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    w = sm["event_weight"].to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), w)
    sm = sm.copy()
    sm["common_missing_z"] = (sm["log1p_MET_pt"] - mean_met) / sd_met
    x = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = x.median().to_numpy(float)
    x = x.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
    y = sm["common_missing_z"].to_numpy(float)
    sw = np.sqrt(np.clip(w, 1e-12, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    sm["common_missing_resid_visible_only"] = y - design @ coef
    return {"mean_logmet": mean_met, "sd_logmet": sd_met, "visible_median": med, "coef": coef}, sm


def apply_visible_residual(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    for c in FEATURES:
        if c not in out:
            out[c] = 0.0
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["common_missing_z"] = (out["log1p_MET_pt"] - params["mean_logmet"]) / params["sd_logmet"]
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["visible_median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["common_missing_resid_visible_only"] = out["common_missing_z"].to_numpy(float) - design @ params["coef"]
    return out


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    w = sm["event_weight"].to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, w, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score = sm["common_missing_resid_visible_only"].to_numpy(float)
    score_edges = {}
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        m = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[m], w[m], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_bands(df: pd.DataFrame, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["met_bin"] = pd.cut(out["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(out), None, dtype=object)
    score = out["common_missing_resid_visible_only"].to_numpy(float)
    met_bin = out["met_bin"].to_numpy()
    for i in range(MET_BINS):
        mask = met_bin == i
        edges = score_edges[i]
        for name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = name
    out["score_band"] = band
    return out[out["score_band"].notna()].copy()


def read_real_all(params: dict, met_edges: list[float], score_edges: dict[int, list[float]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    audit = []
    for sample, path in REAL_INPUTS:
        if not path.exists():
            audit.append({"input_group": sample, "path": str(path), "exists": False, "met_events": 0, "source_files": 0})
            continue
        header = pd.read_csv(path, nrows=0).columns
        use = [c for c in ["primary_dataset", "source_file", "run", "lumi", "event", "sample_id", "record_id"] + FEATURES if c in header]
        df = pd.read_csv(path, usecols=use, low_memory=False)
        if "primary_dataset" in df:
            df = df[df["primary_dataset"].astype(str).eq("MET")].copy()
        df["input_group"] = sample
        for c in ["source_file", "sample_id", "record_id"]:
            if c not in df:
                df[c] = ""
        for c in ["run", "lumi", "event"]:
            if c not in df:
                df[c] = np.nan
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["event_key"] = df["run"].astype("Int64").astype(str) + ":" + df["lumi"].astype("Int64").astype(str) + ":" + df["event"].astype("Int64").astype(str)
        df = assign_bands(apply_visible_residual(df, params), met_edges, score_edges)
        frames.append(df)
        audit.append({"input_group": sample, "path": str(path), "exists": True, "met_events": len(df), "source_files": df["source_file"].nunique()})
    real = pd.concat(frames, ignore_index=True)
    # If the same source file appears in both subset and expanded sets, keep one copy.
    real = real.drop_duplicates(["source_file", "event_key"], keep="last").copy()
    real["jet_bin_frozen"] = pd.cut(real["N_jets_30"].fillna(0), bins=[-np.inf, 0, 2, 4, np.inf], labels=["0jet", "1to2jets", "3to4jets", "5plusjets"]).astype(str)
    return real, pd.DataFrame(audit)


def add_sm_jet_bin(sm: pd.DataFrame) -> pd.DataFrame:
    out = sm.copy()
    out["jet_bin_frozen"] = pd.cut(out["N_jets_30"].fillna(0), bins=[-np.inf, 0, 2, 4, np.inf], labels=["0jet", "1to2jets", "3to4jets", "5plusjets"]).astype(str)
    return out


def counts_for(real_sub: pd.DataFrame, sm_sub: pd.DataFrame, label_cols: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    for met_bin, band in product(range(MET_BINS), SCORE_BANDS):
        r_bin = real_sub[real_sub["met_bin"].eq(met_bin)]
        s_bin = sm_sub[sm_sub["met_bin"].eq(met_bin)]
        if len(r_bin) < 5 or s_bin["event_weight"].sum() <= 0:
            continue
        frac = float(s_bin.loc[s_bin["score_band"].eq(band), "event_weight"].sum() / s_bin["event_weight"].sum())
        rows.append({**label_cols, "met_bin": met_bin, "score_band": band, "met_bin_n": len(r_bin), "observed": int((r_bin["score_band"].eq(band)).sum()), "sm_fraction": frac, "expected_official": len(r_bin) * frac, "midpoint": MIDPOINTS[band]})
    counts = pd.DataFrame(rows)
    if counts.empty:
        return counts, {}
    fit = counts[counts["score_band"].isin(SIDEBAND_FIT_BANDS)]
    oe = (fit["observed"].to_numpy(float) + 0.5) / (fit["expected_official"].to_numpy(float) + 0.5)
    x = fit["midpoint"].to_numpy(float) - 0.90
    y = np.log(np.clip(oe, 1e-6, np.inf))
    w = np.sqrt(np.clip(fit["observed"].to_numpy(float), 1.0, np.inf))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * w[:, None], y * w, rcond=None)
    sideband_rms = float(np.sqrt(np.average((y - design @ coef) ** 2, weights=w)))
    counts["shape_correction"] = np.exp(coef[0] + (counts["midpoint"] - 0.90) * coef[1])
    counts["expected_shape"] = counts["expected_official"] * counts["shape_correction"]
    summary = summarize(counts, sideband_rms)
    summary.update(label_cols)
    return counts, summary


def z_unc(obs: float, exp: float, rel: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel * exp) ** 2, 1e-12)))


def summarize(counts: pd.DataFrame, sideband_rms: float) -> dict:
    rel = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
    side = counts[counts["score_band"].isin(SIDE_REPORT_BANDS)]
    sig = counts[counts["score_band"].eq(SIGNAL_BAND)]
    out = {}
    for prefix, df, exp_col in [
        ("sideband_80_95_official", side, "expected_official"),
        ("q99_official", sig, "expected_official"),
        ("q99_shape", sig, "expected_shape"),
    ]:
        obs = float(df["observed"].sum())
        exp = float(df[exp_col].sum())
        out[f"{prefix}_observed"] = obs
        out[f"{prefix}_expected"] = exp
        out[f"{prefix}_obs_exp"] = obs / exp if exp > 0 else np.inf
        out[f"{prefix}_Z"] = z_unc(obs, exp, rel)
    out["sideband_log_rms"] = sideband_rms
    out["relative_uncertainty_used"] = rel
    return out


def stouffer(zs: pd.Series) -> float:
    vals = zs.replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
    if len(vals) == 0:
        return np.nan
    return float(vals.sum() / np.sqrt(len(vals)))


def fisher(zs: pd.Series) -> float:
    vals = zs.replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
    if len(vals) == 0:
        return np.nan
    ps = np.clip(norm.sf(vals), 1e-300, 1.0)
    p = chi2.sf(-2 * np.log(ps).sum(), 2 * len(ps))
    return float(norm.isf(p))


def main() -> None:
    ensure_dirs()
    sm = read_sm()
    params, sm = fit_visible_residual(sm)
    met_edges, score_edges = define_bins(sm)
    sm = add_sm_jet_bin(assign_bands(sm, met_edges, score_edges))
    real, audit = read_real_all(params, met_edges, score_edges)
    audit.to_csv(TABLES / "00_input_audit.csv", index=False)
    real.to_csv(SOURCES / "all_available_real_met_scored_deduplicated.csv", index=False)

    counts_frames = []
    summaries = []
    for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
        sm_sub = sm[sm["jet_bin_frozen"].eq(jet_bin)]
        real_sub = real[real["jet_bin_frozen"].eq(jet_bin)]
        counts, summary = counts_for(real_sub, sm_sub, {"unit": "all_available_deduped", "source_file": "ALL", "jet_bin": jet_bin})
        if not counts.empty:
            counts_frames.append(counts)
            summaries.append(summary)
        for source_file, real_file in real_sub.groupby("source_file"):
            if len(real_file) < 500:
                continue
            counts, summary = counts_for(real_file, sm_sub, {"unit": "source_file", "source_file": source_file, "jet_bin": jet_bin})
            if not counts.empty:
                counts_frames.append(counts)
                summaries.append(summary)

    counts_df = pd.concat(counts_frames, ignore_index=True)
    summary_df = pd.DataFrame(summaries)
    counts_df.to_csv(TABLES / "01_frozen_q99_counts_by_file_and_control.csv", index=False)
    summary_df.to_csv(TABLES / "02_frozen_q99_summary_by_file_and_control.csv", index=False)

    signal_files = summary_df[(summary_df["unit"].eq("source_file")) & (summary_df["jet_bin"].eq("1to2jets"))].copy()
    controls = summary_df[(summary_df["unit"].eq("all_available_deduped")) & (~summary_df["jet_bin"].eq("1to2jets"))].copy()
    combined = pd.DataFrame(
        [
            {
                "combination": "all_disjoint_source_files_q99_1to2jets",
                "n_files": len(signal_files),
                "total_observed": float(signal_files["q99_shape_observed"].sum()),
                "total_expected_shape": float(signal_files["q99_shape_expected"].sum()),
                "total_obs_exp_shape": float(signal_files["q99_shape_observed"].sum() / signal_files["q99_shape_expected"].sum()),
                "stouffer_Z": stouffer(signal_files["q99_shape_Z"]),
                "fisher_Z": fisher(signal_files["q99_shape_Z"]),
                "min_file_Z": float(signal_files["q99_shape_Z"].min()),
                "files_passing_5sigma": int((signal_files["q99_shape_Z"] >= 5).sum()),
            }
        ]
    )
    combined.to_csv(TABLES / "03_frozen_q99_multifile_combined_significance.csv", index=False)
    controls.to_csv(TABLES / "04_jetbin_control_summary.csv", index=False)

    source_conc = real[real["jet_bin_frozen"].eq("1to2jets") & real["score_band"].eq(SIGNAL_BAND)].groupby(["source_file", "run"], as_index=False).agg(events=("event", "count"), lumis=("lumi", "nunique"))
    source_conc.to_csv(TABLES / "05_q99_1to2jet_run_lumi_concentration.csv", index=False)

    report = f"""# Frozen Q99 1-2 Jet Multifile Breakthrough Audit

## Question

Does the frozen Q99 1-2 jet N-Frame boundary trace survive across all currently available disjoint real MET source files, and do nearby jet-bin controls behave differently?

## Frozen Rule

- CMS real MET data only
- `N_jets_30` in 1-2
- `common_missing_resid_visible_only`
- raw-MET-binned top 1% score band
- shape correction fitted from 50-95% sidebands

## Input Audit

{audit.to_markdown(index=False)}

## Per-File Frozen Signal Result

{signal_files[["source_file", "q99_shape_observed", "q99_shape_expected", "q99_shape_obs_exp", "q99_shape_Z", "sideband_80_95_official_obs_exp", "sideband_log_rms", "relative_uncertainty_used"]].to_markdown(index=False)}

## Combined Signal Result

{combined.to_markdown(index=False)}

## Jet-Bin Controls

{controls[["jet_bin", "q99_shape_observed", "q99_shape_expected", "q99_shape_obs_exp", "q99_shape_Z", "sideband_80_95_official_obs_exp"]].to_markdown(index=False)}

## Interpretation

This audit is stronger than a single-file fresh test because it applies the frozen region uniformly to every currently available disjoint real MET source file.

The strongest discovery-style reading requires:

- the 1-2 jet signal to be consistently positive across files;
- the combined significance to remain above 5 sigma;
- controls not to show the same or larger coherent effect;
- no single file/run/lumi to dominate the candidate.

This is still not a new-era Run2017/Run2018 validation because those open-data records were not available through the CERN Open Data API queries run in the previous step.
"""
    (REPORTS / "01_FROZEN_Q99_MULTIFILE_BREAKTHROUGH_AUDIT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Frozen Q99 Multifile Audit

Frozen region: MET, 1-2 jets, top 1% N-Frame missing-vs-visible boundary score, raw-MET-binned, sideband-shape corrected.

Per-file signal:

{signal_files[["source_file", "q99_shape_obs_exp", "q99_shape_Z"]].to_markdown(index=False)}

Combined:

{combined.to_markdown(index=False)}

Controls:

{controls[["jet_bin", "q99_shape_obs_exp", "q99_shape_Z"]].to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_FROZEN_Q99_MULTIFILE_AUDIT.md").write_text(short, encoding="utf-8")
    print("FROZEN Q99 MULTIFILE BREAKTHROUGH AUDIT COMPLETE")
    print(signal_files[["source_file", "q99_shape_observed", "q99_shape_expected", "q99_shape_obs_exp", "q99_shape_Z"]].to_string(index=False))
    print(combined.to_string(index=False))
    print("Controls")
    print(controls[["jet_bin", "q99_shape_obs_exp", "q99_shape_Z"]].to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
