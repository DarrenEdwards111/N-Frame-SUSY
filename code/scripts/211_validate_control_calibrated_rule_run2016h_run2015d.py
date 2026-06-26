from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN2016H = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv"
RUN2015D_SUMMARY = ROOT / "outputs_run2015d_frozen_q99_pilot" / "tables" / "04_run2015d_frozen_q99_summary.csv"
OUT = ROOT / "outputs_control_calibrated_cross_sample_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

CONTROL_CALIBRATED_RELUNC = 0.47336574523492086
FROZEN_WEIGHTS = {
    "observer_projection": 0.3137254901960784,
    "physical_projection": 0.3137254901960784,
    "algebraic_projection": 0.0,
    "ordinary_qcd_axis": -0.27450980392156865,
    "leptonic_control_axis": -0.09803921568627451,
}
SIGNAL_REGIONS = [("MET", "0jet"), ("HTMHT", "1to2jets")]
TARGET_CONTROLS = [("JetHT", "1to2jets"), ("SingleMuon", "0jet")]
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]


def z_value(obs: float, exp: float, rel_unc: float = CONTROL_CALIBRATED_RELUNC) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def add_frozen_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in FROZEN_WEIGHTS:
        if col not in out:
            raise ValueError(f"Run2016H table is missing required frozen-score component: {col}")
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["frozen_boundary_score_recomputed"] = sum(FROZEN_WEIGHTS[col] * out[col].to_numpy(float) for col in FROZEN_WEIGHTS)
    return out


def run2016h_missing_decile_q99() -> tuple[pd.DataFrame, pd.DataFrame]:
    usecols = [
        "run_era",
        "primary_dataset",
        "run",
        "lumi",
        "event",
        "missing_proxy_pt",
        "jet_bin",
        "strict_quality_clean",
        *FROZEN_WEIGHTS.keys(),
    ]
    header = pd.read_csv(RUN2016H, nrows=0).columns
    usecols = [c for c in usecols if c in header]
    df = pd.read_csv(RUN2016H, usecols=usecols, low_memory=False)
    if "strict_quality_clean" in df:
        df = df[df["strict_quality_clean"].astype(str).str.lower().isin(["true", "1"])].copy()
    df = add_frozen_score(df)
    df["missing_proxy_pt"] = pd.to_numeric(df["missing_proxy_pt"], errors="coerce")
    df = df[df["missing_proxy_pt"].notna()].copy()
    df["jet_bin"] = df["jet_bin"].astype(str)

    tagged = []
    rows = []
    for (era, dataset), group in df.groupby(["run_era", "primary_dataset"], sort=False):
        g = group.copy()
        edges = np.unique(g["missing_proxy_pt"].quantile(np.linspace(0, 1, 11)).to_numpy(float))
        if len(edges) < 3:
            edges = np.array([-np.inf, np.inf])
        else:
            edges[0], edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=edges, labels=False, include_lowest=True)
        thresholds = g.groupby("missing_bin", observed=False)["frozen_boundary_score_recomputed"].quantile(0.99)
        g["q99_tail"] = g["frozen_boundary_score_recomputed"] >= g["missing_bin"].map(thresholds).astype(float)
        g["expected_tail_fraction"] = g.groupby("missing_bin", observed=False)["q99_tail"].transform("mean")
        tagged.append(g)
        for jet, sub in g.groupby("jet_bin", observed=False):
            if str(jet) not in JET_BINS:
                continue
            obs = float(sub["q99_tail"].sum())
            exp = float(sub["expected_tail_fraction"].sum())
            rows.append(
                {
                    "validation_sample": "Run2016H_fresh_same_frozen_score",
                    "score_definition": "same Run2016G frozen N-Frame component score recomputed from Run2016H components",
                    "era": era,
                    "primary_dataset": dataset,
                    "jet_bin": str(jet),
                    "events": len(sub),
                    "q99_observed": obs,
                    "q99_expected": exp,
                    "obs_exp": obs / exp if exp > 0 else np.nan,
                    "Z_control_calibrated": z_value(obs, exp),
                }
            )
    tagged_df = pd.concat(tagged, ignore_index=True)
    return tagged_df, pd.DataFrame(rows)


def run2015d_existing_q99() -> pd.DataFrame:
    df = pd.read_csv(RUN2015D_SUMMARY)
    df = df[(df["unit"].eq("dataset_total")) & (df["source_file"].eq("ALL"))].copy()
    rows = []
    for _, r in df.iterrows():
        obs = float(r["q99_official_observed"])
        exp = float(r["q99_official_expected"])
        rows.append(
            {
                "validation_sample": "Run2015D_existing_residual_score_cross_check",
                "score_definition": "older Run2015D residual Q99 score; same uncertainty only, not identical frozen score",
                "era": "Run2015D",
                "primary_dataset": r["primary_dataset"],
                "jet_bin": r["jet_bin"],
                "events": np.nan,
                "q99_observed": obs,
                "q99_expected": exp,
                "obs_exp": obs / exp if exp > 0 else np.nan,
                "Z_control_calibrated": z_value(obs, exp),
            }
        )
    return pd.DataFrame(rows)


