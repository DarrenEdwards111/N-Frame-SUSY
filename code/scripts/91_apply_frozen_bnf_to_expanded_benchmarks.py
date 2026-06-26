from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
OUT = ROOT / "data" / "processed" / "expanded_benchmark_features"
NEW = OUT / "expanded_benchmark_event_features.csv"
OLD_SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
OLD_SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
REAL = ROOT / "data" / "processed" / "matched_control" / "standard_quality_clean_events.csv"
DATE = "2026-06-09"

FAMILIES = {
    "P_displacement_proxy": ["secondary_vertex_count", "displacement_proxy_raw"],
    "P_reconstruction": ["packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_multiplicity": ["N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["HT", "leading_jet_pt", "subleading_jet_pt"],
    "P_missing": ["MET_pt"],
    "P_compression": ["compression_proxy_raw"],
}
WEIGHTS = {"P_displacement_proxy": .3566, "P_reconstruction": .2112, "P_multiplicity": .2019, "P_btag_structure": .0926, "P_visible_energy": .0728, "P_missing": .0595, "P_compression": .0055}


def prepare(df):
    df = df.copy()
    if "displacement_proxy_raw" not in df and "secondary_vertex_count" in df:
        df["displacement_proxy_raw"] = df["secondary_vertex_count"]
    if "compression_proxy_raw" not in df:
        df["compression_proxy_raw"] = np.log1p(df["MET_pt"].clip(lower=0)) - np.log1p(df["HT"].fillna(0) + df.get("leading_jet_pt", 0).fillna(0) + 1)
    return df


def constants():
    real = prepare(pd.read_csv(REAL))
    cols = sorted({v for vals in FAMILIES.values() for v in vals if v in real})
    return {c: (pd.to_numeric(real[c], errors="coerce").mean(), pd.to_numeric(real[c], errors="coerce").std(ddof=0)) for c in cols}


def z(s, const):
    mean, std = const
    s = pd.to_numeric(s, errors="coerce")
    return (s - mean) / std if std else pd.Series(np.nan, index=s.index)


def score(df, const):
    df = prepare(df)
    availability = []
    total = pd.Series(0.0, index=df.index)
    for fam, variables in FAMILIES.items():
        avail = [v for v in variables if v in df and v in const and df[v].notna().any()]
        miss = [v for v in variables if v not in df or v not in const or not df[v].notna().any()]
        fam_score = pd.concat([z(df[v], const[v]) for v in avail], axis=1).mean(axis=1) if avail else pd.Series(np.nan, index=df.index)
        df[f"B_{fam}"] = fam_score
        if avail:
            total += WEIGHTS[fam] * fam_score.fillna(0)
        availability.append({"sample_id": df["sample_id"].iloc[0], "process_label": df["process_label"].iloc[0], "parameter_family": fam, "available": bool(avail), "available_variables": ";".join(avail), "missing_variables": ";".join(miss), "weight": WEIGHTS[fam]})
    df["B_NF_fitted_frozen_raw"] = total
    df["B_NF_fitted_frozen_z_real_scaled"] = total
    df["component_mode"] = np.where(df[[f"B_{f}" for f in FAMILIES]].notna().all(axis=1), "full-component", "reduced-component")
    return df, pd.DataFrame(availability)


def main():
    const = constants()
    frames = []
    avails = []
    new = pd.read_csv(NEW)
    for _, g in new.groupby("sample_id"):
        scored, avail = score(g, const)
        frames.append(scored)
        avails.append(avail)
    existing = []
    for p in [OLD_SUSY, OLD_SM]:
        if p.exists():
            existing.append(pd.read_csv(p))
    combined = pd.concat(existing + frames, ignore_index=True, sort=False)
    combined.to_csv(OUT / "expanded_benchmark_events_with_BNF.csv", index=False)
    availability = pd.concat(avails, ignore_index=True)
    availability.to_csv(TABLES / "expanded_benchmark_feature_availability.csv", index=False)
    summary = combined.groupby(["sample_id", "process_label", "classification"], as_index=False).agg(events=("event", "count"), mean_BNF=("B_NF_fitted_frozen_raw", "mean"), median_BNF=("B_NF_fitted_frozen_raw", "median"))
    summary.to_csv(TABLES / "expanded_benchmark_bnf_summary.csv", index=False)
    (REPORTS / "EXPANDED_BENCHMARK_BNF_APPLICATION_REPORT.md").write_text("# Expanded Benchmark B_NF Application Report\n\nFrozen B_NF equation was applied without refitting. New NanoAODSIM samples are reduced-component where packed candidates are unavailable.\n\n" + summary.to_markdown(index=False), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
