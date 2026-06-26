from __future__ import annotations

"""Build exact/hybrid SM normalisation tiers from resumable GenFilterInfo sums.

This does not pretend partial records are complete. A record is marked
`exact_record_sumw` only when all online files in the exact-sumweight plan have
successful status rows. Otherwise the older constant-weight approximation is
kept only as an explicitly labelled stress-test tier.
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_remote_opq_sm_background_build"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

METADATA = TABLES / "01_remote_sm_record_metadata.csv"
OLD_TIERS = TABLES / "08_remote_sm_normalisation_tiers.csv"
WEIGHT_AUDIT = TABLES / "04_remote_sm_generator_weight_audit.csv"
PLAN_SUMMARY = TABLES / "15_exact_genfilter_sumweight_file_plan_summary.csv"
EXACT = TABLES / "16_exact_genfilter_sumweights_resumable.csv"

LUMI_PB = 16_380.0


def safe_float(value: object, default: float = np.nan) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if np.isfinite(out) else default


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    meta = pd.read_csv(METADATA)
    old = pd.read_csv(OLD_TIERS) if OLD_TIERS.exists() else pd.DataFrame()
    weight_audit = pd.read_csv(WEIGHT_AUDIT) if WEIGHT_AUDIT.exists() else pd.DataFrame()
    plan = pd.read_csv(PLAN_SUMMARY) if PLAN_SUMMARY.exists() else pd.DataFrame()
    exact = pd.read_csv(EXACT) if EXACT.exists() else pd.DataFrame()

    complete = pd.DataFrame()
    if not exact.empty:
        complete = (
            exact[exact["status"].eq(0)]
            .groupby(["record_id", "process_family"], as_index=False)
            .agg(
                exact_successful_files=("file_index", "nunique"),
                exact_num_events_total=("num_events_total", "sum"),
                exact_num_events_passed=("num_events_passed", "sum"),
                exact_sum_weights_total=("sum_weights_total", "sum"),
                exact_sum_weights_passed=("sum_weights_passed", "sum"),
            )
        )

    old_by_record = old.set_index("record_id").to_dict("index") if not old.empty else {}
    audit_by_record = weight_audit.set_index("record_id").to_dict("index") if not weight_audit.empty else {}
    complete_by_record = complete.set_index("record_id").to_dict("index") if not complete.empty else {}
    plan_by_record = plan.set_index("record_id").to_dict("index") if not plan.empty else {}

    rows: list[dict[str, object]] = []
    for row in meta.itertuples(index=False):
        record_id = int(row.record_id)
        plan_row = plan_by_record.get(record_id, {})
        old_row = old_by_record.get(record_id, {})
        audit_row = audit_by_record.get(record_id, {})
        exact_row = complete_by_record.get(record_id, {})

        online_file_count = int(safe_float(getattr(row, "online_file_count", np.nan), 0.0))
        planned_exact_files = int(safe_float(plan_row.get("files", np.nan), 0.0))
        exact_successful_files = int(safe_float(exact_row.get("exact_successful_files", np.nan), 0.0))
        full_online_target = bool(plan_row.get("mode") == "full_online_exact_target")
        exact_complete = bool(
            full_online_target
            and planned_exact_files > 0
            and exact_successful_files >= planned_exact_files
            and exact_successful_files >= online_file_count
        )

        xsec = safe_float(row.cross_section_pb)
        filt = safe_float(row.filter_efficiency, 1.0)
        match = safe_float(row.matching_efficiency, 1.0)
        generated = safe_float(row.generated_events)

        tier = "shape_only_not_normalised"
        denom = np.nan
        denom_source = "none"
        normalisation_is_final = False

        if exact_complete:
            denom = safe_float(exact_row.get("exact_sum_weights_total"))
            tier = "exact_record_sumw"
            denom_source = "GenFilterInfo_full_online_record_sum_weights_total"
            normalisation_is_final = bool(np.isfinite(denom) and denom > 0)
        elif (
            bool(audit_row.get("generator_weight_valid", False))
            and np.isclose(safe_float(audit_row.get("generator_weight_mean")), 1.0, atol=1e-12)
            and np.isclose(safe_float(audit_row.get("generator_weight_std")), 0.0, atol=1e-12)
            and np.isclose(safe_float(audit_row.get("generator_weight_min")), 1.0, atol=1e-12)
            and np.isclose(safe_float(audit_row.get("generator_weight_max")), 1.0, atol=1e-12)
            and np.isclose(safe_float(row.negative_weight_fraction), 0.0, atol=1e-12)
            and int(safe_float(audit_row.get("feature_rows"), 0.0)) >= 500
            and np.isfinite(generated)
            and generated > 0
        ):
            # This is not a replacement for a scanned GenFilterInfo total. It
            # is a separately labelled tier for samples whose generated-event
            # count equals the generator-weight sum under verified unit weights.
            denom = generated
            tier = "metadata_unit_weight_record"
            denom_source = "official_generated_events_plus_verified_unit_generator_weights"
        elif old_row.get("normalisation_tier") == "approx_constant_weight_sumw":
            denom = safe_float(old_row.get("approx_record_sumw"))
            tier = "approx_constant_weight_sumw_pending_exact"
            denom_source = "generated_events_times_selected_mean_generator_weight"

        base_scale = xsec * LUMI_PB * filt * match / denom if np.isfinite(denom) and denom > 0 else np.nan
        finite_mc_frac = 1 / np.sqrt(safe_float(exact_row.get("exact_num_events_passed"), generated)) if np.isfinite(generated) and generated > 0 else np.nan

        rows.append(
            {
                "record_id": record_id,
                "process_family": row.process_family,
                "cross_section_pb": xsec,
                "cross_section_uncertainty_pb": safe_float(row.cross_section_uncertainty_pb),
                "lumi_pb": LUMI_PB,
                "filter_efficiency": filt,
                "matching_efficiency": match,
                "generated_events_metadata": generated,
                "online_file_count": online_file_count,
                "planned_exact_files": planned_exact_files,
                "exact_successful_files": exact_successful_files,
                "exact_complete_full_online": exact_complete,
                "exact_num_events_total": safe_float(exact_row.get("exact_num_events_total")),
                "exact_num_events_passed": safe_float(exact_row.get("exact_num_events_passed")),
                "exact_sum_weights_total": safe_float(exact_row.get("exact_sum_weights_total")),
                "exact_sum_weights_passed": safe_float(exact_row.get("exact_sum_weights_passed")),
                "normalisation_tier": tier,
                "normalisation_denominator": denom,
                "denominator_source": denom_source,
                "base_event_scale_for_generator_weight": base_scale,
                "finite_mc_fractional_uncertainty_proxy": finite_mc_frac,
                "normalisation_is_final_for_this_record": normalisation_is_final,
                "selected_generator_weight_mean": safe_float(audit_row.get("generator_weight_mean")),
                "selected_generator_weight_std": safe_float(audit_row.get("generator_weight_std")),
                "selected_generator_weight_min": safe_float(audit_row.get("generator_weight_min")),
                "selected_generator_weight_max": safe_float(audit_row.get("generator_weight_max")),
            }
        )

    tiers = pd.DataFrame(rows)
    tiers.to_csv(TABLES / "17_exact_hybrid_sm_normalisation_tiers.csv", index=False)

    summary = (
        tiers.groupby(["normalisation_tier", "process_family"], dropna=False)
        .size()
        .reset_index(name="records")
        .sort_values(["normalisation_tier", "process_family"])
    )
    summary.to_csv(TABLES / "18_exact_hybrid_sm_normalisation_tier_summary.csv", index=False)

    exact_status = tiers[
        [
            "record_id",
            "process_family",
            "online_file_count",
            "planned_exact_files",
            "exact_successful_files",
            "exact_complete_full_online",
            "normalisation_tier",
            "normalisation_denominator",
            "base_event_scale_for_generator_weight",
        ]
    ]

    report = f"""# Exact/Hybrid SM Normalisation Tier Audit

