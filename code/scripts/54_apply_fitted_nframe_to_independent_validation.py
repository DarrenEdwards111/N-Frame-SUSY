from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MINIAOD_INPUT = ROOT / "data" / "processed" / "independent_validation_miniaod" / "validation_miniaod_event_features.csv"
NANOAOD_INPUT = ROOT / "data" / "processed" / "independent_validation_nanoaod" / "validation_nanoaod_event_features.csv"
OUT_DIR = ROOT / "data" / "processed" / "nframe_validation_real_independent"
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
MAJOR = ["P_displacement_proxy", "P_reconstruction", "P_multiplicity", "P_btag_structure", "P_visible_energy", "P_missing"]


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    input_path = MINIAOD_INPUT if MINIAOD_INPUT.exists() else NANOAOD_INPUT
    df = pd.read_csv(input_path)
    weights = pd.read_csv(WEIGHTS).set_index("family")["weight"].to_dict()
    if "displacement_proxy_raw" not in df and "secondary_vertex_count" in df:
        df["displacement_proxy_raw"] = z(df["secondary_vertex_count"])
    if "compression_proxy_raw" not in df:
        df["compression_proxy_raw"] = z(np.log1p(df["MET_pt"].clip(lower=0))) - z(np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1))
    availability = []
    full_score = pd.Series(0.0, index=df.index)
    available_score = pd.Series(0.0, index=df.index)
    available_abs_weight = 0.0
    all_major_available = True
    for fam, vars_ in FAMILIES.items():
        available = [v for v in vars_ if v in df and df[v].notna().any()]
        missing = [v for v in vars_ if v not in df or not df[v].notna().any()]
        fam_series = pd.concat([z(df[v]) for v in available], axis=1).mean(axis=1) if available else pd.Series(np.nan, index=df.index)
        df[f"validation_{fam}"] = fam_series
        availability.append({"parameter_family": fam, "available": bool(available), "available_variables": ";".join(available), "missing_variables": ";".join(missing), "weight": weights.get(fam, 0)})
        if fam in MAJOR and not available:
            all_major_available = False
        if available:
            full_score = full_score + weights.get(fam, 0) * fam_series.fillna(0)
            available_score = available_score + weights.get(fam, 0) * fam_series.fillna(0)
            available_abs_weight += abs(weights.get(fam, 0))
    df["B_NF_fitted_validation_raw"] = full_score if all_major_available else np.nan
    df["B_NF_fitted_validation_z"] = z(full_score) if all_major_available else np.nan
    df["B_NF_available_components_only_raw"] = available_score / available_abs_weight if available_abs_weight else np.nan
    df["B_NF_available_components_only_z"] = z(df["B_NF_available_components_only_raw"])
    # Reduced sensitivity scores, explicitly omitting named component families and renormalising remaining weights.
    for omitted in ["P_displacement_proxy", "P_reconstruction"]:
        score = pd.Series(0.0, index=df.index)
        denom = 0.0
        for fam in FAMILIES:
            if fam == omitted or df[f"validation_{fam}"].isna().all():
                continue
            score += weights.get(fam, 0) * df[f"validation_{fam}"].fillna(0)
            denom += abs(weights.get(fam, 0))
        df[f"B_NF_reduced_no_{omitted.replace('P_', '')}_z"] = z(score / denom) if denom else np.nan
    score_col = "B_NF_fitted_validation_z" if all_major_available else "B_NF_available_components_only_z"
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        df[f"{score_col}_{label}"] = df[score_col] >= df[score_col].quantile(q)
    out = OUT_DIR / "validation_events_with_fitted_boundary_score.csv"
    df.to_csv(out, index=False)
    avail = pd.DataFrame(availability)
    avail.to_csv(TABLES / "validation_fitted_boundary_component_availability.csv", index=False)
    report = [
        "# Validation Fitted Boundary Scoring Report",
        "",
        "Date: 2026-06-09",
        "",
        f"The fitted N-Frame boundary equation was applied to independent Run2016H real collision events from `{input_path}`. No unavailable components were silently set to zero.",
        "",
        f"Primary score column: `{score_col}`",
        "",
        "## Component Availability",
        "",
        avail.to_markdown(index=False),
        "",
        f"Output: `{out}`",
    ]
    (REPORTS / "VALIDATION_FITTED_BOUNDARY_SCORING_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(avail.to_string(index=False))
    print(out)


if __name__ == "__main__":
    main()