def compact_readout(stage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample, g in stage.groupby("validation_sample", sort=False):
        def val(dataset: str, jet: str) -> float:
            row = g[(g["primary_dataset"].eq(dataset)) & (g["jet_bin"].eq(jet))]
            return float(row["Z_control_calibrated"].iloc[0]) if not row.empty else np.nan

        controls = g[g["primary_dataset"].isin(CONTROL_DATASETS)]["Z_control_calibrated"].dropna().to_numpy(float)
        signals = np.array([x for x in [val("MET", "0jet"), val("HTMHT", "1to2jets")] if np.isfinite(x)])
        rows.append(
            {
                "validation_sample": sample,
                "score_definition": str(g["score_definition"].iloc[0]),
                "relative_uncertainty_applied": CONTROL_CALIBRATED_RELUNC,
                "MET_0jet_Z": val("MET", "0jet"),
                "HTMHT_1to2jets_Z": val("HTMHT", "1to2jets"),
                "signal_stouffer_Z": float(signals.sum() / np.sqrt(len(signals))) if len(signals) else np.nan,
                "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                "max_control_absZ": float(np.max(np.abs(controls))) if len(controls) else np.nan,
                "controls_close_under_3sigma": bool(len(controls) and np.max(np.abs(controls)) <= 3.0),
                "MET_survives_Z5": bool(val("MET", "0jet") >= 5),
                "repeatable_trace_pass": bool(len(controls) and np.max(np.abs(controls)) <= 3.0 and val("MET", "0jet") >= 5),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not RUN2016H.exists():
        raise SystemExit(f"Missing Run2016H scored events: {RUN2016H}")
    if not RUN2015D_SUMMARY.exists():
        raise SystemExit(f"Missing Run2015D summary: {RUN2015D_SUMMARY}")

    tagged2016h, stage2016h = run2016h_missing_decile_q99()
    stage2015d = run2015d_existing_q99()
    stage = pd.concat([stage2016h, stage2015d], ignore_index=True)
    compact = compact_readout(stage)

    tagged2016h[
        [
            "run_era",
            "primary_dataset",
            "run",
            "lumi",
            "event",
            "missing_proxy_pt",
            "missing_bin",
            "jet_bin",
            "frozen_boundary_score_recomputed",
            "q99_tail",
            "expected_tail_fraction",
        ]
    ].to_csv(TABLES / "00_run2016h_recomputed_frozen_score_tagged_events.csv.gz", index=False, compression="gzip")
    stage.to_csv(TABLES / "01_cross_sample_control_calibrated_stage_table.csv", index=False)
    compact.to_csv(TABLES / "02_cross_sample_control_calibrated_compact_readout.csv", index=False)

    report = f"""# Control-Calibrated Cross-Sample Validation

## Purpose

This applies the Run2016G-derived control-calibrated uncertainty unchanged:

```text
relative_uncertainty = {CONTROL_CALIBRATED_RELUNC:.12f}
```

This uncertainty was the smallest value that closed all Run2016G JetHT and SingleMuon controls under 3 sigma.

## What Was Validated

1. `Run2016H_fresh_same_frozen_score`: recomputed the same frozen N-Frame component score used in Run2016G, using fresh Run2016H events.
2. `Run2015D_existing_residual_score_cross_check`: applied the same uncertainty to the existing Run2015D residual-score Q99 summary. This is a weaker cross-check because the score definition is not identical.

## Compact Readout

{compact.to_markdown(index=False, floatfmt=".3f")}

## Full Stage Table

{stage.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

A repeatable trace pass requires both:

- MET 0jet remains above 5 sigma.
- JetHT and SingleMuon controls close under 3 sigma.

If Run2016H passes, that is an independent same-era validation of the frozen score. If Run2015D fails or is mixed, it does not fully refute the result because the available 2015 check uses a different residual-score pipeline, but it does show that a true cross-era claim still needs a harmonised 2015/2016 score extraction.
"""
    (REPORTS / "01_CONTROL_CALIBRATED_CROSS_SAMPLE_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_CONTROL_CALIBRATED_CROSS_SAMPLE_VALIDATION_REPORT.md")
    print(compact.to_string(index=False))


if __name__ == "__main__":
    main()
