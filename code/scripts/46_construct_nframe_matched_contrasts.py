from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MC = ROOT / "data" / "processed" / "matched_control"
OUT = ROOT / "data" / "processed" / "nframe_parameter_fit"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

FEATURES = [
    "MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "N_btags_tight",
    "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count",
    "compression_proxy_raw", "displacement_proxy_raw", "R_missing", "R_visible_energy", "R_multiplicity",
    "R_btag_structure", "R_reconstruction_complexity", "R_compression_proxy", "R_displacement_proxy",
    "B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score",
]
MATCH_FILES = {
    "hand_top05": "matched_controls_hand_top05.csv",
    "hand_top01": "matched_controls_hand_top01.csv",
    "hand_top001": "matched_controls_hand_top001.csv",
    "unsup_top05": "matched_controls_unsup_top05.csv",
    "unsup_top01": "matched_controls_unsup_top01.csv",
    "unsup_top001": "matched_controls_unsup_top001.csv",
}
META_COLS = [
    "quality_subset", "boundary_score_type", "tail_definition", "matching_level_used",
    "same_dataset", "same_source_file", "same_run", "same_trigger_combo",
    "vertex_difference", "packed_candidate_difference", "lumi_difference",
]


def load_events() -> pd.DataFrame:
    df = pd.read_csv(MC / "standard_quality_clean_events_rescored.csv")
    if "real_only_unsupervised_boundary_score" not in df and "trigger_filter_unsupervised_boundary_score" in df:
        df["real_only_unsupervised_boundary_score"] = df["trigger_filter_unsupervised_boundary_score"]
    df["event_uid"] = df["source_file_stem"].astype(str) + ":" + df["run"].astype(str) + ":" + df["lumi"].astype(str) + ":" + df["event"].astype(str)
    df["trigger_combo"] = df[["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"]].astype(int).astype(str).agg("".join, axis=1)
    return df.set_index("event_uid", drop=False)


def contrast(match_path: Path, events: pd.DataFrame) -> pd.DataFrame:
    m = pd.read_csv(match_path)
    case_ids = m["case_event_id"].drop_duplicates()
    controls = events.loc[m["control_event_id"]].reset_index(drop=True)
    controls["case_event_id"] = m["case_event_id"].values
    control_mean = controls.groupby("case_event_id")[[c for c in FEATURES if c in controls.columns]].mean()
    control_mean.columns = [f"control_mean_{c}" for c in control_mean.columns]
    meta = m.groupby("case_event_id").agg(
        n_controls=("control_event_id", "count"),
        quality_subset=("quality_subset", "first"),
        boundary_score_type=("boundary_score_type", "first"),
        tail_definition=("tail_definition", "first"),
        dominant_matching_level=("matching_level_used", lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]),
        same_source_file_fraction=("same_source_file", "mean"),
        same_run_fraction=("same_run", "mean"),
        same_trigger_combo_fraction=("same_trigger_combo", "mean"),
        mean_vertex_difference=("vertex_difference", "mean"),
        mean_packed_candidate_difference=("packed_candidate_difference", "mean"),
        mean_lumi_difference=("lumi_difference", "mean"),
    )
    case = events.loc[case_ids].copy()
    keep_meta = ["event_uid", "sample_id", "primary_dataset", "source_file", "source_file_stem", "run", "lumi", "event", "trigger_combo"]
    out = case[keep_meta + [c for c in FEATURES if c in case.columns]].copy().reset_index(drop=True)
    out = out.rename(columns={c: f"case_{c}" for c in FEATURES if c in out.columns})
    out = out.merge(meta.reset_index(), left_on="event_uid", right_on="case_event_id", how="left").drop(columns=["case_event_id"])
    out = out.merge(control_mean.reset_index(), left_on="event_uid", right_on="case_event_id", how="left").drop(columns=["case_event_id"])
    for c in FEATURES:
        cc, mc = f"case_{c}", f"control_mean_{c}"
        if cc in out and mc in out:
            out[f"diff_{c}"] = out[cc] - out[mc]
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    events = load_events()
    rows = []
    for label, name in MATCH_FILES.items():
        df = contrast(MC / name, events)
        path = OUT / f"contrasts_{label}.csv"
        df.to_csv(path, index=False)
        rows.append(
            {
                "contrast": label,
                "rows": len(df),
                "mean_controls_per_case": df["n_controls"].mean(),
                "same_source_file_fraction": df["same_source_file_fraction"].mean(),
                "same_run_fraction": df["same_run_fraction"].mean(),
                "same_trigger_combo_fraction": df["same_trigger_combo_fraction"].mean(),
                "output": str(path),
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "nframe_contrast_summary_by_tail.csv", index=False)
    report = [
        "# N-Frame Matched Contrast Construction Report",
        "",
        "Date: 2026-06-08",
        "",
        "Each row is one high-boundary case. Values are case minus the mean of its matched real-data controls.",
        "",
        summary.to_markdown(index=False),
    ]
    (REPORTS / "NFRAME_MATCHED_CONTRAST_CONSTRUCTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
