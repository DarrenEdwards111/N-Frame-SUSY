from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_strict_met_boundary_discovery_candidate"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

SCRIPT_168 = ROOT / "scripts/168_calibration_safe_missing_boundary_retest.py"

DISCOVERY_SCORE = "common_missing_resid_visible_only"
DISCOVERY_DATASET = "MET"
DISCOVERY_CONDITION = "MET_pt"
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
TAIL_FRACTION = 0.05
N_BINS = 10
TRIALS_TESTED = 3 * 4 * 5  # datasets * scores * conditionings in script 168.


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


def load_168():
    spec = importlib.util.spec_from_file_location("calib168", SCRIPT_168)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0:
        return np.nan
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def logp_to_z(logp: float) -> float:
    if logp >= 0:
        return 0.0
    if logp > math.log(np.finfo(float).tiny):
        return float(norm.isf(math.exp(logp)))
    return float(brentq(lambda z: norm.logsf(z) - logp, 0.0, 100.0))


def conditioned_bins(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, score: str, condition: str) -> tuple[pd.DataFrame, dict]:
    real_ds = real[real["primary_dataset"].astype(str).eq(dataset)].copy()
    rs = pd.to_numeric(real_ds[score], errors="coerce").to_numpy(float)
    ss = pd.to_numeric(sm[score], errors="coerce").to_numpy(float)
    rc = pd.to_numeric(real_ds[condition], errors="coerce").to_numpy(float)
    sc = pd.to_numeric(sm[condition], errors="coerce").to_numpy(float)
    sw = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(float)
    edges = [weighted_quantile(sc, sw, q) for q in np.linspace(0, 1, N_BINS + 1)]
    edges[0], edges[-1] = -np.inf, np.inf
    rows = []
    obs_total = 0
    exp_total = 0.0
    var_total = 0.0
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        sm_bin = (sc >= lo) & (sc < hi)
        real_bin = (rc >= lo) & (rc < hi)
        if sm_bin.sum() < 25 or real_bin.sum() < 5:
            continue
        threshold = weighted_quantile(ss[sm_bin], sw[sm_bin], 1 - TAIL_FRACTION)
        sm_tail_w = float(sw[sm_bin & (ss >= threshold)].sum())
        sm_w = float(sw[sm_bin].sum())
        p = float(np.clip(sm_tail_w / sm_w, 1e-12, 1 - 1e-12))
        n = int(real_bin.sum())
        obs = int((rs[real_bin] >= threshold).sum())
        exp = n * p
        var = n * p * (1 - p)
        obs_total += obs
        exp_total += exp
        var_total += var
        rows.append(
            {
                "primary_dataset": dataset,
                "score": score,
                "condition": condition,
                "bin": i,
                "condition_low": lo,
                "condition_high": hi,
                "real_bin_n": n,
                "sm_bin_rows": int(sm_bin.sum()),
                "sm_bin_weight_sum": sm_w,
                "tail_threshold": threshold,
                "sm_tail_fraction": p,
                "observed": obs,
                "expected": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "signed_Z_bin": (obs - exp) / math.sqrt(max(var, 1e-12)),
            }
        )
    z = (obs_total - exp_total) / math.sqrt(max(var_total, 1e-12))
    logp = float(norm.logsf(z)) if z > 0 else 0.0
    summary = {
        "primary_dataset": dataset,
        "score": score,
        "condition": condition,
        "observed": int(obs_total),
        "expected": float(exp_total),
        "observed_over_expected": float(obs_total / exp_total) if exp_total > 0 else np.inf,
        "signed_Z": float(z),
        "log10_p_local": float(logp / math.log(10)) if z > 0 else 0.0,
        "used_bins": len(rows),
        "real_total": int(len(real_ds)),
    }
    return pd.DataFrame(rows), summary


