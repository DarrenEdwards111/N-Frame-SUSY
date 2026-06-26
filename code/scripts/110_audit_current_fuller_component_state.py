from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
FEATURES = ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_event_features.csv"
SCORED = ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_events_with_BNF.csv"
DATE = "2026-06-09"


def main() -> None:
    df = pd.read_csv(SCORED, low_memory=False)
    thresholds = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    rows = []
    for (sample, process, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        row = {
            "sample_id": sample,
            "process_label": process,
            "classification": cls,
            "events": len(g),
            "has_P_displacement_proxy": "B_P_displacement_proxy" in g.columns and g["B_P_displacement_proxy"].notna().any(),
            "has_secondary_vertex_count": "secondary_vertex_count" in g.columns and g["secondary_vertex_count"].notna().any(),
            "has_P_reconstruction": "B_P_reconstruction" in g.columns and g["B_P_reconstruction"].notna().any(),
            "has_packed_candidate_count": "packed_candidate_count" in g.columns and g["packed_candidate_count"].notna().any(),
            "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
            "median_BNF": g["B_NF_fitted_frozen_raw"].median(),
            "mean_P_displacement_proxy": g["B_P_displacement_proxy"].mean(),
            "mean_P_reconstruction": g["B_P_reconstruction"].mean(),
            "mean_P_missing": g["B_P_missing"].mean(),
            "mean_P_visible_energy": g["B_P_visible_energy"].mean(),
            "component_mode": ";".join(sorted(g["component_mode"].dropna().astype(str).unique())) if "component_mode" in g.columns else "",
        }
        for t in thresholds.itertuples(index=False):
            row[f"{t.threshold}_tail_fraction"] = float((g["B_NF_fitted_frozen_raw"] > t.value).mean())
        rows.append(row)
    audit = pd.DataFrame(rows).sort_values("q95_tail_fraction", ascending=False)
    audit["strongest_mimic_at_q95"] = audit["q95_tail_fraction"].eq(audit["q95_tail_fraction"].max())
    audit["missing_piece"] = "No accessible full-component MiniAODSIM SUSY signal has yet been extracted, so signal-vs-background parity is incomplete."
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    audit.to_csv(TABLES / "current_fuller_component_state_audit.csv", index=False)
    report = [
        "# Current Fuller Component State Audit",
        "",
        f"Date: {DATE}",
        "",
        "This audit checks the existing fuller-component MiniAODSIM background layer before the signal-side parity search.",
        "",
        f"Feature file exists: `{FEATURES.exists()}`",
        "",
        f"Scored file exists: `{SCORED.exists()}`",
        "",
        "## Summary",
        "",
        audit.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "The strongest current fuller-component Standard Model mimic is the sample with the largest q95 tail fraction. The missing piece is an accessible MiniAODSIM SUSY signal processed through the same CMSSW/full-component route.",
    ]
    (REPORTS / "CURRENT_FULLER_COMPONENT_STATE_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
