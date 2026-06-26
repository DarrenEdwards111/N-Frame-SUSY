from __future__ import annotations

"""Measure observed exact-trigger turn-ons in the compact Run2016G sample."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs_exact_trigger_calibration_run2016g" / "tables" / "03_exact_trigger_calibration_events.csv"
OUT = ROOT / "outputs_exact_trigger_calibration_run2016g"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPECS = [
    ("MET", "HLT_MET_high_union", "MET_pt", np.arange(0, 351, 25)),
    ("MET", "HLT_PFMET110_PFMHT110_IDTight", "MET_pt", np.arange(0, 351, 25)),
    ("JetHT", "HLT_PFHT800", "HT", np.arange(0, 1601, 100)),
    ("JetHT", "HLT_PFHT900", "HT", np.arange(0, 1601, 100)),
    ("SingleMuon", "HLT_SingleMuon_high_union", "leading_muon_pt", np.arange(0, 251, 10)),
    ("SingleMuon", "HLT_IsoMu24", "leading_muon_pt", np.arange(0, 251, 10)),
    ("SingleMuon", "HLT_IsoTkMu24", "leading_muon_pt", np.arange(0, 251, 10)),
    ("SingleMuon", "HLT_Mu50", "leading_muon_pt", np.arange(0, 251, 10)),
]


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    df["HLT_MET_high_union"] = (
        df[["HLT_PFMET110_PFMHT110_IDTight", "HLT_PFMET120_PFMHT120_IDTight", "HLT_PFMET170_HBHECleaned", "HLT_PFMET170_NotCleaned"]]
        .fillna(0)
        .max(axis=1)
    )
    df["HLT_SingleMuon_high_union"] = (
        df[["HLT_IsoMu24", "HLT_IsoTkMu24", "HLT_Mu50"]].fillna(0).max(axis=1)
    )
    rows = []
    plateau_rows = []
    for dataset, trigger, variable, edges in SPECS:
        g = df[df["primary_dataset"].eq(dataset)].copy()
        g["bin"] = pd.cut(pd.to_numeric(g[variable], errors="coerce"), edges, right=False, include_lowest=True)
        grouped = g.groupby("bin", observed=False).agg(total=(trigger, "size"), passed=(trigger, "sum"), value_low=(variable, "min"), value_high=(variable, "max")).reset_index()
        grouped["efficiency"] = grouped["passed"] / grouped["total"].replace(0, np.nan)
        grouped.insert(0, "offline_variable", variable)
        grouped.insert(0, "trigger", trigger)
        grouped.insert(0, "primary_dataset", dataset)
        rows.append(grouped)
        stable = grouped[(grouped["total"] >= 20) & (grouped["efficiency"] >= 0.95)]
        plateau_rows.append({"primary_dataset": dataset, "trigger": trigger, "offline_variable": variable, "first_observed_95pct_plateau_low_edge": float(stable["value_low"].min()) if not stable.empty else np.nan, "has_95pct_plateau_in_5000_events": bool(not stable.empty)})
    turnon = pd.concat(rows, ignore_index=True)
    plateaus = pd.DataFrame(plateau_rows)
    turnon.to_csv(TABLES / "04_exact_trigger_turnon_bins.csv", index=False)
    plateaus.to_csv(TABLES / "05_exact_trigger_plateau_summary.csv", index=False)
    report = f"""# Exact Trigger Turn-On Audit

## Plateau Summary

{plateaus.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

The sampled primary datasets are trigger-stream unions. A path can only define
a common offline plateau if its observed efficiency reaches a stable high value
in the relevant offline variable. Missing plateaus mean the current exact path
set is incomplete and must be expanded before stream-matched MC transfer can
be considered resolved.
"""
    (REPORTS / "01_EXACT_TRIGGER_TURNON_AUDIT.md").write_text(report, encoding="utf-8")
    print(plateaus.to_string(index=False))
    print(REPORTS / "01_EXACT_TRIGGER_TURNON_AUDIT.md")


if __name__ == "__main__":
    main()
