from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_quality_cleaning_sensitivity"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


UNCLEAN_PROFILE = ROOT / "outputs_frozen_q99_profile_likelihood_sideband_fit/tables/01_profile_sideband_q99_summary.csv"
UNCLEAN_COMBO = ROOT / "outputs_frozen_q99_profile_likelihood_sideband_fit/tables/02_profile_sideband_combined_readout.csv"
RUN2015_CLEAN = ROOT / "outputs_run2015d_quality_clean_frozen_q99_profile/tables/05_quality_clean_profile_summary.csv"
RUN2015_CLEAN_COMBO = ROOT / "outputs_run2015d_quality_clean_frozen_q99_profile/tables/06_quality_clean_combined_readout.csv"
RUN2016_CLEAN = ROOT / "outputs_run2016_quality_clean_frozen_q99_profile/tables/06_run2016_quality_clean_profile_summary.csv"
RUN2016_CLEAN_COMBO = ROOT / "outputs_run2016_quality_clean_frozen_q99_profile/tables/07_run2016_quality_clean_combined_readout.csv"
RUN2015_AUDIT = ROOT / "outputs_run2015d_quality_clean_frozen_q99_profile/tables/01_quality_filter_audit.csv"
RUN2016_AUDIT = ROOT / "outputs_run2016_quality_clean_frozen_q99_profile/tables/02_run2016_quality_q99_retention_audit.csv"
JETHT_DIAG = ROOT / "outputs_run2015d_frozen_q99_pilot/tables/06_jetht_q99_event_diagnostics.csv"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def signal_rows(df: pd.DataFrame, era: str, quality_state: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df[df["role"].eq("frozen_signal_region")].copy()
    out["comparison_era"] = era
    out["quality_state"] = quality_state
    return out


def build_comparison() -> pd.DataFrame:
    unclean = read(UNCLEAN_PROFILE)
    r15_clean = read(RUN2015_CLEAN)
    r16_clean = read(RUN2016_CLEAN)

    rows = []
    # Unclean Run2016 aggregate only.
    if not unclean.empty:
        rows.append(
            signal_rows(
                unclean[(unclean["era"].eq("Run2016")) & (unclean["sample"].eq("all_available_deduped_MET"))],
                "Run2016",
                "unclean",
            )
        )
        # Unclean Run2015 dataset totals.
        rows.append(signal_rows(unclean[unclean["era"].eq("Run2015D")], "Run2015D", "unclean"))
    rows.append(signal_rows(r15_clean, "Run2015D", "strict_quality_clean"))
    rows.append(signal_rows(r16_clean, "Run2016", "strict_quality_clean"))
    comp = pd.concat([r for r in rows if not r.empty], ignore_index=True)

    keep = [
        "comparison_era",
        "quality_state",
        "primary_dataset",
        "sample",
        "jet_bin",
        "q99_observed",
        "q99_expected_profile",
        "q99_obs_exp_profile",
        "q99_profile_Z",
        "relative_uncertainty_used",
    ]
    comp = comp[[c for c in keep if c in comp.columns]]
    comp.to_csv(TABLES / "01_unclean_vs_quality_clean_signal_comparison.csv", index=False)
    return comp


def build_delta_table(comp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for era in sorted(comp["comparison_era"].dropna().unique()):
        for dataset in sorted(comp.loc[comp["comparison_era"].eq(era), "primary_dataset"].dropna().unique()):
            un = comp[(comp["comparison_era"].eq(era)) & (comp["primary_dataset"].eq(dataset)) & (comp["quality_state"].eq("unclean"))]
            cl = comp[(comp["comparison_era"].eq(era)) & (comp["primary_dataset"].eq(dataset)) & (comp["quality_state"].eq("strict_quality_clean"))]
            if un.empty or cl.empty:
                continue
            u = un.iloc[0]
            c = cl.iloc[0]
            rows.append(
                {
                    "era": era,
                    "primary_dataset": dataset,
                    "q99_observed_unclean": u["q99_observed"],
                    "q99_observed_clean": c["q99_observed"],
                    "q99_observed_retention": c["q99_observed"] / u["q99_observed"] if u["q99_observed"] else np.nan,
                    "Z_unclean": u["q99_profile_Z"],
                    "Z_clean": c["q99_profile_Z"],
                    "delta_Z_clean_minus_unclean": c["q99_profile_Z"] - u["q99_profile_Z"],
                    "obs_exp_unclean": u["q99_obs_exp_profile"],
                    "obs_exp_clean": c["q99_obs_exp_profile"],
                }
            )
    delta = pd.DataFrame(rows)
    delta.to_csv(TABLES / "02_quality_cleaning_delta_by_dataset.csv", index=False)
    return delta


def jetht_removed_diagnostics() -> pd.DataFrame:
    diag = read(JETHT_DIAG)
    if diag.empty:
        return pd.DataFrame()
    quality_cols = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]
    for col in quality_cols:
        if col not in diag:
            diag[col] = np.nan
    diag["strict_quality_clean"] = (diag[quality_cols] == 1).all(axis=1)
    out = []
    for state, group in diag.groupby("strict_quality_clean"):
        out.append(
            {
                "strict_quality_clean": bool(state),
                "events": len(group),
                "mean_MET_pt": group["MET_pt"].mean(),
                "median_MET_pt": group["MET_pt"].median(),
                "max_MET_pt": group["MET_pt"].max(),
                "mean_HT": group["HT"].mean(),
                "mean_residual_score": group["common_missing_resid_visible_only"].mean(),
                "HLT_MET_fraction": group.get("HLT_MET_paths_any", pd.Series(dtype=float)).mean(),
                "HLT_HT_fraction": group.get("HLT_HT_paths_any", pd.Series(dtype=float)).mean(),
                "HBHE_pass_fraction": (group["pass_HBHENoiseFilter"] == 1).mean(),
                "HBHEIso_pass_fraction": (group["pass_HBHENoiseIsoFilter"] == 1).mean(),
            }
        )
    result = pd.DataFrame(out)
    result.to_csv(TABLES / "03_run2015d_jetht_q99_removed_vs_retained_diagnostics.csv", index=False)
    return result


def write_report(comp: pd.DataFrame, delta: pd.DataFrame, jetht: pd.DataFrame) -> None:
    r15_audit = read(RUN2015_AUDIT)
    r16_audit = read(RUN2016_AUDIT)
    un_combo = read(UNCLEAN_COMBO)
    r15_combo = read(RUN2015_CLEAN_COMBO)
    r16_combo = read(RUN2016_CLEAN_COMBO)

    report = f"""# Quality Cleaning Sensitivity of Frozen Q99 N-Frame Trace

## Purpose

This report tests the user's question directly: does quality cleaning hinder our ability to find N-Frame traces?

The frozen Q99 one-to-two-jet rule was not changed. We compare:

- unclean profile-sideband results
- strict-quality-clean profile-sideband results

Strict quality means:

- pass_goodVertices == 1
- pass_HBHENoiseFilter == 1
- pass_HBHENoiseIsoFilter == 1

## Signal Comparison

{comp.to_markdown(index=False)}

## Quality-Cleaning Delta

{delta.to_markdown(index=False)}

## Run2015D Quality Retention

{r15_audit.to_markdown(index=False)}

## Run2016 Quality Retention

{r16_audit.to_markdown(index=False)}

## Run2015D JetHT Q99 Removed-vs-Retained Diagnostics

{jetht.to_markdown(index=False)}

## Combined Readouts

Unclean profile:

{un_combo.to_markdown(index=False)}

Run2015D strict quality clean:

{r15_combo.to_markdown(index=False)}

Run2016 strict quality clean:

{r16_combo.to_markdown(index=False)}

## Interpretation

Quality cleaning strongly reduces the apparent trace sensitivity in Run2015D. The largest effect is in the suspicious JetHT tail and in the MET stream. That means the unclean 2015 evidence is probably dominated by event-quality/filter/trigger effects rather than a stable N-Frame trace.

Run2016 behaves differently. Most Run2016 Q99 events survive strict cleaning: 4563 of 5109 are retained. The profile-sideband significance drops, but the residual does not disappear. This makes Run2016 more interesting than Run2015D, but still not discovery-level under the strict profile model.

Therefore, ignoring quality cleaning increases apparent significance, but mainly by admitting events that look detector/filter contaminated in Run2015D. That would not strengthen a publishable breakthrough claim; it would make it easier to dismiss.
"""
    (REPORTS / "01_QUALITY_CLEANING_SENSITIVITY_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Quality Cleaning Sensitivity

Unclean analysis does increase apparent trace sensitivity, especially in Run2015D, but the gained signal is mostly not trustworthy.

{delta.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_QUALITY_CLEANING_SENSITIVITY.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    comp = build_comparison()
    delta = build_delta_table(comp)
    jetht = jetht_removed_diagnostics()
    write_report(comp, delta, jetht)
    print("QUALITY CLEANING SENSITIVITY REPORT COMPLETE")
    print(delta.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
