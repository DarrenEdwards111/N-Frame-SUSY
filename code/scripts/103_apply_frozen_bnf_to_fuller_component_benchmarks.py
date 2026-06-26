from __future__ import annotations

import pandas as pd

from fuller_component_common import DATE, OUT, REPORTS, TABLES, apply_frozen_bnf


def main() -> None:
    src = OUT / "fuller_component_benchmark_event_features.csv"
    if not src.exists():
        raise SystemExit("Fuller component benchmark features are missing; run script 102 first.")
    df = pd.read_csv(src, low_memory=False)
    scored, availability = apply_frozen_bnf(df)
    out = OUT / "fuller_component_benchmark_events_with_BNF.csv"
    scored.to_csv(out, index=False)
    availability.to_csv(TABLES / "fuller_component_scoring_feature_availability.csv", index=False)
    summary = scored.groupby(["sample_id", "process_label", "classification", "component_mode"], as_index=False).agg(
        events=("event", "count"),
        mean_BNF=("B_NF_fitted_frozen_raw", "mean"),
        median_BNF=("B_NF_fitted_frozen_raw", "median"),
        mean_displacement=("B_P_displacement_proxy", "mean"),
        mean_reconstruction=("B_P_reconstruction", "mean"),
        mean_missing=("B_P_missing", "mean"),
        mean_visible=("B_P_visible_energy", "mean"),
    )
    summary.to_csv(TABLES / "fuller_component_bnf_summary.csv", index=False)
    (REPORTS / "FULLER_COMPONENT_BNF_APPLICATION_REPORT.md").write_text(
        "# Fuller Component Frozen B_NF Application Report\n\n"
        f"Date: {DATE}\n\n"
        "The Run2016G-derived fitted B_NF equation was applied unchanged. No simulated sample was used to refit it.\n\n"
        + summary.to_markdown(index=False)
        + "\n\n## Feature Availability\n\n"
        + availability.to_markdown(index=False),
        encoding="utf-8",
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
