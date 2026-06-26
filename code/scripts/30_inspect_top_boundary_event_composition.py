from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
TOPDIR = TABLES / "top_boundary_events"

SETS = [
    ("hand_top100", "top100_hand_boundary_events.csv", "B_boundary_hand_defined_z"),
    ("hand_top1000", "top1000_hand_boundary_events.csv", "B_boundary_hand_defined_z"),
    ("hand_top0p1pct", "top0p1pct_hand_boundary_events.csv", "B_boundary_hand_defined_z"),
    ("unsup_top100", "top100_unsupervised_boundary_events.csv", "real_only_full_unsupervised_boundary_score"),
    ("unsup_top1000", "top1000_unsupervised_boundary_events.csv", "real_only_full_unsupervised_boundary_score"),
    ("unsup_top0p1pct", "top0p1pct_unsupervised_boundary_events.csv", "real_only_full_unsupervised_boundary_score"),
]
VARS = ["MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "N_btags_tight", "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count", "compression_proxy_raw", "displacement_proxy_raw"]


def describe(top: pd.DataFrame, rest: pd.DataFrame, set_name: str) -> list[dict]:
    rows = []
    for var in VARS:
        rows.append({
            "top_set": set_name, "variable": var,
            "top_mean": top[var].mean(), "rest_mean": rest[var].mean(), "mean_difference": top[var].mean() - rest[var].mean(),
            "top_median": top[var].median(), "rest_median": rest[var].median(),
            "top_p90": top[var].quantile(.9), "rest_p90": rest[var].quantile(.9),
        })
    return rows


def pattern_judgement(row: pd.Series) -> str:
    flags = []
    if row.get("MET_pt", 0) > row.get("MET_pt_rest_p90", np.inf):
        flags.append("MET-dominant")
    if row.get("HT", 0) > row.get("HT_rest_p90", np.inf) or row.get("N_jets_30", 0) > row.get("N_jets_30_rest_p90", np.inf):
        flags.append("HT/JetHT-dominant")
    if row.get("N_btags_medium", 0) > row.get("N_btags_medium_rest_p90", np.inf):
        flags.append("b-tag/heavy-flavour")
    if row.get("secondary_vertex_count", 0) > row.get("secondary_vertex_count_rest_p90", np.inf):
        flags.append("secondary-vertex proxy")
    if row.get("compression_proxy_raw", 0) > row.get("compression_proxy_raw_rest_p90", np.inf):
        flags.append("compression-like")
    return "; ".join(flags) if flags else "mixed/ordinary relative to top-set medians"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    full = pd.read_csv(INPUT)
    sample_rows, file_rows, run_rows, lumi_rows, driver_rows = [], [], [], [], []
    judgement_rows = []
    for set_name, filename, score in SETS:
        top = pd.read_csv(TOPDIR / filename)
        keys = ["sample_id", "run", "lumi", "event"]
        rest = full.merge(top[keys], on=keys, how="left", indicator=True)
        rest = rest[rest["_merge"] == "left_only"].drop(columns=["_merge"])
        for sample, count in top["sample_id"].value_counts().items():
            sample_rows.append({"top_set": set_name, "sample_id": sample, "count": int(count), "fraction": count / len(top)})
        for src, count in top["source_file"].value_counts().items():
            file_rows.append({"top_set": set_name, "source_file": src, "count": int(count), "fraction": count / len(top)})
        for run, count in top["run"].value_counts().items():
            run_rows.append({"top_set": set_name, "run": int(run), "count": int(count), "fraction": count / len(top)})
        top = top.assign(lumi_bin=(top["lumi"] // 50) * 50)
        for (run, lumi_bin), count in top.groupby(["run", "lumi_bin"]).size().items():
            lumi_rows.append({"top_set": set_name, "run": int(run), "lumi_bin": int(lumi_bin), "count": int(count), "fraction": count / len(top)})
        driver_rows.extend(describe(top, rest, set_name))
        med = {v: top[v].median() for v in VARS}
        rest_p90 = {f"{v}_rest_p90": rest[v].quantile(.9) for v in VARS}
        judgement_rows.append({"top_set": set_name, "score": score, "events": len(top), "pattern": pattern_judgement(pd.Series({**med, **rest_p90}))})
    sample_df = pd.DataFrame(sample_rows)
    file_df = pd.DataFrame(file_rows)
    run_df = pd.DataFrame(run_rows)
    lumi_df = pd.DataFrame(lumi_rows)
    driver_df = pd.DataFrame(driver_rows)
    judgement_df = pd.DataFrame(judgement_rows)
    sample_df.to_csv(TABLES / "top_boundary_composition_by_sample.csv", index=False)
    file_df.to_csv(TABLES / "top_boundary_composition_by_source_file.csv", index=False)
    run_df.to_csv(TABLES / "top_boundary_composition_by_run.csv", index=False)
    lumi_df.to_csv(TABLES / "top_boundary_composition_by_lumi_bin.csv", index=False)
    driver_df.to_csv(TABLES / "top_boundary_driver_variable_summary.csv", index=False)
    judgement_df.to_csv(TABLES / "top_boundary_pattern_judgement_by_set.csv", index=False)
    report = [
        "# Top Boundary Event Composition Report",
        "",
        "Date: 2026-06-08",
        "",
        "This report inspects real-data-only top boundary event sets. No simulated samples are used.",
        "",
        "## Pattern Judgement",
        "",
        judgement_df.to_markdown(index=False),
        "",
        "## Composition By Sample",
        "",
        sample_df.to_markdown(index=False),
        "",
        "## Main Driver Variables",
        "",
        driver_df.sort_values(["top_set", "mean_difference"], ascending=[True, False]).groupby("top_set").head(8).to_markdown(index=False),
    ]
    (REPORTS / "TOP_BOUNDARY_EVENT_COMPOSITION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(judgement_df.to_string(index=False))


if __name__ == "__main__":
    main()
