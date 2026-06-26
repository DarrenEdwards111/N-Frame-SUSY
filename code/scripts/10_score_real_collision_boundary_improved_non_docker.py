from __future__ import annotations

import numpy as np
import pandas as pd

from real_collision_common import PROCESSED, REPORTS, TABLES, ensure_dirs


INPUT = PROCESSED / "real_collision_20gb_non_docker_event_features.csv"


def zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    std = values.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(np.nan, index=series.index)
    return (values - values.mean()) / std


def available(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and pd.to_numeric(df[col], errors="coerce").notna().any()


def mean_z(df: pd.DataFrame, cols: list[str], prefix: str) -> pd.Series:
    zcols = []
    for col in cols:
        if available(df, col):
            zname = f"{prefix}_{col}"
            vals = pd.to_numeric(df[col], errors="coerce")
            if col.startswith("N_") or col.startswith("max_abs") or col in {"HT", "sum_jet_pt", "object_multiplicity"}:
                vals = np.log1p(vals.clip(lower=0))
            df[zname] = zscore(vals)
            zcols.append(zname)
    if not zcols:
        return pd.Series(np.nan, index=df.index)
    return df[zcols].mean(axis=1, skipna=True)


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(INPUT)
    notes = []

    if available(df, "MET_pt"):
        df["R_missing"] = zscore(df["MET_pt"])
        notes.append({"component": "R_missing", "available": True, "inputs": "MET_pt", "notes": "z-score of genuine extracted MET"})
    else:
        df["R_missing"] = np.nan
        notes.append({"component": "R_missing", "available": False, "inputs": "", "notes": "MET pt not readable with tested non-Docker tools"})

    mult_cols = ["N_jets_30", "N_jets_50", "object_multiplicity", "N_pfc_pt_gt_1", "N_primary_vertices"]
    df["R_multiplicity"] = mean_z(df, mult_cols, "z_mult")
    notes.append({"component": "R_multiplicity", "available": df["R_multiplicity"].notna().any(), "inputs": ";".join([c for c in mult_cols if available(df, c)]), "notes": "available multiplicity variables, log-scaled before z-scoring where count-like"})

    reco_cols = [
        "HT",
        "sum_jet_pt",
        "jet_mass_sum_30",
        "N_b_hadron_flavour_proxy",
        "N_b_parton_flavour_proxy",
        "N_packed_pf_candidates",
        "N_primary_vertices",
        "primary_vertex_chi2",
        "primary_vertex_ndof",
    ]
    df["R_reconstruction"] = mean_z(df, reco_cols, "z_reco")
    notes.append({"component": "R_reconstruction", "available": df["R_reconstruction"].notna().any(), "inputs": ";".join([c for c in reco_cols if available(df, c)]), "notes": "visible/reconstruction complexity plus labelled flavour proxies"})

    if available(df, "MET_pt") and available(df, "HT") and available(df, "leading_jet_pt"):
        df["R_compression_proxy"] = (zscore(df["MET_pt"] / (df["HT"] + 1.0)) + zscore(df["MET_pt"] / (df["leading_jet_pt"] + 1.0))) / 2.0
        notes.append({"component": "R_compression_proxy", "available": True, "inputs": "MET_pt;HT;leading_jet_pt", "notes": "high MET relative to visible activity"})
    else:
        df["R_compression_proxy"] = np.nan
        notes.append({"component": "R_compression_proxy", "available": False, "inputs": "", "notes": "requires MET plus visible activity"})

    df["R_lifetime_proxy"] = np.nan
    notes.append({"component": "R_lifetime_proxy", "available": False, "inputs": "", "notes": "no validated lifetime variable extracted"})

    disp_cols = ["max_abs_pfc_dxy", "max_abs_pfc_dz", "N_pfc_abs_dxy_gt_0p05", "N_pfc_abs_dxy_gt_0p10", "N_pfc_abs_dz_gt_0p10"]
    df["R_displacement_proxy"] = mean_z(df, disp_cols, "z_disp")
    notes.append({"component": "R_displacement_proxy", "available": df["R_displacement_proxy"].notna().any(), "inputs": ";".join([c for c in disp_cols if available(df, c)]), "notes": "encoded packed-candidate dxy/dz proxy; readable but not CMS-calibrated physical displacement"})

    components = ["R_missing", "R_multiplicity", "R_reconstruction", "R_compression_proxy", "R_lifetime_proxy", "R_displacement_proxy"]
    z_components = []
    for component in components:
        zname = f"z_{component}"
        df[zname] = zscore(df[component])
        z_components.append(zname)
    df["available_component_count"] = df[components].notna().sum(axis=1)
    df["B_boundary_equal_weight"] = df[z_components].mean(axis=1, skipna=True)
    df.loc[df["available_component_count"] == 0, "B_boundary_equal_weight"] = np.nan
    df["B_boundary_equal_weight_z"] = zscore(df["B_boundary_equal_weight"])
    limitations = [
        "MET unavailable",
        "run/lumi/event unavailable",
        "lepton counts unavailable",
        "experimental b-tag discriminator unavailable",
        "displacement proxy uses encoded packed-candidate leaves",
    ]
    df["scoring_limitations"] = "; ".join(limitations)

    for q, flag in [(0.50, "boundary_top_50"), (0.75, "boundary_top_25"), (0.90, "boundary_top_10"), (0.95, "boundary_top_05"), (0.99, "boundary_top_01")]:
        threshold = df["B_boundary_equal_weight_z"].quantile(q)
        df[flag] = df["B_boundary_equal_weight_z"] >= threshold

    out = PROCESSED / "real_collision_20gb_non_docker_event_features_scored.csv"
    df.to_csv(out, index=False)
    pd.DataFrame(notes).to_csv(TABLES / "improved_boundary_component_availability.csv", index=False)
    summary = (
        df.groupby("sample_id", as_index=False)
        .agg(
            n_events=("sample_id", "count"),
            mean_B_z=("B_boundary_equal_weight_z", "mean"),
            sd_B_z=("B_boundary_equal_weight_z", "std"),
            top05_pct=("boundary_top_05", lambda x: 100 * x.mean()),
            mean_R_multiplicity=("R_multiplicity", "mean"),
            mean_R_reconstruction=("R_reconstruction", "mean"),
            mean_R_displacement_proxy=("R_displacement_proxy", "mean"),
            available_component_count=("available_component_count", "mean"),
        )
    )
    summary.to_csv(TABLES / "improved_boundary_summary_by_sample.csv", index=False)

    report = f"""# Improved Non-Docker Boundary Scoring Report

## Input

`{INPUT}`

## What Improved

The improved non-Docker extraction added packed-candidate and primary-vertex leaves to the earlier jet-only table. This allows a broader visible/reconstruction score and an encoded displacement-like proxy.

## What Still Did Not Improve

MET, event IDs, muon/electron counts, experimental b-tag discriminators, and named trigger decisions remain unavailable with the tested non-Docker tools.

## Components

{pd.DataFrame(notes).to_markdown(index=False)}

## Interpretation

This score improves beyond pure jet/HT by adding packed-candidate and vertex information. It still does not reach the full N-Frame boundary model because the missing-information component is absent.
"""
    (REPORTS / "IMPROVED_NON_DOCKER_BOUNDARY_SCORING_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
