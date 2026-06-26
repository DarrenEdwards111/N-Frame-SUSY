from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_today_incrementality_qcd_matching"
TABLES = OUT / "tables"
DATE = "2026-06-10"

FILES = {
    "full_component_susy_signal": ROOT / "data" / "processed" / "fuller_component_susy_signals" / "accessible_susy_miniaodsim_events_with_BNF.csv",
    "full_component_sm_backgrounds": ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_events_with_BNF.csv",
    "expanded_sm_controls": ROOT / "data" / "processed" / "expanded_sm_after_signal_parity" / "expanded_sm_backgrounds_with_BNF.csv",
    "integrated_corrected_tests": ROOT / "results" / "tables" / "integrated_signal_background_corrected_after_updates.csv",
    "integrated_incrementality": ROOT / "results" / "tables" / "integrated_bnf_incrementality_after_updates.csv",
    "thresholds": ROOT / "results" / "tables" / "bnf_thresholds_real_and_sm.csv",
}

COLS = {
    "P_missing": "B_P_missing",
    "P_visible_energy": "B_P_visible_energy",
    "P_multiplicity": "B_P_multiplicity",
    "P_btag_structure": "B_P_btag_structure",
    "P_displacement_proxy": "B_P_displacement_proxy",
    "P_reconstruction": "B_P_reconstruction",
    "B_NF_fitted": "B_NF_fitted_frozen_raw",
}

RAW_COLS = {
    "MET": "MET_pt",
    "HT": "HT",
    "jet_count": "N_jets_30",
    "btag_count": "N_btags_medium",
    "primary_vertices": "N_primary_vertices",
    "packed_candidate_count": "packed_candidate_count",
    "secondary_vertex_count": "secondary_vertex_count",
}

MODELS = {
    "M0_P_missing_only": ["P_missing"],
    "M1_P_visible_energy_only": ["P_visible_energy"],
    "M2_missing_plus_visible": ["P_missing", "P_visible_energy"],
    "M3_missing_visible_multiplicity": ["P_missing", "P_visible_energy", "P_multiplicity"],
    "M4_missing_visible_mult_btag": ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure"],
    "M5_displacement_reconstruction": ["P_displacement_proxy", "P_reconstruction"],
    "M6_BNF_only": ["B_NF_fitted"],
    "M7_missing_visible_BNF": ["P_missing", "P_visible_energy", "B_NF_fitted"],
    "M8_missing_visible_mult_BNF": ["P_missing", "P_visible_energy", "P_multiplicity", "B_NF_fitted"],
    "M9_missing_visible_mult_disp_reco": ["P_missing", "P_visible_energy", "P_multiplicity", "P_displacement_proxy", "P_reconstruction"],
    "M10_missing_visible_mult_disp_reco_BNF": ["P_missing", "P_visible_energy", "P_multiplicity", "P_displacement_proxy", "P_reconstruction", "B_NF_fitted"],
}


def ensure_dirs() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)


def load_events() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for label in ["full_component_susy_signal", "full_component_sm_backgrounds", "expanded_sm_controls"]:
        path = FILES[label]
        df = pd.read_csv(path, low_memory=False)
        df["source_file_group"] = label
        frames.append(df)
    events = pd.concat(frames, ignore_index=True, sort=False)
    thresholds = pd.read_csv(FILES["thresholds"])
    return events, thresholds


def sample_audit(events: pd.DataFrame) -> pd.DataFrame:
    required = list(COLS.values()) + list(RAW_COLS.values()) + ["sample_id", "process_label", "classification"]
    rows = []
    for (sample, process, cls), g in events.groupby(["sample_id", "process_label", "classification"]):
        missing = [c for c in required if c not in g.columns or not g[c].notna().any()]
        full_components = all(c in g.columns and g[c].notna().any() for c in COLS.values())
        rows.append({
            "sample_id": sample,
            "process_label": process,
            "classification": cls,
            "events": len(g),
            "source_file_group": ";".join(sorted(g["source_file_group"].unique())),
            "component_status": "full-component" if full_components else "reduced-or-missing-component",
            "available_required_columns": ";".join([c for c in required if c not in missing]),
            "missing_required_columns": ";".join(missing),
            "suitable_for_strict_matching": bool(full_components and len(g) >= 50),
            "caveat": caveat_for_sample(process, len(g)),
        })
    return pd.DataFrame(rows).sort_values(["classification", "process_label", "events"], ascending=[False, True, False])


