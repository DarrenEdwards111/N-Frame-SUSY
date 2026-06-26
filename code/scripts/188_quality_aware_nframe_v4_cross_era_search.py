from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_quality_aware_nframe_v4_cross_era_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SM_PATH = ROOT / "outputs_breakthrough_full_push_nframe_susy/sources/best_available_full_plus_reduced_weighted_sm_events.csv"
RUN2016_REAL = ROOT / "outputs_run2016_quality_clean_frozen_q99_profile/tables/00_run2016_quality_clean_real_events_scored.csv"
RUN2015_REAL = ROOT / "outputs_run2015d_quality_clean_frozen_q99_profile/tables/00_run2015d_quality_clean_real_events.csv"

BASE_FEATURES = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_btags_medium",
    "N_muons",
    "N_electrons",
    "packed_candidate_count",
    "secondary_vertex_count",
]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = ["q000_050", "q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099", "q099_100"]
FIT_BANDS = ["q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099"]
MIDPOINTS = {
    "q000_050": 0.25,
    "q050_080": 0.65,
    "q080_090": 0.85,
    "q090_095": 0.925,
    "q095_0975": 0.9625,
    "q0975_099": 0.9825,
    "q099_100": 0.995,
}
REL_UNC = 0.127


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
        p.mkdir(parents=True, exist_ok=True)


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    mean = float(np.average(values, weights=weights))
    var = float(np.average((values - mean) ** 2, weights=weights))
    return mean, float(np.sqrt(max(var, 1e-12)))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def read_sm() -> pd.DataFrame:
    use = BASE_FEATURES + ["event_weight"]
    header = pd.read_csv(SM_PATH, nrows=0).columns
    cols = [c for c in use if c in header]
    sm = pd.read_csv(SM_PATH, usecols=cols, low_memory=False)
    for c in use:
        if c not in sm:
            sm[c] = 1.0 if c == "event_weight" else 0.0
        sm[c] = pd.to_numeric(sm[c], errors="coerce").fillna(0.0)
    sm["event_weight"] = sm["event_weight"].replace(0, np.nan).fillna(1.0)
    sm["era"] = "SM_reference"
    sm["primary_dataset"] = "SM"
    sm["source_file"] = "SM"
    return sm


def read_real() -> pd.DataFrame:
    frames = []
    r16 = pd.read_csv(RUN2016_REAL, low_memory=False)
    r16["era"] = "Run2016"
    frames.append(r16)
    r15 = pd.read_csv(RUN2015_REAL, low_memory=False)
    r15["era"] = "Run2015D"
    frames.append(r15)
    real = pd.concat(frames, ignore_index=True)
    for c in BASE_FEATURES:
        if c not in real:
            real[c] = 0.0
        real[c] = pd.to_numeric(real[c], errors="coerce").fillna(0.0)
    real["primary_dataset"] = real["primary_dataset"].astype(str)
    real["source_file"] = real["source_file"].astype(str)
    real["event_weight"] = 1.0
    return real


