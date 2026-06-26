from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_trigger_filter_full" / "real_only_full_event_features_with_trigger_filter_scored.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

TRIGGER_COLS = ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"]
FILTER_COLS = [
    "pass_HBHENoiseFilter",
    "pass_HBHENoiseIsoFilter",
    "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter",
    "pass_BadPFMuonFilter",
    "pass_globalSuperTightHalo2016Filter",
]
DRIVER_COLS = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_jets_50",
    "N_leptons",
    "N_btags_medium",
    "N_btags_tight",
    "N_primary_vertices",
    "packed_candidate_count",
    "secondary_vertex_count",
    "R_missing",
    "R_visible_energy",
    "R_btag_structure",
    "R_reconstruction_complexity",
    "R_compression_proxy",
    "R_displacement_proxy",
]


def top_summary(df: pd.DataFrame, score: str, label: str, n: int) -> dict:
    top = df.sort_values(score, ascending=False).head(n).copy()
    rest = df.drop(index=top.index)
    row = {
        "score": label,
        "tail": f"top{n}",
        "events": len(top),
        "mean_score": top[score].mean(),
        "top_file_fraction": top["source_file"].value_counts(normalize=True).iloc[0],
        "top_run_fraction": top["run"].value_counts(normalize=True).iloc[0],
        "top_lumi_bin_fraction": top.assign(lumi_bin=(top["lumi"] // 25) * 25)["lumi_bin"].value_counts(normalize=True).iloc[0],
    }
    for col in TRIGGER_COLS + FILTER_COLS:
        if col in top:
            row[f"{col}_top_fraction"] = top[col].mean()
            row[f"{col}_rest_fraction"] = rest[col].mean()
            row[f"{col}_top_minus_rest"] = top[col].mean() - rest[col].mean()
    for col in DRIVER_COLS:
        if col in top:
            row[f"{col}_top_mean"] = top[col].mean()
            row[f"{col}_rest_mean"] = rest[col].mean()
    return row


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    score_specs = [
        ("B_boundary_hand_defined_z", "hand_defined"),
        ("trigger_filter_unsupervised_boundary_score", "unsupervised"),
    ]
    sizes = [100, 1000, max(1, round(len(df) * 0.001))]
    rows = []
    top_tables = []
    for score, label in score_specs:
        for n in sizes:
            rows.append(top_summary(df, score, label, n))
        top = df.sort_values(score, ascending=False).head(1000).copy()
        top.insert(0, "boundary_score_type", label)
        top_tables.append(top)
    summary = pd.DataFrame(rows)
    top1000 = pd.concat(top_tables, ignore_index=True)
    summary.to_csv(TABLES / "top_boundary_with_trigger_filter_summary.csv", index=False)
    top1000.to_csv(TABLES / "top_1000_boundary_events_with_trigger_filter.csv", index=False)

    trigger_delta_cols = [c for c in summary.columns if c.endswith("_top_minus_rest")]
    deltas = (
        summary[["score", "tail"] + trigger_delta_cols]
        .melt(id_vars=["score", "tail"], var_name="variable", value_name="top_minus_rest")
        .sort_values(["score", "tail", "top_minus_rest"], ascending=[True, True, False])
    )
    deltas.to_csv(TABLES / "top_boundary_trigger_filter_top_minus_rest.csv", index=False)

    report = [
        "# Top Boundary Events With Trigger/Filter Diagnostics",
        "",
        "Date: 2026-06-08",
        "",
        "This report inspects the high-boundary tails after adding broad HLT and event-quality diagnostics. The trigger/filter flags are diagnostic only and were not used to compute the boundary scores.",
        "",
        "## Tail Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Largest Trigger/Filter Top-minus-Rest Differences",
        "",
        deltas.groupby(["score", "tail"]).head(8).to_markdown(index=False),
    ]
    (REPORTS / "TOP_BOUNDARY_WITH_TRIGGER_FILTER_ANALYSIS.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
