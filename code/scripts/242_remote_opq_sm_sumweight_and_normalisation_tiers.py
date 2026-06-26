from __future__ import annotations

"""Search CERN metadata for sum-weights and build strict normalisation tiers."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
METADATA = TABLES / "01_remote_sm_record_metadata.csv"
AUDIT = TABLES / "04_remote_sm_generator_weight_audit.csv"
API = "https://opendata.cern.ch/api/records/"
LUMI_PB = 16_380.0


def walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            rows.append((child, value))
            rows.extend(walk(value, child))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            child = f"{path}[{i}]"
            rows.extend(walk(value, child))
    return rows


def find_sumweight_fields(payload: dict) -> list[dict[str, str]]:
    hits = []
    for path, value in walk(payload):
        lower = path.lower()
        if any(token in lower for token in ["sumw", "sum_w", "sumweight", "sum_weight", "sumofweight", "sum_of_weight"]):
            hits.append({"json_path": path, "value_preview": str(value)[:300]})
    return hits


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    metadata = pd.read_csv(METADATA)
    audit = pd.read_csv(AUDIT)
    rows = []
    sumw_hits = []
    for item in audit.itertuples(index=False):
        record_id = int(item.record_id)
        payload = requests.get(f"{API}{record_id}", timeout=60).json()
        hits = find_sumweight_fields(payload)
        for hit in hits:
            sumw_hits.append({"record_id": record_id, **hit})
        meta = metadata[metadata["record_id"].eq(record_id)].iloc[0]
        generated = float(meta.generated_events)
        xsec = float(meta.cross_section_pb)
        filt = float(meta.filter_efficiency) if pd.notna(meta.filter_efficiency) else 1.0
        matching = float(meta.matching_efficiency) if pd.notna(meta.matching_efficiency) else 1.0
        mean_w = float(item.generator_weight_mean)
        std_w = float(item.generator_weight_std)
        cv = abs(std_w / mean_w) if mean_w else np.inf
        exact_sumw = np.nan
        has_exact = False
        approx_allowed = bool(
            item.generator_weight_valid
            and pd.notna(generated)
            and generated > 0
            and pd.notna(xsec)
            and xsec > 0
            and cv <= 0.01
            and float(item.negative_weight_fraction_metadata) == 0.0
            and int(item.feature_rows) >= 500
        )
        approx_sumw = generated * mean_w if approx_allowed else np.nan
        if has_exact:
            norm_denom = exact_sumw
            tier = "exact_record_sumw"
        elif approx_allowed:
            norm_denom = approx_sumw
            tier = "approx_constant_weight_sumw"
        else:
            norm_denom = np.nan
            tier = "shape_only_not_normalised"
        base_scale = xsec * LUMI_PB * filt * matching / norm_denom if np.isfinite(norm_denom) and norm_denom > 0 else np.nan
        rows.append(
            {
                "record_id": record_id,
                "process_family": item.process_family,
                "feature_rows": int(item.feature_rows),
                "cross_section_pb": xsec,
                "lumi_pb": LUMI_PB,
                "filter_efficiency": filt,
                "matching_efficiency": matching,
                "generated_events": generated,
                "generator_weight_mean_selected": mean_w,
                "generator_weight_cv_selected": cv,
                "negative_weight_fraction_metadata": item.negative_weight_fraction_metadata,
                "sumweight_fields_found_in_record_json": len(hits),
                "exact_record_sumw_available": has_exact,
                "approx_record_sumw": approx_sumw,
                "normalisation_tier": tier,
                "base_event_scale_for_generator_weight": base_scale,
                "eligible_for_approx_lumi_shape_yields": tier == "approx_constant_weight_sumw",
            }
        )

    tiers = pd.DataFrame(rows)
    hits = pd.DataFrame(sumw_hits)
    tiers.to_csv(TABLES / "08_remote_sm_normalisation_tiers.csv", index=False)
    hits.to_csv(TABLES / "09_cern_record_sumweight_field_search.csv", index=False)

    report = f"""# Remote OPQ SM Sum-Weight and Normalisation Tier Audit

## Result

No exact record-level sum-of-generator-weights field was found in the CERN record
JSON for the extracted records. The table therefore separates records into:

- `approx_constant_weight_sumw`: generator weights are stable enough that
  `generated_events * selected_mean_generator_weight` is a defensible temporary
  approximation for a **stress test**.
- `shape_only_not_normalised`: too sparse or too variable for approximate yield
  use.

{tiers.to_markdown(index=False, floatfmt='.6g')}

## Sum-Weight Field Search Hits

{hits.to_markdown(index=False) if not hits.empty else '_No sum-weight-like JSON fields found._'}

## Interpretation

This does not produce official CMS-grade absolute backgrounds. It does,
however, permit a stricter approximate stress test than before for the records
with stable generator weights. Any likelihood built from this table must be
called approximate and must keep a nuisance for normalisation and process
coverage.
"""
    (REPORTS / "04_REMOTE_OPQ_SM_NORMALISATION_TIER_AUDIT.md").write_text(report, encoding="utf-8")
    print(tiers[["record_id", "process_family", "normalisation_tier", "generator_weight_cv_selected", "base_event_scale_for_generator_weight"]].to_string(index=False))
    print(REPORTS / "04_REMOTE_OPQ_SM_NORMALISATION_TIER_AUDIT.md")


if __name__ == "__main__":
    main()
