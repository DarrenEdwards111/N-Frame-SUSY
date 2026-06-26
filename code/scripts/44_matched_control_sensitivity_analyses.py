from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
IN = ROOT / "data" / "processed" / "matched_control"


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    diff = pd.read_csv(TABLES / "matched_case_control_feature_differences.csv")
    match = pd.read_csv(TABLES / "matched_control_matching_quality_summary.csv")
    standard = pd.read_csv(IN / "standard_quality_clean_events_rescored.csv")
    relaxed = pd.read_csv(IN / "relaxed_quality_clean_events_rescored.csv")

    key_features = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "secondary_vertex_count", "R_missing", "R_visible_energy", "R_btag_structure", "R_reconstruction_complexity", "R_compression_proxy", "R_displacement_proxy"]
    sens = diff[diff.feature.isin(key_features)].groupby(["quality_subset", "boundary_score_type", "tail_definition", "feature"], as_index=False).agg(
        paired_mean_difference=("paired_mean_difference", "mean"),
        standardised_paired_mean_difference=("standardised_paired_mean_difference", "mean"),
        cases=("matched_cases", "max"),
    )
    sens.to_csv(TABLES / "matched_control_sensitivity_summary.csv", index=False)

    score = "mc_B_boundary_hand_defined_z"
    suspect_run = int(standard.groupby("run")[score].mean().sort_values(ascending=False).index[0])
    suspect_file = str(standard.groupby("source_file")[score].mean().sort_values(ascending=False).index[0])
    excl_rows = []
    for name, df in {"standard_quality_clean": standard, "relaxed_quality_clean": relaxed}.items():
        for exclusion, sub in {
            "none": df,
            f"exclude_run_{suspect_run}": df[df.run != suspect_run],
            f"exclude_file_{suspect_file}": df[df.source_file != suspect_file],
        }.items():
            base = sub.primary_dataset.value_counts(normalize=True)
            for q, tail in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
                top = sub[sub[score] >= sub[score].quantile(q)]
                for ds, frac in top.primary_dataset.value_counts(normalize=True).items():
                    excl_rows.append({"subset": name, "exclusion": exclusion, "score": score, "tail": tail, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base.get(ds, 0), "enrichment_ratio": frac / base.get(ds, 1), "events": int((top.primary_dataset == ds).sum())})
    excl = pd.DataFrame(excl_rows)
    excl.to_csv(TABLES / "matched_control_exclusion_sensitivity.csv", index=False)

    report = ["# Matched Control Sensitivity Report", "", "Date: 2026-06-08", "", "Sensitivity checks compare quality subsets, tail thresholds, score types, and exclusions of the strongest suspect run/source file.", "", "## Matching Quality", "", match.to_markdown(index=False), "", "## Key Feature Sensitivity", "", sens.to_markdown(index=False), "", "## Exclusion Sensitivity", "", excl.to_markdown(index=False)]
    (REPORTS / "MATCHED_CONTROL_SENSITIVITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(sens.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
