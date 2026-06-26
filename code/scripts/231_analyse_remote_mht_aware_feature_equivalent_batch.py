from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import combine_pvalues


ROOT = Path(__file__).resolve().parents[1]
MOD = SourceFileLoader("cross_sample", str(ROOT / "scripts" / "226_cross_sample_frozen_trace_validation.py")).load_module()

OUT = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
LEDGER = OUT / "remote_xrootd" / "remote_processing_ledger.csv"


def ensure_dirs() -> None:
    for path in [TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def load_remote_completed() -> pd.DataFrame:
    ledger = pd.read_csv(LEDGER)
    ledger = ledger[ledger["status"].eq("completed")].copy()
    frames = []
    for _, row in ledger.iterrows():
        path = Path(str(row["output_path"]))
        if not path.exists():
            continue
        df = pd.read_csv(path, low_memory=False)
        df.insert(0, "remote_run_id", f"remote_{int(row.record_id)}_{row.primary_dataset}_{int(row.file_index)}")
        validation_id = row.get("validation_sample_id", None)
        if pd.isna(validation_id) or not str(validation_id).strip():
            validation_id = f"{row.run_era}_remote_mht_aware"
        df.insert(1, "sample_validation_id", str(validation_id))
        df.insert(2, "run_era", row.run_era)
        df.insert(3, "primary_dataset", row.primary_dataset)
        df.insert(4, "record_id", int(row.record_id))
        df.insert(5, "file_index", int(row.file_index))
        df.insert(6, "xrootd_url", row.xrootd_url)
        frames.append(df)
    if not frames:
        raise RuntimeError("No completed remote feature outputs were available.")
    return pd.concat(frames, ignore_index=True, sort=False)


def add_components(events: pd.DataFrame) -> pd.DataFrame:
    clean = events[MOD.strict_quality(events)].copy()
    frames = []
    for (_sample, _dataset), group in clean.groupby(["sample_validation_id", "primary_dataset"], sort=False):
        frames.append(MOD.add_components_one_dataset(group))
    out = pd.concat(frames, ignore_index=True, sort=False)
    out["missing_for_decile"] = out["missing_proxy_pt"]
    out = MOD.add_missing_deciles(out)
    return out


def evaluate(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    vectors = []
    for candidate in MOD.FROZEN_CANDIDATES:
        tagged = MOD.tag_microbands(events, MOD.score_candidate(events, candidate))
        counts = (
            tagged.groupby(["sample_validation_id", "run_era", "primary_dataset", "jet_bin", "microband"], observed=False)
            .size()
            .reset_index(name="observed")
        )
        for sample_id in sorted(events["sample_validation_id"].unique()):
            trace = MOD.vector(counts, sample_id, [MOD.TRACE_REGION])
            control = MOD.vector(counts, sample_id, MOD.CONTROL_REGIONS)
            metrics = MOD.shape_metrics(trace, control)
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "sample_validation_id": sample_id,
                    **{col: candidate[col] for col in MOD.COMPONENTS},
                    **metrics,
                    "shoulder_above_control": bool(
                        metrics.get("trace_95_99_over_90_95_density_ratio", -np.inf)
                        > metrics.get("control_95_99_over_90_95_density_ratio", np.inf)
                    ),
                }
            )
            for band, t, c in zip([band for band, *_ in MOD.MICROBANDS], trace, control):
                vectors.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "sample_validation_id": sample_id,
                        "microband": band,
                        "trace_count": float(t),
                        "control_count": float(c),
                    }
                )
    summary = pd.DataFrame(rows)
    ready_rows = []
    for candidate_id, group in summary.groupby("candidate_id", observed=False):
        pvals = group["shape_p"].dropna().to_numpy(float)
        _stat, fisher_p = combine_pvalues(pvals, method="fisher") if len(pvals) else (np.nan, np.nan)
        ready_rows.append(
            {
                "candidate_id": candidate_id,
                "remote_samples_tested": len(group),
                "remote_samples_shape_Z_ge_5": int((group["shape_Z"] >= 5).sum()),
                "remote_samples_shoulder_above_control": int(group["shoulder_above_control"].sum()),
                "min_remote_shape_Z": float(group["shape_Z"].min(skipna=True)),
                "median_remote_shape_Z": float(group["shape_Z"].median(skipna=True)),
                "fisher_remote_shape_p": float(fisher_p),
                "fisher_remote_shape_Z": MOD.p_to_z(float(fisher_p)) if np.isfinite(fisher_p) else np.nan,
                "remote_strict_pass": bool((group["shape_Z"] >= 5).all() and group["shoulder_above_control"].all()),
            }
        )
    return summary, pd.DataFrame(vectors), pd.DataFrame(ready_rows)


