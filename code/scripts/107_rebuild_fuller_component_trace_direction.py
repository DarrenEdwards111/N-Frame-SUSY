from __future__ import annotations

import numpy as np
import pandas as pd

from fuller_component_common import DATE, FAMILIES, OUT, REPORTS, TABLES


COMPONENTS = list(FAMILIES.keys())


def unit(series: pd.Series) -> pd.Series:
    norm = np.linalg.norm(series.to_numpy(float))
    return series / norm if norm else series


def main() -> None:
    fuller = pd.read_csv(OUT / "fuller_component_benchmark_events_with_BNF.csv", low_memory=False)
    rows = []
    for (sample, proc, cls), g in fuller.groupby(["sample_id", "process_label", "classification"]):
        row = {"sample_id": sample, "process_label": proc, "classification": cls, "events": len(g)}
        for c in COMPONENTS:
            row[c] = g[f"B_{c}"].mean()
        rows.append(row)
    means = pd.DataFrame(rows)
    sm = fuller[fuller["classification"].eq("SM_background")]
    pooled = {"sample_id": "fuller_pooled_sm", "process_label": "Fuller pooled SM", "classification": "SM_background", "events": len(sm)}
    for c in COMPONENTS:
        pooled[c] = sm[f"B_{c}"].mean()
    means = pd.concat([means, pd.DataFrame([pooled])], ignore_index=True)
    means.to_csv(TABLES / "fuller_component_trace_direction_component_means.csv", index=False)
    weights = []
    indexed = means.set_index("sample_id")
    signals = means[means["classification"].eq("signal") & ~means["sample_id"].eq("fuller_pooled_sm")]
    for _, sig in signals.iterrows():
        raw = indexed.loc[sig["sample_id"], COMPONENTS] - indexed.loc["fuller_pooled_sm", COMPONENTS]
        u = unit(raw)
        weights.extend({
            "direction": f"{sig['sample_id']}_vs_fuller_pooled_sm",
            "component": c,
            "raw_contrast": float(raw[c]),
            "unit_weight": float(u[c]),
            "signal_mean": float(indexed.loc[sig["sample_id"], c]),
            "background_mean": float(indexed.loc["fuller_pooled_sm", c]),
        } for c in COMPONENTS)
    weights_df = pd.DataFrame(weights)
    weights_df.to_csv(TABLES / "fuller_component_trace_direction_weights.csv", index=False)
    report = [
        "# Fuller Component Trace Direction Definition Report",
        "",
        f"Date: {DATE}",
        "",
        "The available full-component signal is the selected MiniAODSIM compressed T2tt benchmark. SMS-T5Wg MiniAODSIM was not found in the automatic open-data search, so this is not a full-component T5Wg direction.",
        "",
        "## Component Means",
        "",
        means.to_markdown(index=False),
        "",
        "## Direction Weights",
        "",
        weights_df.to_markdown(index=False) if not weights_df.empty else "No full-component signal sample was available.",
    ]
    (REPORTS / "FULLER_COMPONENT_TRACE_DIRECTION_DEFINITION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(weights_df.to_string(index=False) if not weights_df.empty else "No signal direction available.")


if __name__ == "__main__":
    main()
