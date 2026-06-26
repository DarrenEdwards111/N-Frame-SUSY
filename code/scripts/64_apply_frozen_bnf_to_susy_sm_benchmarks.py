from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
CMSSW_OUT = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction" / "outputs"
OUT_DIR = ROOT / "data" / "processed" / "susy_relevance_benchmark_features"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
REAL_SCALE = ROOT / "data" / "processed" / "matched_control" / "standard_quality_clean_events.csv"
REAL_FITTED = ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv"

SAMPLES = [
    {
        "sample_id": "sms_t5wg_mg1500_mlsp1_signal",
        "process_label": "SMS-T5Wg mGluino1500 mLSP1",
        "classification": "signal",
        "topology_group": "gluino/squark; missing-energy plus jets",
        "record_id": 63465,
        "feature_path": CMSSW_OUT / "sms_t5wg_mg1500_mlsp1_signal_cmssw5000" / "event_features.csv",
    },
    {
        "sample_id": "susy_htoaa4b_m12_signal",
        "process_label": "SUSY HToAA4B mA12",
        "classification": "signal",
        "topology_group": "heavy-flavour/Higgs-to-b",
        "record_id": 64906,
        "feature_path": CMSSW_OUT / "susy_htoaa4b_m12_signal_cmssw5000" / "event_features.csv",
    },
]

