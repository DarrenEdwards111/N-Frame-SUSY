from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import FactorAnalysis, PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_scored.csv"
OUTPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
FEATURES = ["log1p_MET_pt", "log1p_HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "N_btags_tight", "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count", "compression_proxy_raw", "displacement_proxy_raw"]


def z(s):
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    features = [c for c in FEATURES if c in df and df[c].notna().any()]
    X = df[features].replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=min(5, len(features)), random_state=42)
    pcs = pca.fit_transform(Xs)
    for i in range(pcs.shape[1]):
        df[f"real_only_full_pca_axis_{i+1}"] = pcs[:, i]
    loadings = []
    for i in range(pcs.shape[1]):
        for feature, loading in zip(features, pca.components_[i]):
            loadings.append({"axis": f"PC{i+1}", "feature": feature, "loading": loading, "explained_variance_ratio": pca.explained_variance_ratio_[i]})
    load_df = pd.DataFrame(loadings)
    load_df.to_csv(TABLES / "real_only_full_pca_loadings.csv", index=False)
    fa = FactorAnalysis(n_components=min(3, len(features)), random_state=42)
    factors = fa.fit_transform(Xs)
    for i in range(factors.shape[1]):
        df[f"real_only_full_factor_axis_{i+1}"] = factors[:, i]
    iso = IsolationForest(n_estimators=160, contamination=0.05, random_state=42, n_jobs=-1, max_samples=60000)
    df["real_only_full_isolation_anomaly_score_raw"] = -iso.fit(Xs).score_samples(Xs)
    df["real_only_full_isolation_anomaly_score_z"] = z(df["real_only_full_isolation_anomaly_score_raw"])
    df["real_only_full_unsupervised_boundary_score"] = z(
        0.70 * df["real_only_full_isolation_anomaly_score_z"].fillna(0)
        + 0.30 * z(df["real_only_full_pca_axis_1"]).abs().fillna(0)
    )
    for q, name in [(0.9, "10"), (0.95, "05"), (0.99, "01"), (0.999, "001")]:
        df[f"real_only_full_unsup_top_{name}"] = df["real_only_full_unsupervised_boundary_score"] >= df["real_only_full_unsupervised_boundary_score"].quantile(q)
    km = MiniBatchKMeans(n_clusters=8, random_state=42, batch_size=20000, n_init=10)
    df["real_only_full_kmeans_cluster"] = km.fit_predict(Xs)
    summary = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(
        events=("event", "count"), mean_unsup_boundary=("real_only_full_unsupervised_boundary_score", "mean"),
        median_unsup_boundary=("real_only_full_unsupervised_boundary_score", "median"), top10_frac=("real_only_full_unsup_top_10", "mean"),
        top05_frac=("real_only_full_unsup_top_05", "mean"), top01_frac=("real_only_full_unsup_top_01", "mean"), top001_frac=("real_only_full_unsup_top_001", "mean"),
    )
    summary.to_csv(TABLES / "real_only_full_unsupervised_summary_by_sample.csv", index=False)
    cluster = df.groupby(["real_only_full_kmeans_cluster", "sample_id"], as_index=False).agg(
        events=("event", "count"), mean_MET_pt=("MET_pt", "mean"), mean_HT=("HT", "mean"), mean_boundary=("real_only_full_unsupervised_boundary_score", "mean"),
        mean_N_jets_30=("N_jets_30", "mean"), mean_N_leptons=("N_leptons", "mean"), mean_N_btags_medium=("N_btags_medium", "mean"),
    )
    cluster.to_csv(TABLES / "real_only_full_cluster_summary.csv", index=False)
    df.to_csv(OUTPUT, index=False)
    report = ["# Real-Only Full Unsupervised Boundary Model Report", "", "Date: 2026-06-08", "", "This full model uses only real CMS collision events.", "", "## Features", "", ", ".join(f"`{f}`" for f in features), "", "## Sample Summary", "", summary.to_markdown(index=False), "", "## Leading PCA Loadings", "", load_df.assign(abs_loading=lambda d: d.loading.abs()).sort_values(["axis", "abs_loading"], ascending=[True, False]).groupby("axis").head(8).to_markdown(index=False)]
    (REPORTS / "REAL_ONLY_FULL_UNSUPERVISED_BOUNDARY_MODEL_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