def add_base_transforms(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["lepton_count"] = out["N_muons"] + out["N_electrons"]
    out["jet_btag_ratio"] = out["N_btags_medium"] / np.maximum(out["N_jets_30"], 1.0)
    out["met_ht_ratio"] = out["MET_pt"] / np.maximum(out["HT"], 1.0)
    out["jet_bin"] = pd.cut(
        out["N_jets_30"].fillna(0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    return out


def fit_reference(sm: pd.DataFrame) -> dict:
    w = sm["event_weight"].to_numpy(float)
    stats = {}
    for col in ["log1p_MET_pt", "log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "packed_candidate_count", "secondary_vertex_count", "jet_btag_ratio", "met_ht_ratio"]:
        stats[col] = weighted_stats(sm[col].to_numpy(float), w)
    # Missing residual conditioned on visible structure.
    mean_met, sd_met = stats["log1p_MET_pt"]
    y = (sm["log1p_MET_pt"].to_numpy(float) - mean_met) / sd_met
    xdf = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = xdf.median().to_numpy(float)
    x = xdf.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    sw = np.sqrt(np.clip(w, 1e-12, np.inf))
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    return {"stats": stats, "visible_median": med, "visible_coef": coef}


def apply_reference(df: pd.DataFrame, ref: dict) -> pd.DataFrame:
    out = add_base_transforms(df)
    for col, (mean, sd) in ref["stats"].items():
        out[f"z_{col}"] = (out[col].to_numpy(float) - mean) / sd
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(ref["visible_median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["missing_resid"] = out["z_log1p_MET_pt"].to_numpy(float) - design @ ref["visible_coef"]
    out["disp_reco"] = 0.55 * out["z_secondary_vertex_count"] + 0.45 * out["z_packed_candidate_count"]
    out["visible_energy"] = out["z_log1p_HT"]
    out["multiplicity"] = out["z_N_jets_30"]
    out["btag_structure"] = 0.7 * out["z_N_btags_medium"] + 0.3 * out["z_jet_btag_ratio"]
    out["lepton_suppression"] = -(out["z_N_muons"] + out["z_N_electrons"]) / 2.0
    out["original_proxy"] = (
        0.3566 * out["z_secondary_vertex_count"]
        + 0.2112 * out["z_packed_candidate_count"]
        + 0.2019 * out["z_N_jets_30"]
        + 0.0926 * out["z_N_btags_medium"]
        + 0.0728 * out["z_log1p_HT"]
        + 0.0595 * out["z_log1p_MET_pt"]
        - 0.0055 * out["z_met_ht_ratio"]
    )
    return out


def candidate_formulas() -> list[tuple[str, dict[str, float]]]:
    formulas: list[tuple[str, dict[str, float]]] = [
        ("v3_missing_resid", {"missing_resid": 1.0}),
        ("original_proxy", {"original_proxy": 1.0}),
        ("disp_reco_only", {"disp_reco": 1.0}),
        ("missing_plus_disp", {"missing_resid": 0.7, "disp_reco": 0.3}),
        ("missing_plus_original", {"missing_resid": 0.6, "original_proxy": 0.4}),
        ("missing_disp_leptonveto", {"missing_resid": 0.65, "disp_reco": 0.25, "lepton_suppression": 0.10}),
        ("balanced_boundary", {"missing_resid": 0.35, "disp_reco": 0.25, "visible_energy": 0.15, "multiplicity": 0.15, "btag_structure": 0.10}),
        ("darren_like_boundary", {"disp_reco": 0.45, "multiplicity": 0.22, "btag_structure": 0.10, "visible_energy": 0.08, "missing_resid": 0.15}),
        ("missing_low_qcd", {"missing_resid": 0.8, "multiplicity": -0.15, "btag_structure": -0.05}),
        ("simple_recoil_trace", {"missing_resid": 0.75, "visible_energy": -0.15, "lepton_suppression": 0.10}),
        ("missing_disp_equal", {"missing_resid": 0.5, "disp_reco": 0.5}),
        ("missing_disp_visible", {"missing_resid": 0.5, "disp_reco": 0.3, "visible_energy": 0.2}),
        ("missing_disp_antivisible", {"missing_resid": 0.55, "disp_reco": 0.35, "visible_energy": -0.10}),
        ("original_plus_missing", {"original_proxy": 0.5, "missing_resid": 0.5}),
        ("original_plus_missing_leptonveto", {"original_proxy": 0.45, "missing_resid": 0.45, "lepton_suppression": 0.10}),
    ]
    return formulas


def apply_score(df: pd.DataFrame, weights: dict[str, float]) -> np.ndarray:
    score = np.zeros(len(df), dtype=float)
    for col, weight in weights.items():
        score += weight * df[col].to_numpy(float)
    return score


def define_edges(sm: pd.DataFrame, score_col: str) -> tuple[list[float], dict[int, list[float]]]:
    w = sm["event_weight"].to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, w, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score = sm[score_col].to_numpy(float)
    score_edges = {}
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        m = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[m], w[m], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_bands(df: pd.DataFrame, score_col: str, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["met_bin_v4"] = pd.cut(out["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(out), None, dtype=object)
    score = out[score_col].to_numpy(float)
    met_bin = out["met_bin_v4"].to_numpy()
    for i in range(MET_BINS):
        mask = met_bin == i
        edges = score_edges[i]
        for name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = name
    out["score_band_v4"] = band
    return out[out["score_band_v4"].notna()].copy()


def split_files(real: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (era, dataset), group in real.groupby(["era", "primary_dataset"]):
        files = sorted(group["source_file"].dropna().unique())
        for i, f in enumerate(files):
            split = "validation" if i % 3 == 2 else "development"
            rows.append({"era": era, "primary_dataset": dataset, "source_file": f, "split": split})
    splits = pd.DataFrame(rows)
    return real.merge(splits, on=["era", "primary_dataset", "source_file"], how="left")


def fit_shape_z(counts: pd.DataFrame) -> tuple[float, float, float, float]:
    fit = counts[counts["score_band"].isin(FIT_BANDS)].copy()
    if fit.empty or counts[counts["score_band"].eq("q099_100")].empty:
        return np.nan, np.nan, np.nan, np.nan
    obs = fit["observed"].to_numpy(float)
    exp = fit["expected_official"].to_numpy(float)
    x = fit["midpoint"].to_numpy(float) - 0.90

    def nll(theta: np.ndarray) -> float:
        a, b = theta
        lam = np.clip(exp * np.exp(a + b * x), 1e-9, np.inf)
        return float(np.sum(lam - obs * np.log(lam)) + 0.5 * (a / 3.0) ** 2 + 0.5 * (b / 10.0) ** 2)

    ratio = (obs.sum() + 0.5) / (exp.sum() + 0.5)
    result = minimize(nll, np.array([np.log(max(ratio, 1e-6)), 0.0]), method="Nelder-Mead", options={"maxiter": 5000})
    a, b = result.x
    pred_fit = exp * np.exp(a + b * x)
    resid = np.log((obs + 0.5) / (pred_fit + 0.5))
    rms = float(np.sqrt(np.average(resid**2, weights=np.sqrt(np.clip(obs, 1.0, np.inf)))))
    rel = float(np.sqrt(REL_UNC**2 + rms**2))
    tail = counts[counts["score_band"].eq("q099_100")]
    obs_tail = float(tail["observed"].sum())
    exp_tail = float((tail["expected_official"] * np.exp(a + b * (tail["midpoint"] - 0.90))).sum())
    z = float((obs_tail - exp_tail) / np.sqrt(max(exp_tail + (rel * exp_tail) ** 2, 1e-12)))
    return obs_tail, exp_tail, obs_tail / exp_tail if exp_tail > 0 else np.inf, z


def score_counts(real: pd.DataFrame, sm: pd.DataFrame, split: str, candidate: str, score_col: str) -> pd.DataFrame:
    rows = []
    sm_topo_cache = {}
    for era, dataset, jet_bin in product(["Run2016", "Run2015D"], ["MET", "HTMHT", "JetHT", "SingleMuon"], ["0jet", "1to2jets", "3to4jets", "5plusjets"]):
        r = real[(real["split"].eq(split)) & (real["era"].eq(era)) & (real["primary_dataset"].eq(dataset)) & (real["jet_bin"].eq(jet_bin))]
        if r.empty:
            continue
        if jet_bin not in sm_topo_cache:
            sm_topo_cache[jet_bin] = sm[sm["jet_bin"].eq(jet_bin)]
        s = sm_topo_cache[jet_bin]
        for met_bin, band in product(range(MET_BINS), SCORE_BANDS):
            rb = r[r["met_bin_v4"].eq(met_bin)]
            sb = s[s["met_bin_v4"].eq(met_bin)]
            if len(rb) < 5 or sb["event_weight"].sum() <= 0:
                continue
            frac = float(sb.loc[sb["score_band_v4"].eq(band), "event_weight"].sum() / sb["event_weight"].sum())
            rows.append(
                {
                    "candidate": candidate,
                    "split": split,
                    "era": era,
                    "primary_dataset": dataset,
                    "jet_bin": jet_bin,
                    "met_bin": met_bin,
                    "score_band": band,
                    "observed": int((rb["score_band_v4"].eq(band)).sum()),
                    "expected_official": len(rb) * frac,
                    "midpoint": MIDPOINTS[band],
                }
            )
    return pd.DataFrame(rows)


def summarize_counts(counts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if counts.empty:
        return pd.DataFrame()
    for keys, group in counts.groupby(["candidate", "split", "era", "primary_dataset", "jet_bin"]):
        obs, exp, oe, z = fit_shape_z(group)
        candidate, split, era, dataset, jet_bin = keys
        rows.append(
            {
                "candidate": candidate,
                "split": split,
                "era": era,
                "primary_dataset": dataset,
                "jet_bin": jet_bin,
                "q99_observed": obs,
                "q99_expected_profile": exp,
                "q99_obs_exp_profile": oe,
                "q99_profile_Z": z,
            }
        )
    return pd.DataFrame(rows)


def evaluate_candidate(summary: pd.DataFrame, split: str) -> dict:
    sub = summary[summary["split"].eq(split)]
    def z(era: str, dataset: str, jet_bin: str = "1to2jets") -> float:
        r = sub[(sub["era"].eq(era)) & (sub["primary_dataset"].eq(dataset)) & (sub["jet_bin"].eq(jet_bin))]
        return float(r["q99_profile_Z"].iloc[0]) if not r.empty and pd.notna(r["q99_profile_Z"].iloc[0]) else np.nan

    r16_sig = z("Run2016", "MET")
    r15_met = z("Run2015D", "MET")
    r15_htmht = z("Run2015D", "HTMHT")
    r15_jetht = z("Run2015D", "JetHT")
    r15_mu = z("Run2015D", "SingleMuon")
    # Jet-bin controls for Run2016 MET.
    r16_controls = []
    for jb in ["0jet", "3to4jets", "5plusjets"]:
        r16_controls.append(z("Run2016", "MET", jb))
    max_r16_ctrl = np.nanmax(np.abs(r16_controls)) if any(np.isfinite(r16_controls)) else np.nan
    max_2015_dataset_ctrl = np.nanmax(np.abs([r15_jetht, r15_mu]))
    stouffer_signal = np.nansum([r16_sig, r15_met, r15_htmht]) / np.sqrt(np.sum(np.isfinite([r16_sig, r15_met, r15_htmht])))
    # Penalize control failures and missing/negative validation.
    score = np.nanmin([r16_sig, r15_met, r15_htmht])
    score = score - max(0.0, max_r16_ctrl - 3.0) - max(0.0, max_2015_dataset_ctrl - 3.0)
    return {
        "split": split,
        "Run2016_MET_Z": r16_sig,
        "Run2015D_MET_Z": r15_met,
        "Run2015D_HTMHT_Z": r15_htmht,
        "Run2015D_JetHT_control_Z": r15_jetht,
        "Run2015D_SingleMuon_control_Z": r15_mu,
        "Run2016_max_jetbin_control_absZ": max_r16_ctrl,
        "Run2015D_max_dataset_control_absZ": max_2015_dataset_ctrl,
        "signal_stouffer_Z": stouffer_signal,
        "min_signal_Z": np.nanmin([r16_sig, r15_met, r15_htmht]),
        "selection_score": score,
        "passes_discovery_like_screen": bool(
            np.nanmin([r16_sig, r15_met, r15_htmht]) >= 5
            and max_r16_ctrl < 3
            and max_2015_dataset_ctrl < 3
        ),
    }


def main() -> None:
    ensure_dirs()
    sm_raw = read_sm()
    real_raw = read_real()
    sm_raw = add_base_transforms(sm_raw)
    ref = fit_reference(sm_raw)
    sm = apply_reference(sm_raw, ref)
    real = apply_reference(real_raw, ref)
    real = split_files(real)
    real.head(5000).to_csv(TABLES / "00_quality_clean_cross_era_real_features_preview.csv", index=False)

    split_audit = real.groupby(["era", "primary_dataset", "split"])["source_file"].nunique().reset_index(name="source_files")
    split_audit["events"] = real.groupby(["era", "primary_dataset", "split"]).size().to_numpy()
    split_audit.to_csv(TABLES / "01_train_validation_split_audit.csv", index=False)

    all_counts = []
    all_summaries = []
    evaluations = []
    formula_rows = []
    for candidate, weights in candidate_formulas():
        score_col = f"score_{candidate}"
        sm[score_col] = apply_score(sm, weights)
        real[score_col] = apply_score(real, weights)
        met_edges, score_edges = define_edges(sm, score_col)
        sm_b = assign_bands(sm, score_col, met_edges, score_edges)
        real_b = assign_bands(real, score_col, met_edges, score_edges)
        formula_rows.append({"candidate": candidate, **weights})
        for split in ["development", "validation"]:
            counts = score_counts(real_b, sm_b, split, candidate, score_col)
            summary = summarize_counts(counts)
            all_counts.append(counts)
            all_summaries.append(summary)
            evaluations.append({"candidate": candidate, **evaluate_candidate(summary, split)})

    counts_df = pd.concat(all_counts, ignore_index=True)
    summary_df = pd.concat(all_summaries, ignore_index=True)
    eval_df = pd.DataFrame(evaluations)
    formulas = pd.DataFrame(formula_rows).fillna(0.0)
    counts_df.to_csv(TABLES / "02_candidate_score_band_counts.csv", index=False)
    summary_df.to_csv(TABLES / "03_candidate_profile_summary.csv", index=False)
    eval_df.to_csv(TABLES / "04_candidate_screen_evaluations.csv", index=False)
    formulas.to_csv(TABLES / "05_candidate_formula_weights.csv", index=False)

    dev = eval_df[eval_df["split"].eq("development")].sort_values("selection_score", ascending=False)
    best_names = dev.head(10)["candidate"].tolist()
    validation = eval_df[(eval_df["split"].eq("validation")) & (eval_df["candidate"].isin(best_names))].copy()
    validation = validation.merge(dev[["candidate", "selection_score"]].rename(columns={"selection_score": "development_selection_score"}), on="candidate", how="left")
    validation = validation.sort_values(["passes_discovery_like_screen", "min_signal_Z", "signal_stouffer_Z"], ascending=False)
    validation.to_csv(TABLES / "06_top_development_candidates_validation_readout.csv", index=False)

    report = f"""# Quality-Aware N-Frame v4 Cross-Era Search

## Purpose

This is an exploratory parameter-adjustment search after the frozen Q99 v3 region failed to validate cleanly in Run2015D. The search is quality-clean from the start and compares candidate N-Frame scores across Run2016 and Run2015D.

The goal is to find whether any N-Frame parameterisation gives a promising cross-era pattern:

- Run2016 MET 1-to-2 jet q99 positive
- Run2015D MET and HTMHT 1-to-2 jet q99 positive
- Run2015D JetHT and SingleMuon controls not large
- Run2016 jet-bin controls not large

This is exploratory model development, not a discovery claim.

## Split Audit

{split_audit.to_markdown(index=False)}

## Top Development Candidates and Held-Out Validation

{validation.head(15).to_markdown(index=False)}

## Interpretation

If no candidate passes the held-out validation screen, then simple N-Frame parameter retuning is not enough to produce a breakthrough-level cross-era result with the current data and SM reference. If a candidate is strong only in development but not validation, it is likely overfitting file/era-specific structure.
"""
    (REPORTS / "01_QUALITY_AWARE_NFRAME_V4_CROSS_ERA_SEARCH_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: N-Frame v4 Cross-Era Search

Top development candidates were tested on held-out files.

{validation.head(10).to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_NFRAME_V4_CROSS_ERA_SEARCH.md").write_text(short, encoding="utf-8")
    print("QUALITY-AWARE N-FRAME V4 CROSS-ERA SEARCH COMPLETE")
    print(validation.head(10).to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
