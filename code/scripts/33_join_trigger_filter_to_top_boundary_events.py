from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TOPDIR = ROOT / "results" / "tables" / "top_boundary_events"
TRIGGER = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_event_quality_trigger_features.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def main() -> None:
    hand = pd.read_csv(TOPDIR / "top1000_hand_boundary_events.csv")
    unsup = pd.read_csv(TOPDIR / "top1000_unsupervised_boundary_events.csv")
    if not TRIGGER.exists():
        report = "# Top Boundary Trigger/Filter Join Report\n\nTrigger/filter table is missing, so no join was possible.\n"
        (REPORTS / "TOP_BOUNDARY_TRIGGER_FILTER_JOIN_REPORT.md").write_text(report, encoding="utf-8")
        print("missing trigger table")
        return
    trig = pd.read_csv(TRIGGER)
    keys = ["run", "lumi", "event"]
    trigger_cols = [c for c in trig.columns if c not in ["sample_id", "primary_dataset", "source_file", *keys]]
    outputs = []
    for name, df in [("hand", hand), ("unsupervised", unsup)]:
        joined = df.merge(trig[keys + trigger_cols], on=keys, how="left", indicator=True)
        out = TOPDIR / f"top1000_{name}_boundary_events_with_trigger_filter.csv"
        joined.to_csv(out, index=False)
        coverage = (joined["_merge"] == "both").mean()
        summary = {"top_set": name, "events": len(joined), "trigger_rows_matched": int((joined["_merge"] == "both").sum()), "coverage_fraction": coverage}
        for col in trigger_cols:
            summary[col + "_mean_matched"] = pd.to_numeric(joined.loc[joined["_merge"] == "both", col], errors="coerce").mean()
        outputs.append(summary)
    summary_df = pd.DataFrame(outputs)
    summary_df.to_csv(TABLES / "top_boundary_trigger_filter_summary.csv", index=False)
    report = [
        "# Top Boundary Trigger/Filter Join Report",
        "",
        "Date: 2026-06-08",
        "",
        f"Trigger/filter source table: `{TRIGGER}`",
        "",
        "The trigger/filter probe was intentionally small, so coverage of the full top-1000 event tables is expected to be limited.",
        "",
        summary_df.to_markdown(index=False),
        "",
        "A full trigger/filter join would require re-running the full file-by-file extraction with the patched trigger/filter analyser.",
    ]
    (REPORTS / "TOP_BOUNDARY_TRIGGER_FILTER_JOIN_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
