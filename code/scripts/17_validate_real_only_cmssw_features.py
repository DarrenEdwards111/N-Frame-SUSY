from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_combined.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)

    validation_rows = []
    validation_rows.append({"check": "total_events", "status": "pass", "value": len(df), "notes": ""})
    by_sample = df.groupby("sample_id").size().reset_index(name="events")
    for _, row in by_sample.iterrows():
        validation_rows.append({
            "check": "events_by_sample",
            "status": "pass" if row.events > 0 else "fail",
            "value": int(row.events),
            "notes": row.sample_id,
        })

    identity_cols = [c for c in ["sample_id", "primary_dataset", "source_file", "record_id"] if c in df.columns]
    token_hits = pd.Series(False, index=df.index)
    for col in identity_cols:
        if col == "record_id":
            token_hits = token_hits | df[col].astype(str).isin(["63465", "64906"])
        else:
            token_hits = token_hits | df[col].astype(str).str.contains(
                "susy|t5wg|htoaa|signal", case=False, regex=True, na=False
            )
    simulated_hits = int(token_hits.sum())
    validation_rows.append({
        "check": "no_simulated_labels",
        "status": "pass" if simulated_hits == 0 else "fail",
        "value": int(simulated_hits),
        "notes": "Checked sample identity fields only; numeric event IDs can coincidentally contain excluded record numbers.",
    })

    if {"run", "lumi", "event"}.issubset(df.columns):
        dupes = df.duplicated(["run", "lumi", "event"]).sum()
        validation_rows.append({
            "check": "duplicate_run_lumi_event",
            "status": "warn" if dupes else "pass",
            "value": int(dupes),
            "notes": "Duplicates may indicate overlap between primary datasets if non-zero.",
        })

    ranges = {
        "MET_pt": (0, None),
        "HT": (0, None),
        "N_jets": (0, None),
        "N_jets_30": (0, None),
        "N_jets_50": (0, None),
        "N_muons": (0, None),
        "N_electrons": (0, None),
        "N_leptons": (0, None),
        "N_btags_loose": (0, None),
        "N_btags_medium": (0, None),
        "N_btags_tight": (0, None),
        "N_primary_vertices": (0, None),
        "packed_candidate_count": (0, None),
        "secondary_vertex_count": (0, None),
    }
    for col, (lo, hi) in ranges.items():
        if col not in df:
            validation_rows.append({"check": f"range_{col}", "status": "warn", "value": "missing", "notes": ""})
            continue
        bad = df[col].lt(lo).sum() if lo is not None else 0
        if hi is not None:
            bad += df[col].gt(hi).sum()
        validation_rows.append({
            "check": f"range_{col}",
            "status": "pass" if bad == 0 else "fail",
            "value": int(bad),
            "notes": f"Expected {col} >= {lo}." if hi is None else f"Expected {lo} <= {col} <= {hi}.",
        })

    extreme_rows = []
    numeric_cols = df.select_dtypes("number").columns
    for col in numeric_cols:
        s = df[col].dropna()
        if s.empty:
            continue
        q01, q50, q99 = s.quantile([0.01, 0.50, 0.99])
        extreme_rows.append({
            "variable": col,
            "min": s.min(),
            "p01": q01,
            "median": q50,
            "p99": q99,
            "max": s.max(),
        })

    missing = pd.DataFrame({
        "variable": df.columns,
        "missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "missing_fraction": [float(df[c].isna().mean()) for c in df.columns],
    }).sort_values(["missing_fraction", "variable"], ascending=[False, True])

    validation = pd.DataFrame(validation_rows)
    validation.to_csv(TABLES / "real_only_cmssw_feature_validation.csv", index=False)
    missing.to_csv(TABLES / "real_only_cmssw_missingness_summary.csv", index=False)
    pd.DataFrame(extreme_rows).to_csv(TABLES / "real_only_cmssw_extreme_value_summary.csv", index=False)

    report = [
        "# Real-Only Feature Validation Report",
        "",
        "Date: 2026-06-08",
        "",
        f"Input: `{INPUT}`",
        "",
        "## Event Counts",
        "",
        by_sample.to_markdown(index=False),
        "",
        "## Validation Checks",
        "",
        validation.to_markdown(index=False),
        "",
        "## Missingness",
        "",
        "Full missingness table written to `results/tables/real_only_cmssw_missingness_summary.csv`.",
        "",
        "## Notes",
        "",
        "No simulated samples are used in this validation. Extreme values are flagged in a separate table, not removed.",
    ]
    (REPORTS / "REAL_ONLY_FEATURE_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(validation.to_string(index=False))


if __name__ == "__main__":
    main()
