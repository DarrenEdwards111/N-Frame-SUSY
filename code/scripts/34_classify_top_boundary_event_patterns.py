from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
TOPDIR = ROOT / "results" / "tables" / "top_boundary_events"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def main() -> None:
    full = pd.read_csv(FULL, usecols=[
        "MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_btags_tight",
        "secondary_vertex_count", "packed_candidate_count", "compression_proxy_raw",
        "source_file", "run", "lumi",
    ])
    thresholds = {
        "high_MET": full["MET_pt"].quantile(.95),
        "high_HT": full["HT"].quantile(.95),
        "high_jets": full["N_jets_30"].quantile(.95),
        "high_btags": full["N_btags_medium"].quantile(.95),
        "high_secondary_vertices": full["secondary_vertex_count"].quantile(.95),
        "high_candidates": full["packed_candidate_count"].quantile(.95),
        "high_compression": full["compression_proxy_raw"].quantile(.95),
    }
    conc = pd.read_csv(TABLES / "top_boundary_concentration_summary.csv")
    concerning_sets = set(conc[conc["judgement"].str.contains("strongly|partly", case=False, regex=True)]["top_set"])
    sets = {
        "hand_top1000": TOPDIR / "top1000_hand_boundary_events.csv",
        "unsup_top1000": TOPDIR / "top1000_unsupervised_boundary_events.csv",
    }
    frames = []
    for set_name, path in sets.items():
        df = pd.read_csv(path)
        df["top_set"] = set_name
        df["flag_missing_energy_dominant"] = (df["MET_pt"] >= thresholds["high_MET"]) & (df["compression_proxy_raw"] >= thresholds["high_compression"])
        df["flag_visible_energy_jetht_dominant"] = (df["HT"] >= thresholds["high_HT"]) | (df["N_jets_30"] >= thresholds["high_jets"])
        df["flag_heavy_flavour_reconstruction"] = (df["N_btags_medium"] >= thresholds["high_btags"]) | (df["N_btags_tight"] > 0)
        df["flag_displacement_secondary_vertex_proxy"] = df["secondary_vertex_count"] >= thresholds["high_secondary_vertices"]
        df["flag_reconstruction_complexity"] = df["packed_candidate_count"] >= thresholds["high_candidates"]
        df["flag_mixed_high_boundary"] = df[[
            "flag_missing_energy_dominant", "flag_visible_energy_jetht_dominant",
            "flag_heavy_flavour_reconstruction", "flag_displacement_secondary_vertex_proxy",
            "flag_reconstruction_complexity",
        ]].sum(axis=1) >= 3
        df["flag_possible_data_quality_trigger_followup"] = set_name in concerning_sets
        frames.append(df)
    flagged = pd.concat(frames, ignore_index=True)
    flag_cols = [c for c in flagged.columns if c.startswith("flag_")]
    summary = flagged.groupby("top_set")[flag_cols].mean().reset_index()
    flagged.to_csv(TABLES / "top_boundary_event_pattern_flags.csv", index=False)
    summary.to_csv(TABLES / "top_boundary_pattern_summary.csv", index=False)
    report = [
        "# Top Boundary Pattern Classification Report",
        "",
        "Date: 2026-06-08",
        "",
        "This is an exploratory descriptive categorisation, not a particle classifier.",
        "",
        "Thresholds use full real-data 95th percentiles for relevant variables.",
        "",
        "## Thresholds",
        "",
        pd.DataFrame([thresholds]).to_markdown(index=False),
        "",
        "## Pattern Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "Events may have multiple flags. The displacement category is a secondary-vertex proxy, not proof of displaced particles.",
    ]
    (REPORTS / "TOP_BOUNDARY_PATTERN_CLASSIFICATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
