from __future__ import annotations

import numpy as np
import pandas as pd

from fuller_component_common import FAMILIES
from susy_signal_common import DATE, REPORTS, ROOT, TABLES


COMPONENTS = list(FAMILIES.keys())


def unit(v: pd.Series) -> pd.Series:
    n = np.linalg.norm(v.to_numpy(float))
    return v / n if n else v


def main() -> None:
    sig = pd.read_csv(ROOT / "data" / "processed" / "fuller_component_susy_signals" / "accessible_susy_miniaodsim_events_with_BNF.csv", low_memory=False)
    bg = pd.read_csv(ROOT / "data" / "processed" / "fuller_component_benchmarks" / "fuller_component_benchmark_events_with_BNF.csv", low_memory=False)
    df = pd.concat([sig, bg], ignore_index=True, sort=False)
    rows = []
    for (sample, proc, cls), g in df.groupby(["sample_id", "process_label", "classification"]):
        row = {"sample_id": sample, "process_label": proc, "classification": cls, "events": len(g)}
        for c in COMPONENTS:
            row[c] = g[f"B_{c}"].mean()
        rows.append(row)
    means = pd.DataFrame(rows)
    qcd = means[means["process_label"].eq("QCD HT1000to1500")].iloc[0]
    weights = []
    for _, s in means[means["classification"].eq("signal")].iterrows():
        raw = s[COMPONENTS] - qcd[COMPONENTS]
        u = unit(raw)
        for c in COMPONENTS:
            weights.append({
                "direction": f"{s['sample_id']}_vs_qcd_ht1000to1500",
                "signal_sample": s["sample_id"],
                "background_sample": qcd["sample_id"],
                "component": c,
                "raw_contrast": float(raw[c]),
                "unit_weight": float(u[c]),
                "signal_mean": float(s[c]),
                "qcd_ht1000_mean": float(qcd[c]),
            })
    means.to_csv(TABLES / "full_component_trace_direction_component_means.csv", index=False)
    weights_df = pd.DataFrame(weights)
    weights_df.to_csv(TABLES / "full_component_trace_direction_weights.csv", index=False)
    dominant = weights_df.reindex(weights_df["unit_weight"].abs().sort_values(ascending=False).index).groupby("direction").head(3)
    report = [
        "# Full Component Trace Direction Test Report",
        "",
        f"Date: {DATE}",
        "",
        "Trace directions were built as each full-component SUSY signal centroid minus the fuller-component QCD HT1000to1500 centroid. This is a benchmark direction, not a discovery claim.",
        "",
        "## Component Means",
        "",
        means.to_markdown(index=False),
        "",
        "## Direction Weights",
        "",
        weights_df.to_markdown(index=False),
        "",
        "## Dominant Absolute Weights",
        "",
        dominant.to_markdown(index=False),
    ]
    (REPORTS / "FULL_COMPONENT_TRACE_DIRECTION_TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(dominant.to_string(index=False))


if __name__ == "__main__":
    main()
