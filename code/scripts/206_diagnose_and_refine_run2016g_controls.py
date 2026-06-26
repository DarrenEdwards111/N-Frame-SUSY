from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_run2016g_control_diagnostics"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCE201 = ROOT / "scripts" / "201_overnight_frozen_trace_validation.py"
FEATURE_DIR = ROOT / "outputs_overnight_frozen_trace_validation" / "sources"


def load_stage201():
    spec = importlib.util.spec_from_file_location("stage201", SOURCE201)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {SOURCE201}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finite_z(observed: float, expected: float, rel_unc: float = 0.30) -> float:
    if expected <= 0:
        return np.nan
    return float((observed - expected) / np.sqrt(expected + (rel_unc * expected) ** 2))


def add_bins(df: pd.DataFrame) -> pd.DataFrame:
    g = df.copy()
    for col in ["HT", "N_btags_medium", "N_muons", "N_electrons", "N_leptons", "N_primary_vertices"]:
        if col not in g:
            g[col] = 0
        g[col] = pd.to_numeric(g[col], errors="coerce").fillna(0)
    g["lepton_bin"] = np.select(
        [g["N_leptons"] <= 0, g["N_leptons"].eq(1), g["N_leptons"] >= 2],
        ["0lep", "1lep", "2pluslep"],
        default="unknown",
    )
    g["btag_bin"] = np.select(
        [g["N_btags_medium"] <= 0, g["N_btags_medium"].eq(1), g["N_btags_medium"] >= 2],
        ["0b", "1b", "2plusb"],
        default="unknown",
    )
    g["pv_bin"] = pd.cut(g["N_primary_vertices"], bins=[-np.inf, 12, 20, 30, np.inf], labels=["pv_low", "pv_mid", "pv_high", "pv_vhigh"])
    return g


def assign_tail(
    df: pd.DataFrame,
    threshold_cols: list[str],
    expectation_cols: list[str],
    label: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    tagged = []
    for (era, dataset), group in df.groupby(["era", "primary_dataset"], sort=False):
        g = group.copy()
        edges = np.unique(g["missing_proxy_pt"].quantile(np.linspace(0, 1, 11)).to_numpy(float))
        if len(edges) < 3:
            edges = np.array([-np.inf, np.inf])
        else:
            edges[0], edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=edges, labels=False, include_lowest=True)
        threshold_group = ["missing_bin", *threshold_cols]
        expectation_group = ["missing_bin", *expectation_cols]
        g["_threshold_key"] = g[threshold_group].astype(str).agg("|".join, axis=1)
        g["_expectation_key"] = g[expectation_group].astype(str).agg("|".join, axis=1)
        thresholds = g.groupby("_threshold_key", dropna=False)["frozen_boundary_score"].quantile(0.99)
        g["q99_tail_refined"] = g["frozen_boundary_score"] >= g["_threshold_key"].map(thresholds).astype(float)
        expected_frac = g.groupby("_expectation_key", dropna=False)["q99_tail_refined"].mean()
        g["expected_tail_fraction_refined"] = g["_expectation_key"].map(expected_frac).astype(float).fillna(0.0)
        g["diagnostic_definition"] = label
        tagged.append(g)
        for jet, sub in g.groupby("jet_bin", observed=False):
            if str(jet) not in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
                continue
            observed = int(sub["q99_tail_refined"].sum())
            expected = float(sub["expected_tail_fraction_refined"].sum())
            rows.append(
                {
                    "diagnostic_definition": label,
                    "era": era,
                    "primary_dataset": dataset,
                    "jet_bin": str(jet),
                    "events": len(sub),
                    "q99_observed": observed,
                    "q99_expected": expected,
                    "q99_obs_exp": observed / expected if expected > 0 else np.nan,
                    "q99_Z_relunc30": finite_z(observed, expected),
                }
            )
    return pd.concat(tagged, ignore_index=True), pd.DataFrame(rows)


