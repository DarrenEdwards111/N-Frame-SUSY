from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_combined.csv"
OUTPUT = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_scored.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    std = s.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(np.nan, index=series.index)
    return (s - s.mean()) / std


def component_mean(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    available = [c for c in cols if c in df.columns and df[c].notna().any()]
    if not available:
        return pd.Series(np.nan, index=df.index)
    return df[available].mean(axis=1, skipna=True)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)

    df["log1p_MET_pt"] = np.log1p(df["MET_pt"].clip(lower=0))
    df["log1p_HT"] = np.log1p(df["HT"].clip(lower=0))
    df["log1p_leading_jet_pt"] = np.log1p(df["leading_jet_pt"].clip(lower=0))
    df["log1p_subleading_jet_pt"] = np.log1p(df["subleading_jet_pt"].clip(lower=0))
    visible_raw = df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1
    df["compression_proxy_raw"] = zscore(df["log1p_MET_pt"]) - zscore(np.log1p(visible_raw))
    df["displacement_proxy_raw"] = zscore(df["secondary_vertex_count"]) if "secondary_vertex_count" in df else np.nan

    transformed = {
        "MET_z": zscore(df["log1p_MET_pt"]),
        "HT_z": zscore(df["log1p_HT"]),
        "leading_jet_z": zscore(df["log1p_leading_jet_pt"]),
        "subleading_jet_z": zscore(df["log1p_subleading_jet_pt"]),
        "N_jets_30_z": zscore(df["N_jets_30"]),
        "N_jets_50_z": zscore(df["N_jets_50"]),
        "N_leptons_z": zscore(df["N_leptons"]),
        "N_objects_z": zscore(df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0)),
        "N_btags_loose_z": zscore(df["N_btags_loose"]),
        "N_btags_medium_z": zscore(df["N_btags_medium"]),
        "N_btags_tight_z": zscore(df["N_btags_tight"]),
        "max_btag_discriminator_z": zscore(df["max_btag_discriminator"].replace(-999, np.nan)),
        "N_primary_vertices_z": zscore(df["N_primary_vertices"]),
        "packed_candidate_count_z": zscore(df["packed_candidate_count"]),
        "secondary_vertex_count_z": zscore(df["secondary_vertex_count"]),
        "compression_proxy_z": zscore(df["compression_proxy_raw"]),
        "displacement_proxy_z": zscore(df["displacement_proxy_raw"]),
    }
    for col, value in transformed.items():
        df[col] = value

    components = {
        "R_missing": ["MET_z"],
        "R_visible_energy": ["HT_z", "leading_jet_z", "subleading_jet_z"],
        "R_multiplicity": ["N_jets_30_z", "N_jets_50_z", "N_leptons_z", "N_objects_z"],
        "R_btag_structure": ["N_btags_loose_z", "N_btags_medium_z", "N_btags_tight_z", "max_btag_discriminator_z"],
        "R_reconstruction_complexity": ["N_primary_vertices_z", "packed_candidate_count_z", "secondary_vertex_count_z", "N_objects_z", "N_btags_medium_z"],
        "R_compression_proxy": ["compression_proxy_z"],
        "R_displacement_proxy": ["displacement_proxy_z"],
    }
    availability = []
    for comp, cols in components.items():
        df[comp] = component_mean(df, cols)
        available_cols = [c for c in cols if c in df and df[c].notna().any()]
        availability.append({
            "component": comp,
            "available": bool(available_cols),
            "available_inputs": ";".join(available_cols),
            "missing_fraction": float(df[comp].isna().mean()),
        })

    component_cols = list(components)
    df["available_component_count"] = df[component_cols].notna().sum(axis=1)
    df["B_boundary_hand_defined"] = df[component_cols].mean(axis=1, skipna=True)
    df["B_boundary_hand_defined_z"] = zscore(df["B_boundary_hand_defined"])
    df["scoring_limitations"] = "Transparent real-data-only score; components averaged only where genuine inputs are available; compression/displacement are proxies."

    for q, name in [(0.50, "50"), (0.75, "25"), (0.90, "10"), (0.95, "05"), (0.99, "01"), (0.999, "001")]:
        threshold = df["B_boundary_hand_defined"].quantile(q)
        df[f"real_boundary_top_{name}"] = df["B_boundary_hand_defined"] >= threshold

    df.to_csv(OUTPUT, index=False)
    pd.DataFrame(availability).to_csv(TABLES / "real_only_boundary_component_availability.csv", index=False)
    summary = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(
        events=("event", "count"),
        mean_boundary_z=("B_boundary_hand_defined_z", "mean"),
        median_boundary_z=("B_boundary_hand_defined_z", "median"),
        top10_frac=("real_boundary_top_10", "mean"),
        top05_frac=("real_boundary_top_05", "mean"),
        top01_frac=("real_boundary_top_01", "mean"),
        mean_R_missing=("R_missing", "mean"),
        mean_R_visible_energy=("R_visible_energy", "mean"),
        mean_R_multiplicity=("R_multiplicity", "mean"),
        mean_R_btag_structure=("R_btag_structure", "mean"),
        mean_R_reconstruction_complexity=("R_reconstruction_complexity", "mean"),
        mean_R_compression_proxy=("R_compression_proxy", "mean"),
    )
    summary.to_csv(TABLES / "real_only_boundary_component_summary_by_sample.csv", index=False)

    report = [
        "# Real-Only Hand-Defined Boundary Scoring Report",
        "",
        "Date: 2026-06-08",
        "",
        "The hand-defined boundary score uses only real CMS collision data. It does not use simulated samples, signal labels or supervised classification.",
        "",
        "## Component Availability",
        "",
        pd.DataFrame(availability).to_markdown(index=False),
        "",
        "## Sample Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "The score is a transparent stress estimate across missing information, visible energy, multiplicity, b-tag/reconstruction structure, compression-like imbalance and secondary-vertex displacement proxy. It is not a discovery statistic.",
    ]
    (REPORTS / "REAL_ONLY_HAND_DEFINED_BOUNDARY_SCORING_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