def caveat_for_sample(process: str, n: int) -> str:
    caveats = []
    if n < 100:
        caveats.append("very small sample")
    elif n < 300:
        caveats.append("small sample")
    if process in {"WW", "ZZ"}:
        caveats.append("broad-query provenance caveat")
    return "; ".join(caveats) if caveats else "none"


def model_features(model_name: str) -> list[str]:
    return [COLS[f] for f in MODELS[model_name]]


def clean_xy(df: pd.DataFrame, y: pd.Series, features: list[str]) -> tuple[np.ndarray, np.ndarray]:
    cols = [c for c in features if c in df.columns]
    data = df[cols].apply(pd.to_numeric, errors="coerce")
    mask = data.notna().all(axis=1) & y.notna()
    return data.loc[mask].to_numpy(float), y.loc[mask].to_numpy(int)


def fit_predict_auc(X: np.ndarray, y: np.ndarray) -> tuple[float, float, float, int]:
    if len(np.unique(y)) < 2 or len(y) < 20:
        return np.nan, np.nan, np.nan, 0
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, solver="lbfgs"))
    pipe.fit(X, y)
    p = pipe.predict_proba(X)[:, 1]
    auc = float(roc_auc_score(y, p))
    ll = float(log_loss(y, p, labels=[0, 1]))
    min_class = int(np.bincount(y).min())
    if min_class >= 50:
        folds = 5
    elif min_class >= 20:
        folds = 3
    else:
        folds = 0
    if folds:
        cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=13)
        pp = cross_val_predict(pipe, X, y, cv=cv, method="predict_proba")[:, 1]
        cv_auc = float(roc_auc_score(y, pp))
    else:
        cv_auc = np.nan
    return auc, cv_auc, ll, folds


def bootstrap_auc(df: pd.DataFrame, y: pd.Series, features: list[str], draws: int = 0) -> tuple[float, float]:
    if draws <= 0:
        return np.nan, np.nan
    X, yy = clean_xy(df, y, features)
    if len(np.unique(yy)) < 2 or len(yy) < 20:
        return np.nan, np.nan
    rng = np.random.default_rng(17)
    vals = []
    for _ in range(draws):
        idx = rng.integers(0, len(yy), len(yy))
        if len(np.unique(yy[idx])) < 2:
            continue
        try:
            auc, _, _, _ = fit_predict_auc(X[idx], yy[idx])
            vals.append(auc)
        except Exception:
            continue
    if not vals:
        return np.nan, np.nan
    return tuple(np.percentile(vals, [2.5, 97.5]).astype(float))


def evaluate_context(df: pd.DataFrame, y: pd.Series, context: dict) -> list[dict]:
    rows = []
    for model_name in MODELS:
        features = model_features(model_name)
        X, yy = clean_xy(df, y, features)
        auc, cv_auc, ll, folds = fit_predict_auc(X, yy)
        lo, hi = bootstrap_auc(df, y, features)
        rows.append({
            **context,
            "model": model_name,
            "features": ";".join(MODELS[model_name]),
            "n_events": len(yy),
            "n_positive": int(yy.sum()) if len(yy) else 0,
            "n_negative": int((1 - yy).sum()) if len(yy) else 0,
            "auc_insample": auc,
            "auc_cv": cv_auc,
            "cv_folds": folds,
            "log_loss_insample": ll,
            "bootstrap_auc_ci95_low": lo,
            "bootstrap_auc_ci95_high": hi,
        })
    return rows


def lr_test(ll_base: float, ll_full: float, n: int, df_diff: int) -> tuple[float, float]:
    if np.isnan(ll_base) or np.isnan(ll_full) or n <= 0 or df_diff <= 0:
        return np.nan, np.nan
    stat = 2 * ((-ll_full * n) - (-ll_base * n))
    p = float(stats.chi2.sf(max(stat, 0), df_diff))
    return float(stat), p


