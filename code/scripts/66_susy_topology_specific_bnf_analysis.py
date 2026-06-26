from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
PARAMS = ["B_P_displacement_proxy", "B_P_reconstruction", "B_P_multiplicity", "B_P_btag_structure", "B_P_visible_energy", "B_P_missing", "B_P_compression"]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    summary = df.groupby(["topology_group", "sample_id", "process_label"], as_index=False).agg(events=("event", "count"), mean_BNF=("B_NF_fitted_frozen_raw", "mean"), median_BNF=("B_NF_fitted_frozen_raw", "median"))
    summary.to_csv(TABLES / "susy_topology_bnf_summary.csv", index=False)
    rows = []
    for keys, group in df.groupby(["topology_group", "sample_id"]):
        for p in PARAMS:
            rows.append({"topology_group": keys[0], "sample_id": keys[1], "parameter_family": p.replace("B_", ""), "mean_parameter": group[p].mean(), "median_parameter": group[p].median()})
    drivers = pd.DataFrame(rows)
    drivers.to_csv(TABLES / "susy_topology_parameter_driver_summary.csv", index=False)
    report = ["# SUSY Topology B_NF Analysis Report", "", "Date: 2026-06-09", "", "This topology analysis uses available local SUSY-like benchmark samples only. No SM simulated backgrounds were available locally.", "", "## Topology Summary", "", summary.to_markdown(index=False), "", "## Parameter Drivers", "", drivers.to_markdown(index=False)]
    (REPORTS / "SUSY_TOPOLOGY_BNF_ANALYSIS_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    synthesis = ["# Boundary Stress To SUSY Relevance Synthesis", "", "Date: 2026-06-09", "", "The real-data fitted N-Frame boundary equation was frozen and applied to available local SUSY-like benchmark samples. This asks whether benchmark signals occupy high real-data B_NF tails.", "", "The current pilot is incomplete for SUSY specificity because no local SM simulated backgrounds were found. Therefore it cannot yet establish that SUSY-like benchmarks are more high-boundary than ttbar or QCD backgrounds.", "", "This is not a discovery claim and not evidence that SUSY was found. The result is best treated as a benchmark-level pilot and a preparation step for a proper SUSY-vs-SM specificity test.", "", "Next step: process small ttbar and QCD MiniAOD/NanoAOD background samples, then rerun the frozen B_NF tail-fraction comparison."]
    update = ["# Update To Darren: SUSY Relevance Pilot", "", "Date: 2026-06-09", "", "We froze the real-data-fitted N-Frame boundary equation and applied it to the local SUSY-like benchmark samples.", "", "Available local SUSY-like samples: SMS-T5Wg and HToAA4B. No local SM simulated backgrounds were available, so the key SUSY > SM comparison is not complete yet.", "", "This is not evidence that SUSY was found. It is a benchmark-level pilot showing how to test SUSY relevance once ttbar/QCD/W/Z backgrounds are added.", "", "Next step: add small ttbar and QCD background samples and compare their high-B_NF tail fractions against the SUSY benchmarks."]
    (REPORTS / "BOUNDARY_STRESS_TO_SUSY_RELEVANCE_SYNTHESIS.md").write_text("\n".join(synthesis), encoding="utf-8")
    (REPORTS / "UPDATE_TO_DARREN_SUSY_RELEVANCE_PILOT.md").write_text("\n".join(update), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
