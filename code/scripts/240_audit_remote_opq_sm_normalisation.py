from __future__ import annotations

"""Audit whether the remote OPQ MC sample is eligible for yield inference."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
METADATA = TABLES / "01_remote_sm_record_metadata.csv"
LEDGER = TABLES / "03_remote_sm_extraction_ledger.csv"


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    metadata = pd.read_csv(METADATA)
    ledger = pd.read_csv(LEDGER)
    rows = []
    for item in ledger.itertuples(index=False):
        path = Path(str(item.output_path))
        frame = pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()
        weights = pd.to_numeric(frame.get("generator_weight", pd.Series(dtype=float)), errors="coerce")
        statuses = pd.to_numeric(frame.get("generator_weight_status", pd.Series(dtype=float)), errors="coerce")
        meta = metadata[metadata["record_id"].eq(int(item.record_id))].iloc[0]
        valid = bool(len(frame) and statuses.notna().all() and (statuses == 1).all() and weights.notna().all())
        n_eff = float(weights.sum() ** 2 / np.square(weights).sum()) if len(weights) and np.square(weights).sum() > 0 else np.nan
        # An all-event sum of generator weights is not present in the portal
        # metadata. The selected distributed sample can estimate shape but it
        # cannot be promoted to an official absolute yield without that value.
        sumw_available = False
        rows.append(
            {
                "record_id": int(item.record_id),
                "process_family": item.process_family,
                "feature_rows": int(len(frame)),
                "generator_weight_valid": valid,
                "generator_weight_mean": float(weights.mean()) if len(weights) else np.nan,
                "generator_weight_std": float(weights.std(ddof=0)) if len(weights) else np.nan,
                "generator_weight_min": float(weights.min()) if len(weights) else np.nan,
                "generator_weight_max": float(weights.max()) if len(weights) else np.nan,
                "generator_weight_sum_selected": float(weights.sum()) if len(weights) else np.nan,
                "effective_selected_events": n_eff,
                "cross_section_pb": meta.cross_section_pb,
                "generated_events_record": meta.generated_events,
                "negative_weight_fraction_metadata": meta.negative_weight_fraction,
                "record_sum_generator_weights_available": sumw_available,
                "eligible_for_remote_shape_model": bool(valid and len(frame) >= 500),
                "eligible_for_absolute_luminosity_yield": False,
                "yield_status": "not_final_missing_record_sum_generator_weights",
            }
        )
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "04_remote_sm_generator_weight_audit.csv", index=False)
    summary = (
        audit.groupby("process_family", as_index=False)
        .agg(records=("record_id", "count"), feature_rows=("feature_rows", "sum"), effective_selected_events=("effective_selected_events", "sum"), shape_eligible_records=("eligible_for_remote_shape_model", "sum"))
    )
    summary.to_csv(TABLES / "05_remote_sm_coverage_summary.csv", index=False)
    report = f"""# Remote OPQ Standard-Model Generator-Weight Audit

## Result

The remote batch contains {int(audit['feature_rows'].sum()):,} compact
MiniAODSIM feature rows. Generator weights are present and valid for the
extracted events. This makes the data suitable for a process-aware **shape**
model with finite-MC uncertainty.

{audit.to_markdown(index=False, floatfmt='.6g')}

## Coverage

{summary.to_markdown(index=False, floatfmt='.6g')}

## Absolute-Yield Status

No row is yet eligible for a final luminosity-normalised yield. The CERN record
metadata provides cross sections and generated-event counts, but not the
record-level sum of generator weights required for a correct normalisation when
generator weights are non-unit. Replacing it with the sum from a small selected
file subset would reintroduce the partial-sample normalisation error this stage
was designed to remove.

## Next Action

Use the remote MC now for an explicitly shape-only, process-aware OPQ sideband
fit with finite-MC uncertainties. In parallel, obtain or compute record-level
sum-of-weights provenance before making any absolute-yield or discovery claim.
"""
    (REPORTS / "02_REMOTE_OPQ_SM_GENERATOR_WEIGHT_AUDIT.md").write_text(report, encoding="utf-8")
    print(audit.to_string(index=False))
    print(REPORTS / "02_REMOTE_OPQ_SM_GENERATOR_WEIGHT_AUDIT.md")


if __name__ == "__main__":
    main()
