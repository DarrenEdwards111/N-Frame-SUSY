from __future__ import annotations

from pathlib import Path

import importlib.util
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_run2016_quality_clean_frozen_q99_profile"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

spec = importlib.util.spec_from_file_location("audit176", ROOT / "scripts/176_frozen_q99_multifile_breakthrough_audit.py")
audit176 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit176)

spec2 = importlib.util.spec_from_file_location("profile184", ROOT / "scripts/184_frozen_q99_profile_likelihood_sideband_fit.py")
profile = importlib.util.module_from_spec(spec2)
assert spec2.loader is not None
spec2.loader.exec_module(profile)

QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def read_real_quality_inputs(params: dict, met_edges: list[float], score_edges: dict[int, list[float]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = audit176.FEATURES
    frames = []
    audit_rows = []
    for sample, path in audit176.REAL_INPUTS:
        if not path.exists():
            continue
        header = pd.read_csv(path, nrows=0).columns
        wanted = ["primary_dataset", "source_file", "run", "lumi", "event", "sample_id", "record_id"] + features + QUALITY_FILTERS
        use = [c for c in wanted if c in header]
        df = pd.read_csv(path, usecols=use, low_memory=False)
        if "primary_dataset" in df:
            df = df[df["primary_dataset"].astype(str).eq("MET")].copy()
        for col in QUALITY_FILTERS:
            if col not in df:
                df[col] = -999
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(-999)
        df["strict_quality_clean_2016"] = (df[QUALITY_FILTERS] == 1).all(axis=1)
        before = len(df)
        q99_input = df.copy()
        for col in ["run", "lumi", "event"]:
            if col not in df:
                df[col] = np.nan
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["event_key"] = df["run"].astype("Int64").astype(str) + ":" + df["lumi"].astype("Int64").astype(str) + ":" + df["event"].astype("Int64").astype(str)
        df = df[df["strict_quality_clean_2016"]].copy()
        df = audit176.assign_bands(audit176.apply_visible_residual(df, params), met_edges, score_edges)
        df["input_group"] = sample
        frames.append(df)
        audit_rows.append(
            {
                "input_group": sample,
                "path": str(path),
                "events_before": before,
                "events_after_strict_quality_and_band_assignment": len(df),
                "retention_fraction": len(df) / before if before else np.nan,
                "source_files": df["source_file"].nunique() if "source_file" in df else 0,
            }
        )
    real = pd.concat(frames, ignore_index=True)
    real = real.drop_duplicates(["source_file", "event_key"], keep="last").copy()
    real["jet_bin_frozen"] = pd.cut(
        real["N_jets_30"].fillna(0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    return real, pd.DataFrame(audit_rows)


def build_counts() -> tuple[pd.DataFrame, pd.DataFrame]:
    sm = audit176.read_sm()
    params, sm = audit176.fit_visible_residual(sm)
    met_edges, score_edges = audit176.define_bins(sm)
    sm = audit176.add_sm_jet_bin(audit176.assign_bands(sm, met_edges, score_edges))
    real, input_audit = read_real_quality_inputs(params, met_edges, score_edges)
    real.to_csv(TABLES / "00_run2016_quality_clean_real_events_scored.csv", index=False)
    input_audit.to_csv(TABLES / "01_run2016_quality_clean_input_audit.csv", index=False)

    before_scored = pd.read_csv(ROOT / "outputs_frozen_q99_multifile_breakthrough_audit/sources/all_available_real_met_scored_deduplicated.csv", usecols=["source_file", "event_key", "jet_bin_frozen", "score_band"], low_memory=False)
    before_q99 = before_scored[(before_scored["jet_bin_frozen"].eq("1to2jets")) & (before_scored["score_band"].eq("q099_100"))]
    after_q99 = real[(real["jet_bin_frozen"].eq("1to2jets")) & (real["score_band"].eq("q099_100"))]
    q_audit = pd.DataFrame(
        [
            {
                "q99_1to2_before": len(before_q99),
                "q99_1to2_after_strict_quality": len(after_q99),
                "q99_1to2_retention_fraction": len(after_q99) / len(before_q99) if len(before_q99) else np.nan,
                "total_events_before": len(before_scored),
                "total_events_after_strict_quality": len(real),
            }
        ]
    )
    q_audit.to_csv(TABLES / "02_run2016_quality_q99_retention_audit.csv", index=False)

    counts_frames = []
    summaries = []
    for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
        sm_sub = sm[sm["jet_bin_frozen"].eq(jet_bin)]
        real_sub = real[real["jet_bin_frozen"].eq(jet_bin)]
        counts, summary = audit176.counts_for(real_sub, sm_sub, {"unit": "run2016_quality_clean_all", "source_file": "ALL", "jet_bin": jet_bin})
        if not counts.empty:
            counts_frames.append(counts)
        summaries.append(summary)
        for source_file, real_file in real_sub.groupby("source_file"):
            if len(real_file) < 500:
                continue
            counts, summary = audit176.counts_for(real_file, sm_sub, {"unit": "source_file", "source_file": source_file, "jet_bin": jet_bin})
            if not counts.empty:
                counts_frames.append(counts)
            summaries.append(summary)
    counts = pd.concat(counts_frames, ignore_index=True)
    summary = pd.DataFrame(summaries)
    counts.to_csv(TABLES / "03_run2016_quality_clean_score_band_counts.csv", index=False)
    summary.to_csv(TABLES / "04_run2016_quality_clean_shape_summary.csv", index=False)
    return counts, summary


def profile_counts(counts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fitted, summary, meta = profile.run_unit(
        counts[counts["unit"].eq("run2016_quality_clean_all")],
        {"era": "Run2016_quality_clean", "sample": "all_quality_clean_MET", "primary_dataset": "MET"},
    )
    fitted.to_csv(TABLES / "05_run2016_quality_clean_profile_fitted_counts.csv", index=False)
    summary.to_csv(TABLES / "06_run2016_quality_clean_profile_summary.csv", index=False)
    signal = summary[summary["role"].eq("frozen_signal_region")]
    controls = summary[summary["role"].eq("jet_bin_control")]
    combo = pd.DataFrame(
        [
            {
                "test": "Run2016 strict quality clean aggregate MET",
                "signal_Z": float(signal["q99_profile_Z"].iloc[0]) if not signal.empty else np.nan,
                "signal_obs_exp": float(signal["q99_obs_exp_profile"].iloc[0]) if not signal.empty else np.nan,
                "max_abs_control_Z": float(controls["q99_profile_Z"].abs().max()) if not controls.empty else np.nan,
                "controls_close_absZ_lt3": bool((controls["q99_profile_Z"].abs() < 3).all()) if not controls.empty else False,
                "discovery_like_pattern": bool((not signal.empty) and (float(signal["q99_profile_Z"].iloc[0]) >= 5) and ((controls["q99_profile_Z"].abs() < 3).all() if not controls.empty else False)),
            }
        ]
    )
    combo.to_csv(TABLES / "07_run2016_quality_clean_combined_readout.csv", index=False)
    return summary, combo


def write_report(summary: pd.DataFrame, combo: pd.DataFrame) -> None:
    input_audit = pd.read_csv(TABLES / "01_run2016_quality_clean_input_audit.csv")
    retention = pd.read_csv(TABLES / "02_run2016_quality_q99_retention_audit.csv")
    report = f"""# Run2016 Strict Quality-Clean Frozen Q99 Profile

## Purpose

The Run2015D pilot largely collapsed after strict event-quality cleaning. This report tests whether the main Run2016 Q99 candidate behaves the same way.

Strict quality definition:

- pass_goodVertices == 1
- pass_HBHENoiseFilter == 1
- pass_HBHENoiseIsoFilter == 1

The frozen Q99 rule is not changed.

## Input Audit

{input_audit.to_markdown(index=False)}

## Q99 Retention Audit

{retention.to_markdown(index=False)}

## Quality-Clean Profile Readout

{summary.to_markdown(index=False)}

## Combined Readout

{combo.to_markdown(index=False)}

## Interpretation

If the Run2016 Q99 signal remains while controls close, then the Run2016 candidate is less likely to be the same quality/filter artefact seen in Run2015D. If it collapses, the candidate is weakened substantially.
"""
    (REPORTS / "01_RUN2016_QUALITY_CLEAN_FROZEN_Q99_PROFILE_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Run2016 Quality-Clean Q99

{combo.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_RUN2016_QUALITY_CLEAN_Q99.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    counts, _ = build_counts()
    summary, combo = profile_counts(counts)
    write_report(summary, combo)
    print("RUN2016 QUALITY-CLEAN FROZEN Q99 PROFILE COMPLETE")
    print(combo.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
