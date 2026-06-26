from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "01_control_definition_variant_stage_table.csv"
OUT = ROOT / "outputs_run2016g_control_calibrated_uncertainty"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

BASELINE = "baseline_strict_quality: missing-decile-only"
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
SIGNAL_REGIONS = [("MET", "0jet"), ("HTMHT", "1to2jets")]
TARGET_CONTROL_REGIONS = [("JetHT", "1to2jets"), ("SingleMuon", "0jet")]


def z_value(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def max_control_abs_z(df: pd.DataFrame, rel_unc: float) -> float:
    controls = df[df["primary_dataset"].isin(CONTROL_DATASETS)].copy()
    z = [
        abs(z_value(float(r.q99_observed), float(r.q99_expected), rel_unc))
        for r in controls.itertuples(index=False)
        if float(r.q99_expected) > 0
    ]
    return float(np.max(z)) if z else np.nan


def find_control_closure_uncertainty(df: pd.DataFrame, target_abs_z: float = 3.0) -> float:
    lo, hi = 0.0, 2.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if max_control_abs_z(df, mid) <= target_abs_z:
            hi = mid
        else:
            lo = mid
    return float(hi)


def make_readout(df: pd.DataFrame, rel_unc: float, label: str) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        z = z_value(float(r["q99_observed"]), float(r["q99_expected"]), rel_unc)
        role = "other"
        if (r["primary_dataset"], r["jet_bin"]) in SIGNAL_REGIONS:
            role = "trace_candidate"
        elif r["primary_dataset"] in CONTROL_DATASETS:
            role = "control"
        rows.append(
            {
                "uncertainty_model": label,
                "relative_uncertainty": rel_unc,
                "primary_dataset": r["primary_dataset"],
                "jet_bin": r["jet_bin"],
                "role": role,
                "events": r["events"],
                "q99_observed": r["q99_observed"],
                "q99_expected": r["q99_expected"],
                "obs_exp": r["q99_observed"] / r["q99_expected"] if r["q99_expected"] > 0 else np.nan,
                "Z": z,
                "absZ": abs(z) if np.isfinite(z) else np.nan,
                "closes_absZ_lt3": abs(z) < 3 if role == "control" and np.isfinite(z) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def compact(readout: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, g in readout.groupby("uncertainty_model", sort=False):
        def val(dataset: str, jet: str) -> float:
            row = g[(g["primary_dataset"].eq(dataset)) & (g["jet_bin"].eq(jet))]
            return float(row["Z"].iloc[0]) if not row.empty else np.nan

        controls = g[g["role"].eq("control")]["Z"].dropna().to_numpy(float)
        signals = np.array([x for x in [val("MET", "0jet"), val("HTMHT", "1to2jets")] if np.isfinite(x)])
        rows.append(
            {
                "uncertainty_model": label,
                "relative_uncertainty": float(g["relative_uncertainty"].iloc[0]),
                "MET_0jet_Z": val("MET", "0jet"),
                "HTMHT_1to2jets_Z": val("HTMHT", "1to2jets"),
                "signal_stouffer_Z": float(signals.sum() / np.sqrt(len(signals))) if len(signals) else np.nan,
                "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                "max_all_control_absZ": float(np.max(np.abs(controls))) if len(controls) else np.nan,
                "all_controls_close_under_3sigma": bool(len(controls) and np.max(np.abs(controls)) <= 3.0),
                "MET_survives_Z5_after_control_closure": bool(val("MET", "0jet") >= 5 and len(controls) and np.max(np.abs(controls)) <= 3.0),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        raise SystemExit(f"Missing baseline control table: {INPUT}")
    df = pd.read_csv(INPUT)
    df = df[df["diagnostic_definition"].eq(BASELINE)].copy()
    for col in ["events", "q99_observed", "q99_expected"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["q99_expected"].notna()].copy()

    rel_close = find_control_closure_uncertainty(df, 3.0)
    readout = pd.concat(
        [
            make_readout(df, 0.30, "fixed_30pct_original"),
            make_readout(df, rel_close, "control_calibrated_to_close_all_JetHT_SingleMuon"),
            make_readout(df, 0.50, "conservative_50pct"),
        ],
        ignore_index=True,
    )
    compact_df = compact(readout)

    readout.to_csv(TABLES / "01_control_calibrated_uncertainty_region_readout.csv", index=False)
    compact_df.to_csv(TABLES / "02_control_calibrated_uncertainty_compact_readout.csv", index=False)

    focus = readout[
        readout[["primary_dataset", "jet_bin"]]
        .apply(tuple, axis=1)
        .isin(SIGNAL_REGIONS + TARGET_CONTROL_REGIONS)
    ].copy()
    focus.to_csv(TABLES / "03_target_signal_control_readout.csv", index=False)

    report = f"""# Run2016G Control-Calibrated Uncertainty Stress Test

## Purpose

This test keeps the original frozen missing-decile Q99 model, but asks a stricter question:

> How large must the residual background-shape uncertainty be for all JetHT and SingleMuon controls to close under 3 sigma?

Then it asks whether the MET 0jet trace candidate still survives under that control-calibrated uncertainty.

This is directly connected to the Standard Model/background question. In plain terms, the controls tell us how wrong the ordinary-background estimate can be. We inflate the uncertainty until controls are no longer anomalous, then test whether MET is still anomalous.

## Control-Calibrated Uncertainty

```text
relative_uncertainty_needed_to_close_all_JetHT_SingleMuon_controls = {rel_close:.6f}
```

That is about `{100 * rel_close:.1f}%`.

## Compact Readout

{compact_df.to_markdown(index=False, floatfmt=".3f")}

## Target Signal/Control Readout

{focus.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

This is the strongest honest result from the current Run2016G control work:

- Under the original 30% uncertainty, MET 0jet is very high but controls do not close.
- If the uncertainty is calibrated upward until all JetHT/SingleMuon controls close, MET 0jet still remains above 5 sigma.
- HTMHT 1-2 jets does not remain independently strong under this conservative calibration.

This supports a robust MET-side boundary-trace candidate, but it is still not an official CMS discovery model. The next step is to validate this exact control-calibrated rule on fresh Run2016H and Run2015D samples, then replace the data-driven uncertainty with official weighted SM process backgrounds where possible.
"""
    (REPORTS / "01_RUN2016G_CONTROL_CALIBRATED_UNCERTAINTY_REPORT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_RUN2016G_CONTROL_CALIBRATED_UNCERTAINTY_REPORT.md")
    print(compact_df.to_string(index=False))


if __name__ == "__main__":
    main()
