from __future__ import annotations

"""Score the remote MC as a process-aware OPQ shape layer, not a yield model."""

from importlib.machinery import SourceFileLoader
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
LEDGER = TABLES / "03_remote_sm_extraction_ledger.csv"
MOD = SourceFileLoader("cross_sample", str(ROOT / "scripts" / "226_cross_sample_frozen_trace_validation.py")).load_module()


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ledger = pd.read_csv(LEDGER)
    frames = []
    for item in ledger.itertuples(index=False):
        frame = pd.read_csv(item.output_path, low_memory=False)
        frame["record_id"] = int(item.record_id)
        frame["process_family"] = item.process_family
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[MOD.strict_quality(raw)].copy()
    scored = []
    # Components are built within each simulated record to preserve its own
    # detector-level distribution. These are shape diagnostics only.
    for record_id, group in raw.groupby("record_id", sort=False):
        group = group.copy()
        group["primary_dataset"] = str(group["process_family"].iloc[0])
        group["sample_validation_id"] = f"UL16_MC_{record_id}"
        group["run_era"] = "UL16_MC"
        scored.append(MOD.add_components_one_dataset(group))
    scored_df = pd.concat(scored, ignore_index=True)
    score = (
        0.344828 * scored_df["observer_projection"].to_numpy(float)
        + 0.517241 * scored_df["physical_projection"].to_numpy(float)
        - 0.137931 * scored_df["ordinary_qcd_axis"].to_numpy(float)
    )
    scored_df["B_OPQ"] = score
    rows = []
    for (record_id, family), group in scored_df.groupby(["record_id", "process_family"], sort=False):
        threshold = float(group["B_OPQ"].quantile(0.99))
        tail = group[group["B_OPQ"] >= threshold]
        weights = pd.to_numeric(group["generator_weight"], errors="coerce").fillna(0.0)
        rows.append(
            {
                "record_id": record_id,
                "process_family": family,
                "quality_events": len(group),
                "B_OPQ_q99_threshold_within_record": threshold,
                "B_OPQ_q99_events": len(tail),
                "B_OPQ_q99_fraction": len(tail) / len(group),
                "generator_weight_sum_selected": float(weights.sum()),
                "mean_MET_pt": float(group["MET_pt"].mean()),
                "mean_HT": float(group["HT"].mean()),
                "mean_Njets30": float(group["N_jets_30"].mean()),
                "shape_only": True,
                "absolute_yield_interpretation": "not permitted without record-level sum of generator weights",
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "06_remote_sm_opq_shape_summary.csv", index=False)
    scored_df.to_csv(TABLES / "07_remote_sm_opq_shape_scored_events.csv", index=False)
    report = f"""# Remote OPQ Process-Aware SM Shape Layer

## Scope

The frozen score is evaluated as a within-process shape diagnostic:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

Every row comes from remote CMS UL16 MiniAODSIM extraction with valid generator
weight information. The q99 threshold is calculated separately for each record,
so the table measures tail occupancy and event composition, not a cross-section
weighted prediction for CMS data.

## Summary

{summary.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

This creates the process-aware SM shape layer required for the next sideband
fit. It is intentionally not converted into predicted yields until record-level
sum-of-generator-weight provenance is supplied. That avoids the earlier error
of treating a limited file subset as a complete luminosity-normalised sample.
"""
    (REPORTS / "03_REMOTE_OPQ_SM_SHAPE_LAYER.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(REPORTS / "03_REMOTE_OPQ_SM_SHAPE_LAYER.md")


if __name__ == "__main__":
    main()
