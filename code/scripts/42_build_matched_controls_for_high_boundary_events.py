from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "data" / "processed" / "matched_control"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
TRIG = ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"]


def prep(df):
    df = df.copy().reset_index(drop=True)
    df["event_uid"] = df["source_file_stem"].astype(str) + ":" + df["run"].astype(str) + ":" + df["lumi"].astype(str) + ":" + df["event"].astype(str)
    df["trigger_combo"] = df[TRIG].astype(int).astype(str).agg("".join, axis=1)
    df["vertex_bin"] = (df["N_primary_vertices"] // 2).astype(int)
    df["packed_bin"] = pd.qcut(df["packed_candidate_count"].rank(method="first"), 20, labels=False, duplicates="drop").astype(int)
    df["lumi_bin"] = (df["lumi"] // 25).astype(int)
    return df


def build_index(pool, keys):
    return {k: v.index.to_numpy() for k, v in pool.groupby(keys, sort=False)}


def choose(case, candidates, df, used):
    candidates = [i for i in candidates if df.at[i, "event_uid"] != case.event_uid and df.at[i, "event_uid"] not in used]
    if not candidates:
        return []
    cand = df.loc[candidates].copy()
    dist = (
        (cand["N_primary_vertices"] - case.N_primary_vertices).abs() / 2
        + (cand["packed_candidate_count"] - case.packed_candidate_count).abs() / max(1, df["packed_candidate_count"].std())
        + (cand["lumi"] - case.lumi).abs() / 25
    )
    cand = cand.assign(_dist=dist).sort_values("_dist").head(5)
    return list(zip(cand.index, cand["_dist"]))


def match(df, score, tail, q, subset):
    cases = df[df[score] >= df[score].quantile(q)].copy()
    controls = df[df[score] < df[score].quantile(q)].copy()
    levels = [
        ("same_file_run_trigger_vertex_packed_lumi", ["primary_dataset", "source_file", "run", "trigger_combo", "vertex_bin", "packed_bin", "lumi_bin"]),
        ("same_file_trigger_vertex_packed", ["primary_dataset", "source_file", "trigger_combo", "vertex_bin", "packed_bin"]),
        ("same_file_trigger_vertex", ["primary_dataset", "source_file", "trigger_combo", "vertex_bin"]),
        ("same_file_vertex", ["primary_dataset", "source_file", "vertex_bin"]),
        ("same_dataset_run_trigger", ["primary_dataset", "run", "trigger_combo"]),
        ("same_dataset_trigger_vertex", ["primary_dataset", "trigger_combo", "vertex_bin"]),
        ("same_dataset_only", ["primary_dataset"]),
    ]
    indexes = [(name, keys, build_index(controls, keys)) for name, keys in levels]
    rows = []
    for case in cases.itertuples(index=False):
        used = set()
        selected = []
        selected_level = None
        for name, keys, idx in indexes:
            key = tuple(getattr(case, k) for k in keys)
            cand_idx = idx.get(key, [])
            chosen = choose(case, cand_idx, controls, used)
            if chosen:
                selected.extend([(i, d, name) for i, d in chosen])
                used.update(controls.at[i, "event_uid"] for i, _ in chosen)
                selected_level = name
            if len(selected) >= 5:
                break
        for rank, (i, dist, level) in enumerate(selected[:5], start=1):
            ctrl = controls.loc[i]
            rows.append({
                "quality_subset": subset, "boundary_score_type": score, "tail_definition": tail,
                "case_event_id": case.event_uid, "control_event_id": ctrl.event_uid, "control_rank": rank,
                "matching_level_used": level or selected_level, "distance_metric": dist,
                "same_dataset": case.primary_dataset == ctrl.primary_dataset,
                "same_source_file": case.source_file == ctrl.source_file,
                "same_run": case.run == ctrl.run,
                "same_trigger_combo": case.trigger_combo == ctrl.trigger_combo,
                "vertex_difference": abs(case.N_primary_vertices - ctrl.N_primary_vertices),
                "packed_candidate_difference": abs(case.packed_candidate_count - ctrl.packed_candidate_count),
                "lumi_difference": abs(case.lumi - ctrl.lumi),
            })
    return pd.DataFrame(rows)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    outputs = []
    for subset, path in {"standard_quality_clean": IN / "standard_quality_clean_events_rescored.csv", "relaxed_quality_clean": IN / "relaxed_quality_clean_events_rescored.csv"}.items():
        df = prep(pd.read_csv(path))
        if subset == "standard_quality_clean":
            specs = [
                ("mc_B_boundary_hand_defined_z", "hand", .95, "top05"),
                ("mc_B_boundary_hand_defined_z", "hand", .99, "top01"),
                ("mc_B_boundary_hand_defined_z", "hand", .999, "top001"),
                ("mc_unsupervised_boundary_score", "unsup", .95, "top05"),
                ("mc_unsupervised_boundary_score", "unsup", .99, "top01"),
                ("mc_unsupervised_boundary_score", "unsup", .999, "top001"),
            ]
        else:
            specs = [("mc_B_boundary_hand_defined_z", "hand", .99, "top01"), ("mc_unsupervised_boundary_score", "unsup", .99, "top01")]
        for score, label, q, tail in specs:
            m = match(df, score, tail, q, subset)
            if subset == "standard_quality_clean":
                out = IN / f"matched_controls_{label}_{tail}.csv"
            else:
                out = IN / f"matched_controls_{subset}_{label}_{tail}.csv"
            m.to_csv(out, index=False)
            outputs.append(m.assign(file=out.name))
    allm = pd.concat(outputs, ignore_index=True)
    summary = allm.groupby(["quality_subset", "boundary_score_type", "tail_definition"], as_index=False).agg(
        matched_pairs=("case_event_id", "count"), matched_cases=("case_event_id", "nunique"),
        avg_controls_per_case=("control_event_id", lambda s: len(s) / allm.loc[s.index, "case_event_id"].nunique()),
        same_file_fraction=("same_source_file", "mean"), same_run_fraction=("same_run", "mean"),
        same_trigger_fraction=("same_trigger_combo", "mean"), mean_vertex_difference=("vertex_difference", "mean"),
        mean_packed_candidate_difference=("packed_candidate_difference", "mean"),
    )
    summary.to_csv(TABLES / "matched_control_matching_quality_summary.csv", index=False)
    report = ["# Matched Control Construction Report", "", "Date: 2026-06-08", "", "Controls were selected from real collision events outside the target high-boundary tail. Matching prioritised dataset, source file, run, trigger combination, vertex count, packed-candidate load and luminosity context.", "", "## Matching Quality", "", summary.to_markdown(index=False)]
    (REPORTS / "MATCHED_CONTROL_CONSTRUCTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