def region_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    masks: dict[str, pd.Series] = {}
    masks["baseline_strict_quality"] = pd.Series(True, index=df.index)
    masks["trigger_exclusive_streams"] = (
        (df["primary_dataset"].eq("MET") & df["HLT_MET_paths_any"].eq(1) & df["HLT_HT_paths_any"].eq(0) & df["HLT_Mu_paths_any"].eq(0))
        | (df["primary_dataset"].eq("HTMHT") & df["HLT_HT_paths_any"].eq(1) & df["HLT_MET_paths_any"].eq(0) & df["HLT_Mu_paths_any"].eq(0))
        | (df["primary_dataset"].eq("JetHT") & df["HLT_HT_paths_any"].eq(1) & df["HLT_MET_paths_any"].eq(0) & df["HLT_Mu_paths_any"].eq(0))
        | (df["primary_dataset"].eq("SingleMuon") & df["HLT_Mu_paths_any"].eq(1) & df["HLT_MET_paths_any"].eq(0) & df["HLT_HT_paths_any"].eq(0))
    )
    masks["met_orthogonal_controls"] = (
        df["primary_dataset"].isin(["MET", "HTMHT"])
        | (df["primary_dataset"].isin(["JetHT", "SingleMuon"]) & df["HLT_MET_paths_any"].eq(0))
    )
    masks["analysis_quality_plus_badpf_halo_ecal"] = (
        df[["pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter"]]
        .fillna(0)
        .eq(1)
        .all(axis=1)
    )
    masks["singlemuon_requires_muon_jetht_zero_lepton"] = (
        df["primary_dataset"].isin(["MET", "HTMHT"])
        | (df["primary_dataset"].eq("JetHT") & df["N_leptons"].eq(0))
        | (df["primary_dataset"].eq("SingleMuon") & df["N_muons"].ge(1))
    )
    masks["combined_refined_selection"] = (
        masks["met_orthogonal_controls"]
        & masks["analysis_quality_plus_badpf_halo_ecal"]
        & masks["singlemuon_requires_muon_jetht_zero_lepton"]
    )
    return masks


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    stage201 = load_stage201()
    files = sorted(FEATURE_DIR.glob("overnight_run2016g_*_event_features.csv"))
    if not files:
        raise SystemExit(f"No Run2016G feature files in {FEATURE_DIR}")

    usecols = [
        "sample_id",
        "era",
        "primary_dataset",
        "source_file",
        "run",
        "lumi",
        "event",
        "MET_pt",
        "MHT_pt",
        "MHT_phi",
        "MHT_over_HT",
        "MET_minus_MHT",
        "HT",
        "N_jets_30",
        "N_btags_medium",
        "N_muons",
        "N_electrons",
        "N_leptons",
        "N_primary_vertices",
        "secondary_vertex_count",
        "packed_candidate_count",
        "HLT_MET_paths_any",
        "HLT_HT_paths_any",
        "HLT_Mu_paths_any",
        "HLT_Ele_paths_any",
        "pass_HBHENoiseFilter",
        "pass_HBHENoiseIsoFilter",
        "pass_goodVertices",
        "pass_EcalDeadCellTriggerPrimitiveFilter",
        "pass_BadPFMuonFilter",
        "pass_globalSuperTightHalo2016Filter",
    ]
    frames = []
    for path in files:
        header = pd.read_csv(path, nrows=0).columns
        cols = [c for c in usecols if c in header]
        frames.append(pd.read_csv(path, usecols=cols, low_memory=False))
    raw = pd.concat(frames, ignore_index=True)
    clean, quality = stage201.strict_quality(raw)
    scored = []
    for _, group in clean.groupby(["era", "primary_dataset"], sort=False):
        scored.append(stage201.add_dataset_components(group))
    df = add_bins(pd.concat(scored, ignore_index=True))
    for col in ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0).astype(int)
    df["N_leptons"] = pd.to_numeric(df.get("N_leptons", df["N_muons"] + df["N_electrons"]), errors="coerce").fillna(0)
    df.to_csv(TABLES / "00_scored_events_for_control_diagnostics.csv.gz", index=False, compression="gzip")
    quality.to_csv(TABLES / "00_quality_reproduction.csv", index=False)

    variant_rows = []
    for mask_name, mask in region_masks(df).items():
        sub = df.loc[mask].copy()
        if sub.empty:
            continue
        _, table = assign_tail(sub, [], [], f"{mask_name}: missing-decile-only")
        table.insert(0, "selection_mask", mask_name)
        variant_rows.append(table)
        _, conditioned = assign_tail(
            sub,
            threshold_cols=[],
            expectation_cols=["lepton_bin", "btag_bin", "pv_bin"],
            label=f"{mask_name}: missing+lepton+btag+pv expectation",
        )
        conditioned.insert(0, "selection_mask", mask_name)
        variant_rows.append(conditioned)
    variant_table = pd.concat(variant_rows, ignore_index=True)
    variant_table.to_csv(TABLES / "01_control_definition_variant_stage_table.csv", index=False)

    focus = df[
        ((df["primary_dataset"].eq("JetHT")) & (df["jet_bin"].astype(str).eq("1to2jets")))
        | ((df["primary_dataset"].eq("SingleMuon")) & (df["jet_bin"].astype(str).eq("0jet")))
    ].copy()
    tagged, _ = assign_tail(df, [], [], "baseline_for_composition")
    focus_tail = tagged[
        ((tagged["primary_dataset"].eq("JetHT")) & (tagged["jet_bin"].astype(str).eq("1to2jets")) & tagged["q99_tail_refined"])
        | ((tagged["primary_dataset"].eq("SingleMuon")) & (tagged["jet_bin"].astype(str).eq("0jet")) & tagged["q99_tail_refined"])
    ].copy()
    run_lumi = (
        focus_tail.groupby(["primary_dataset", "jet_bin", "run", "lumi"], as_index=False)
        .agg(tail_events=("event", "count"), median_score=("frozen_boundary_score", "median"), median_missing=("missing_proxy_pt", "median"), median_ht=("HT", "median"))
        .sort_values(["primary_dataset", "jet_bin", "tail_events"], ascending=[True, True, False])
    )
    run_lumi.to_csv(TABLES / "02_control_tail_run_lumi_concentration.csv", index=False)

    trigger_summary = (
        df.groupby(["primary_dataset", "jet_bin"], observed=False)
        .agg(
            events=("event", "count"),
            hlt_met_frac=("HLT_MET_paths_any", "mean"),
            hlt_ht_frac=("HLT_HT_paths_any", "mean"),
            hlt_mu_frac=("HLT_Mu_paths_any", "mean"),
            mean_n_leptons=("N_leptons", "mean"),
            mean_ht=("HT", "mean"),
            mean_missing=("missing_proxy_pt", "mean"),
            mean_score=("frozen_boundary_score", "mean"),
        )
        .reset_index()
    )
    trigger_summary.to_csv(TABLES / "03_trigger_topology_summary_by_stream_jetbin.csv", index=False)

    # Build compact readout for the exact signal/control question.
    readout_rows = []
    for (mask, definition), g in variant_table.groupby(["selection_mask", "diagnostic_definition"], sort=False):
        def val(dataset: str, jet: str) -> float:
            row = g[(g["primary_dataset"].eq(dataset)) & (g["jet_bin"].eq(jet))]
            return float(row["q99_Z_relunc30"].iloc[0]) if not row.empty else np.nan

        control_vals = []
        for dataset in ["JetHT", "SingleMuon"]:
            for jet in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
                x = val(dataset, jet)
                if np.isfinite(x):
                    control_vals.append(x)
        met = val("MET", "0jet")
        htmht = val("HTMHT", "1to2jets")
        finite = np.array([x for x in [met, htmht] if np.isfinite(x)])
        readout_rows.append(
            {
                "selection_mask": mask,
                "diagnostic_definition": definition,
                "MET_0jet_Z": met,
                "HTMHT_1to2jets_Z": htmht,
                "signal_stouffer_Z": float(finite.sum() / np.sqrt(len(finite))) if len(finite) else np.nan,
                "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                "max_control_absZ": float(np.max(np.abs(control_vals))) if control_vals else np.nan,
                "controls_close_under_3sigma": bool(control_vals and np.max(np.abs(control_vals)) < 3.0),
            }
        )
    readout = pd.DataFrame(readout_rows).sort_values(["controls_close_under_3sigma", "signal_stouffer_Z"], ascending=[False, False])
    readout.to_csv(TABLES / "04_refined_control_readout.csv", index=False)

    report = f"""# Run2016G Control Diagnostics and Refined Control Definitions

## Purpose

This diagnostic keeps the frozen N-Frame score fixed and investigates why the fresh Run2016G validation had non-quiet controls:

- JetHT `1to2jets`
- SingleMuon `0jet`

No N-Frame weights were refit in this script.

## Inputs

- Strict-quality fresh Run2016G MiniAOD events: {len(df):,}
- Source feature files: {len(files)}

## Main Readout

{readout.to_markdown(index=False, floatfmt=".3f")}

## Interpretation Rules

- A useful refined control definition should keep MET/HTMHT signal stages high while pushing JetHT/SingleMuon controls below about 3 sigma.
- If a definition closes controls only by deleting the signal-like phase space itself, it is not useful.
- These are diagnostic/refinement tests, not a discovery claim.

## Outputs

- `01_control_definition_variant_stage_table.csv`
- `02_control_tail_run_lumi_concentration.csv`
- `03_trigger_topology_summary_by_stream_jetbin.csv`
- `04_refined_control_readout.csv`
"""
    (REPORTS / "01_RUN2016G_CONTROL_DIAGNOSTICS_REPORT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_RUN2016G_CONTROL_DIAGNOSTICS_REPORT.md")
    print(readout.to_string(index=False))


if __name__ == "__main__":
    main()
