from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
TRACE = ROOT / "data" / "processed" / "trace_direction"
DATE = "2026-06-09"
CANDIDATES = [TABLES / "top_real_trace_candidates_run2016g.csv", TABLES / "top_real_trace_candidates_run2016h.csv", TABLES / "top_real_trace_candidates_combined.csv"]
FULL = TRACE / "combined_real_with_trace_distances.csv"


def q(df: pd.DataFrame, col: str, p: float) -> float:
    return float(df[col].quantile(p)) if col in df else np.nan


def main() -> None:
    full = pd.read_csv(FULL, low_memory=False)
    cand = pd.concat([pd.read_csv(p).assign(candidate_set=p.stem.replace("top_real_trace_candidates_", "")) for p in CANDIDATES], ignore_index=True)
    thresholds = {col: {p: q(full, col, p) for p in [.90, .95, .99, .999]} for col in [
        "B_NF_trace_base", "Trace_sms_vs_pooledSM", "MET_pt", "HT", "N_jets_30",
        "N_btags_medium", "secondary_vertex_count", "packed_candidate_count",
        "real_displacement_reconstruction_axis"
    ] if col in full}
    source_counts = cand.groupby("source_file").size()
    run_counts = cand.groupby("run").size()
    lumi_counts = cand.groupby(["run", "lumi"]).size()

    df = cand.copy()
    passq = df.get("passes_available_quality_filters", pd.Series(True, index=df.index)).fillna(True).astype(bool)
    df["fails_any_available_quality_filter"] = ~passq
    df["missing_quality_filter_info"] = "passes_available_quality_filters" not in df.columns
    for name in ["HBHENoiseFilter", "HBHENoiseIsoFilter", "goodVertices", "EcalDeadCellTriggerPrimitiveFilter", "BadPFMuonFilter", "globalSuperTightHalo2016Filter"]:
        df[f"fails_{name}"] = False
    df["trigger_category_MET"] = df["primary_dataset"].astype(str).str.contains("MET", case=False, na=False)
    df["trigger_category_HT"] = df["primary_dataset"].astype(str).str.contains("JetHT|HT", case=False, na=False)
    df["trigger_category_Mu"] = df["primary_dataset"].astype(str).str.contains("Muon", case=False, na=False)
    df["trigger_category_Ele"] = df["primary_dataset"].astype(str).str.contains("Electron|EGamma", case=False, na=False)
    df["source_file_overconcentration_flag"] = df["source_file"].map(source_counts).fillna(0) >= 10
    df["run_overconcentration_flag"] = df["run"].map(run_counts).fillna(0) >= 10
    df["lumi_overconcentration_flag"] = [lumi_counts.get((r, l), 0) >= 3 for r, l in zip(df["run"], df["lumi"])]
    df["candidate_from_previously_suspect_run_or_file"] = False

    df["high_MET"] = df["MET_pt"] >= thresholds["MET_pt"][.90]
    df["extreme_MET"] = df["MET_pt"] >= thresholds["MET_pt"][.99]
    df["high_HT"] = df["HT"] >= thresholds["HT"][.90]
    df["extreme_HT"] = df["HT"] >= thresholds["HT"][.99]
    df["high_jet_multiplicity"] = df["N_jets_30"] >= thresholds["N_jets_30"][.90]
    df["extreme_jet_multiplicity"] = df["N_jets_30"] >= thresholds["N_jets_30"][.99]
    df["high_btag_structure"] = df["N_btags_medium"] >= thresholds["N_btags_medium"][.90]
    df["high_secondary_vertex_proxy"] = df["secondary_vertex_count"] >= thresholds["secondary_vertex_count"][.90]
    df["high_reconstruction_complexity"] = df["packed_candidate_count"] >= thresholds["packed_candidate_count"][.90]
    df["high_visible_recoil"] = df["HT"] >= thresholds["HT"][.90]
    df["high_missing_plus_visible"] = df["high_MET"] & df["high_HT"]
    df["high_missing_plus_multiplicity"] = df["high_MET"] & df["high_jet_multiplicity"]
    df["isolated_single_lepton_like"] = df["N_leptons"].eq(1)
    df["multilepton_like"] = df["N_leptons"] >= 2
    df["fully_hadronic_like"] = df["N_leptons"].eq(0)
    df["low_lepton_high_MET_like"] = (df["N_leptons"] <= 1) & df["high_MET"]
    df["high_btag_top_like"] = (df["N_btags_medium"] >= 1) & (df["N_jets_30"] >= 4)
    df["QCD_like_high_HT_low_MET"] = df["high_HT"] & (df["MET_pt"] < thresholds["MET_pt"][.50] if .50 in thresholds.get("MET_pt", {}) else df["MET_pt"] < full["MET_pt"].median()) & df["fully_hadronic_like"]
    df["SMS_trace_like_high_MET_HT_mult"] = df["high_MET"] & df["high_HT"] & df["high_jet_multiplicity"]

    df["top_1pct_BNF"] = df["B_NF_trace_base"] >= thresholds["B_NF_trace_base"][.99]
    df["top_0p1pct_BNF"] = df["B_NF_trace_base"] >= thresholds["B_NF_trace_base"][.999]
    df["high_trace_direction_score"] = df["Trace_sms_vs_pooledSM"] >= thresholds["Trace_sms_vs_pooledSM"][.90]
    df["high_BNF_and_high_trace"] = df["top_1pct_BNF"] & df["high_trace_direction_score"]
    df["closer_to_SMS_than_pooledSM"] = df["distance_to_SMS"] < df["distance_to_pooledSM"]
    df["closer_to_TTJets_than_SMS"] = df["distance_to_TTJets"] < df["distance_to_SMS"]
    df["closer_to_QCD_than_SMS"] = df["distance_to_QCD"] < df["distance_to_SMS"]
    df["SM_centroid_like"] = df[["distance_to_TTJets", "distance_to_QCD", "distance_to_pooledSM"]].min(axis=1) < df["distance_to_SMS"]
    df["trace_direction_aligned_but_SM_centroid_close"] = df["high_BNF_and_high_trace"] & df["SM_centroid_like"]

    out = TRACE / "top_trace_candidates_with_diagnostic_flags.csv"
    df.to_csv(out, index=False)
    bool_cols = [c for c in df.columns if df[c].dtype == bool]
    summary = pd.DataFrame([{"flag": c, "events": int(df[c].sum()), "fraction": float(df[c].mean())} for c in bool_cols]).sort_values("events", ascending=False)
    summary.to_csv(TABLES / "trace_candidate_flag_summary.csv", index=False)
    report = ["# Trace Candidate Diagnostic Flag Report", "", f"Date: {DATE}", "", "Thresholds are quantile-derived from the full combined real trace-distance table where possible.", "", summary.to_markdown(index=False)]
    (REPORTS / "TRACE_CANDIDATE_DIAGNOSTIC_FLAG_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
