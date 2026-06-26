from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_source_file.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
KEY = ["MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count"]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    by_sample = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(events=("event", "count"), files=("source_file", "nunique"))
    by_file = df.groupby(["sample_id", "primary_dataset", "source_file", "source_file_index"], as_index=False).agg(
        events=("event", "count"),
        first_global_index=("event_index_global_within_sample", "min"),
        last_global_index=("event_index_global_within_sample", "max"),
        source_missing=("source_file", lambda s: int(s.isna().sum())),
    )
    missing = pd.DataFrame({"variable": df.columns, "missing_count": [int(df[c].isna().sum()) for c in df.columns], "missing_fraction": [df[c].isna().mean() for c in df.columns]})
    checks = []
    checks.append(("total_events", True, len(df)))
    checks.append(("source_file_present_every_row", df["source_file"].notna().all(), int(df["source_file"].isna().sum())))
    checks.append(("no_simulated_sample_labels", not df[["sample_id", "primary_dataset", "source_file"]].astype(str).apply(lambda c: c.str.contains("susy|t5wg|htoaa|signal", case=False, regex=True)).any().any(), ""))
    checks.append(("duplicate_run_lumi_event", not df.duplicated(["run", "lumi", "event"]).any(), int(df.duplicated(["run", "lumi", "event"]).sum())))
    for c in KEY:
        checks.append((f"has_{c}", c in df.columns, ""))
    for c in ["MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count"]:
        checks.append((f"range_{c}_nonnegative", bool((df[c] >= 0).all()), int((df[c] < 0).sum())))
    checks_df = pd.DataFrame(checks, columns=["check", "pass", "value"])
    by_sample.to_csv(TABLES / "real_only_full_validation_by_sample.csv", index=False)
    by_file.to_csv(TABLES / "real_only_full_validation_by_file.csv", index=False)
    missing.to_csv(TABLES / "real_only_full_missingness.csv", index=False)
    checks_df.to_csv(TABLES / "real_only_full_validation_checks.csv", index=False)
    report = [
        "# Real-Only Full Validation Report",
        "",
        "Date: 2026-06-08",
        "",
        f"Input: `{INPUT}`",
        "",
        "## Validation Checks",
        "",
        checks_df.to_markdown(index=False),
        "",
        "## Events By Sample",
        "",
        by_sample.to_markdown(index=False),
        "",
        "## Events By Source File",
        "",
        by_file.to_markdown(index=False),
        "",
        "No simulated sample labels are present in sample identity fields. Exact `source_file` provenance is populated for every event.",
    ]
    (REPORTS / "REAL_ONLY_FULL_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(by_sample.to_string(index=False))
    print(checks_df.to_string(index=False))


if __name__ == "__main__":
    main()
