from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_strict_met_uncertainty_replication"
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
FEATURES = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
TAIL_FRAC = 0.05
N_BINS = 10


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
    m = float(np.average(values[mask], weights=weights[mask]))
    v = float(np.average((values[mask] - m) ** 2, weights=weights[mask]))
    return m, np.sqrt(max(v, 1e-12))


def read_sm() -> pd.DataFrame:
    use = FEATURES + ["event_weight", "component_layer", "process_family_norm", "sample_id", "record_id", "source_file"]
    header = pd.read_csv(FULL_WEIGHTED_SM, nrows=0).columns
    use = [c for c in use if c in header]
    sm = pd.read_csv(FULL_WEIGHTED_SM, usecols=use, low_memory=False)
    for c in FEATURES + ["event_weight"]:
        if c not in sm:
            sm[c] = 1.0 if c == "event_weight" else np.nan
        sm[c] = pd.to_numeric(sm[c], errors="coerce")
    sm["event_weight"] = sm["event_weight"].fillna(1.0)
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    return sm


def read_real_met(path: Path, sample_name: str) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0).columns
    use = [c for c in ["primary_dataset", "sample_id", "record_id", "run", "lumi", "event", "source_file"] + FEATURES if c in header]
    frames = []
    for chunk in pd.read_csv(path, usecols=use, chunksize=200_000, low_memory=False):
        if "primary_dataset" not in chunk:
            continue
        chunk = chunk[chunk["primary_dataset"].astype(str).eq("MET")].copy()
        if chunk.empty:
            continue
        for c in FEATURES + ["run", "lumi", "event"]:
            if c not in chunk:
                chunk[c] = np.nan
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce")
        for c in ["sample_id", "record_id", "source_file"]:
            if c not in chunk:
                chunk[c] = ""
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
    params = {"mean_logmet": mean_met, "sd_logmet": sd_met, "visible_median": med, "coef": coef}
    return params, sm


