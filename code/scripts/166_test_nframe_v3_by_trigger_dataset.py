from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, norm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_nframe_v3_trigger_dataset_tests"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"

REAL = ROOT / "outputs_realdata_residual_nframe_v2_trace_test/sources/run2016h_real_miniaod_scored_with_residual_nframe_v2.csv"
SM = ROOT / "outputs_realdata_residual_nframe_v2_trace_test/sources/weighted_sm_scored_with_residual_nframe_v2_sample.csv"

V3_SCORE = "resid_P_missing"
DATASET_TO_TRIGGER = {
    "JetHT": "HLT_HT_paths_any",
    "MET": "HLT_MET_paths_any",
    "SingleMuon": "HLT_Mu_paths_any",
}


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)


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


def count_z(obs: int, n: int, p: float) -> tuple[float, float, float, float]:
    p = float(np.clip(p, 1e-12, 1 - 1e-12))
    exp = n * p
    var = n * p * (1 - p)
    z = (obs - exp) / np.sqrt(max(var, 1e-12))
    p_up = float(binom.sf(obs - 1, n, p)) if obs >= exp else 1.0
    p_down = float(binom.cdf(obs, n, p)) if obs <= exp else 1.0
    return exp, z, p_up, p_down


def global_tail_tests(real: pd.DataFrame, sm: pd.DataFrame, dataset: str) -> pd.DataFrame:
    rs = pd.to_numeric(real[V3_SCORE], errors="coerce").to_numpy(float)
    ss = pd.to_numeric(sm[V3_SCORE], errors="coerce").to_numpy(float)
    sw = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(float)
    rows = []
    for frac in [0.10, 0.05, 0.01, 0.005, 0.001]:
        thr = weighted_quantile(ss, sw, 1 - frac)
        p = float(sw[ss >= thr].sum() / sw.sum())
        obs = int((rs >= thr).sum())
        exp, z, p_up, p_down = count_z(obs, len(rs), p)
        rows.append(
            {
                "primary_dataset": dataset,
                "matched_trigger": DATASET_TO_TRIGGER[dataset],
                "test": "global_v3_tail_vs_trigger_matched_sm",
                "tail_label": f"SM_trigger_matched_top_{frac:g}",
                "tail_threshold": thr,
                "real_observed_tail": obs,
                "real_total": len(rs),
                "expected_from_trigger_matched_sm_shape": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "Z_signed": z,
                "Z_upward": float(norm.isf(p_up)) if p_up > 0 and p_up < 1 else (np.inf if p_up == 0 else -np.inf),
                "p_upward": p_up,
                "p_downward": p_down,
            }
        )
    return pd.DataFrame(rows)


def conditioned_tail_test(real: pd.DataFrame, sm: pd.DataFrame, dataset: str, tail_frac: float = 0.05, n_bins: int = 8) -> pd.DataFrame:
    real_std = pd.to_numeric(real["standard_score"], errors="coerce").to_numpy(float)
    sm_std = pd.to_numeric(sm["standard_score"], errors="coerce").to_numpy(float)
    real_score = pd.to_numeric(real[V3_SCORE], errors="coerce").to_numpy(float)
    sm_score = pd.to_numeric(sm[V3_SCORE], errors="coerce").to_numpy(float)
    sw = pd.to_numeric(sm["event_weight"], errors="coerce").fillna(1.0).to_numpy(float)
    edges = [weighted_quantile(sm_std, sw, q) for q in np.linspace(0, 1, n_bins + 1)]
    edges[0] = -np.inf
    edges[-1] = np.inf
    rows = []
    total_obs = 0
    total_exp = 0.0
    total_var = 0.0
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        sm_bin = (sm_std >= lo) & (sm_std < hi)
        real_bin = (real_std >= lo) & (real_std < hi)
        if sm_bin.sum() < 25 or real_bin.sum() < 5:
            continue
        thr = weighted_quantile(sm_score[sm_bin], sw[sm_bin], 1 - tail_frac)
        p = float(sw[sm_bin & (sm_score >= thr)].sum() / sw[sm_bin].sum())
        obs = int((real_score[real_bin] >= thr).sum())
        n = int(real_bin.sum())
        exp, z, p_up, p_down = count_z(obs, n, p)
        total_obs += obs
        total_exp += exp
        total_var += n * p * (1 - p)
        rows.append(
            {
                "primary_dataset": dataset,
                "matched_trigger": DATASET_TO_TRIGGER[dataset],
                "standard_score_bin": i,
                "standard_score_low": lo,
                "standard_score_high": hi,
                "real_bin_n": n,
                "tail_fraction": tail_frac,
                "tail_threshold": thr,
                "real_observed_tail": obs,
                "expected_from_trigger_matched_sm_shape": exp,
                "observed_over_expected": obs / exp if exp > 0 else np.inf,
                "Z_signed": z,
                "p_upward": p_up,
                "p_downward": p_down,
            }
        )
    z_combined = (total_obs - total_exp) / np.sqrt(max(total_var, 1e-12))
    rows.append(
        {
            "primary_dataset": dataset,
            "matched_trigger": DATASET_TO_TRIGGER[dataset],
            "standard_score_bin": "combined",
            "standard_score_low": np.nan,
            "standard_score_high": np.nan,
            "real_bin_n": int(len(real)),
            "tail_fraction": tail_frac,
            "tail_threshold": np.nan,
            "real_observed_tail": int(total_obs),
            "expected_from_trigger_matched_sm_shape": float(total_exp),
            "observed_over_expected": total_obs / total_exp if total_exp > 0 else np.inf,
            "Z_signed": float(z_combined),
            "p_upward": float(norm.sf(z_combined)) if z_combined > 0 else 1.0,
            "p_downward": float(norm.cdf(z_combined)) if z_combined < 0 else 1.0,
        }
    )
    return pd.DataFrame(rows)