## Purpose

This table upgrades the previous approximate SM normalisation layer by using
the resumable `GenFilterInfo` sumweight production when, and only when, a full
online record has successful exact rows.

## Exact Coverage Status

{exact_status.to_markdown(index=False, floatfmt='.6g')}

## Tier Summary

{summary.to_markdown(index=False)}

## Interpretation

`exact_record_sumw` is the tier needed for a publication-grade luminosity
normalisation component for that record. `approx_constant_weight_sumw_pending_exact`
is still a stress-test tier, not final evidence, because it relies on metadata
generated-event counts and selected generator-weight stability rather than the
full record-level generator-weight sum.

`metadata_unit_weight_record` is an intermediate, explicitly non-GenFilterInfo
tier. It is permitted only where the extracted generator weights are all
exactly +1, the selected variance is zero, the official negative-weight
fraction is zero, and the record supplies a generated-event count. This makes
the generator-weight denominator equal to the official generated-event count
under the stated unit-weight condition, but it remains distinct from a
full-file `GenFilterInfo` scan.
"""
    (REPORTS / "10_EXACT_HYBRID_SM_NORMALISATION_TIER_AUDIT.md").write_text(report, encoding="utf-8")
    print(exact_status.to_string(index=False))
    print(REPORTS / "10_EXACT_HYBRID_SM_NORMALISATION_TIER_AUDIT.md")


if __name__ == "__main__":
    main()
