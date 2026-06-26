from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_trigger_filter_full" / "real_only_full_event_features_with_trigger_filter_scored.csv"
OUT = ROOT / "data" / "processed" / "matched_control"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
FILTERS = [
    "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter", "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter",
]
CORE_FILTERS = ["pass_goodVertices", "pass_BadPFMuonFilter", "pass_EcalDeadCellTriggerPrimitiveFilter"]


def subset_summary(df: pd.DataFrame, name: str) -> list[dict]:
    rows = []
    for score in ["B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score"]:
        if score not in df:
            continue
        rows.append({
            "subset": name, "score": score, "events": len(df), "mean": df[score].mean(),
            "median": df[score].median(), "p95": df[score].quantile(.95), "p99": df[score].quantile(.99),
            "p999": df[score].quantile(.999),
        })
    return rows


def composition(df: pd.DataFrame, name: str, score: str, q: float, label: str) -> pd.DataFrame:
    tail = df[df[score] >= df[score].quantile(q)].copy()
    base = df["primary_dataset"].value_counts(normalize=True)
    rows = []
    for ds, frac in tail["primary_dataset"].value_counts(normalize=True).items():
        rows.append({"subset": name, "score": score, "tail": label, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base.get(ds, 0), "events": int((tail.primary_dataset == ds).sum())})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    if "real_only_unsupervised_boundary_score" not in df and "trigger_filter_unsupervised_boundary_score" in df:
        df["real_only_unsupervised_boundary_score"] = df["trigger_filter_unsupervised_boundary_score"]
    df["standard_quality_clean"] = df[FILTERS].eq(1).all(axis=1)
    df["relaxed_quality_clean"] = df[CORE_FILTERS].eq(1).all(axis=1)
    df["failed_standard_quality_filter_count"] = (df[FILTERS] != 1).sum(axis=1)
    df["top_quality_failures"] = df["failed_standard_quality_filter_count"] > 0

    subsets = {
        "all_events": df,
        "standard_quality_clean": df[df.standard_quality_clean].copy(),
        "relaxed_quality_clean": df[df.relaxed_quality_clean].copy(),
        "top_quality_failures": df[df.top_quality_failures].copy(),
    }
    paths = {
        "all_events": OUT / "all_events_with_quality_flags.csv",
        "standard_quality_clean": OUT / "standard_quality_clean_events.csv",
        "relaxed_quality_clean": OUT / "relaxed_quality_clean_events.csv",
        "top_quality_failures": OUT / "quality_failure_events.csv",
    }
    for name, sub in subsets.items():
        sub.to_csv(paths[name], index=False)

    summary_rows, tail_parts = [], []
    for name, sub in subsets.items():
        summary_rows.extend(subset_summary(sub, name))
        for score in ["B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score"]:
            for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
                tail_parts.append(composition(sub, name, score, q, label))
    summary = pd.DataFrame(summary_rows)
    tails = pd.concat(tail_parts, ignore_index=True)
    summary.to_csv(TABLES / "quality_subset_summary.csv", index=False)
    tails.to_csv(TABLES / "quality_subset_tail_composition.csv", index=False)

    impact_rows = []
    for score in ["B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score"]:
        for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
            full_tail = df[df[score] >= df[score].quantile(q)]
            for filt in FILTERS:
                impact_rows.append({
                    "score": score, "tail": label, "filter": filt, "tail_events": len(full_tail),
                    "failed_in_tail": int((full_tail[filt] != 1).sum()),
                    "failed_fraction_in_tail": float((full_tail[filt] != 1).mean()),
                    "failed_fraction_all": float((df[filt] != 1).mean()),
                })
    impact = pd.DataFrame(impact_rows)
    impact.to_csv(TABLES / "quality_filter_impact_on_boundary_tail.csv", index=False)

    report = [
        "# Event Quality Subset Report", "", "Date: 2026-06-08", "",
        "This report defines real-data-only quality subsets for matched-control analysis.", "",
        "## Subset Boundary Summary", "", summary.to_markdown(index=False),
        "", "## Filters Removing Top-Boundary Events", "",
        impact.sort_values("failed_fraction_in_tail", ascending=False).head(30).to_markdown(index=False),
        "", "## Tail Composition", "", tails.to_markdown(index=False),
    ]
    (REPORTS / "EVENT_QUALITY_SUBSET_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
