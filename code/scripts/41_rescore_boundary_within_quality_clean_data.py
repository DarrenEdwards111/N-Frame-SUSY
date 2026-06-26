from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "data" / "processed" / "matched_control"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def mean_cols(df, cols):
    cols = [c for c in cols if c in df and df[c].notna().any()]
    return df[cols].mean(axis=1, skipna=True) if cols else pd.Series(np.nan, index=df.index)


def rescore(path: Path, subset: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "real_only_unsupervised_boundary_score" not in df and "trigger_filter_unsupervised_boundary_score" in df:
        df["real_only_unsupervised_boundary_score"] = df["trigger_filter_unsupervised_boundary_score"]
    for c in ["MET_pt", "HT", "leading_jet_pt", "subleading_jet_pt"]:
        if f"log1p_{c}" not in df:
            df[f"log1p_{c}"] = np.log1p(pd.to_numeric(df[c], errors="coerce").clip(lower=0))
    df["mc_compression_proxy_raw"] = z(df["log1p_MET_pt"]) - z(np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1))
    df["mc_displacement_proxy_raw"] = z(df["secondary_vertex_count"])
    for name, series in {
        "mc_MET_z": df["log1p_MET_pt"], "mc_HT_z": df["log1p_HT"], "mc_leading_jet_z": df["log1p_leading_jet_pt"],
        "mc_subleading_jet_z": df["log1p_subleading_jet_pt"], "mc_N_jets_30_z": df["N_jets_30"], "mc_N_jets_50_z": df["N_jets_50"],
        "mc_N_leptons_z": df["N_leptons"], "mc_N_objects_z": df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0),
        "mc_N_btags_loose_z": df.get("N_btags_loose", 0), "mc_N_btags_medium_z": df["N_btags_medium"],
        "mc_N_btags_tight_z": df.get("N_btags_tight", 0), "mc_max_btag_discriminator_z": df["max_btag_discriminator"].replace(-999, np.nan),
        "mc_N_primary_vertices_z": df["N_primary_vertices"], "mc_packed_candidate_count_z": df["packed_candidate_count"],
        "mc_secondary_vertex_count_z": df["secondary_vertex_count"], "mc_compression_proxy_z": df["mc_compression_proxy_raw"],
        "mc_displacement_proxy_z": df["mc_displacement_proxy_raw"],
    }.items():
        df[name] = z(series)
    comps = {
        "mc_R_missing": ["mc_MET_z"],
        "mc_R_visible_energy": ["mc_HT_z", "mc_leading_jet_z", "mc_subleading_jet_z"],
        "mc_R_multiplicity": ["mc_N_jets_30_z", "mc_N_jets_50_z", "mc_N_leptons_z", "mc_N_objects_z", "mc_packed_candidate_count_z"],
        "mc_R_btag_structure": ["mc_N_btags_loose_z", "mc_N_btags_medium_z", "mc_N_btags_tight_z", "mc_max_btag_discriminator_z"],
        "mc_R_reconstruction_complexity": ["mc_N_primary_vertices_z", "mc_packed_candidate_count_z", "mc_secondary_vertex_count_z", "mc_N_objects_z", "mc_N_leptons_z", "mc_N_btags_medium_z"],
        "mc_R_compression_proxy": ["mc_compression_proxy_z"],
        "mc_R_displacement_proxy": ["mc_displacement_proxy_z"],
    }
    for comp, cols in comps.items():
        df[comp] = mean_cols(df, cols)
    df["mc_B_boundary_hand_defined"] = df[list(comps)].mean(axis=1, skipna=True)
    df["mc_B_boundary_hand_defined_z"] = z(df["mc_B_boundary_hand_defined"])
    feats = ["log1p_MET_pt", "log1p_HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count", "mc_compression_proxy_raw", "mc_displacement_proxy_raw"]
    X = df[[c for c in feats if c in df]].replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))
    Xs = StandardScaler().fit_transform(X)
    iso = IsolationForest(n_estimators=120, contamination=0.05, random_state=42, n_jobs=-1, max_samples=60000)
    df["mc_unsupervised_boundary_score"] = z(-iso.fit(Xs).score_samples(Xs))
    for score in ["mc_B_boundary_hand_defined_z", "mc_unsupervised_boundary_score", "B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score"]:
        for q, label in [(0.9, "top10"), (0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
            df[f"{score}_{label}"] = df[score] >= df[score].quantile(q)
    df["quality_subset"] = subset
    return df


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    outputs = {
        "standard_quality_clean": IN / "standard_quality_clean_events_rescored.csv",
        "relaxed_quality_clean": IN / "relaxed_quality_clean_events_rescored.csv",
    }
    rows, enrich = [], []
    for subset, src in {
        "standard_quality_clean": IN / "standard_quality_clean_events.csv",
        "relaxed_quality_clean": IN / "relaxed_quality_clean_events.csv",
    }.items():
        df = rescore(src, subset)
        df.to_csv(outputs[subset], index=False)
        for score in ["mc_B_boundary_hand_defined_z", "mc_unsupervised_boundary_score"]:
            rows.append({"subset": subset, "score": score, "events": len(df), "mean": df[score].mean(), "p95": df[score].quantile(.95), "p99": df[score].quantile(.99), "p999": df[score].quantile(.999)})
            base = df.primary_dataset.value_counts(normalize=True)
            for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
                tail = df[df[score] >= df[score].quantile(q)]
                for ds, frac in tail.primary_dataset.value_counts(normalize=True).items():
                    enrich.append({"subset": subset, "score": score, "tail": label, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base.get(ds, 0), "enrichment_ratio": frac / base.get(ds, 1), "events": int((tail.primary_dataset == ds).sum())})
    summary = pd.DataFrame(rows)
    enrichment = pd.DataFrame(enrich)
    summary.to_csv(TABLES / "quality_clean_boundary_summary_by_sample.csv", index=False)
    enrichment.to_csv(TABLES / "quality_clean_tail_enrichment.csv", index=False)
    report = ["# Quality-Clean Boundary Rescoring Report", "", "Date: 2026-06-08", "", "Boundary z-scores and quantile tails were recomputed within each quality-clean subset.", "", "## Summary", "", summary.to_markdown(index=False), "", "## Tail Enrichment", "", enrichment.to_markdown(index=False)]
    (REPORTS / "QUALITY_CLEAN_BOUNDARY_RESCORING_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
