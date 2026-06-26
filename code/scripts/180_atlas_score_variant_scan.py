from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "outputs_atlas_open_data_q99_analogue"
OUT = ROOT / "outputs_atlas_score_variant_scan"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = PREV / "sources"

SM_FEATURES = [
    SOURCES / "mc_410025.single_top_schan.1lep_features.csv",
    SOURCES / "mc_364165.Wmunu_PTV280_500_CVetoBVeto.1lep_features.csv",
    SOURCES / "mc_364166.Wmunu_PTV280_500_CFilterBVeto.1lep_features.csv",
    SOURCES / "mc_364167.Wmunu_PTV280_500_BFilter.1lep_features.csv",
    SOURCES / "mc_364168.Wmunu_PTV500_1000.1lep_features.csv",
]
DATA_FEATURES = SOURCES / "data_A.1lep_features.csv"

MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = ["q000_050", "q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099", "q099_100"]
MIDPOINTS = {"q000_050": 0.25, "q050_080": 0.65, "q080_090": 0.85, "q090_095": 0.925, "q095_0975": 0.9625, "q0975_099": 0.9825, "q099_100": 0.995}
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
SIDE_REPORT_BANDS = ["q080_090", "q090_095"]
REL_UNC = 0.30

VARIANTS = {
    "lepton_aware_resid": ["log1p_HT", "N_jets_30", "N_btags_medium", "N_leptons", "leading_lepton_pt"],
    "jets_only_resid": ["log1p_HT", "N_jets_30", "N_btags_medium"],
    "jetcount_only_resid": ["N_jets_30"],
    "raw_missing_z": [],
}


def ensure_dirs() -> None:
    for p in [OUT, TABLES, REPORTS]:
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


def load_sm() -> pd.DataFrame:
    frames = []
    for p in SM_FEATURES:
        if p.exists():
            frames.append(pd.read_csv(p, low_memory=False))
    if not frames:
        raise SystemExit("No SM feature files found.")
    sm = pd.concat(frames, ignore_index=True)
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    return sm


def fit_variant(sm: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, dict]:
    sm = sm.copy()
    w = sm["event_weight"].abs().clip(lower=1e-12).to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), w)
    y = ((sm["log1p_MET_pt"] - mean_met) / sd_met).to_numpy(float)
    if not columns:
        sm["score"] = y
        return sm, {"mean_met": mean_met, "sd_met": sd_met, "columns": columns, "median": [], "coef": []}
    x_df = sm[columns].apply(pd.to_numeric, errors="coerce")
    med = x_df.median().to_numpy(float)
    x = x_df.fillna(pd.Series(med, index=columns)).to_numpy(float)
    sw = np.sqrt(w)
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    sm["score"] = y - design @ coef
    return sm, {"mean_met": mean_met, "sd_met": sd_met, "columns": columns, "median": med, "coef": coef}


def apply_variant(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    y = ((out["log1p_MET_pt"] - params["mean_met"]) / params["sd_met"]).to_numpy(float)
    cols = params["columns"]
    if not cols:
        out["score"] = y
        return out
    x = out[cols].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["median"], index=cols)).to_numpy(float)
    out["score"] = y - np.column_stack([np.ones(len(x)), x]) @ params["coef"]
    return out


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    w = sm["event_weight"].abs().clip(lower=1e-12).to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, w, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score_edges = {}
    score = sm["score"].to_numpy(float)
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
    score = out["score"].to_numpy(float)
    met_bin = out["met_bin"].to_numpy()
    for i in range(MET_BINS):
        m = met_bin == i
        edges = score_edges[i]
        for name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[m & (score >= lo) & (score < hi)] = name
    out["score_band"] = band
    return out[out["score_band"].notna()].copy()


def expected_fractions(sm: pd.DataFrame) -> dict:
    sm = sm.copy()
    sm["jet_bin"] = pd.cut(sm["N_jets_30"], bins=[-np.inf, 0, 2, 4, np.inf], labels=["0jet", "1to2jets", "3to4jets", "5plusjets"]).astype(str)
    out = {}
    for jet, met, band in product(["0jet", "1to2jets", "3to4jets", "5plusjets"], range(MET_BINS), SCORE_BANDS):
        sub = sm[(sm["jet_bin"].eq(jet)) & (sm["met_bin"].eq(met))]
        den = sub["event_weight"].abs().sum()
        num = sub.loc[sub["score_band"].eq(band), "event_weight"].abs().sum()
        out[(jet, met, band)] = float(num / den) if den > 0 else 0.0
    return out


def init_counts() -> dict:
    return {
        (jet, met, band): {"observed": 0, "met_bin_n": 0}
        for jet, met, band in product(["0jet", "1to2jets", "3to4jets", "5plusjets"], range(MET_BINS), SCORE_BANDS)
    }


