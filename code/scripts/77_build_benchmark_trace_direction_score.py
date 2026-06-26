from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
OUT = ROOT / "data" / "processed" / "trace_direction"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
THRESHOLDS = TABLES / "bnf_thresholds_real_and_sm.csv"
DATE = "2026-06-09"
INPUTS = [
    ROOT / "reports" / "FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md",
    ROOT / "reports" / "UPDATE_TO_DARREN_FIVE_SIGMA_BOUNDARY_ENRICHMENT_TEST.md",
    ROOT / "reports" / "SUSY_VS_SM_SPECIFICITY_TEST_REPORT.md",
    ROOT / "reports" / "SM_BACKGROUND_MIMICRY_ANALYSIS_REPORT.md",
    ROOT / "reports" / "BOUNDARY_STRESS_TO_SUSY_RELEVANCE_WITH_SM_BACKGROUNDS.md",
    ROOT / "reports" / "EXPANDED_RUN2016H_MINIAOD_BOUNDARY_VALIDATION_REPORT.md",
    ROOT / "reports" / "EXPANDED_RUN2016H_NFRAME_INTERPRETATION.md",
    ROOT / "reports" / "FITTED_NFRAME_BOUNDARY_EQUATION.md",
    ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv",
    ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_with_fitted_nframe_score.csv",
    SUSY,
    SM,
    THRESHOLDS,
]

COMPONENTS = ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression"]
COL = {c: f"B_{c}" for c in COMPONENTS}


def load_benchmarks() -> pd.DataFrame:
    return pd.concat([pd.read_csv(SUSY), pd.read_csv(SM)], ignore_index=True)


def unit(v: pd.Series) -> pd.Series:
    norm = float(np.linalg.norm(v.to_numpy(float)))
    return v / norm if norm else v


def direction(means: pd.DataFrame, signal: str, background: str) -> pd.DataFrame:
    s = means.loc[signal, COMPONENTS]
    b = means.loc[background, COMPONENTS]
    raw = s - b
    u = unit(raw)
    return pd.DataFrame({
        "direction": background.replace("_benchmark", "").replace("pooled_sm", "sms_vs_pooledSM").replace("ttjets", "sms_vs_TTJets").replace("qcd", "sms_vs_QCD"),
        "component": COMPONENTS,
        "raw_contrast": raw.to_numpy(float),
        "unit_weight": u.to_numpy(float),
        "signal_mean": s.to_numpy(float),
        "background_mean": b.to_numpy(float),
    })


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bench = load_benchmarks()
    inv_rows = []
    for path in INPUTS:
        row = {"path": str(path), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0}
        if path.suffix.lower() == ".csv" and path.exists():
            sample = pd.read_csv(path, nrows=5)
            row["columns"] = ";".join(sample.columns)
            try:
                row["rows"] = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1
            except Exception:
                row["rows"] = ""
            row["bnf_columns"] = ";".join([c for c in sample.columns if "B_NF" in c])
            row["parameter_columns"] = ";".join([c for c in sample.columns if "P_" in c])
        inv_rows.append(row)
    inv = pd.DataFrame(inv_rows)
    inv.to_csv(TABLES / "trace_direction_input_inventory.csv", index=False)
    rows = []
    for sample, group in bench.groupby("sample_id"):
        row = {"sample_id": sample, "process_label": group["process_label"].iloc[0], "classification": group["classification"].iloc[0], "events": len(group)}
        for comp, col in COL.items():
            row[comp] = group[col].mean() if col in group else np.nan
        rows.append(row)
    means = pd.DataFrame(rows)
    pooled_sm = bench[bench["classification"].eq("SM_background")]
    pooled_row = {"sample_id": "pooled_sm_benchmark", "process_label": "Pooled TTJets + QCD", "classification": "SM_background", "events": len(pooled_sm)}
    for comp, col in COL.items():
        pooled_row[comp] = pooled_sm[col].mean()
    means = pd.concat([means, pd.DataFrame([pooled_row])], ignore_index=True)
    means.to_csv(TABLES / "benchmark_trace_direction_component_means.csv", index=False)
    means_idx = means.set_index("sample_id")
    weights = pd.concat([
        direction(means_idx, "sms_t5wg_mg1500_mlsp1_signal", "pooled_sm_benchmark"),
        direction(means_idx, "sms_t5wg_mg1500_mlsp1_signal", "ttjets_nanoaodsim_pilot"),
        direction(means_idx, "sms_t5wg_mg1500_mlsp1_signal", "qcd_ht700to1000_nanoaodsim_pilot"),
    ], ignore_index=True)
    weights.to_csv(TABLES / "benchmark_trace_direction_weights.csv", index=False)
    definition = {
        "date": DATE,
        "note": "Benchmark simulations define only a direction. B_NF is frozen and not refitted.",
        "components": COMPONENTS,
        "directions": {
            d: weights[weights["direction"].eq(d)].set_index("component")["unit_weight"].to_dict()
            for d in weights["direction"].unique()
        },
        "real_boundary_axis_components": ["P_displacement_proxy", "P_reconstruction"],
    }
    (OUT / "benchmark_trace_direction_definitions.json").write_text(json.dumps(definition, indent=2), encoding="utf-8")
    report = [
        "# Benchmark Trace Direction Definition Report",
        "",
        f"Date: {DATE}",
        "",
        "Simulation is used only to define benchmark contrast directions. The frozen real-data-fitted B_NF equation is not refitted.",
        "",
        "## Component Means",
        "",
        means.to_markdown(index=False),
        "",
        "## Direction Weights",
        "",
        weights.to_markdown(index=False),
        "",
        "P_displacement_proxy and P_reconstruction are kept as a separate real-data boundary axis because they are unavailable or reduced in the SMS benchmark features.",
    ]
    (REPORTS / "BENCHMARK_TRACE_DIRECTION_DEFINITION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    audit = [
        "# Trace Direction Input Audit",
        "",
        f"Date: {DATE}",
        "",
        "Run2016G and Run2016H are analysed separately first, then combined as a replication/synthesis view.",
        "",
        "## Input Inventory",
        "",
        inv.to_markdown(index=False),
        "",
        "## Thresholds",
        "",
        pd.read_csv(THRESHOLDS).to_markdown(index=False),
        "",
        "Benchmark direction is reduced-component because SMS-T5Wg lacks P_displacement_proxy and P_reconstruction. Real data retain those as a separate boundary axis.",
    ]
    (REPORTS / "TRACE_DIRECTION_INPUT_AUDIT.md").write_text("\n".join(audit), encoding="utf-8")
    print(weights.to_string(index=False))


if __name__ == "__main__":
    main()