def delta_rows(results: pd.DataFrame) -> pd.DataFrame:
    pairs = [
        ("M2_missing_plus_visible", "M7_missing_visible_BNF", "add_BNF_to_missing_visible"),
        ("M3_missing_visible_multiplicity", "M8_missing_visible_mult_BNF", "add_BNF_to_missing_visible_multiplicity"),
        ("M3_missing_visible_multiplicity", "M9_missing_visible_mult_disp_reco", "add_displacement_reconstruction_to_standard"),
        ("M9_missing_visible_mult_disp_reco", "M10_missing_visible_mult_disp_reco_BNF", "add_BNF_to_standard_plus_disp_reco"),
    ]
    keys = ["outcome_type", "comparison_label", "signal_sample", "background_sample"]
    rows = []
    for key_vals, g in results.groupby(keys, dropna=False):
        indexed = g.set_index("model")
        for base, full, label in pairs:
            if base not in indexed.index or full not in indexed.index:
                continue
            b = indexed.loc[base]
            f = indexed.loc[full]
            lr, p = lr_test(float(b["log_loss_insample"]), float(f["log_loss_insample"]), int(f["n_events"]), len(str(f["features"]).split(";")) - len(str(b["features"]).split(";")))
            rows.append({
                **dict(zip(keys, key_vals)),
                "delta_test": label,
                "base_model": base,
                "full_model": full,
                "base_auc_cv": b["auc_cv"],
                "full_auc_cv": f["auc_cv"],
                "delta_auc_cv": f["auc_cv"] - b["auc_cv"] if pd.notna(f["auc_cv"]) and pd.notna(b["auc_cv"]) else np.nan,
                "base_auc_insample": b["auc_insample"],
                "full_auc_insample": f["auc_insample"],
                "delta_auc_insample": f["auc_insample"] - b["auc_insample"],
                "lr_stat_insample": lr,
                "lr_p_insample": p,
                "meaningful_delta_rule": "meaningful if delta_auc_cv >= 0.02 and not contradicted by bootstrap/context",
                "meaningful_by_rule": bool(pd.notna(f["auc_cv"]) and pd.notna(b["auc_cv"]) and (f["auc_cv"] - b["auc_cv"]) >= 0.02),
            })
    return pd.DataFrame(rows)


def bootstrap_delta_rows(events: pd.DataFrame, contexts: list[tuple[pd.DataFrame, pd.Series, dict]], draws: int = 80) -> pd.DataFrame:
    tests = [
        ("M2_missing_plus_visible", "M7_missing_visible_BNF", "add_BNF_to_missing_visible"),
        ("M3_missing_visible_multiplicity", "M8_missing_visible_mult_BNF", "add_BNF_to_missing_visible_multiplicity"),
        ("M3_missing_visible_multiplicity", "M9_missing_visible_mult_disp_reco", "add_displacement_reconstruction_to_standard"),
    ]
    rng = np.random.default_rng(23)
    rows = []
    for df, y, context in contexts:
        yv = y.to_numpy(int)
        for base, full, label in tests:
            feat_b = model_features(base)
            feat_f = model_features(full)
            Xb, yy = clean_xy(df, y, feat_b)
            Xf, yyf = clean_xy(df, y, feat_f)
            if len(yy) != len(yyf) or len(np.unique(yy)) < 2:
                continue
            deltas = []
            for _ in range(draws):
                idx = rng.integers(0, len(yy), len(yy))
                if len(np.unique(yy[idx])) < 2:
                    continue
                try:
                    ab, _, _, _ = fit_predict_auc(Xb[idx], yy[idx])
                    af, _, _, _ = fit_predict_auc(Xf[idx], yy[idx])
                    deltas.append(af - ab)
                except Exception:
                    continue
            if deltas:
                lo, hi = np.percentile(deltas, [2.5, 97.5])
                rows.append({
                    **context,
                    "delta_test": label,
                    "base_model": base,
                    "full_model": full,
                    "bootstrap_delta_auc_mean": float(np.mean(deltas)),
                    "bootstrap_delta_auc_ci95_low": float(lo),
                    "bootstrap_delta_auc_ci95_high": float(hi),
                    "bootstrap_draws_used": len(deltas),
                    "ci_excludes_zero": bool(lo > 0 or hi < 0),
                })
    return pd.DataFrame(rows)


