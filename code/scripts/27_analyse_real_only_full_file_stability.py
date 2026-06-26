from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    score = "B_boundary_hand_defined_z"
    thresholds = {name: df[score].quantile(q) for name, q in [("top10", .9), ("top05", .95), ("top01", .99), ("top001", .999)]}
    by_file = df.groupby(["sample_id", "primary_dataset", "source_file", "source_file_index"], as_index=False).agg(
        events=("event", "count"), mean_B=("B_boundary_hand_defined_z", "mean"), mean_unsup=("real_only_full_unsupervised_boundary_score", "mean"),
        mean_MET=("MET_pt", "mean"), mean_HT=("HT", "mean"), mean_N_jets_30=("N_jets_30", "mean"), mean_N_leptons=("N_leptons", "mean"),
        mean_N_btags_medium=("N_btags_medium", "mean"), mean_secondary_vertex_count=("secondary_vertex_count", "mean"), mean_packed_candidate_count=("packed_candidate_count", "mean"),
    )
    for name, thr in thresholds.items():
        by_file[f"{name}_frac"] = df.groupby(["sample_id", "primary_dataset", "source_file", "source_file_index"])[score].apply(lambda s: (s >= thr).mean()).values
    by_file.to_csv(TABLES / "real_only_full_boundary_summary_by_source_file.csv", index=False)
    enrich_rows = []
    total = len(df)
    for name, thr in thresholds.items():
        tail = df[df[score] >= thr]
        for (sample, pdset, src), group in df.groupby(["sample_id", "primary_dataset", "source_file"]):
            expected = len(group) * len(tail) / total
            observed = int(((tail["sample_id"] == sample) & (tail["source_file"] == src)).sum())
            enrich_rows.append({"tail": name, "sample_id": sample, "primary_dataset": pdset, "source_file": src, "observed": observed, "expected": expected, "enrichment_ratio": observed / expected if expected else np.nan})
    enrich = pd.DataFrame(enrich_rows)
    enrich.to_csv(TABLES / "real_only_full_tail_enrichment_by_source_file.csv", index=False)
    loo = []
    for src in df["source_file"].unique():
        train = df[df["source_file"] != src]
        thr = train[score].quantile(.95)
        held = df[df["source_file"] == src]
        pattern = df[df[score] >= thr].groupby("sample_id").size() / len(df[df[score] >= thr])
        loo.append({"left_out_source_file": src, "threshold_without_file": thr, "held_out_top05_frac": (held[score] >= thr).mean(), **{f"tail_fraction_{k}": v for k, v in pattern.to_dict().items()}})
    loo_df = pd.DataFrame(loo)
    loo_df.to_csv(TABLES / "real_only_full_leave_one_file_out_stability.csv", index=False)
    within = by_file.copy()
    within["within_sample_top05_mean"] = within.groupby("sample_id")["top05_frac"].transform("mean")
    within["top05_frac_minus_sample_mean"] = within["top05_frac"] - within["within_sample_top05_mean"]
    within.to_csv(TABLES / "real_only_full_within_sample_file_stability.csv", index=False)
    lumi = df.assign(lumi_bin=(df["lumi"] // 50) * 50).groupby(["sample_id", "run", "lumi_bin"], as_index=False).agg(events=("event", "count"), top05_frac=(score, lambda s: (s >= thresholds["top05"]).mean()), mean_B=(score, "mean"))
    lumi.to_csv(TABLES / "real_only_full_run_lumi_stability.csv", index=False)
    report = ["# Real-Only Full File Stability Report", "", "Date: 2026-06-08", "", "Exact source-file provenance is available for every event.", "", "## Boundary Summary By File", "", by_file.to_markdown(index=False), "", "## Strongest Source-File Tail Enrichments", "", enrich.sort_values("enrichment_ratio", ascending=False).head(20).to_markdown(index=False), "", "## Leave-One-File-Out Stability", "", loo_df.to_markdown(index=False), "", "## Interpretation", "", "The file-level tables show whether the high-boundary tail is spread across files or dominated by individual files. This is a robustness check, not a discovery statistic."]
    (REPORTS / "REAL_ONLY_FULL_FILE_STABILITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(by_file.to_string(index=False))


if __name__ == "__main__":
    main()
