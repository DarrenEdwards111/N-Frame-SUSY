from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import FactorAnalysis, PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_trigger_filter_full" / "real_only_full_event_features_with_trigger_filter.csv"
OUTPUT = ROOT / "data" / "processed" / "cmssw_real_only_trigger_filter_full" / "real_only_full_event_features_with_trigger_filter_scored.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

FEATURES = [
    "log1p_MET_pt",
    "log1p_HT",
    "N_jets_30",
    "N_jets_50",
    "N_leptons",
    "N_btags_medium",
    "N_btags_tight",
    "max_btag_discriminator",
    "N_primary_vertices",
    "packed_candidate_count",
    "secondary_vertex_count",
    "compression_proxy_raw",
    "displacement_proxy_raw",
]


def z(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def mean_cols(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    cols = [c for c in cols if c in df and df[c].notna().any()]
    return df[cols].mean(axis=1, skipna=True) if cols else pd.Series(np.nan, index=df.index)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)

    for c in ["MET_pt", "HT", "leading_jet_pt", "subleading_jet_pt"]:
        df[f"log1p_{c}"] = np.log1p(pd.to_numeric(df[c], errors="coerce").clip(lower=0))
    df["compression_proxy_raw"] = z(df["log1p_MET_pt"]) - z(np.log1p(df["HT"].fillna(0) + df["leading_jet_pt"].fillna(0) + 1))
    df["displacement_proxy_raw"] = z(df["secondary_vertex_count"])

    zcols = {
        "MET_z": df["log1p_MET_pt"],
        "HT_z": df["log1p_HT"],
        "leading_jet_z": df["log1p_leading_jet_pt"],
        "subleading_jet_z": df["log1p_subleading_jet_pt"],
        "N_jets_30_z": df["N_jets_30"],
        "N_jets_50_z": df["N_jets_50"],
        "N_leptons_z": df["N_leptons"],
        "N_objects_z": df["N_jets_30"].fillna(0) + df["N_leptons"].fillna(0),
        "N_btags_loose_z": df["N_btags_loose"],
        "N_btags_medium_z": df["N_btags_medium"],
        "N_btags_tight_z": df["N_btags_tight"],
        "max_btag_discriminator_z": df["max_btag_discriminator"].replace(-999, np.nan),
        "N_primary_vertices_z": df["N_primary_vertices"],
        "packed_candidate_count_z": df["packed_candidate_count"],
        "secondary_vertex_count_z": df["secondary_vertex_count"],
        "compression_proxy_z": df["compression_proxy_raw"],
        "displacement_proxy_z": df["displacement_proxy_raw"],
    }
    for name, series in zcols.items():
        df[name] = z(series)

    comps = {
        "R_missing": ["MET_z"],
        "R_visible_energy": ["HT_z", "leading_jet_z", "subleading_jet_z"],
        "R_multiplicity": ["N_jets_30_z", "N_jets_50_z", "N_leptons_z", "N_objects_z", "packed_candidate_count_z"],
        "R_btag_structure": ["N_btags_loose_z", "N_btags_medium_z", "N_btags_tight_z", "max_btag_discriminator_z"],
        "R_reconstruction_complexity": ["N_primary_vertices_z", "packed_candidate_count_z", "secondary_vertex_count_z", "N_objects_z", "N_leptons_z", "N_btags_medium_z"],
        "R_compression_proxy": ["compression_proxy_z"],
        "R_displacement_proxy": ["displacement_proxy_z"],
    }
    avail = []
    for comp, cols in comps.items():
        df[comp] = mean_cols(df, cols)
        used = [c for c in cols if c in df and df[c].notna().any()]
        avail.append({"component": comp, "available_inputs": ";".join(used), "missing_fraction": df[comp].isna().mean()})

    component_cols = list(comps)
    df["available_component_count"] = df[component_cols].notna().sum(axis=1)
    df["B_boundary_hand_defined"] = df[component_cols].mean(axis=1, skipna=True)
    df["B_boundary_hand_defined_z"] = z(df["B_boundary_hand_defined"])
    for q, name in [(0.9, "10"), (0.95, "05"), (0.99, "01"), (0.999, "001")]:
        df[f"real_boundary_top_{name}"] = df["B_boundary_hand_defined"] >= df["B_boundary_hand_defined"].quantile(q)

    features = [c for c in FEATURES if c in df and df[c].notna().any()]
    X = df[features].replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))
    Xs = StandardScaler().fit_transform(X)

    pca = PCA(n_components=min(5, len(features)), random_state=42)
    pcs = pca.fit_transform(Xs)
    for i in range(pcs.shape[1]):
        df[f"trigger_filter_pca_axis_{i + 1}"] = pcs[:, i]
    loadings = []
    for i in range(pcs.shape[1]):
        for feature, loading in zip(features, pca.components_[i]):
            loadings.append({"axis": f"PC{i + 1}", "feature": feature, "loading": loading, "explained_variance_ratio": pca.explained_variance_ratio_[i]})

    fa = FactorAnalysis(n_components=min(3, len(features)), random_state=42)
    factors = fa.fit_transform(Xs)
    for i in range(factors.shape[1]):
        df[f"trigger_filter_factor_axis_{i + 1}"] = factors[:, i]

    iso = IsolationForest(n_estimators=160, contamination=0.05, random_state=42, n_jobs=-1, max_samples=60000)
    df["trigger_filter_isolation_anomaly_score_raw"] = -iso.fit(Xs).score_samples(Xs)
    df["trigger_filter_isolation_anomaly_score_z"] = z(df["trigger_filter_isolation_anomaly_score_raw"])
    df["trigger_filter_unsupervised_boundary_score"] = z(
        0.70 * df["trigger_filter_isolation_anomaly_score_z"].fillna(0)
        + 0.30 * z(df["trigger_filter_pca_axis_1"]).abs().fillna(0)
    )
    for q, name in [(0.9, "10"), (0.95, "05"), (0.99, "01"), (0.999, "001")]:
        df[f"trigger_filter_unsup_top_{name}"] = df["trigger_filter_unsupervised_boundary_score"] >= df["trigger_filter_unsupervised_boundary_score"].quantile(q)

    km = MiniBatchKMeans(n_clusters=8, random_state=42, batch_size=20000, n_init=10)
    df["trigger_filter_kmeans_cluster"] = km.fit_predict(Xs)

    summary = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(
        events=("event", "count"),
        mean_boundary_z=("B_boundary_hand_defined_z", "mean"),
        top05_frac=("real_boundary_top_05", "mean"),
        mean_unsup_boundary=("trigger_filter_unsupervised_boundary_score", "mean"),
        unsup_top05_frac=("trigger_filter_unsup_top_05", "mean"),
    )
    pd.DataFrame(avail).to_csv(TABLES / "trigger_filter_boundary_component_availability.csv", index=False)
    pd.DataFrame(loadings).to_csv(TABLES / "trigger_filter_pca_loadings.csv", index=False)
    summary.to_csv(TABLES / "trigger_filter_boundary_summary_by_sample.csv", index=False)
    df.to_csv(OUTPUT, index=False)

    report = [
        "# Trigger/Filter Boundary Rescoring Report",
        "",
        "Date: 2026-06-08",
        "",
        "The boundary scores were recomputed on the full real CMS collision table with trigger/filter diagnostics present. Trigger/filter flags were not used as score inputs; they are reserved for later interpretation.",
        "",
        "## Sample Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Boundary Components",
        "",
        pd.DataFrame(avail).to_markdown(index=False),
    ]
    (REPORTS / "TRIGGER_FILTER_BOUNDARY_RESCORING_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