def accumulate_real(params: dict, met_edges: list[float], score_edges: dict[int, list[float]]) -> dict:
    counts = init_counts()
    for chunk in pd.read_csv(DATA_FEATURES, chunksize=700_000):
        chunk = assign_bands(apply_variant(chunk, params), met_edges, score_edges)
        chunk["jet_bin"] = pd.cut(chunk["N_jets_30"], bins=[-np.inf, 0, 2, 4, np.inf], labels=["0jet", "1to2jets", "3to4jets", "5plusjets"]).astype(str)
        met_totals = chunk.groupby(["jet_bin", "met_bin"], observed=False).size()
        band_totals = chunk.groupby(["jet_bin", "met_bin", "score_band"], observed=False).size()
        for (jet, met), n in met_totals.items():
            if pd.isna(met):
                continue
            for band in SCORE_BANDS:
                counts[(str(jet), int(met), band)]["met_bin_n"] += int(n)
        for (jet, met, band), n in band_totals.items():
            if pd.isna(met):
                continue
            counts[(str(jet), int(met), str(band))]["observed"] += int(n)
    return counts


def z_unc(obs: float, exp: float, rel: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel * exp) ** 2, 1e-12)))


def summarize_counts(variant: str, counts: dict, fractions: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for key, val in counts.items():
        jet, met, band = key
        exp = val["met_bin_n"] * fractions[key]
        rows.append({"variant": variant, "jet_bin": jet, "met_bin": met, "score_band": band, "observed": val["observed"], "met_bin_n": val["met_bin_n"], "sm_fraction": fractions[key], "expected_official_shape": exp, "midpoint": MIDPOINTS[band]})
    table = pd.DataFrame(rows)
    summaries = []
    for jet, sub in table.groupby("jet_bin"):
        fit = sub[sub["score_band"].isin(SIDEBAND_FIT_BANDS)]
        oe = (fit["observed"].to_numpy(float) + 0.5) / (fit["expected_official_shape"].to_numpy(float) + 0.5)
        x = fit["midpoint"].to_numpy(float) - 0.90
        y = np.log(np.clip(oe, 1e-6, np.inf))
        w = np.sqrt(np.clip(fit["observed"].to_numpy(float), 1.0, np.inf))
        design = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(design * w[:, None], y * w, rcond=None)
        sideband_rms = float(np.sqrt(np.average((y - design @ coef) ** 2, weights=w)))
        idx = table["jet_bin"].eq(jet)
        table.loc[idx, "shape_correction"] = np.exp(coef[0] + (table.loc[idx, "midpoint"] - 0.90) * coef[1])
        table.loc[idx, "expected_shape"] = table.loc[idx, "expected_official_shape"] * table.loc[idx, "shape_correction"]
        shaped = table[idx]
        sig = shaped[shaped["score_band"].eq("q099_100")]
        side = shaped[shaped["score_band"].isin(SIDE_REPORT_BANDS)]
        rel = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
        obs = float(sig["observed"].sum())
        exp = float(sig["expected_shape"].sum())
        side_obs = float(side["observed"].sum())
        side_exp = float(side["expected_official_shape"].sum())
        summaries.append({"variant": variant, "jet_bin": jet, "real_events": int(shaped.groupby("met_bin")["met_bin_n"].first().sum()), "sideband_80_95_obs_exp": side_obs / side_exp if side_exp > 0 else np.inf, "q99_observed": obs, "q99_expected_shape": exp, "q99_obs_exp": obs / exp if exp > 0 else np.inf, "sideband_log_rms": sideband_rms, "relative_uncertainty_used": rel, "q99_Z": z_unc(obs, exp, rel)})
    return table, pd.DataFrame(summaries)


def main() -> None:
    ensure_dirs()
    sm_base = load_sm()
    all_tables = []
    all_summaries = []
    for variant, columns in VARIANTS.items():
        print(f"Running variant {variant}", flush=True)
        sm, params = fit_variant(sm_base, columns)
        met_edges, score_edges = define_bins(sm)
        sm = assign_bands(sm, met_edges, score_edges)
        fractions = expected_fractions(sm)
        counts = accumulate_real(params, met_edges, score_edges)
        table, summary = summarize_counts(variant, counts, fractions)
        all_tables.append(table)
        all_summaries.append(summary)
    counts_df = pd.concat(all_tables, ignore_index=True)
    summary_df = pd.concat(all_summaries, ignore_index=True)
    counts_df.to_csv(TABLES / "01_atlas_score_variant_counts.csv", index=False)
    summary_df.to_csv(TABLES / "02_atlas_score_variant_summary.csv", index=False)
    report = f"""# ATLAS Score Variant Scan

## Purpose

The first ATLAS one-lepton analogue did not reproduce the CMS 1-2 jet Q99 excess. This scan checks whether that depends on the exact visible-axis definition.

## Variants

{pd.DataFrame([{"variant": k, "visible_columns": ", ".join(v) if v else "none/raw missing z"} for k, v in VARIANTS.items()]).to_markdown(index=False)}

## Result

{summary_df.to_markdown(index=False)}

## Interpretation

The key row is `1to2jets` for each variant. If none is strongly positive, the public ATLAS exactly-one-lepton channel does not replicate the CMS MET-stream Q99 1-2 jet trace.
"""
    (REPORTS / "01_ATLAS_SCORE_VARIANT_SCAN_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: ATLAS Score Variant Scan

{summary_df.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_ATLAS_SCORE_VARIANT_SCAN.md").write_text(short, encoding="utf-8")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