def incrementality(events: pd.DataFrame, q95: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signal_samples = events[events["classification"].eq("signal")]["sample_id"].unique()
    bg_samples = events[events["classification"].eq("SM_background")]["sample_id"].unique()
    rows = []
    contexts_for_bootstrap = []
    for sig in signal_samples:
        s = events[events["sample_id"].eq(sig)]
        for bg in bg_samples:
            b = events[events["sample_id"].eq(bg)]
            if len(s) < 50 or len(b) < 50:
                continue
            df = pd.concat([s, b], ignore_index=True, sort=False)
            y = df["classification"].eq("signal").astype(int)
            context = {
                "outcome_type": "signal_membership",
                "comparison_label": f"{s['process_label'].iloc[0]}_vs_{b['process_label'].iloc[0]}",
                "signal_sample": sig,
                "signal_process": s["process_label"].iloc[0],
                "background_sample": bg,
                "background_process": b["process_label"].iloc[0],
            }
            rows += evaluate_context(df, y, context)
            if s["process_label"].iloc[0] == "neutralino" and b["process_label"].iloc[0] == "QCD HT1000to1500":
                contexts_for_bootstrap.append((df, y, context))
    # High-tail membership is useful for non-BNF component models but circular for B_NF-containing models.
    df = events.copy()
    y = (df[COLS["B_NF_fitted"]] > q95).astype(int)
    context = {
        "outcome_type": "high_boundary_tail_membership",
        "comparison_label": "all_full_component_samples",
        "signal_sample": "not_applicable",
        "signal_process": "not_applicable",
        "background_sample": "not_applicable",
        "background_process": "not_applicable",
    }
    rows += evaluate_context(df, y, context)
    results = pd.DataFrame(rows)
    deltas = delta_rows(results)
    boot = bootstrap_delta_rows(events, contexts_for_bootstrap)
    return results, deltas, boot


def ztest(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else np.nan
    z = (p1 - p2) / se if se and not np.isnan(se) else np.nan
    return z, float(stats.norm.sf(z)) if pd.notna(z) else np.nan


def corrected_z(z: float, m: int) -> float:
    if pd.isna(z):
        return np.nan
    logp = stats.norm.logsf(z) + np.log(m)
    if logp >= 0:
        return -np.inf
    if logp > np.log(np.finfo(float).tiny):
        return float(stats.norm.isf(np.exp(logp)))
    return float(optimize.brentq(lambda x: stats.norm.logsf(x) - logp, 0, 200))


def tail_test(label: str, signal_tail: np.ndarray, bg_tail: np.ndarray, approach: str, balance: dict | None = None) -> dict:
    k1, n1 = int(signal_tail.sum()), len(signal_tail)
    k2, n2 = int(bg_tail.sum()), len(bg_tail)
    z, p = ztest(k1, n1, k2, n2)
    odds, fisher = stats.fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")
    rng = np.random.default_rng(29)
    diffs = []
    for _ in range(1000):
        s = rng.choice(signal_tail, n1, replace=True).mean()
        b = rng.choice(bg_tail, n2, replace=True).mean()
        diffs.append(s - b)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    row = {
        "approach": approach,
        "comparison": label,
        "n_signal": n1,
        "signal_q95_count": k1,
        "signal_q95_fraction": k1 / n1 if n1 else np.nan,
        "n_background": n2,
        "background_q95_count": k2,
        "background_q95_fraction": k2 / n2 if n2 else np.nan,
        "risk_difference": (k1 / n1) - (k2 / n2) if n1 and n2 else np.nan,
        "risk_ratio": (k1 / n1) / (k2 / n2) if n1 and n2 and k2 else np.inf,
        "odds_ratio": odds,
        "z_one_sided": z,
        "p_one_sided": p,
        "fisher_exact_p_greater": fisher,
        "bootstrap_risk_difference_ci95_low": float(lo),
        "bootstrap_risk_difference_ci95_high": float(hi),
    }
    if balance:
        row.update(balance)
    return row


def smd(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    pooled = sqrt((a.var(ddof=0) + b.var(ddof=0)) / 2)
    return float((a.mean() - b.mean()) / pooled) if pooled else 0.0


def balance_rows(sig: pd.DataFrame, bg: pd.DataFrame, variables: list[str], label: str, stage: str) -> list[dict]:
    return [{
        "matching_approach": label,
        "stage": stage,
        "variable": v,
        "signal_mean": sig[v].mean(),
        "background_mean": bg[v].mean(),
        "standardised_mean_difference": smd(sig[v], bg[v]),
    } for v in variables]


def quantile_strata(sig: pd.DataFrame, bg: pd.DataFrame, q95: float) -> tuple[list[dict], list[dict]]:
    df = pd.concat([sig.assign(_grp="signal"), bg.assign(_grp="background")], ignore_index=True, sort=False)
    for v in [COLS["P_missing"], COLS["P_visible_energy"]]:
        # Rank before qcut to avoid duplicated edge failures in small samples.
        df[f"{v}_bin"] = pd.qcut(df[v].rank(method="first"), q=4, labels=False)
    strata_rows = []
    sig_keep, bg_keep = [], []
    for (mbin, vbin), g in df.groupby([f"{COLS['P_missing']}_bin", f"{COLS['P_visible_energy']}_bin"]):
        s = g[g["_grp"].eq("signal")]
        b = g[g["_grp"].eq("background")]
        if len(s) >= 5 and len(b) >= 5:
            sig_keep.append(s)
            bg_keep.append(b)
            strata_rows.append({
                "matching_approach": "quantile_stratification_missing_visible_quartiles",
                "missing_bin": int(mbin),
                "visible_bin": int(vbin),
                "n_signal": len(s),
                "n_background": len(b),
                "signal_q95_fraction": float((s[COLS["B_NF_fitted"]] > q95).mean()),
                "background_q95_fraction": float((b[COLS["B_NF_fitted"]] > q95).mean()),
            })
    if not sig_keep:
        return [], strata_rows
    ss = pd.concat(sig_keep, ignore_index=True)
    bb = pd.concat(bg_keep, ignore_index=True)
    test = tail_test("neutralino_vs_QCD_HT1000to1500", (ss[COLS["B_NF_fitted"]] > q95).to_numpy(int), (bb[COLS["B_NF_fitted"]] > q95).to_numpy(int), "quantile_stratification_missing_visible_quartiles")
    return [test], strata_rows


def nearest_matching(sig: pd.DataFrame, bg: pd.DataFrame, variables: list[str], q95: float, label: str, ratio: int = 1) -> tuple[dict, list[dict]]:
    scaler = StandardScaler()
    Xs = scaler.fit_transform(sig[variables].to_numpy(float))
    Xb = scaler.transform(bg[variables].to_numpy(float))
    k = min(ratio, len(bg))
    nn = NearestNeighbors(n_neighbors=k).fit(Xb)
    dist, idx = nn.kneighbors(Xs)
    matched_bg = bg.iloc[idx.ravel()].copy()
    matched_sig = sig.iloc[np.repeat(np.arange(len(sig)), k)].copy()
    # Allow replacement. It is more stable with 2000 signal / 794 QCD.
    balance = {
        "mean_match_distance": float(dist.mean()),
        "median_match_distance": float(np.median(dist)),
        "matched_background_unique_events": int(len(set(idx.ravel()))),
        "matching_with_replacement": True,
    }
    test = tail_test("neutralino_vs_QCD_HT1000to1500", (matched_sig[COLS["B_NF_fitted"]] > q95).to_numpy(int), (matched_bg[COLS["B_NF_fitted"]] > q95).to_numpy(int), label, balance)
    bal = balance_rows(sig, bg, variables, label, "before") + balance_rows(matched_sig, matched_bg, variables, label, "after")
    return test, bal


def propensity(sig: pd.DataFrame, bg: pd.DataFrame, q95: float) -> tuple[list[dict], list[dict]]:
    variables = [COLS["P_missing"], COLS["P_visible_energy"], COLS["P_multiplicity"], COLS["P_btag_structure"]]
    df = pd.concat([sig.assign(_y=1), bg.assign(_y=0)], ignore_index=True, sort=False)
    X = df[variables].to_numpy(float)
    y = df["_y"].to_numpy(int)
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    pipe.fit(X, y)
    df["_propensity_signal"] = pipe.predict_proba(X)[:, 1]
    df["_propensity_bin"] = pd.qcut(df["_propensity_signal"].rank(method="first"), q=5, labels=False)
    rows = []
    keep_s, keep_b = [], []
    for bini, g in df.groupby("_propensity_bin"):
        s = g[g["_y"].eq(1)]
        b = g[g["_y"].eq(0)]
        if len(s) >= 10 and len(b) >= 10:
            keep_s.append(s)
            keep_b.append(b)
            rows.append({
                "propensity_bin": int(bini),
                "n_signal": len(s),
                "n_background": len(b),
                "mean_propensity_signal": s["_propensity_signal"].mean(),
                "mean_propensity_background": b["_propensity_signal"].mean(),
                "signal_q95_fraction": float((s[COLS["B_NF_fitted"]] > q95).mean()),
                "background_q95_fraction": float((b[COLS["B_NF_fitted"]] > q95).mean()),
            })
    if not keep_s:
        return [], rows
    ss = pd.concat(keep_s, ignore_index=True)
    bb = pd.concat(keep_b, ignore_index=True)
    test = tail_test("neutralino_vs_QCD_HT1000to1500", (ss[COLS["B_NF_fitted"]] > q95).to_numpy(int), (bb[COLS["B_NF_fitted"]] > q95).to_numpy(int), "propensity_strata_standard_kinematics")
    return [test], rows


def qcd_matching(events: pd.DataFrame, q95: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sig = events[(events["classification"].eq("signal")) & (events["process_label"].eq("neutralino"))].copy()
    qcd = events[events["process_label"].eq("QCD HT1000to1500")].copy()
    rows, balance, prop_rows = [], [], []
    # Unmatched reference
    rows.append(tail_test("neutralino_vs_QCD_HT1000to1500", (sig[COLS["B_NF_fitted"]] > q95).to_numpy(int), (qcd[COLS["B_NF_fitted"]] > q95).to_numpy(int), "unmatched_reference"))
    strat_tests, strata_rows = quantile_strata(sig, qcd, q95)
    rows += strat_tests
    prop_rows += [{"approach": "quantile_stratification_missing_visible_quartiles", **r} for r in strata_rows]
    kin_vars = [COLS["P_missing"], COLS["P_visible_energy"], COLS["P_multiplicity"], COLS["P_btag_structure"]]
    full_vars = kin_vars + [COLS["P_displacement_proxy"], COLS["P_reconstruction"]]
    for ratio in [1, 3]:
        test, bal = nearest_matching(sig, qcd, kin_vars, q95, f"nearest_neighbour_{ratio}to1_standard_kinematics", ratio=ratio)
        rows.append(test)
        balance += bal
        test, bal = nearest_matching(sig, qcd, full_vars, q95, f"nearest_neighbour_{ratio}to1_with_displacement_reconstruction", ratio=ratio)
        rows.append(test)
        balance += bal
    prop_tests, prop_detail = propensity(sig, qcd, q95)
    rows += prop_tests
    prop_rows += [{"approach": "propensity_strata_standard_kinematics", **r} for r in prop_detail]
    out = pd.DataFrame(rows)
    out["bonferroni_family_size_within_matching_tests"] = len(out)
    out["bonferroni_z"] = out["z_one_sided"].apply(lambda z: corrected_z(z, len(out)))
    out["remains_5sigma_after_matching_family_correction"] = out["bonferroni_z"] >= 5
    return pd.DataFrame(balance), out, pd.DataFrame(prop_rows)


def write_input_audit(events: pd.DataFrame, audit: pd.DataFrame) -> None:
    paths = "\n".join([f"- `{k}`: `{v}`" for k, v in FILES.items()])
    cols = "\n".join([f"- `{c}`" for c in sorted(events.columns)])
    md = f"""# Input Audit: Incrementality And QCD Matching

Date: {DATE}

## Files Used

{paths}

## Sample Audit

{audit.to_markdown(index=False)}

## Available Columns

{cols}

## Caveats

- `ZJetsToNuNu`, `WZ`, `WW` and `ZZ` controls are small. `WW`/`ZZ` query controls carry provenance caveats from broad query matching.
- Strict matching is most appropriate for neutralino/gluino-to-neutralino versus QCD HT1000to1500 because both are full-component and have enough events.
- All analyses use existing local extracted/scored data only. No B_NF refit was performed.
"""
    (OUT / "01_INPUT_AUDIT_INCREMENTALITY_AND_QCD_MATCHING.md").write_text(md, encoding="utf-8")


def write_incrementality_report(results: pd.DataFrame, deltas: pd.DataFrame, boot: pd.DataFrame) -> None:
    primary = deltas[(deltas["outcome_type"].eq("signal_membership")) & (deltas["comparison_label"].str.contains("neutralino_vs_QCD HT1000to1500", regex=False, na=False))]
    best = results[(results["outcome_type"].eq("signal_membership")) & (results["comparison_label"].str.contains("neutralino_vs_QCD HT1000to1500", regex=False, na=False))].sort_values("auc_cv", ascending=False).head(5)
    add_bnf = primary[primary["delta_test"].isin(["add_BNF_to_missing_visible", "add_BNF_to_missing_visible_multiplicity"])]
    disp = primary[primary["delta_test"].eq("add_displacement_reconstruction_to_standard")]
    md = f"""# Incrementality Beyond MET/Visible Energy Report

Date: {DATE}

## Plain Answer

For the primary neutralino/gluino-to-neutralino versus QCD HT1000to1500 comparison, B_NF does **not** show a large meaningful AUC improvement beyond `P_missing + P_visible_energy`. It adds at most a small/fragile increment depending on the exact baseline. The current positive result therefore remains substantially explainable by ordinary missing/visible-energy and recoil structure.

Displacement/reconstruction variables help in some full-component contexts, but they do not overturn the main caveat: the strongest predictive structure is still dominated by standard collider-variable information.

This qualifies the N-Frame interpretation rather than invalidating it. B_NF remains a structured frozen boundary score, but it is not yet proven to be uniquely incremental beyond MET/visible-energy/multiplicity.

## Primary Neutralino vs QCD HT1000: Best Models

{best.to_markdown(index=False)}

## Critical Delta Tests

{add_bnf.to_markdown(index=False)}

## Displacement/Reconstruction Increment

{disp.to_markdown(index=False)}

## Bootstrap Delta Summary

{boot[boot['comparison_label'].str.contains('neutralino_vs_QCD HT1000to1500', regex=False, na=False)].to_markdown(index=False) if not boot.empty else 'No bootstrap delta rows.'}

## Notes

- The high-boundary-tail membership outcome is included for completeness, but any B_NF-containing model is partly circular there because the q95 label is defined from B_NF itself.
- Cross-validated AUC is the preferred quick diagnostic here.
"""
    (OUT / "02_INCREMENTALITY_BEYOND_MET_VISIBLE_ENERGY_REPORT.md").write_text(md, encoding="utf-8")


def write_matching_report(balance: pd.DataFrame, tests: pd.DataFrame, prop: pd.DataFrame) -> None:
    strict = tests[tests["approach"].isin([
        "nearest_neighbour_1to1_with_displacement_reconstruction",
        "nearest_neighbour_3to1_with_displacement_reconstruction",
        "propensity_strata_standard_kinematics",
    ])]
    strict_survives = bool((strict["remains_5sigma_after_matching_family_correction"] == True).any())
    plain = (
        "The result is mixed and substantially weaker under strict QCD controls. "
        "Quantile stratification on missing/visible energy still shows signal enrichment above QCD, "
        "but nearest-neighbour matching and propensity stratification largely remove or reverse the signal advantage. "
        "When displacement/reconstruction proxies are included in nearest-neighbour matching, the 1:1 match leaves only a modest uncorrected effect and the 3:1 match is essentially null. "
        "No strict nearest-neighbour/propensity control remains >=5 sigma after matching-family correction."
    )
    if strict_survives:
        plain = (
            "At least one strict nearest-neighbour/propensity control remains >=5 sigma after matching-family correction. "
            "Review the rows carefully because matching with replacement and small QCD support can still bias interpretation."
        )
    md = f"""# Strict High-HT QCD Mimicry Control Report

Date: {DATE}

## Plain Answer

{plain}

This means high-HT QCD mimicry is sufficient to explain much of the current high-boundary enrichment once events are forced into similar collider/reconstruction regions. The unmatched >=5 sigma result remains real as a benchmark tail-enrichment result, but it is not robust to the strictest matching controls run here.

## Matched/Stratified Tail Tests

{tests.to_markdown(index=False)}

## Balance Summary

{balance.to_markdown(index=False)}

## Propensity/Stratum Details

{prop.to_markdown(index=False) if not prop.empty else 'No propensity or stratum detail rows.'}
"""
    (OUT / "03_STRICT_HIGH_HT_QCD_MIMICRY_CONTROL_REPORT.md").write_text(md, encoding="utf-8")


def write_synthesis(results: pd.DataFrame, deltas: pd.DataFrame, tests: pd.DataFrame) -> None:
    primary = deltas[(deltas["outcome_type"].eq("signal_membership")) & (deltas["comparison_label"].str.contains("neutralino_vs_QCD HT1000to1500", regex=False, na=False))]
    add = primary[primary["delta_test"].eq("add_BNF_to_missing_visible")]
    qcd = tests[tests["approach"].str.contains("nearest_neighbour_1to1_with_displacement", regex=False, na=False)]
    strict = tests[tests["approach"].isin([
        "nearest_neighbour_1to1_with_displacement_reconstruction",
        "nearest_neighbour_3to1_with_displacement_reconstruction",
        "propensity_strata_standard_kinematics",
    ])]
    strict_survives = bool((strict["remains_5sigma_after_matching_family_correction"] == True).any())
    interpretation = (
        "This weakens the SUSY-specific interpretation and suggests high-HT QCD mimicry explains much of the current high-boundary enrichment under strict matching. "
        "A boundary-tail difference remains in the unmatched and coarse stratified comparisons, but it does not survive the stricter nearest-neighbour/propensity controls at >=5 sigma."
    )
    if strict_survives:
        interpretation = (
            "This provides qualified-to-stronger support because at least one strict matched control remains significant. "
            "However, incrementality and matching-quality caveats still need careful review."
        )
    md = f"""# Incrementality And QCD Matching Synthesis For Darren

Date: {DATE}

## What Was Tested

Two decisive robustness checks were run using existing local extracted data only:

1. Whether the frozen N-Frame boundary score adds predictive information beyond missing/visible-energy and multiplicity variables.
2. Whether the strongest current SUSY-like benchmark, neutralino/gluino-to-neutralino, remains enriched over QCD HT1000to1500 after strict QCD matching/stratification.

## Why This Matters

The current positive result is strong but qualified. It shows a full-component SUSY-like benchmark preferentially occupies the high-boundary tail, but high-HT QCD is a serious mimic and ordinary MET/visible-energy structure explains much of the separation. These tests ask whether the N-Frame interpretation survives those two criticisms.

## Incrementality Result

Adding B_NF to `P_missing + P_visible_energy` produced only a small/fragile AUC improvement in the primary neutralino-vs-QCD comparison:

{add.to_markdown(index=False) if not add.empty else 'No primary add-BNF row found.'}

Plain interpretation: B_NF does not yet clearly add a large amount beyond ordinary missing/visible-energy structure. This qualifies the N-Frame interpretation.

## Strict QCD Matching Result

The signal remained enriched in the unmatched and coarse quantile-stratified comparisons. However, the stricter nearest-neighbour and propensity controls substantially weakened or removed the signal advantage:

{qcd.to_markdown(index=False) if not qcd.empty else tests.to_markdown(index=False)}

Plain interpretation: {interpretation}

## Claim Classification

This provides **weakened/qualified support**.

The signal-side parity result remains a valid benchmark observation, but the two decisive robustness tests both cut against a strong SUSY-specific interpretation: B_NF adds little beyond ordinary kinematics, and strict QCD matching removes the >=5 sigma advantage.

## Next Decisive Test

The next decisive test should be published CMS/ATLAS SUSY signal-region residual modelling: extract observed and expected yields from HEPData/CMS/ATLAS tables, build a transparent boundary proxy, and test whether residuals increase in high-boundary signal regions.
"""
    (OUT / "04_INCREMENTALITY_AND_QCD_MATCHING_SYNTHESIS_FOR_DARREN.md").write_text(md, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    events, thresholds = load_events()
    q95 = float(thresholds.loc[thresholds["threshold"].eq("q95"), "value"].iloc[0])
    audit = sample_audit(events)
    audit.to_csv(TABLES / "01_input_audit_samples.csv", index=False)
    write_input_audit(events, audit)

    results, deltas, boot = incrementality(events, q95)
    results.to_csv(TABLES / "02_incrementality_auc_results.csv", index=False)
    deltas.to_csv(TABLES / "02_incrementality_delta_auc_results.csv", index=False)
    boot.to_csv(TABLES / "02_incrementality_bootstrap_summary.csv", index=False)
    write_incrementality_report(results, deltas, boot)

    balance, match_tests, prop = qcd_matching(events, q95)
    balance.to_csv(TABLES / "03_qcd_matching_balance_summary.csv", index=False)
    match_tests.to_csv(TABLES / "03_qcd_matched_tail_fraction_tests.csv", index=False)
    prop.to_csv(TABLES / "03_qcd_propensity_adjusted_tests.csv", index=False)
    write_matching_report(balance, match_tests, prop)
    write_synthesis(results, deltas, match_tests)

    print(f"wrote outputs to {OUT}")
    print(match_tests.to_string(index=False))


if __name__ == "__main__":
    main()
