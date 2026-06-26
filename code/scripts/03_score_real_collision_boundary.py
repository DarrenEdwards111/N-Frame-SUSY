from __future__ import annotations

import numpy as np
import pandas as pd

from real_collision_common import PROCESSED, REPORTS, TABLES, ensure_dirs


CMSSW_INPUT = PROCESSED / "real_collision_20gb_cmssw_event_features.csv"
UPROOT_INPUT = PROCESSED / "real_collision_20gb_uproot_partial_event_features.csv"


def zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    std = values.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(np.nan, index=series.index)
    return (values - values.mean()) / std


def first_existing(df: pd.DataFrame, names: list[str]) -> str | None:
    return next((name for name in names if name in df.columns), None)


def main() -> None:
    ensure_dirs()
    input_path = CMSSW_INPUT if CMSSW_INPUT.exists() and CMSSW_INPUT.stat().st_size > 0 else UPROOT_INPUT
    if not input_path.exists():
        raise FileNotFoundError("No CMSSW or uproot event-feature input exists.")

    df = pd.read_csv(input_path)
    component_notes = []

    met_col = first_existing(df, ["MET_pt", "met_pt"])
    has_met = met_col is not None and pd.to_numeric(df[met_col], errors="coerce").notna().any()
    if has_met:
        df["R_missing"] = zscore(df[met_col])
        component_notes.append({"component": "R_missing", "available": True, "inputs": met_col, "notes": "z-score of MET pt"})
    else:
        df["R_missing"] = np.nan
        component_notes.append({"component": "R_missing", "available": False, "inputs": "", "notes": "MET unavailable in current extraction"})

    multiplicity_inputs = [name for name in ["N_jets_30", "N_jets_50", "object_multiplicity"] if name in df.columns]
    if multiplicity_inputs:
        zcols = []
        for name in multiplicity_inputs:
            zname = f"z_{name}"
            df[zname] = zscore(df[name])
            zcols.append(zname)
        df["R_multiplicity"] = df[zcols].mean(axis=1, skipna=True)
        component_notes.append({"component": "R_multiplicity", "available": True, "inputs": ";".join(multiplicity_inputs), "notes": "mean z-score of available multiplicity variables"})
    else:
        df["R_multiplicity"] = np.nan
        component_notes.append({"component": "R_multiplicity", "available": False, "inputs": "", "notes": "no multiplicity inputs"})

    reconstruction_inputs = [
        name
        for name in ["HT", "N_btags_medium", "max_btag_discriminator", "N_muons", "N_electrons", "object_multiplicity", "sum_jet_pt", "jet_mass_sum_30"]
        if name in df.columns and pd.to_numeric(df[name], errors="coerce").notna().any()
    ]
    if reconstruction_inputs:
        zcols = []
        for name in reconstruction_inputs:
            zname = f"z_reco_{name}"
            df[zname] = zscore(df[name])
            zcols.append(zname)
        df["R_reconstruction"] = df[zcols].mean(axis=1, skipna=True)
        component_notes.append({"component": "R_reconstruction", "available": True, "inputs": ";".join(reconstruction_inputs), "notes": "visible/reconstruction complexity proxy from available variables"})
    else:
        df["R_reconstruction"] = np.nan
        component_notes.append({"component": "R_reconstruction", "available": False, "inputs": "", "notes": "no reconstruction inputs"})

    if has_met and {"HT", "leading_jet_pt"}.issubset(df.columns):
        met = pd.to_numeric(df[met_col], errors="coerce")
        ht = pd.to_numeric(df["HT"], errors="coerce")
        lead = pd.to_numeric(df["leading_jet_pt"], errors="coerce")
        df["R_compression_proxy"] = zscore(met / (ht + 1.0)) + zscore(met / (lead + 1.0))
        df["R_compression_proxy"] = df["R_compression_proxy"] / 2.0
        component_notes.append({"component": "R_compression_proxy", "available": True, "inputs": f"{met_col};HT;leading_jet_pt", "notes": "high MET relative to visible jet activity"})
    else:
        df["R_compression_proxy"] = np.nan
        component_notes.append({"component": "R_compression_proxy", "available": False, "inputs": "", "notes": "requires MET and visible activity variables"})

    for component, note in [
        ("R_lifetime_proxy", "no genuine lifetime variables available"),
        ("R_displacement_proxy", "no genuine displaced-track/vertex variables available"),
    ]:
        df[component] = np.nan
        component_notes.append({"component": component, "available": False, "inputs": "", "notes": note})

    components = [
        "R_missing",
        "R_multiplicity",
        "R_reconstruction",
        "R_compression_proxy",
        "R_lifetime_proxy",
        "R_displacement_proxy",
    ]
    component_z = []
    for component in components:
        zname = f"z_{component}"
        df[zname] = zscore(df[component])
        component_z.append(zname)
    df["available_component_count"] = df[components].notna().sum(axis=1)
    df["B_boundary_equal_weight"] = df[component_z].mean(axis=1, skipna=True)
    df.loc[df["available_component_count"] == 0, "B_boundary_equal_weight"] = np.nan
    df["B_boundary_equal_weight_z"] = zscore(df["B_boundary_equal_weight"])

    limitations = []
    if not has_met:
        limitations.append("MET unavailable")
    if df["R_compression_proxy"].isna().all():
        limitations.append("compression proxy unavailable")
    limitations.extend(["lifetime proxy unavailable", "displacement proxy unavailable"])
    df["scoring_limitations"] = "; ".join(limitations)

    score = df["B_boundary_equal_weight_z"]
    for q, name in [(0.50, "boundary_top_50"), (0.75, "boundary_top_25"), (0.90, "boundary_top_10"), (0.95, "boundary_top_05"), (0.99, "boundary_top_01")]:
        threshold = score.quantile(q)
        df[name] = score >= threshold

    out = PROCESSED / "real_collision_20gb_event_features_scored.csv"
    df.to_csv(out, index=False)

    availability = pd.DataFrame(component_notes)
    availability.to_csv(TABLES / "boundary_component_availability.csv", index=False)
    summary = (
        df.groupby("sample_id", as_index=False)
        .agg(
            n_events=("sample_id", "count"),
            mean_B_z=("B_boundary_equal_weight_z", "mean"),
            sd_B_z=("B_boundary_equal_weight_z", "std"),
            mean_R_multiplicity=("R_multiplicity", "mean"),
            mean_R_reconstruction=("R_reconstruction", "mean"),
            available_component_count=("available_component_count", "mean"),
        )
    )
    summary.to_csv(TABLES / "boundary_component_summary_by_sample.csv", index=False)

    report = f"""# Boundary Scoring Report

## Input

Used `{input_path}`.

## What Was Computed

The current score uses only available real-data event features. In this run, the Python/uproot fallback provides visible jet activity, so `R_multiplicity` and `R_reconstruction` are available.

`R_missing`, `R_compression_proxy`, `R_lifetime_proxy`, and `R_displacement_proxy` are unavailable because the required MET or genuine displacement/lifetime variables were not extracted. They were kept as missing values, not replaced with zero.

## Main Limitation

This is not the full N-Frame boundary model. It is a visible-jet boundary dry run on real collision data. CMSSW is still required for the proper boundary-stress model.

## Output

- Scored events: `{out}`
- Component availability: `{TABLES / 'boundary_component_availability.csv'}`
- Component summary by sample: `{TABLES / 'boundary_component_summary_by_sample.csv'}`
"""
    (REPORTS / "BOUNDARY_SCORING_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
