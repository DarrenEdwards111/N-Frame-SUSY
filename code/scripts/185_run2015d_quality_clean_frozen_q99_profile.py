from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import importlib.util


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_run2015d_quality_clean_frozen_q99_profile"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCE_REAL = ROOT / "outputs_run2015d_frozen_q99_pilot/sources/run2015d_all_selected_real_events_scored.csv"

spec = importlib.util.spec_from_file_location("pilot182", ROOT / "scripts/182_run2015d_frozen_q99_pilot.py")
pilot = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(pilot)

spec2 = importlib.util.spec_from_file_location("profile184", ROOT / "scripts/184_frozen_q99_profile_likelihood_sideband_fit.py")
profile = importlib.util.module_from_spec(spec2)
assert spec2.loader is not None
spec2.loader.exec_module(profile)


QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def build_quality_counts() -> tuple[pd.DataFrame, pd.DataFrame]:
    sm = pilot.read_sm()
    params, sm = pilot.fit_visible_residual(sm)
    met_edges, score_edges = pilot.define_bins(sm)
    sm = pilot.assign_bands(sm, met_edges, score_edges)
    sm["jet_bin_frozen"] = pd.cut(
        sm["N_jets_30"].fillna(0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)

    real = pd.read_csv(SOURCE_REAL, low_memory=False)
    before = real.copy()
    for col in QUALITY_FILTERS:
        if col not in real:
            real[col] = -999
        real[col] = pd.to_numeric(real[col], errors="coerce").fillna(-999)
    real["strict_quality_clean_2015"] = (real[QUALITY_FILTERS] == 1).all(axis=1)
    audit = []
    for dataset, group in before.groupby("primary_dataset"):
        cleaned = real[real["primary_dataset"].eq(dataset) & real["strict_quality_clean_2015"]]
        q99_before = real[
            real["primary_dataset"].eq(dataset)
            & real["jet_bin_frozen"].eq("1to2jets")
            & real["score_band"].eq("q099_100")
        ]
        q99_after = cleaned[cleaned["jet_bin_frozen"].eq("1to2jets") & cleaned["score_band"].eq("q099_100")]
        audit.append(
            {
                "primary_dataset": dataset,
                "events_before": len(group),
                "events_after_strict_quality": len(cleaned),
                "retention_fraction": len(cleaned) / len(group) if len(group) else np.nan,
                "q99_1to2_before": len(q99_before),
                "q99_1to2_after": len(q99_after),
                "q99_1to2_retention_fraction": len(q99_after) / len(q99_before) if len(q99_before) else np.nan,
            }
        )
    real = real[real["strict_quality_clean_2015"]].copy()
    real.to_csv(TABLES / "00_run2015d_quality_clean_real_events.csv", index=False)
    pd.DataFrame(audit).to_csv(TABLES / "01_quality_filter_audit.csv", index=False)

    counts_frames = []
    summaries = []
    for dataset in sorted(real["primary_dataset"].dropna().unique()):
        for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
            real_sub = real[(real["primary_dataset"].eq(dataset)) & (real["jet_bin_frozen"].eq(jet_bin))]
            sm_sub = sm[sm["jet_bin_frozen"].eq(jet_bin)]
            counts, summary = pilot.counts_for(
                real_sub,
                sm_sub,
                {"primary_dataset": dataset, "unit": "quality_clean_dataset_total", "source_file": "ALL", "jet_bin": jet_bin},
            )
            if not counts.empty:
                counts_frames.append(counts)
            summaries.append(summary)
    counts = pd.concat(counts_frames, ignore_index=True) if counts_frames else pd.DataFrame()
    summary = pd.DataFrame(summaries)
    counts.to_csv(TABLES / "02_quality_clean_score_band_counts.csv", index=False)
    summary.to_csv(TABLES / "03_quality_clean_shape_summary.csv", index=False)
    return counts, summary


def run_profile(counts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    fitted_frames = []
    for dataset, sub in counts.groupby("primary_dataset"):
        fitted, summary, meta = profile.run_unit(
            sub,
            {"era": "Run2015D_quality_clean", "sample": f"{dataset}_quality_clean", "primary_dataset": str(dataset)},
        )
        fitted_frames.append(fitted)
        summaries.append(summary)
    all_fitted = pd.concat(fitted_frames, ignore_index=True) if fitted_frames else pd.DataFrame()
    all_summary = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    all_fitted.to_csv(TABLES / "04_quality_clean_profile_fitted_counts.csv", index=False)
    all_summary.to_csv(TABLES / "05_quality_clean_profile_summary.csv", index=False)

    signal = all_summary[
        (all_summary["role"].eq("frozen_signal_region"))
        & (all_summary["primary_dataset"].isin(["MET", "HTMHT"]))
    ]
    controls = all_summary[
        (all_summary["role"].eq("frozen_signal_region"))
        & (all_summary["primary_dataset"].isin(["JetHT", "SingleMuon"]))
    ]
    z = signal["q99_profile_Z"].replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
    combo = pd.DataFrame(
        [
            {
                "test": "Run2015D strict quality clean MET+HTMHT with JetHT/SingleMuon controls",
                "signal_units": len(z),
                "min_signal_Z": float(np.min(z)) if len(z) else np.nan,
                "stouffer_signal_Z": float(z.sum() / np.sqrt(len(z))) if len(z) else np.nan,
                "max_abs_dataset_control_Z": float(controls["q99_profile_Z"].abs().max()) if not controls.empty else np.nan,
                "controls_close_absZ_lt3": bool((controls["q99_profile_Z"].abs() < 3).all()) if not controls.empty else False,
                "discovery_like_pattern": bool((len(z) > 0) and (np.min(z) >= 5) and ((controls["q99_profile_Z"].abs() < 3).all() if not controls.empty else False)),
            }
        ]
    )
    combo.to_csv(TABLES / "06_quality_clean_combined_readout.csv", index=False)
    return all_summary, combo


def write_report(summary: pd.DataFrame, combo: pd.DataFrame) -> None:
    audit = pd.read_csv(TABLES / "01_quality_filter_audit.csv")
    one_two = summary[(summary["role"].eq("frozen_signal_region"))]
    report = f"""# Run2015D Strict Quality-Clean Frozen Q99 Profile

## Purpose

This test follows the JetHT diagnostic. The unclean Run2015D JetHT q99 tail was concentrated in the highest MET bin; all q99 JetHT events had both HLT_MET and HLT_HT flags, and many failed or lacked HBHE noise/Iso filter flags. We therefore rerun the frozen Q99 profile test after a strict 2015 event-quality filter:

- pass_goodVertices == 1
- pass_HBHENoiseFilter == 1
- pass_HBHENoiseIsoFilter == 1

The frozen Q99 1-to-2 jet rule is not changed.

## Quality Filter Audit

{audit.to_markdown(index=False)}

## Quality-Clean Q99 Profile Readout

{one_two.to_markdown(index=False)}

## Combined Readout

{combo.to_markdown(index=False)}

## Interpretation

If the JetHT q99 excess disappears under strict quality cleaning while MET/HTMHT remain positive, the previous JetHT problem was likely dominated by event-quality/filter artefacts. If all signal-like streams also disappear, the 2015 pilot does not support the frozen trace. If JetHT remains large, the blocker is not solved.
"""
    (REPORTS / "01_RUN2015D_QUALITY_CLEAN_FROZEN_Q99_PROFILE_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Run2015D Quality-Clean Q99

Strict quality filters were applied before rerunning the frozen Q99 profile test.

{combo.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_RUN2015D_QUALITY_CLEAN_Q99.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    counts, _ = build_quality_counts()
    summary, combo = run_profile(counts)
    write_report(summary, combo)
    print("RUN2015D QUALITY-CLEAN FROZEN Q99 PROFILE COMPLETE")
    print(combo.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
