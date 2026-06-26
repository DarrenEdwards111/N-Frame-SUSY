from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
G = ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv"
H = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_with_fitted_nframe_score.csv"
DATE = "2026-06-09"

COMPONENTS = ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression"]


def norm_series(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std else s * np.nan


def prepare(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    out = df.copy()
    out["real_dataset"] = dataset
    if dataset == "Run2016G":
        prefix = "fitted_"
        out["B_NF_trace_base"] = out["B_NF_fitted_z"]
        out["B_NF_trace_raw"] = out["B_NF_fitted_raw"]
    else:
        prefix = "expanded_"
        out["B_NF_trace_base"] = out["B_NF_fitted_expanded_run2016h_z"]
        out["B_NF_trace_raw"] = out["B_NF_fitted_expanded_run2016h_raw"]
    for comp in COMPONENTS + ["P_displacement_proxy", "P_reconstruction"]:
        src = prefix + comp
        out[comp] = out[src] if src in out else np.nan
    out["real_displacement_reconstruction_axis"] = out[["P_displacement_proxy", "P_reconstruction"]].mean(axis=1)
    return out


def apply_scores(df: pd.DataFrame, defs: dict) -> pd.DataFrame:
    for direction, weights in defs["directions"].items():
        score = pd.Series(0.0, index=df.index)
        for comp, w in weights.items():
            score += float(w) * df[comp].fillna(0)
        df[f"Trace_{direction}"] = score
    red = [c for c in ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure"] if c in df]
    wdf = pd.read_csv(TABLES / "benchmark_trace_direction_weights.csv")
    pooled = wdf[wdf["direction"].eq("sms_vs_pooledSM")].set_index("component")["unit_weight"].to_dict()
    df["Trace_SMS_reduced"] = sum(float(pooled.get(c, 0)) * df[c].fillna(0) for c in red)
    df["trace_composite_score"] = norm_series(df["B_NF_trace_base"]) + norm_series(df["Trace_sms_vs_pooledSM"]) + 0.5 * norm_series(df["real_displacement_reconstruction_axis"])
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    defs = json.loads((OUT / "benchmark_trace_direction_definitions.json").read_text(encoding="utf-8"))
    g = apply_scores(prepare(pd.read_csv(G), "Run2016G"), defs)
    h = apply_scores(prepare(pd.read_csv(H), "Run2016H"), defs)
    keep_cols = [c for c in g.columns if c in h.columns or c not in h.columns]
    g.to_csv(OUT / "run2016g_real_with_trace_direction.csv", index=False)
    h.to_csv(OUT / "run2016h_real_with_trace_direction.csv", index=False)
    combined = pd.concat([g, h], ignore_index=True, sort=False)
    combined.to_csv(OUT / "combined_real_with_trace_direction.csv", index=False)
    rows = []
    for name, df in [("Run2016G", g), ("Run2016H", h), ("combined", combined)]:
        rows.append({
            "dataset": name,
            "events": len(df),
            "mean_BNF": df["B_NF_trace_base"].mean(),
            "mean_trace_sms_pooled": df["Trace_sms_vs_pooledSM"].mean(),
            "mean_trace_composite": df["trace_composite_score"].mean(),
            "has_displacement_reconstruction_axis": df["real_displacement_reconstruction_axis"].notna().any(),
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "real_trace_direction_application_summary.csv", index=False)
    report = ["# Real Data Trace Direction Application Report", "", f"Date: {DATE}", "", summary.to_markdown(index=False)]
    (REPORTS / "REAL_DATA_TRACE_DIRECTION_APPLICATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