def real_same_trigger_controls(real: pd.DataFrame, dataset: str) -> pd.DataFrame:
    out = real.copy()
    out["v3_percentile_within_dataset"] = out[V3_SCORE].rank(pct=True)
    out["standard_percentile_within_dataset"] = out["standard_score"].rank(pct=True)
    controls = {
        "low_standard_control_bottom50": out["standard_percentile_within_dataset"] <= 0.50,
        "mid_standard_control_25_75": (out["standard_percentile_within_dataset"] >= 0.25) & (out["standard_percentile_within_dataset"] <= 0.75),
        "high_standard_region_top10": out["standard_percentile_within_dataset"] >= 0.90,
        "high_v3_region_top05": out["v3_percentile_within_dataset"] >= 0.95,
        "high_v3_region_top01": out["v3_percentile_within_dataset"] >= 0.99,
    }
    rows = []
    for name, mask in controls.items():
        sub = out[mask]
        rows.append(
            {
                "primary_dataset": dataset,
                "same_trigger_region": name,
                "n_events": len(sub),
                "mean_v3_score": float(sub[V3_SCORE].mean()) if len(sub) else np.nan,
                "median_v3_score": float(sub[V3_SCORE].median()) if len(sub) else np.nan,
                "mean_standard_score": float(sub["standard_score"].mean()) if len(sub) else np.nan,
                "median_MET_pt": float(sub["MET_pt"].median()) if "MET_pt" in sub and len(sub) else np.nan,
                "median_HT": float(sub["HT"].median()) if "HT" in sub and len(sub) else np.nan,
                "median_N_jets_30": float(sub["N_jets_30"].median()) if "N_jets_30" in sub and len(sub) else np.nan,
                "median_N_btags_medium": float(sub["N_btags_medium"].median()) if "N_btags_medium" in sub and len(sub) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    real = pd.read_csv(REAL, low_memory=False)
    sm = pd.read_csv(SM, low_memory=False)
    for df in [real, sm]:
        for c in [V3_SCORE, "standard_score", "event_weight", "MET_pt", "HT", "N_jets_30", "N_btags_medium"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "event_weight" not in df.columns:
            df["event_weight"] = 1.0

    audit_rows = []
    global_frames = []
    cond_frames = []
    control_frames = []
    candidate_frames = []
    for dataset, trigger in DATASET_TO_TRIGGER.items():
        real_ds = real[real["primary_dataset"].astype(str).eq(dataset)].copy()
        trigger_values = pd.to_numeric(sm.get(trigger, pd.Series(np.nan, index=sm.index)), errors="coerce")
        sm_match = sm[trigger_values > 0].copy()
        audit_rows.append(
            {
                "primary_dataset": dataset,
                "matched_trigger": trigger,
                "real_rows": len(real_ds),
                "trigger_matched_sm_rows": len(sm_match),
                "trigger_matched_sm_weight_sum": float(pd.to_numeric(sm_match["event_weight"], errors="coerce").fillna(1.0).sum()),
                "note": "Reduced-component SM rows without HLT flags are excluded from this trigger-matched test.",
            }
        )
        if len(real_ds) == 0 or len(sm_match) < 50:
            continue
        global_frames.append(global_tail_tests(real_ds, sm_match, dataset))
        cond_frames.append(conditioned_tail_test(real_ds, sm_match, dataset, tail_frac=0.05))
        control_frames.append(real_same_trigger_controls(real_ds, dataset))
        candidate_frames.append(
            real_ds.sort_values(V3_SCORE, ascending=False)
            .head(100)
            .assign(primary_dataset_tested=dataset)[
                [
                    "primary_dataset_tested",
                    "primary_dataset",
                    "sample_id",
                    "record_id",
                    "run",
                    "lumi",
                    "event",
                    "source_file",
                    "MET_pt",
                    "HT",
                    "N_jets_30",
                    "N_btags_medium",
                    "N_muons",
                    "N_electrons",
                    "standard_score",
                    V3_SCORE,
                    "nframe_v2_over_standard",
                ]
            ]
        )

    audit = pd.DataFrame(audit_rows)
    global_tests = pd.concat(global_frames, ignore_index=True)
    conditioned = pd.concat(cond_frames, ignore_index=True)
    controls = pd.concat(control_frames, ignore_index=True)
    candidates = pd.concat(candidate_frames, ignore_index=True)

    audit.to_csv(TABLES / "00_trigger_dataset_test_audit.csv", index=False)
    global_tests.to_csv(TABLES / "01_v3_global_tail_by_primary_dataset.csv", index=False)
    conditioned.to_csv(TABLES / "02_v3_standard_conditioned_tail_by_primary_dataset.csv", index=False)
    controls.to_csv(TABLES / "03_same_trigger_real_control_summaries.csv", index=False)
    candidates.to_csv(SOURCES / "top100_real_events_by_dataset_v3_missing_residual_score.csv", index=False)

    combined = conditioned[conditioned["standard_score_bin"].astype(str).eq("combined")].copy()
    top01 = global_tests[global_tests["tail_label"].eq("SM_trigger_matched_top_0.01")].copy()
    report = f"""# N-Frame v3 Trigger/Dataset-Stratified Test

## Purpose

Test the N-Frame v3 missing-residual boundary score separately inside JetHT, MET, and SingleMuon, using trigger-matched SM rows and same-trigger real controls.

The v3 score tested here is:

`B_NF_v3_real_boundary_score = resid_P_missing`

This follows the previous real-boundary parameter search, where `resid_P_missing_positive` was the strongest held-out candidate.

## Important data limitation

Most reduced-component SM rows do not include HLT trigger flags. Therefore this trigger-matched test excludes those rows and uses the smaller full-component SM subset where HLT information exists. This is a better trigger match, but lower-statistics and not yet a full luminosity-complete background model.

## Audit

{audit.to_markdown(index=False)}

## Main Stratified Result

Global top-1% v3 score by trigger-matched SM threshold:

{top01[['primary_dataset','matched_trigger','real_observed_tail','expected_from_trigger_matched_sm_shape','observed_over_expected','Z_signed','p_upward','p_downward']].to_markdown(index=False)}

Standard-score-conditioned top-5% v3 score:

{combined[['primary_dataset','matched_trigger','real_observed_tail','expected_from_trigger_matched_sm_shape','observed_over_expected','Z_signed','p_upward','p_downward']].to_markdown(index=False)}

## Interpretation

If the v3 finding were only caused by mixing JetHT, MET, and SingleMuon together, it should disappear when each primary dataset is tested separately. If it remains large within each stream, the mismatch or trace is present inside same-trigger conditions.

This still does not prove hidden-sector/bulk-space physics. The next question is whether these same large residual-missing differences remain after using full luminosity-weighted, process-complete, trigger-matched SM backgrounds for each primary dataset.

## Same-Trigger Real Control Summaries

{controls.to_markdown(index=False)}
"""
    (REPORTS / "01_NFRAME_V3_TRIGGER_DATASET_STRATIFIED_TEST_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: N-Frame v3 By Trigger Dataset

We tested the v3 missing-residual boundary score separately in JetHT, MET, and SingleMuon.

The tested score was:

`B_NF_v3_real_boundary_score = resid_P_missing`

Standard-score-conditioned top-5% result:

{combined[['primary_dataset','real_observed_tail','expected_from_trigger_matched_sm_shape','observed_over_expected','Z_signed']].to_markdown(index=False)}

Interpretation: this checks whether the v3 effect survives inside each real trigger stream. The test uses only SM rows with matching HLT flags, so reduced-component SM rows without trigger information are excluded.
"""
    (REPORTS / "02_SHORT_UPDATE_NFRAME_V3_TRIGGER_DATASET_TEST.md").write_text(short, encoding="utf-8")

    print("N-FRAME V3 TRIGGER/DATASET TEST COMPLETE")
    print(audit.to_string(index=False))
    print(combined[["primary_dataset", "real_observed_tail", "expected_from_trigger_matched_sm_shape", "observed_over_expected", "Z_signed"]].to_string(index=False))
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
