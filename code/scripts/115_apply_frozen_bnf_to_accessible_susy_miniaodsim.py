from __future__ import annotations

import pandas as pd

from fuller_component_common import FAMILIES
from susy_signal_common import DATE, REPORTS, SIGNAL_OUT, TABLES, score_signal_file


def main() -> None:
    src = SIGNAL_OUT / "accessible_susy_miniaodsim_event_features.csv"
    out = SIGNAL_OUT / "accessible_susy_miniaodsim_events_with_BNF.csv"
    scored, availability = score_signal_file(src, out)
    availability.to_csv(TABLES / "accessible_susy_signal_scoring_feature_availability.csv", index=False)
    thresholds = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    rows = []
    for (sample, process, topology), g in scored.groupby(["sample_id", "process_label", "topology_class"]):
        row = {
            "sample_id": sample,
            "process_label": process,
            "topology_class": topology,
            "events": len(g),
            "full_component_score_available": bool(g[[f"B_{c}" for c in FAMILIES]].notna().all(axis=1).any()),
            "missing_components": ";".join([c for c in FAMILIES if f"B_{c}" not in g.columns or not g[f"B_{c}"].notna().any()]),
            "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
            "median_BNF": g["B_NF_fitted_frozen_raw"].median(),
        }
        for c in FAMILIES:
            row[f"mean_{c}"] = g[f"B_{c}"].mean()
        for t in thresholds.itertuples(index=False):
            row[f"{t.threshold}_tail_fraction"] = float((g["B_NF_fitted_frozen_raw"] > t.value).mean())
        rows.append(row)
    summary = pd.DataFrame(rows).sort_values("q95_tail_fraction", ascending=False)
    summary.to_csv(TABLES / "accessible_susy_signal_bnf_summary.csv", index=False)
    report = [
        "# Accessible SUSY Signal Frozen B_NF Application Report",
        "",
        f"Date: {DATE}",
        "",
        "The frozen Run2016G-fitted B_NF equation was applied unchanged. No refit was performed.",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Feature Availability",
        "",
        availability.to_markdown(index=False),
    ]
    (REPORTS / "ACCESSIBLE_SUSY_SIGNAL_BNF_APPLICATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
