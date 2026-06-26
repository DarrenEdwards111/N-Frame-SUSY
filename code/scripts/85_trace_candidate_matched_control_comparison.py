from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
CAND = TABLES / "classified_top_trace_candidates_combined.csv"
FULL = TRACE / "combined_real_with_trace_distances.csv"
COMPARE = [
    "B_NF_trace_base", "Trace_sms_vs_pooledSM", "MET_pt", "HT", "N_jets_30",
    "N_btags_medium", "N_leptons", "secondary_vertex_count", "packed_candidate_count",
    "P_missing", "P_visible_energy", "P_multiplicity", "P_displacement_proxy",
    "P_reconstruction", "distance_to_SMS", "distance_to_pooledSM"
]


def event_key(df: pd.DataFrame) -> pd.Series:
    return df["real_dataset"].astype(str) + "|" + df["run"].astype(str) + "|" + df["lumi"].astype(str) + "|" + df["event"].astype(str)


def main() -> None:
    cand = pd.read_csv(CAND)
    full = pd.read_csv(FULL, low_memory=False)
    full["event_key"] = event_key(full)
    cand["event_key"] = event_key(cand)
    top5 = full["B_NF_trace_base"].quantile(.95)
    ordinary = full[~full["event_key"].isin(set(cand["event_key"])) & (full["B_NF_trace_base"] < top5)].copy()
    controls, diffs = [], []
    for i, c in cand.head(100).reset_index(drop=True).iterrows():
        pool = ordinary[ordinary["primary_dataset"].eq(c.get("primary_dataset"))]
        if c.get("source_file") in set(pool.get("source_file", [])):
            same = pool[pool["source_file"].eq(c.get("source_file"))]
            if len(same) >= 5:
                pool = same
        if len(pool) == 0:
            pool = ordinary
        pool = pool.copy()
        scale_pv = pool["N_primary_vertices"].std() or 1
        scale_pack = pool["packed_candidate_count"].std() or 1
        pool["match_distance"] = (
            (pool["N_primary_vertices"] - c.get("N_primary_vertices", pool["N_primary_vertices"].median())).abs() / scale_pv
            + (pool["packed_candidate_count"] - c.get("packed_candidate_count", pool["packed_candidate_count"].median())).abs() / scale_pack
            + (pool["N_jets_30"] - c.get("N_jets_30", pool["N_jets_30"].median())).abs()
        )
        selected = pool.sort_values("match_distance").head(5).copy()
        selected["candidate_rank"] = i + 1
        selected["candidate_event_key"] = c["event_key"]
        controls.append(selected)
        row = {"candidate_rank": i + 1, "candidate_event_key": c["event_key"], "control_count": len(selected), "candidate_category": c["primary_category"]}
        for col in COMPARE:
            if col in c and col in selected:
                row[f"candidate_{col}"] = c[col]
                row[f"control_mean_{col}"] = selected[col].mean()
                row[f"candidate_minus_control_{col}"] = c[col] - selected[col].mean()
        diffs.append(row)
    ctrl = pd.concat(controls, ignore_index=True) if controls else pd.DataFrame()
    diff = pd.DataFrame(diffs)
    ctrl.to_csv(TABLES / "trace_candidate_matched_controls.csv", index=False)
    diff.to_csv(TABLES / "trace_candidate_vs_matched_control_differences.csv", index=False)
    summary_cols = [c for c in diff.columns if c.startswith("candidate_minus_control_")]
    summary = pd.DataFrame({"metric": summary_cols, "median_candidate_minus_control": [diff[c].median() for c in summary_cols], "mean_candidate_minus_control": [diff[c].mean() for c in summary_cols]})
    report = ["# Trace Candidate Matched Control Comparison", "", f"Date: {DATE}", "", "Controls are ordinary real events from similar dataset/source context where possible, excluding the top 5% B_NF tail.", "", "## Difference Summary", "", summary.to_markdown(index=False)]
    (REPORTS / "TRACE_CANDIDATE_MATCHED_CONTROL_COMPARISON.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
