from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_event_features_combined.csv"
OUTPUT = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_with_fitted_nframe_score.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
WEIGHTS = ROOT / "results" / "tables" / "nframe_fitted_boundary_equation_weights.csv"

FAMILIES = {
    "P_displacement_proxy": ["secondary_vertex_count", "displacement_proxy_raw"],
    "P_reconstruction": ["packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_multiplicity": ["N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["HT", "leading_jet_pt", "subleading_jet_pt"],
    "P_missing": ["MET_pt"],
    "P_compression": ["compression_proxy_raw"],
}


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    weights = pd.read_csv(WEIGHTS).set_index("family")["weight"].to_dict()
    df["displacement_proxy_raw"] = z(df["secondary_vertex_count"])
    df["compression_proxy_raw"] = z(np.log1p(df["MET_pt"].clip(lower=0))) - z(np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1))
    score = pd.Series(0.0, index=df.index)
    rows = []
    for fam, vars_ in FAMILIES.items():
        available = [v for v in vars_ if v in df and df[v].notna().any()]
        missing = [v for v in vars_ if v not in df or not df[v].notna().any()]
        fam_score = pd.concat([z(df[v]) for v in available], axis=1).mean(axis=1) if available else pd.Series(np.nan, index=df.index)
        df[f"expanded_{fam}"] = fam_score
        if available:
            score += weights.get(fam, 0) * fam_score.fillna(0)
        rows.append({"parameter_family": fam, "available": bool(available), "available_variables": ";".join(available), "missing_variables": ";".join(missing), "weight": weights.get(fam, 0)})
    df["B_NF_fitted_expanded_run2016h_raw"] = score
    df["B_NF_fitted_expanded_run2016h_z"] = z(score)
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        df[f"B_NF_fitted_expanded_run2016h_{label}"] = df["B_NF_fitted_expanded_run2016h_z"] >= df["B_NF_fitted_expanded_run2016h_z"].quantile(q)
    df.to_csv(OUTPUT, index=False)
    comp = pd.DataFrame(rows)
    comp.to_csv(TABLES / "expanded_run2016h_component_availability.csv", index=False)
    report = ["# Expanded Run2016H Fitted Boundary Scoring Report", "", "Date: 2026-06-09", "", "The existing fitted N-Frame equation was applied without refitting.", "", comp.to_markdown(index=False), "", f"Output: `{OUTPUT}`"]
    (REPORTS / "EXPANDED_RUN2016H_FITTED_BOUNDARY_SCORING_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(comp.to_string(index=False))
    print(OUTPUT)


if __name__ == "__main__":
    main()