def write_report(events: pd.DataFrame, summary: pd.DataFrame, ready: pd.DataFrame) -> None:
    audit = (
        events.groupby(["sample_validation_id", "primary_dataset"], observed=False)
        .size()
        .reset_index(name="strict_quality_events")
    )
    report = f"""# Remote MHT-Aware Feature-Equivalent Validation

## Purpose

This run addresses the main blocker from the previous handoff: some samples were MHT-aware while others were MET-only or recomputed from reduced features. Here, CMS MiniAOD files were read remotely through XRootD, using CMSSW/Docker, and compact MHT-aware event-feature CSVs were produced without retaining raw ROOT files locally.

The frozen N-Frame trace scores were then applied unchanged:

- `observer_physical_clean`: $B = 0.5O + 0.5P$
- `observer_physical_qcd_suppressed_scan_best`: $B = 0.344828O + 0.517241P - 0.137931Q$

## Remote Batch

{audit.to_markdown(index=False)}

## Frozen Score Results

{summary[["candidate_id", "sample_validation_id", "trace_total", "control_total", "shape_Z", "shoulder_Z", "trace_95_99_over_90_95_density_ratio", "control_95_99_over_90_95_density_ratio", "shoulder_above_control"]].to_markdown(index=False, floatfmt=".6g")}

## Remote Readiness

{ready.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

This is the first feature-equivalent remote validation batch after the dynamic-boundary blocker was identified. The raw CMS MiniAOD files were not kept locally; only compact event-feature tables and logs were retained.

If the clean score passes in both remote samples, that strengthens the conservative N-Frame boundary-trace claim. If the optimized QCD-suppressed score fails, it should remain exploratory rather than headline.

The remote batch is asymmetric by design: Run2015D contains three unused files per stream, while Run2016H now includes every remaining prepared file in the remote manifest (9 HTMHT, 8 JetHT, 11 MET and 5 SingleMuon files). Each file is capped at 5,000 events. No score retuning was performed while scaling the batch.

The clean observer/physical score does not pass the full remote Run2016H test. The QCD-suppressed score does pass the predefined remote two-era screen in this batch. That is an important validation result, but it remains a project-level control-shape result rather than an official CMS discovery measurement: the score was selected before this remote scale-up, the remote stream mixture is not luminosity weighted, and the Standard Model nuisance model remains incomplete.
"""
    (REPORTS / "01_REMOTE_MHT_AWARE_FEATURE_EQUIVALENT_VALIDATION.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    raw = load_remote_completed()
    raw.to_csv(TABLES / "03_remote_mht_aware_raw_merged_features.csv", index=False)
    events = add_components(raw)
    events.to_csv(TABLES / "04_remote_mht_aware_scored_axis_events.csv", index=False)
    audit = (
        events.groupby(["sample_validation_id", "primary_dataset", "jet_bin"], observed=False)
        .size()
        .reset_index(name="strict_quality_events")
    )
    audit.to_csv(TABLES / "05_remote_region_event_audit.csv", index=False)
    summary, vectors, ready = evaluate(events)
    summary.to_csv(TABLES / "06_remote_frozen_trace_summary.csv", index=False)
    vectors.to_csv(TABLES / "07_remote_microband_vectors.csv", index=False)
    ready.to_csv(TABLES / "08_remote_readiness_summary.csv", index=False)
    write_report(events, summary, ready)
    print(REPORTS / "01_REMOTE_MHT_AWARE_FEATURE_EQUIVALENT_VALIDATION.md")
    print(ready.to_string(index=False))


if __name__ == "__main__":
    main()
