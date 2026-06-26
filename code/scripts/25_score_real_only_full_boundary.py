from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_source_file.csv"
OUTPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_scored.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def mean_cols(df, cols):
    cols = [c for c in cols if c in df and df[c].notna().any()]
    return df[cols].mean(axis=1, skipna=True) if cols else pd.Series(np.nan, index=df.index)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    for c in ["MET_pt", "HT", "leading_jet_pt", "subleading_jet_pt"]:
        df[f"log1p_{c}"] = np.log1p(df[c].clip(lower=0))
    df["compression_proxy_raw"] = z(df["log1p_MET_pt"]) - z(np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1))
    df["displacement_proxy_raw"] = z(df["secondary_vertex_count"])
    zcols = {
        "MET_z": df["log1p_MET_pt"], "HT_z": df["log1p_HT"], "leading_jet_z": df["log1p_leading_jet_pt"],
        "subleading_jet_z": df["log1p_subleading_jet_pt"], "N_jets_30_z": df["N_jets_30"], "N_jets_50_z": df["N_jets_50"],
        "N_leptons_z": df["N_leptons"], "N_objects_z": df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0),
        "N_btags_loose_z": df["N_btags_loose"], "N_btags_medium_z": df["N_btags_medium"], "N_btags_tight_z": df["N_btags_tight"],
        "max_btag_discriminator_z": df["max_btag_discriminator"].replace(-999, np.nan), "N_primary_vertices_z": df["N_primary_vertices"],
        "packed_candidate_count_z": df["packed_candidate_count"], "secondary_vertex_count_z": df["secondary_vertex_count"],
        "compression_proxy_z": df["compression_proxy_raw"], "displacement_proxy_z": df["displacement_proxy_raw"],
    }
    for name, series in zcols.items():
        df[name] = z(series)
    comps = {
        "R_missing": ["MET_z"],
        "R_visible_energy": ["HT_z", "leading_jet_z", "subleading_jet_z"],
        "R_multiplicity": ["N_jets_30_z", "N_jets_50_z", "N_leptons_z", "N_objects_z", "packed_candidate_count_z"],
        "R_btag_structure": ["N_btags_loose_z", "N_btags_medium_z", "N_btags_tight_z", "max_btag_discriminator_z"],
        "R_reconstruction_complexity": ["N_primary_vertices_z", "packed_candidate_count_z", "secondary_vertex_count_z", "N_objects_z", "N_leptons_z", "N_btags_medium_z"],
        "R_compression_proxy": ["compression_proxy_z"],
        "R_displacement_proxy": ["displacement_proxy_z"],
    }
    avail = []
    for comp, cols in comps.items():
        df[comp] = mean_cols(df, cols)
        used = [c for c in cols if c in df and df[c].notna().any()]
        avail.append({"component": comp, "available": bool(used), "available_inputs": ";".join(used), "missing_fraction": df[comp].isna().mean()})
    component_cols = list(comps)
    df["available_component_count"] = df[component_cols].notna().sum(axis=1)
    df["B_boundary_hand_defined"] = df[component_cols].mean(axis=1, skipna=True)
    df["B_boundary_hand_defined_z"] = z(df["B_boundary_hand_defined"])
    df["scoring_limitations"] = "real-data-only hand-defined score; compression and displacement are labelled proxies"
    for q, name in [(0.5, "50"), (0.75, "25"), (0.9, "10"), (0.95, "05"), (0.99, "01"), (0.999, "001")]:
        df[f"real_boundary_top_{name}"] = df["B_boundary_hand_defined"] >= df["B_boundary_hand_defined"].quantile(q)
    df.to_csv(OUTPUT, index=False)
    pd.DataFrame(avail).to_csv(TABLES / "real_only_full_boundary_component_availability.csv", index=False)
    summary = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(
        events=("event", "count"), mean_boundary_z=("B_boundary_hand_defined_z", "mean"),
        median_boundary_z=("B_boundary_hand_defined_z", "median"), top10_frac=("real_boundary_top_10", "mean"),
        top05_frac=("real_boundary_top_05", "mean"), top01_frac=("real_boundary_top_01", "mean"), top001_frac=("real_boundary_top_001", "mean"),
        mean_R_missing=("R_missing", "mean"), mean_R_visible_energy=("R_visible_energy", "mean"), mean_R_multiplicity=("R_multiplicity", "mean"),
        mean_R_btag_structure=("R_btag_structure", "mean"), mean_R_reconstruction_complexity=("R_reconstruction_complexity", "mean"),
        mean_R_compression_proxy=("R_compression_proxy", "mean"), mean_R_displacement_proxy=("R_displacement_proxy", "mean"),
    )
    summary.to_csv(TABLES / "real_only_full_boundary_component_summary.csv", index=False)
    report = ["# Real-Only Full Boundary Scoring Report", "", "Date: 2026-06-08", "", "No simulated samples were used.", "", "## Component Availability", "", pd.DataFrame(avail).to_markdown(index=False), "", "## Summary", "", summary.to_markdown(index=False)]
    (REPORTS / "REAL_ONLY_FULL_BOUNDARY_SCORING_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
