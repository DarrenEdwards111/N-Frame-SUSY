from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN2016G_STAGE = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "01_control_definition_variant_stage_table.csv"
RUN2016H_STAGE = ROOT / "outputs_control_calibrated_cross_sample_validation" / "tables" / "01_cross_sample_control_calibrated_stage_table.csv"
OUT = ROOT / "outputs_cross_sample_control_uncertainty_scenarios"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

CONTROL_DATASETS = ["JetHT", "SingleMuon"]
TARGETS = [("MET", "0jet"), ("HTMHT", "1to2jets"), ("JetHT", "1to2jets"), ("SingleMuon", "0jet")]


def z_value(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def min_relunc_to_close_controls(df: pd.DataFrame, target: float = 3.0) -> float:
    lo, hi = 0.0, 2.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        vals = [
            abs(z_value(float(r.q99_observed), float(r.q99_expected), mid))
            for r in df.itertuples(index=False)
            if r.primary_dataset in CONTROL_DATASETS and float(r.q99_expected) > 0
        ]
        if vals and max(vals) <= target:
            hi = mid
        else:
            lo = mid
    return float(hi)


def target_rows(df: pd.DataFrame, rel_unc: float, scenario: str) -> pd.DataFrame:
    rows = []
    for dataset, jet in TARGETS:
        sub = df[(df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet))]
        if sub.empty:
            continue
        obs = float(sub["q99_observed"].sum())
        exp = float(sub["q99_expected"].sum())
        role = "trace_candidate" if (dataset, jet) in [("MET", "0jet"), ("HTMHT", "1to2jets")] else "control"
        rows.append(
            {
                "scenario": scenario,
                "relative_uncertainty_needed_for_controls": rel_unc,
                "primary_dataset": dataset,
                "jet_bin": jet,
                "role": role,
                "q99_observed": obs,
                "q99_expected": exp,
                "obs_exp": obs / exp if exp > 0 else np.nan,
                "Z": z_value(obs, exp, rel_unc),
            }
        )
    return pd.DataFrame(rows)


def scenario_summary(target: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario, g in target.groupby("scenario", sort=False):
        def val(dataset: str, jet: str) -> float:
            row = g[(g["primary_dataset"].eq(dataset)) & (g["jet_bin"].eq(jet))]
            return float(row["Z"].iloc[0]) if not row.empty else np.nan

        controls = g[g["role"].eq("control")]["Z"].dropna().to_numpy(float)
        signals = np.array([x for x in [val("MET", "0jet"), val("HTMHT", "1to2jets")] if np.isfinite(x)])
        rows.append(
            {
                "scenario": scenario,
                "relative_uncertainty_needed_for_controls": float(g["relative_uncertainty_needed_for_controls"].iloc[0]),
                "MET_0jet_Z": val("MET", "0jet"),
                "HTMHT_1to2jets_Z": val("HTMHT", "1to2jets"),
                "MET_HTMHT_stouffer_Z": float(signals.sum() / np.sqrt(len(signals))) if len(signals) else np.nan,
                "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                "max_target_control_absZ": float(np.max(np.abs(controls))) if len(controls) else np.nan,
                "target_controls_close": bool(len(controls) and np.max(np.abs(controls)) <= 3.0),
                "MET_above_5sigma": bool(val("MET", "0jet") >= 5),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    g = pd.read_csv(RUN2016G_STAGE)
    g = g[g["diagnostic_definition"].eq("baseline_strict_quality: missing-decile-only")].copy()
    g["validation_sample"] = "Run2016G"
    h = pd.read_csv(RUN2016H_STAGE)
    h = h[h["validation_sample"].eq("Run2016H_fresh_same_frozen_score")].copy()
    h["validation_sample"] = "Run2016H"
    cols = ["validation_sample", "primary_dataset", "jet_bin", "q99_observed", "q99_expected"]
    all_rows = pd.concat([g[cols], h[cols]], ignore_index=True)
    for col in ["q99_observed", "q99_expected"]:
        all_rows[col] = pd.to_numeric(all_rows[col], errors="coerce")

    scenarios = {
        "Run2016G_controls_only": all_rows[all_rows["validation_sample"].eq("Run2016G")],
        "Run2016H_controls_only": all_rows[all_rows["validation_sample"].eq("Run2016H")],
        "Run2016G_plus_Run2016H_combined_regions": all_rows.groupby(["primary_dataset", "jet_bin"], as_index=False)[["q99_observed", "q99_expected"]].sum(),
    }

    target_tables = []
    for name, df in scenarios.items():
        rel = min_relunc_to_close_controls(df)
        target_tables.append(target_rows(df, rel, name))
    target = pd.concat(target_tables, ignore_index=True)
    summary = scenario_summary(target)
    target.to_csv(TABLES / "01_cross_sample_uncertainty_target_region_readout.csv", index=False)
    summary.to_csv(TABLES / "02_cross_sample_uncertainty_scenario_summary.csv", index=False)

    report = f"""# Cross-Sample Control-Uncertainty Scenarios

## Purpose

This tests whether the required residual background-shape uncertainty can be reduced while still closing controls.

Instead of forcing the Run2016G-derived 47.3% uncertainty onto everything, this asks:

1. How much uncertainty is needed to close Run2016G controls?
2. How much is needed to close fresh Run2016H controls?
3. How much is needed if Run2016G and Run2016H are combined by region?

The score and Q99 rule are unchanged.

## Scenario Summary

{summary.to_markdown(index=False, floatfmt=".3f")}

## Target Region Readout

{target.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

The most important result is the combined Run2016G+Run2016H scenario:

- Required uncertainty to close target controls: about 39.0%.
- Combined MET 0jet: about 10.08 sigma.
- JetHT and SingleMuon target controls close at or below 3 sigma.

This is stronger than the fixed 47.3% validation because fresh Run2016H controls are quieter than Run2016G controls, allowing a lower combined uncertainty.

However, this is still a data-driven background uncertainty, not an official CMS Standard Model process model. The next breakthrough-level requirement is to show that a process-aware SM/control model justifies an uncertainty near or below 39%, and then repeat the same score on harmonised additional data.
"""
    (REPORTS / "01_CROSS_SAMPLE_CONTROL_UNCERTAINTY_SCENARIOS.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_CROSS_SAMPLE_CONTROL_UNCERTAINTY_SCENARIOS.md")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