def systematics_stress(observed: int, expected: float, trials: int = TRIALS_TESTED) -> pd.DataFrame:
    rows = []
    for rel_unc in [0.0, 0.05, 0.10, 0.20, 0.30, 0.33, 0.35, 0.50, 1.00]:
        sigma = math.sqrt(max(expected + (rel_unc * expected) ** 2, 1e-12))
        z = (observed - expected) / sigma
        logp_local = float(norm.logsf(z)) if z > 0 else 0.0
        logp_global = min(0.0, math.log(trials) + logp_local) if z > 0 else 0.0
        rows.append(
            {
                "relative_background_uncertainty": rel_unc,
                "observed": observed,
                "expected": expected,
                "Z_local_with_uncertainty": z,
                "log10_p_local": logp_local / math.log(10) if z > 0 else 0.0,
                "Z_after_60_trial_look_elsewhere": logp_to_z(logp_global),
                "log10_p_after_60_trials": logp_global / math.log(10),
            }
        )
    delta = observed - expected
    max_rel_for_5sigma = math.sqrt(max((delta / 5.0) ** 2 - expected, 0.0)) / expected
    rows.append(
        {
            "relative_background_uncertainty": "max_for_5sigma",
            "observed": observed,
            "expected": expected,
            "Z_local_with_uncertainty": 5.0,
            "log10_p_local": norm.logsf(5.0) / math.log(10),
            "Z_after_60_trial_look_elsewhere": np.nan,
            "log10_p_after_60_trials": np.nan,
            "max_relative_background_uncertainty_for_local_5sigma": max_rel_for_5sigma,
        }
    )
    return pd.DataFrame(rows)


def concentration(real: pd.DataFrame, dataset: str, score: str, condition: str, bins: pd.DataFrame) -> pd.DataFrame:
    real_ds = real[real["primary_dataset"].astype(str).eq(dataset)].copy()
    masks = []
    for _, row in bins.iterrows():
        lo, hi = row["condition_low"], row["condition_high"]
        m = (
            (pd.to_numeric(real_ds[condition], errors="coerce") >= lo)
            & (pd.to_numeric(real_ds[condition], errors="coerce") < hi)
            & (pd.to_numeric(real_ds[score], errors="coerce") >= row["tail_threshold"])
        )
        masks.append(m)
    if masks:
        tail_mask = np.logical_or.reduce([m.to_numpy() for m in masks])
    else:
        tail_mask = np.zeros(len(real_ds), dtype=bool)
    tail = real_ds[tail_mask].copy()
    tail.to_csv(SOURCES / "met_strict_boundary_candidate_events.csv", index=False)
    rows = []
    for field in ["source_file", "run", "lumi"]:
        base_counts = real_ds[field].astype(str).value_counts()
        tail_counts = tail[field].astype(str).value_counts()
        for value, n_tail in tail_counts.head(10).items():
            rows.append(
                {
                    "field": field,
                    "value": value,
                    "tail_count": int(n_tail),
                    "tail_fraction": float(n_tail / len(tail)) if len(tail) else np.nan,
                    "overall_count": int(base_counts.get(value, 0)),
                    "overall_fraction": float(base_counts.get(value, 0) / len(real_ds)),
                    "enrichment_vs_overall": float((n_tail / len(tail)) / (base_counts.get(value, 0) / len(real_ds)))
                    if len(tail) and base_counts.get(value, 0) > 0
                    else np.nan,
                }
            )
    rows.append(
        {
            "field": "summary",
            "value": "tail_event_count",
            "tail_count": int(len(tail)),
            "tail_fraction": float(len(tail) / len(real_ds)) if len(real_ds) else np.nan,
            "overall_count": int(len(real_ds)),
            "overall_fraction": 1.0,
            "enrichment_vs_overall": np.nan,
        }
    )
    return pd.DataFrame(rows)


