from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from importlib.machinery import SourceFileLoader


ROOT = Path(__file__).resolve().parents[1]
MOD = SourceFileLoader("cross_sample", str(ROOT / "scripts" / "226_cross_sample_frozen_trace_validation.py")).load_module()
OUT = ROOT / "outputs_trace_sample_mismatch_diagnostic"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def quantile_row(group: pd.DataFrame, value_col: str) -> dict[str, float]:
    values = pd.to_numeric(group[value_col], errors="coerce").fillna(0.0)
    return {
        f"{value_col}_mean": float(values.mean()),
        f"{value_col}_p50": float(values.quantile(0.50)),
        f"{value_col}_p90": float(values.quantile(0.90)),
        f"{value_col}_p95": float(values.quantile(0.95)),
        f"{value_col}_p99": float(values.quantile(0.99)),
    }


def load_all() -> pd.DataFrame:
    frames = []
    for config in MOD.SAMPLES:
        path = Path(config["path"])
        if path.exists():
            sample = MOD.load_sample(config)
            sample = MOD.add_missing_deciles(sample)
            for candidate in MOD.FROZEN_CANDIDATES:
                sample[candidate["candidate_id"]] = MOD.score_candidate(sample, candidate)
            frames.append(sample)
    return pd.concat(frames, ignore_index=True, sort=False)


def feature_audit(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cols = [
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "secondary_vertex_count",
        "packed_candidate_count",
        "observer_projection",
        "physical_projection",
        "ordinary_qcd_axis",
        "observer_physical_clean",
        "observer_physical_qcd_suppressed_scan_best",
    ]
    for (sample_id, dataset), group in events.groupby(["sample_validation_id", "primary_dataset"], observed=False):
        row = {"sample_validation_id": sample_id, "primary_dataset": dataset, "events": len(group)}
        for col in cols:
            if col in group.columns:
                row.update(quantile_row(group, col))
        rows.append(row)
    return pd.DataFrame(rows)


def trace_vs_controls_feature_audit(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample_id, sample in events.groupby("sample_validation_id", observed=False):
        trace = sample[sample["primary_dataset"].eq("MET") & sample["jet_bin"].astype(str).eq("0jet")]
        controls = sample[sample["primary_dataset"].isin(["JetHT", "SingleMuon"])]
        for label, group in [("MET_0jet_trace", trace), ("JetHT_SingleMuon_controls", controls)]:
            row = {"sample_validation_id": sample_id, "region": label, "events": len(group)}
            for col in [
                "MET_pt",
                "HT",
                "N_jets_30",
                "secondary_vertex_count",
                "packed_candidate_count",
                "observer_projection",
                "physical_projection",
                "ordinary_qcd_axis",
                "observer_physical_clean",
                "observer_physical_qcd_suppressed_scan_best",
            ]:
                if col in group.columns:
                    row.update(quantile_row(group, col))
            rows.append(row)
    return pd.DataFrame(rows)


def write_report(feature: pd.DataFrame, trace_control: pd.DataFrame, cross: pd.DataFrame) -> None:
    expanded = cross[cross["sample_validation_id"].eq("Run2016H_expanded_miniaod")]
    report = f"""# Trace Sample Mismatch Diagnostic

## Purpose

The frozen cross-sample validation showed that the trace is strong in Run2015D, Run2016G and the MHT-aware Run2016H sample, but less stable in the expanded Run2016H MiniAOD sample. This diagnostic checks whether that is a real contradiction or a feature/proxy/sample-composition mismatch.

## Expanded Run2016H Readout

{expanded[["candidate_id", "shape_Z", "shoulder_Z", "trace_95_99_over_90_95_density_ratio", "control_95_99_over_90_95_density_ratio", "trace_99_over_95_99_density_ratio", "control_99_over_95_99_density_ratio"]].to_markdown(index=False, floatfmt=".6g")}

## Trace vs Controls Feature Summary

{trace_control.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

The expanded Run2016H MiniAOD sample is not a simple repeat of the MHT-aware fresh Run2016H validation. It lacks HTMHT coverage in this table and uses recomputed MET-only axes rather than the precomputed MHT-aware axes. The clean observer/physical score still gives a formal shape difference above 5 sigma in this sample, but it does not reproduce the same elevated 95-99 shoulder direction. The QCD-suppressed score keeps the shoulder direction, but its total shape significance falls to about 1.3 sigma.

This means the current evidence is strongest for a repeated boundary-transition trace across several samples, but not yet a universal score that is invariant to feature availability and sample construction. The next publishability step is a cloud/remote extraction that computes the same MHT-aware axis set for the expanded/unused samples, rather than mixing MHT-aware and MET-only feature sets.
"""
    (REPORTS / "01_TRACE_SAMPLE_MISMATCH_DIAGNOSTIC.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    events = load_all()
    feature = feature_audit(events)
    trace_control = trace_vs_controls_feature_audit(events)
    cross = pd.read_csv(ROOT / "outputs_cross_sample_frozen_trace_validation" / "tables" / "02_cross_sample_frozen_trace_summary.csv")
    feature.to_csv(TABLES / "01_sample_feature_audit.csv", index=False)
    trace_control.to_csv(TABLES / "02_trace_vs_controls_feature_audit.csv", index=False)
    write_report(feature, trace_control, cross)
    print(REPORTS / "01_TRACE_SAMPLE_MISMATCH_DIAGNOSTIC.md")


if __name__ == "__main__":
    main()
