from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
EVENTS = ROOT / "data" / "processed" / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv"
DATE = "2026-06-09"
COMPONENTS = ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression"]


def unit(v):
    n = np.linalg.norm(v.to_numpy(float))
    return v / n if n else v


def main():
    df = pd.read_csv(EVENTS)
    rows = []
    for (sample, proc, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        row = {"sample_id": sample, "process_label": proc, "classification": cls, "events": len(g)}
        for c in COMPONENTS:
            row[c] = g[f"B_{c}"].mean()
        rows.append(row)
    means = pd.DataFrame(rows)
    sm = df[df["classification"].eq("SM_background")]
    pooled = {"sample_id": "expanded_pooled_sm", "process_label": "Expanded pooled SM", "classification": "SM_background", "events": len(sm)}
    for c in COMPONENTS:
        pooled[c] = sm[f"B_{c}"].mean()
    means = pd.concat([means, pd.DataFrame([pooled])], ignore_index=True)
    means.to_csv(TABLES / "expanded_trace_direction_component_means.csv", index=False)
    m = means.set_index("sample_id")
    s = m.loc["sms_t5wg_mg1500_mlsp1_signal", COMPONENTS]
    b = m.loc["expanded_pooled_sm", COMPONENTS]
    raw = s - b
    u = unit(raw)
    weights = pd.DataFrame({"direction": "sms_t5wg_vs_expanded_pooled_sm", "component": COMPONENTS, "raw_contrast": raw.to_numpy(float), "unit_weight": u.to_numpy(float), "signal_mean": s.to_numpy(float), "background_mean": b.to_numpy(float)})
    weights.to_csv(TABLES / "expanded_trace_direction_weights.csv", index=False)
    old = pd.read_csv(TABLES / "benchmark_trace_direction_weights.csv")
    old = old[old["direction"].eq("sms_vs_pooledSM")][["component", "unit_weight"]].rename(columns={"unit_weight": "previous_unit_weight"})
    comp = weights.merge(old, on="component", how="left")
    report = ["# Expanded Trace Direction Definition Report", "", f"Date: {DATE}", "", "The expanded trace direction uses SMS-T5Wg versus the expanded pooled SM background set. B_NF is frozen and not refitted.", "", "## Component Means", "", means.to_markdown(index=False), "", "## New Versus Previous Direction", "", comp.to_markdown(index=False)]
    (REPORTS / "EXPANDED_TRACE_DIRECTION_DEFINITION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(comp.to_string(index=False))


if __name__ == "__main__":
    main()