def apply_visible_residual(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    out["common_missing_z"] = (out["log1p_MET_pt"] - params["mean_logmet"]) / params["sd_logmet"]
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["visible_median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["common_missing_resid_visible_only"] = out["common_missing_z"].to_numpy(float) - design @ params["coef"]
    return out


def conditioned_test(real: pd.DataFrame, sm_template: pd.DataFrame, sample_name: str, template_name: str) -> tuple[pd.DataFrame, dict]:
    rs = real["common_missing_resid_visible_only"].to_numpy(float)
    ss = sm_template["common_missing_resid_visible_only"].to_numpy(float)
    rc = real["MET_pt"].to_numpy(float)
    sc = sm_template["MET_pt"].to_numpy(float)
    sw = sm_template["event_weight"].fillna(1.0).to_numpy(float)
    edges = [weighted_quantile(sc, sw, q) for q in np.linspace(0, 1, N_BINS + 1)]
    edges[0], edges[-1] = -np.inf, np.inf
    rows = []
    obs_total = 0
    exp_total = 0.0
    var_total = 0.0
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        sm_bin = (sc >= lo) & (sc < hi)
        real_bin = (rc >= lo) & (rc < hi)
        if sm_bin.sum() < 20 or real_bin.sum() < 5:
            continue
        thr = weighted_quantile(ss[sm_bin], sw[sm_bin], 1 - TAIL_FRAC)
        p = float(sw[sm_bin & (ss >= thr)].sum() / sw[sm_bin].sum())
        n = int(real_bin.sum())
        obs = int((rs[real_bin] >= thr).sum())
        exp = n * p
        var = n * p * (1 - p)
        obs_total += obs
        exp_total += exp
        var_total += var
        rows.append(
            {
                "real_sample": sample_name,
                "sm_template": template_name,
                "met_bin": i,
                "real_bin_n": n,
                "tail_threshold": thr,
                "sm_tail_fraction": p,
                "observed": obs,
                "expected": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "signed_Z_bin": (obs - exp) / np.sqrt(max(var, 1e-12)),
            }
        )
    z = (obs_total - exp_total) / np.sqrt(max(var_total, 1e-12))
    summary = {
        "real_sample": sample_name,
        "sm_template": template_name,
        "real_events": int(len(real)),
        "observed": int(obs_total),
        "expected": float(exp_total),
        "observed_over_expected": float(obs_total / exp_total) if exp_total > 0 else np.inf,
        "signed_Z": float(z),
        "used_bins": len(rows),
    }
    return pd.DataFrame(rows), summary


def sm_templates(sm: pd.DataFrame) -> dict[str, pd.DataFrame]:
    layer = sm["component_layer"].fillna("").astype(str) if "component_layer" in sm else pd.Series("", index=sm.index)
    out = {
        "all_weighted_sm": sm,
        "full_component_sm": sm[layer.str.contains("MINIAODSIM_full_component", case=False, na=False)],
        "reduced_component_sm": sm[layer.str.contains("NANOAODSIM_reduced_component", case=False, na=False)],
    }
    return {k: v for k, v in out.items() if len(v) >= 100}


def pseudo_closure(sm: pd.DataFrame, rng: np.random.Generator, n_iter: int = 80) -> pd.DataFrame:
    rows = []
    fam = sm["process_family_norm"].fillna("unknown").astype(str) if "process_family_norm" in sm else pd.Series("unknown", index=sm.index)
    for i in range(n_iter):
        idx = np.arange(len(sm))
        fit_idx = rng.choice(idx, size=len(idx) // 2, replace=False)
        mask = np.zeros(len(sm), dtype=bool)
        mask[fit_idx] = True
        template = sm.iloc[mask].copy()
        pseudo = sm.iloc[~mask].copy()
        bins, summary = conditioned_test(pseudo.assign(real_sample="sm_pseudo"), template, f"sm_pseudo_{i:03d}", "heldout_sm_half")
        rows.append(summary)
    # Leave-one-family template stress: use all but one family as template, held out family as pseudo-data.
    for family in sorted(fam.unique()):
        pseudo = sm[fam.eq(family)].copy()
        template = sm[~fam.eq(family)].copy()
        if len(pseudo) < 500 or len(template) < 1000:
            continue
        _, summary = conditioned_test(pseudo.assign(real_sample=f"heldout_{family}"), template, f"heldout_family_{family}", "all_other_families")
        rows.append(summary)
    return pd.DataFrame(rows)


def event_overlap(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    keys = {k: set(v["event_key"].dropna().astype(str)) for k, v in samples.items()}
    names = list(keys)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            inter = keys[a] & keys[b]
            rows.append(
                {
                    "sample_a": a,
                    "sample_b": b,
                    "overlap_events": len(inter),
                    "overlap_fraction_of_a": len(inter) / max(len(keys[a]), 1),
                    "overlap_fraction_of_b": len(inter) / max(len(keys[b]), 1),
                }
            )
    return pd.DataFrame(rows)


def uncertainty_summary(replication: pd.DataFrame, closure: pd.DataFrame) -> pd.DataFrame:
    main = replication[replication["sm_template"].eq("all_weighted_sm")].copy()
    ratio_mean = main["observed_over_expected"].mean()
    ratio_sd = main["observed_over_expected"].std(ddof=1)
    ratio_cv = ratio_sd / ratio_mean
    # Pseudo-closure around 1.0 estimates finite-template/background-shape closure spread.
    pseudo = closure[closure["sm_template"].eq("heldout_sm_half")].copy()
    pseudo_cv = pseudo["observed_over_expected"].std(ddof=1) / pseudo["observed_over_expected"].mean()
    # Family closure is not a pure uncertainty, but a stress-test upper bound.
    fam = closure[closure["sm_template"].eq("all_other_families")].copy()
    fam_cv = fam["observed_over_expected"].std(ddof=1) / fam["observed_over_expected"].mean() if len(fam) > 1 else np.nan
    conservative_uncertainty = max(float(ratio_cv), float(pseudo_cv))
    rows = [
        {
            "uncertainty_source": "independent_real_MET_replication_obs_exp_CV",
            "relative_uncertainty": ratio_cv,
            "passes_below_30pct": ratio_cv < 0.30,
            "note": "Spread of observed/expected across independent MET real samples using all weighted SM.",
        },
        {
            "uncertainty_source": "SM_random_half_pseudo_closure_CV",
            "relative_uncertainty": pseudo_cv,
            "passes_below_30pct": pseudo_cv < 0.30,
            "note": "Finite SM shape closure uncertainty from random held-out SM halves.",
        },
        {
            "uncertainty_source": "SM_leave_family_out_closure_CV_stress",
            "relative_uncertainty": fam_cv,
            "passes_below_30pct": bool(fam_cv < 0.30) if np.isfinite(fam_cv) else False,
            "note": "Stress test, not a pure systematic: process families intentionally have different shapes.",
        },
        {
            "uncertainty_source": "conservative_for_current_test",
            "relative_uncertainty": conservative_uncertainty,
            "passes_below_30pct": conservative_uncertainty < 0.30,
            "note": "Max of real replication spread and random SM closure spread.",
        },
    ]
    return pd.DataFrame(rows)


def z_with_uncertainty(obs: float, exp: float, rel_unc: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel_unc * exp) ** 2, 1e-12)))


def main() -> None:
    ensure_dirs()
    sm = read_sm()
    params, sm_scored = fit_visible_residual(sm)
    templates = sm_templates(sm_scored)

    real_samples = {}
    audit_rows = []
    for name, path in REAL_SAMPLES:
        real = read_real_met(path, name)
        real = apply_visible_residual(real, params) if not real.empty else real
        real_samples[name] = real
        audit_rows.append({"real_sample": name, "path": str(path.relative_to(ROOT)), "met_events": len(real)})
        if not real.empty:
            keep = ["real_sample", "sample_id", "record_id", "run", "lumi", "event", "source_file"] + FEATURES + [
                "common_missing_z",
                "common_missing_resid_visible_only",
                "event_key",
            ]
            real[keep].to_csv(SOURCES / f"{name}_scored_met_events.csv", index=False)

    bin_frames = []
    summary_rows = []
    for sample_name, real in real_samples.items():
        if real.empty:
            continue
        for template_name, template in templates.items():
            bins, summary = conditioned_test(real, template, sample_name, template_name)
            bin_frames.append(bins)
            summary_rows.append(summary)

    replication = pd.DataFrame(summary_rows)
    binned = pd.concat(bin_frames, ignore_index=True)
    closure = pseudo_closure(sm_scored, np.random.default_rng(170), n_iter=80)
    overlap = event_overlap(real_samples)
    uncertainty = uncertainty_summary(replication, closure)

    conservative_unc = float(
        uncertainty.loc[uncertainty["uncertainty_source"].eq("conservative_for_current_test"), "relative_uncertainty"].iloc[0]
    )
    main = replication[replication["sm_template"].eq("all_weighted_sm")].copy()
    main["Z_with_conservative_uncertainty"] = [
        z_with_uncertainty(o, e, conservative_unc) for o, e in zip(main["observed"], main["expected"])
    ]
    main["passes_5sigma_with_conservative_uncertainty"] = main["Z_with_conservative_uncertainty"] >= 5.0

    audit = pd.DataFrame(audit_rows)
    audit.to_csv(TABLES / "00_independent_met_sample_audit.csv", index=False)
    binned.to_csv(TABLES / "01_independent_met_binned_strict_tests.csv", index=False)
    replication.to_csv(TABLES / "02_independent_met_replication_summary.csv", index=False)
    closure.to_csv(TABLES / "03_sm_background_shape_closure_uncertainty.csv", index=False)
    uncertainty.to_csv(TABLES / "04_background_shape_uncertainty_summary.csv", index=False)
    main.to_csv(TABLES / "05_met_replication_with_conservative_uncertainty.csv", index=False)
    overlap.to_csv(TABLES / "06_independent_met_event_overlap_audit.csv", index=False)

    n_pass = int(main["passes_5sigma_with_conservative_uncertainty"].sum())
    report = f"""# Strict MET Boundary Background-Uncertainty Replication Test

## Question

Can we show the residual background-shape uncertainty is below ~30% using independent MET samples/eras, and does the strict MET boundary result remain discovery-level?

## Strict Score

- Score: `common_missing_resid_visible_only`
- Conditioning: raw `MET_pt`
- Tail: top 5% within MET bins
- SM template: luminosity-weighted full available SM table

## Independent MET Samples

{audit.to_markdown(index=False)}

## Replication Summary

All weighted SM template:

{main.to_markdown(index=False)}

All SM templates:

{replication.to_markdown(index=False)}

## Background-Shape Uncertainty Estimate

{uncertainty.to_markdown(index=False)}

Conservative current uncertainty estimate: **{conservative_unc:.1%}**.

Independent MET samples passing 5 sigma after this uncertainty: **{n_pass}/{len(main)}**.

## Event Overlap Audit

{overlap.to_markdown(index=False)}

## Interpretation

This test estimates the uncertainty from two directions:

1. real-data replication spread across independent MET samples;
2. random held-out SM pseudo-closure spread.

The leave-one-family SM closure is included as a stress test, but it is not the main uncertainty estimate because QCD, WJets and top-like samples genuinely have different physical shapes.

If the conservative uncertainty is below 30% and the independent MET samples remain above 5 sigma under that uncertainty, the strict MET boundary candidate survives the decisive uncertainty test.
"""
    (REPORTS / "01_STRICT_MET_BACKGROUND_UNCERTAINTY_REPLICATION_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Strict MET Background-Uncertainty Replication

We tested the strict calibration-safe MET boundary result on independent MET samples.

Conservative residual background-shape uncertainty estimate:

{uncertainty.to_markdown(index=False)}

Replication with conservative uncertainty applied:

{main.to_markdown(index=False)}

Result: {n_pass}/{len(main)} independent MET samples remain above 5 sigma after applying the conservative uncertainty estimate.
"""
    (REPORTS / "02_SHORT_UPDATE_STRICT_MET_BACKGROUND_UNCERTAINTY_REPLICATION.md").write_text(short, encoding="utf-8")

    print("STRICT MET BACKGROUND-UNCERTAINTY REPLICATION COMPLETE")
    print(uncertainty.to_string(index=False))
    print(main[["real_sample", "observed", "expected", "observed_over_expected", "signed_Z", "Z_with_conservative_uncertainty", "passes_5sigma_with_conservative_uncertainty"]].to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
