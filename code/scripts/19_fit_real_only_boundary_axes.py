from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import FactorAnalysis, PCA
from sklearn.ensemble import IsolationForest
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_scored.csv"
OUTPUT = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_with_unsupervised_boundary.csv"
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


def zscore(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(np.nan, index=s.index)
    return (s - s.mean()) / std


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    features = [c for c in FEATURES if c in df.columns and df[c].notna().any()]
    X = df[features].replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    pca = PCA(n_components=min(5, len(features)), random_state=42)
    pcs = pca.fit_transform(Xs)
    for i in range(pcs.shape[1]):
        df[f"real_only_pca_axis_{i+1}"] = pcs[:, i]

    loadings = []
    for pc_idx in range(pcs.shape[1]):
        for feature, loading in zip(features, pca.components_[pc_idx]):
            loadings.append({
                "axis": f"PC{pc_idx+1}",
                "feature": feature,
                "loading": loading,
                "explained_variance_ratio": pca.explained_variance_ratio_[pc_idx],
            })
    loadings_df = pd.DataFrame(loadings)
    loadings_df.to_csv(TABLES / "real_only_pca_boundary_loadings.csv", index=False)

    fa = FactorAnalysis(n_components=min(3, len(features)), random_state=42)
    factors = fa.fit_transform(Xs)
    for i in range(factors.shape[1]):
        df[f"real_only_factor_axis_{i+1}"] = factors[:, i]

    iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42, n_jobs=-1)
    df["real_only_isolation_anomaly_score_raw"] = -iso.fit(Xs).score_samples(Xs)
    df["real_only_isolation_anomaly_score_z"] = zscore(df["real_only_isolation_anomaly_score_raw"])

    # LOF is useful but expensive; 150k rows is acceptable with a moderate neighbourhood.
    lof = LocalOutlierFactor(n_neighbors=35, contamination=0.05, n_jobs=-1)
    lof.fit_predict(Xs)
    df["real_only_lof_anomaly_score_raw"] = -lof.negative_outlier_factor_
    df["real_only_lof_anomaly_score_z"] = zscore(df["real_only_lof_anomaly_score_raw"])

    df["real_only_unsupervised_boundary_score"] = zscore(
        0.50 * df["real_only_isolation_anomaly_score_z"].fillna(0)
        + 0.25 * df["real_only_lof_anomaly_score_z"].fillna(0)
        + 0.25 * zscore(df["real_only_pca_axis_1"]).abs().fillna(0)
    )

    for q, name in [(0.90, "10"), (0.95, "05"), (0.99, "01"), (0.999, "001")]:
        threshold = df["real_only_unsupervised_boundary_score"].quantile(q)
        df[f"real_only_unsup_top_{name}"] = df["real_only_unsupervised_boundary_score"] >= threshold

    kmeans = KMeans(n_clusters=6, random_state=42, n_init=20)
    df["real_only_kmeans_cluster"] = kmeans.fit_predict(Xs)
    gm = GaussianMixture(n_components=6, random_state=42, covariance_type="diag")
    df["real_only_gmm_cluster"] = gm.fit_predict(Xs)

    anomaly_summary = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(
        events=("event", "count"),
        mean_unsup_boundary=("real_only_unsupervised_boundary_score", "mean"),
        median_unsup_boundary=("real_only_unsupervised_boundary_score", "median"),
        top10_frac=("real_only_unsup_top_10", "mean"),
        top05_frac=("real_only_unsup_top_05", "mean"),
        top01_frac=("real_only_unsup_top_01", "mean"),
        top001_frac=("real_only_unsup_top_001", "mean"),
    )
    anomaly_summary.to_csv(TABLES / "real_only_anomaly_score_summary_by_sample.csv", index=False)

    cluster_summary = df.groupby(["real_only_kmeans_cluster", "sample_id"], as_index=False).agg(
        events=("event", "count"),
        mean_MET_pt=("MET_pt", "mean"),
        mean_HT=("HT", "mean"),
        mean_N_jets_30=("N_jets_30", "mean"),
        mean_N_leptons=("N_leptons", "mean"),
        mean_N_btags_medium=("N_btags_medium", "mean"),
        mean_unsup_boundary=("real_only_unsupervised_boundary_score", "mean"),
    )
    cluster_summary.to_csv(TABLES / "real_only_cluster_summary.csv", index=False)

    df.to_csv(OUTPUT, index=False)

    report = [
        "# Real-Only Unsupervised Boundary Model Report",
        "",
        "Date: 2026-06-08",
        "",
        "This model uses only real CMS collision events. No simulated samples or signal labels are used.",
        "",
        "## Methods",
        "",
        "- PCA on standardised event/boundary variables.",
        "- FactorAnalysis on the same real-only feature space.",
        "- IsolationForest and LocalOutlierFactor for rare-event boundary scoring.",
        "- KMeans and GaussianMixture clustering to group event families.",
        "",
        "## Features Used",
        "",
        ", ".join(f"`{f}`" for f in features),
        "",
        "## PCA Axes",
        "",
        loadings_df.sort_values(["axis", "loading"], ascending=[True, False]).groupby("axis").head(8).to_markdown(index=False),
        "",
        "## Anomaly Summary By Sample",
        "",
        anomaly_summary.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "The unsupervised boundary score estimates rare structure inside real collision data only. It is a map of unusual real event conditions, not evidence for a new particle.",
    ]
    (REPORTS / "REAL_ONLY_UNSUPERVISED_BOUNDARY_MODEL_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(anomaly_summary.to_string(index=False))


if __name__ == "__main__":
    main()