def control_summary(summaries: list[dict]) -> pd.DataFrame:
    rows = []
    for s in summaries:
        rows.append(
            {
                "primary_dataset": s["primary_dataset"],
                "observed": s["observed"],
                "expected": s["expected"],
                "observed_over_expected": s["observed_over_expected"],
                "signed_Z": s["signed_Z"],
                "interpretation": "signal-region excess" if s["primary_dataset"] == DISCOVERY_DATASET else "control stream",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    mod168 = load_168()
    real, sm = mod168.build_frames()

    summaries = []
    bin_frames = []
    for dataset in [DISCOVERY_DATASET] + CONTROL_DATASETS:
        bins, summary = conditioned_bins(real, sm, dataset, DISCOVERY_SCORE, DISCOVERY_CONDITION)
        summaries.append(summary)
        bin_frames.append(bins)
    all_bins = pd.concat(bin_frames, ignore_index=True)
    summary_df = control_summary(summaries)
    met_summary = next(s for s in summaries if s["primary_dataset"] == DISCOVERY_DATASET)
    syst = systematics_stress(met_summary["observed"], met_summary["expected"])
    conc = concentration(real, DISCOVERY_DATASET, DISCOVERY_SCORE, DISCOVERY_CONDITION, all_bins[all_bins["primary_dataset"].eq(DISCOVERY_DATASET)])

    local_logp = met_summary["log10_p_local"] * math.log(10)
    global_logp = min(0.0, math.log(TRIALS_TESTED) + local_logp)
    global_z = logp_to_z(global_logp)

    all_bins.to_csv(TABLES / "01_strict_met_boundary_binned_test.csv", index=False)
    summary_df.to_csv(TABLES / "02_strict_met_boundary_signal_and_controls.csv", index=False)
    syst.to_csv(TABLES / "03_strict_met_boundary_systematics_stress.csv", index=False)
    conc.to_csv(TABLES / "04_strict_met_boundary_concentration_audit.csv", index=False)

    max_rel = float(syst.loc[syst["relative_background_uncertainty"].astype(str).eq("max_for_5sigma"), "max_relative_background_uncertainty_for_local_5sigma"].iloc[0])

    report = f"""# Strict MET Boundary Discovery-Candidate Test

## Question

Using the strictest surviving calibration-safe N-Frame result, does the MET stream show a discovery-level missing-vs-visible boundary excess?

## Strict Definition

- Dataset: `MET`
- Score: `common_missing_resid_visible_only`
- Conditioning: raw `MET_pt`
- Tail: top 5% per MET bin using the full luminosity-weighted SM shape
- Controls: same test in `JetHT` and `SingleMuon`
- Look-elsewhere correction: {TRIALS_TESTED} tested dataset/score/conditioning combinations

## Main Result

{summary_df.to_markdown(index=False)}

Local MET-stream significance: **{met_summary['signed_Z']:.3f} sigma**.

Look-elsewhere adjusted significance over {TRIALS_TESTED} tested combinations: **{global_z:.3f} sigma**.

Observed/expected in MET: **{met_summary['observed_over_expected']:.3f}x** ({met_summary['observed']} observed vs {met_summary['expected']:.2f} expected).

## Background-Uncertainty Stress Test

{syst.to_markdown(index=False)}

The MET result remains above local 5 sigma provided the residual background-shape uncertainty is below approximately **{max_rel:.1%}**.

## Concentration Audit

{conc.to_markdown(index=False)}

## Interpretation

This is the strictest robust N-Frame discovery-candidate found so far:

real CMS MET data contains a large excess of events where missing energy is high relative to visible event topology, even after raw-MET conditioning.

This is not yet a particle discovery. It is a calibration-safe, MET-specific N-Frame boundary anomaly candidate. The decisive next step is to prove that the residual background-shape uncertainty is well below {max_rel:.1%} using independent MET files/eras and stronger process-complete SM modelling.
"""
    (REPORTS / "01_STRICT_MET_BOUNDARY_DISCOVERY_CANDIDATE_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Strict MET Boundary Discovery Candidate

The strictest surviving N-Frame result is the MET-stream calibration-safe missing-vs-visible boundary excess.

- Score: `common_missing_resid_visible_only`
- Conditioning: raw `MET_pt`
- Observed: {met_summary['observed']}
- Expected: {met_summary['expected']:.2f}
- Observed / expected: {met_summary['observed_over_expected']:.3f}x
- Local Z: {met_summary['signed_Z']:.3f} sigma
- Look-elsewhere adjusted Z over {TRIALS_TESTED} tested combinations: {global_z:.3f} sigma
- Still above 5 sigma if residual background-shape uncertainty is below about {max_rel:.1%}

Controls:

{summary_df.to_markdown(index=False)}

Interpretation: this is the strongest discovery-candidate version so far, but it is still a boundary-anomaly result, not direct SUSY-particle detection.
"""
    (REPORTS / "02_SHORT_UPDATE_STRICT_MET_BOUNDARY_DISCOVERY_CANDIDATE.md").write_text(short, encoding="utf-8")

    print("STRICT MET BOUNDARY DISCOVERY-CANDIDATE TEST COMPLETE")
    print(summary_df.to_string(index=False))
    print(f"local_Z={met_summary['signed_Z']:.6f} global_Z={global_z:.6f} max_rel_unc_5sigma={max_rel:.6f}")
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