FAMILIES = {
    "P_displacement_proxy": ["secondary_vertex_count", "displacement_proxy_raw"],
    "P_reconstruction": ["packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_multiplicity": ["N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["HT", "leading_jet_pt", "subleading_jet_pt"],
    "P_missing": ["MET_pt"],
    "P_compression": ["compression_proxy_raw"],
}
WEIGHTS = {
    "P_displacement_proxy": 0.3566,
    "P_reconstruction": 0.2112,
    "P_multiplicity": 0.2019,
    "P_btag_structure": 0.0926,
    "P_visible_energy": 0.0728,
    "P_missing": 0.0595,
    "P_compression": 0.0055,
}


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "displacement_proxy_raw" not in df and "secondary_vertex_count" in df:
        df["displacement_proxy_raw"] = df["secondary_vertex_count"]
    if "compression_proxy_raw" not in df:
        df["compression_proxy_raw"] = np.log1p(df["MET_pt"].clip(lower=0)) - np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1)
    return df


def scale_constants(real: pd.DataFrame) -> dict:
    real = prepare(real)
    cols = sorted({v for vals in FAMILIES.values() for v in vals if v in real})
    rows = []
    for col in cols:
        s = pd.to_numeric(real[col], errors="coerce")
        rows.append({"variable": col, "mean": s.mean(), "std": s.std(ddof=0)})
    return {r["variable"]: (r["mean"], r["std"]) for r in rows}, pd.DataFrame(rows)


def z_with_constants(s: pd.Series, constants: tuple[float, float]) -> pd.Series:
    mean, std = constants
    s = pd.to_numeric(s, errors="coerce")
    return (s - mean) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def score(df: pd.DataFrame, constants: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = prepare(df)
    availability = []
    total = pd.Series(0.0, index=df.index)
    for fam, variables in FAMILIES.items():
        available = [v for v in variables if v in df and v in constants and df[v].notna().any()]
        missing = [v for v in variables if v not in df or v not in constants or not df[v].notna().any()]
        fam_score = pd.concat([z_with_constants(df[v], constants[v]) for v in available], axis=1).mean(axis=1) if available else pd.Series(np.nan, index=df.index)
        df[f"B_{fam}"] = fam_score
        if available:
            total += WEIGHTS[fam] * fam_score.fillna(0)
        availability.append({"parameter_family": fam, "available": bool(available), "available_variables": ";".join(available), "missing_variables": ";".join(missing), "weight": WEIGHTS[fam]})
    df["B_NF_fitted_frozen_raw"] = total
    df["B_NF_fitted_frozen_z_real_scaled"] = total
    return df, pd.DataFrame(availability)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    real = pd.read_csv(REAL_SCALE)
    constants, const_df = scale_constants(real)
    const_df.to_csv(TABLES / "bnf_real_scaling_constants.csv", index=False)
    inventory_rows, frames, availability_rows = [], [], []
    for sample in SAMPLES:
        path = sample["feature_path"]
        exists = path.exists()
        rows = 0
        if exists:
            df = pd.read_csv(path)
            rows = len(df)
            for key, value in sample.items():
                if key != "feature_path":
                    df[key] = value
            df["real_or_simulated"] = "simulated benchmark"
            df, avail = score(df, constants)
            frames.append(df)
            out = OUT_DIR / f"{sample['sample_id']}_events_with_BNF.csv"
            df.to_csv(out, index=False)
            avail.insert(0, "sample_id", sample["sample_id"])
            availability_rows.append(avail)
        inventory_rows.append({
            "sample_id": sample["sample_id"],
            "record_id": sample["record_id"],
            "local_path": str(path),
            "file_count": 1 if exists else 0,
            "size_bytes": path.stat().st_size if exists else 0,
            "data_tier": "MiniAOD-derived features",
            "real_or_simulated": "simulated benchmark",
            "signal_background_real_classification": sample["classification"],
            "process_label": sample["process_label"],
            "suitability": "usable for frozen B_NF pilot" if exists else "missing",
            "cmssw_extraction_needed": False if exists else True,
            "already_processed_features_exist": exists,
            "events": rows,
        })
    inventory = pd.DataFrame(inventory_rows)
    inventory.to_csv(TABLES / "susy_relevance_local_data_inventory.csv", index=False)
    candidate = inventory.copy()
    candidate["priority"] = ["signal_high", "signal_high"]
    candidate["benchmark_role"] = ["SUSY-like gluino/missing-energy signal", "SUSY-like heavy-flavour signal"]
    candidate.to_csv(TABLES / "susy_relevance_candidate_benchmark_samples.csv", index=False)
    availability = pd.concat(availability_rows, ignore_index=True) if availability_rows else pd.DataFrame()
    availability.to_csv(TABLES / "susy_relevance_feature_availability_by_sample.csv", index=False)
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    combined_path = OUT_DIR / "susy_sm_benchmark_events_with_BNF.csv"
    combined.to_csv(combined_path, index=False)
    summary = combined.groupby(["sample_id", "classification", "process_label"], as_index=False).agg(events=("event", "count"), mean_BNF=("B_NF_fitted_frozen_raw", "mean"), median_BNF=("B_NF_fitted_frozen_raw", "median")) if not combined.empty else pd.DataFrame()
    summary.to_csv(TABLES / "susy_sm_benchmark_bnf_summary.csv", index=False)
    for name, title, body in [
        ("SUSY_RELEVANCE_LOCAL_DATA_AUDIT.md", "SUSY Relevance Local Data Audit", inventory),
        ("SUSY_RELEVANCE_BENCHMARK_SELECTION_PLAN.md", "SUSY Relevance Benchmark Selection Plan", candidate),
        ("SUSY_RELEVANCE_FEATURE_EXTRACTION_REPORT.md", "SUSY Relevance Feature Extraction Report", availability),
        ("SUSY_SM_BENCHMARK_BNF_APPLICATION_REPORT.md", "SUSY/SM Benchmark B_NF Application Report", summary),
    ]:
        report = [f"# {title}", "", "Date: 2026-06-09", "", body.to_markdown(index=False)]
        if name == "SUSY_RELEVANCE_BENCHMARK_SELECTION_PLAN.md":
            report.extend(["", "No local SM simulated background samples were found. ttbar and QCD MiniAOD/NanoAOD background samples are required before a true SUSY-vs-SM specificity ratio can be claimed."])
        (REPORTS / name).write_text("\n".join(report), encoding="utf-8")
    print(inventory.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
