from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "scripts" / "215_harmonised_sm_shape_template_pyhf_fit.py"
OUT = ROOT / "outputs_sm_template_rebalance_sensitivity"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def load_prev():
    spec = importlib.util.spec_from_file_location("stage215", PREV)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {PREV}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_template_from_weighted_sm(stage215, sm: pd.DataFrame, mode_name: str) -> pd.DataFrame:
    rows = []
    for jet_bin, jet_group in sm.groupby("jet_bin", observed=False):
        if str(jet_bin) not in stage215.JET_BINS or jet_group.empty:
            continue
        weights = jet_group["analysis_weight"].to_numpy(float)
        if weights.sum() <= 0:
            continue
        met_edges = stage215.weighted_quantile(jet_group["MET_pt"].to_numpy(float), weights, np.linspace(0, 1, 11))
        if np.isnan(met_edges).any():
            continue
        met_edges[0], met_edges[-1] = -np.inf, np.inf
        jet_group = jet_group.copy()
        jet_group["missing_bin"] = pd.cut(jet_group["MET_pt"], bins=met_edges, labels=False, include_lowest=True)
        for mb, group in jet_group.groupby("missing_bin", observed=False):
            if group.empty or group["analysis_weight"].sum() <= 0:
                continue
            score_edges = stage215.weighted_quantile(
                group["sm_frozen_proxy_score"].to_numpy(float),
                group["analysis_weight"].to_numpy(float),
                [0.50, 0.80, 0.90, 0.95, 0.99, 1.00],
            )
            if np.isnan(score_edges).any():
                continue
            score_edges[0], score_edges[-1] = -np.inf, np.inf
            tmp = group.copy()
            labels = np.full(len(tmp), None, dtype=object)
            scores = tmp["sm_frozen_proxy_score"].to_numpy(float)
            for (name, _, _), lo, hi in zip(stage215.BANDS, score_edges[:-1], score_edges[1:]):
                labels[(scores >= lo) & (scores < hi)] = name
            tmp["score_band"] = labels
            tmp = tmp[tmp["score_band"].notna()]
            total = float(tmp["analysis_weight"].sum())
            side = float(tmp.loc[tmp["score_band"].isin(stage215.SIDEBANDS), "analysis_weight"].sum())
            tail = float(tmp.loc[tmp["score_band"].eq(stage215.TAIL), "analysis_weight"].sum())
            for band, band_group in tmp.groupby("score_band", observed=False):
                rows.append(
                    {
                        "sm_template_mode": mode_name,
                        "jet_bin": str(jet_bin),
                        "missing_bin": int(mb),
                        "score_band": str(band),
                        "sm_weight": float(band_group["analysis_weight"].sum()),
                        "sm_total_weight_in_cell": total,
                        "sm_side_weight_in_cell": side,
                        "sm_tail_weight_in_cell": tail,
                        "sm_tail_to_side_ratio": tail / side if side > 0 else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def family_reweight(sm: pd.DataFrame, mode_name: str, cap_share: float | None = None, equal_family: bool = False) -> pd.DataFrame:
    out = sm.copy()
    out["analysis_weight"] = out["event_weight"].to_numpy(float)
    if equal_family:
        for jet_bin, group in out.groupby("jet_bin", observed=False):
            fam_weights = group.groupby("process_family_base", observed=False)["analysis_weight"].sum()
            active = fam_weights[fam_weights > 0]
            if active.empty:
                continue
            target = float(active.mean())
            for fam, weight in active.items():
                out.loc[group.index[group["process_family_base"].eq(fam)], "analysis_weight"] *= target / float(weight)
    if cap_share is not None:
        # Iterative cap within each jet bin: no family may exceed cap_share of total.
        for jet_bin, group in out.groupby("jet_bin", observed=False):
            idx = group.index
            for _ in range(20):
                fam_weights = out.loc[idx].groupby("process_family_base", observed=False)["analysis_weight"].sum()
                total = float(fam_weights.sum())
                if total <= 0:
                    break
                changed = False
                for fam, weight in fam_weights.items():
                    share = float(weight) / total
                    if share > cap_share:
                        factor = (cap_share * (total - float(weight))) / ((1.0 - cap_share) * float(weight))
                        factor = max(min(factor, 1.0), 0.0)
                        out.loc[idx[out.loc[idx, "process_family_base"].eq(fam)], "analysis_weight"] *= factor
                        changed = True
                if not changed:
                    break
    out["template_mode_detail"] = mode_name
    return out


def readout_for_template(stage215, real_cells: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    pred = stage215.predict_from_template(real_cells, template)
    agg = stage215.aggregate_predictions(pred)
    scenarios, _target = stage215.build_readouts(agg)
    return scenarios


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    stage215 = load_prev()
    real_cells = pd.concat([stage215.load_real_g_cells(), stage215.load_real_h_cells()], ignore_index=True)
    sm = stage215.load_sm()
    sm["is_reduced"] = sm["process_family_norm"].astype(str).str.contains("_reduced", case=False, na=False)
    sm["analysis_weight"] = sm["event_weight"].to_numpy(float)

    templates = []
    summaries = []

    # Reduced-component sensitivity: alpha=0 is non-reduced-only, alpha=1 is all weighted SM.
    for alpha in [0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.0]:
        tmp = sm.copy()
        tmp["analysis_weight"] = tmp["event_weight"].to_numpy(float)
        tmp.loc[tmp["is_reduced"], "analysis_weight"] *= alpha
        mode = f"reduced_scale_{alpha:.2f}"
        template = make_template_from_weighted_sm(stage215, tmp[tmp["analysis_weight"] > 0].copy(), mode)
        templates.append(template)
        s = readout_for_template(stage215, real_cells, template)
        s["test_family"] = "reduced_component_scale_scan"
        s["test_parameter"] = alpha
        summaries.append(s)

    # Family rebalance/capping tests on all weighted SM.
    for mode, adjusted in [
        ("family_equal_weight_by_jet", family_reweight(sm, "family_equal_weight_by_jet", equal_family=True)),
        ("family_cap_80pct_by_jet", family_reweight(sm, "family_cap_80pct_by_jet", cap_share=0.80)),
        ("family_cap_70pct_by_jet", family_reweight(sm, "family_cap_70pct_by_jet", cap_share=0.70)),
        ("family_cap_60pct_by_jet", family_reweight(sm, "family_cap_60pct_by_jet", cap_share=0.60)),
    ]:
        template = make_template_from_weighted_sm(stage215, adjusted[adjusted["analysis_weight"] > 0].copy(), mode)
        templates.append(template)
        s = readout_for_template(stage215, real_cells, template)
        s["test_family"] = "family_rebalance"
        s["test_parameter"] = mode
        summaries.append(s)

    all_templates = pd.concat(templates, ignore_index=True)
    all_summaries = pd.concat(summaries, ignore_index=True)
    combined = all_summaries[all_summaries["scenario"].eq("Run2016G_plus_Run2016H")].copy()
    combined = combined.sort_values(["breakthrough_screen_pass", "MET_0jet_Z"], ascending=[False, False])

    all_templates.to_csv(TABLES / "01_rebalanced_sm_shape_templates.csv", index=False)
    all_summaries.to_csv(TABLES / "02_rebalanced_sm_scenario_summary.csv", index=False)
    combined.to_csv(TABLES / "03_combined_run2016_rebalance_summary.csv", index=False)

    pass_rows = combined[combined["breakthrough_screen_pass"].eq(True)].copy()
    min_alpha_pass = np.nan
    alpha_pass = pass_rows[pass_rows["test_family"].eq("reduced_component_scale_scan")]
    if not alpha_pass.empty:
        min_alpha_pass = float(pd.to_numeric(alpha_pass["test_parameter"], errors="coerce").min())

    report = f"""# SM Template Rebalance and Reduced-Component Sensitivity

## Purpose

The previous harmonised SM shape-template fit passed for `all_weighted_sm` and `full_component_only`, but failed for `non_reduced_only`. This script tests whether the pass is robust to reduced-component scaling and to family rebalancing.

## Combined Run2016G+Run2016H Summary

{combined.to_markdown(index=False, floatfmt=".3f")}

## Passing Rows

{pass_rows.to_markdown(index=False, floatfmt=".3f") if not pass_rows.empty else "_No passing rows._"}

## Reduced-Component Dependence

Minimum reduced-component scale that passes the breakthrough screen:

```text
{min_alpha_pass}
```

Interpretation:

- If the minimum scale is close to 0, the result is not very dependent on reduced components.
- If the minimum scale is high, the current pass relies on reduced-component shape support and needs a larger harmonised full-component SM template.

## Meaning for the Project

This does not change the frozen N-Frame score or the real-data regions. It only stress-tests the SM background template. A robust breakthrough-grade claim should survive several plausible SM template choices, especially family caps/rebalancing, while keeping controls closed and MET above 5 sigma.
"""
    (REPORTS / "01_SM_TEMPLATE_REBALANCE_AND_REDUCED_SENSITIVITY.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_SM_TEMPLATE_REBALANCE_AND_REDUCED_SENSITIVITY.md")
    print(combined.to_string(index=False))


if __name__ == "__main__":
    main()
