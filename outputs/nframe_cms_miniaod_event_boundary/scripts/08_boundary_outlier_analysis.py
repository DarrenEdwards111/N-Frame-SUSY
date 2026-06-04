import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import MinCovDet
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from common import PROCESSED_DIR, TABLES_DIR, read_features, ensure_dirs


FEATURES = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_jets_50",
    "leading_jet_pt",
    "N_leptons",
    "N_btags_medium",
    "MET_fraction",
    "S_event_proxy",
    "B_event_jetonly_z",
    "B_event_z",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Find high-boundary event outliers without physics claims.")
    parser.add_argument("--input", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    parser.add_argument("--max-events", type=int, default=200000)
    args = parser.parse_args()

    ensure_dirs()
    df = read_features(Path(args.input)).head(args.max_events).copy()
    cols = [col for col in FEATURES if col in df.columns and df[col].notna().any()]
    x = df[cols].fillna(0)
    x_scaled = StandardScaler().fit_transform(x)
    df["isolation_score"] = -IsolationForest(n_estimators=200, contamination="auto", random_state=4).fit(x_scaled).score_samples(x_scaled)
    df["lof_score"] = -LocalOutlierFactor(n_neighbors=35, contamination="auto").fit_predict(x_scaled)
    try:
        mcd = MinCovDet(random_state=4, support_fraction=0.8).fit(x_scaled)
        df["robust_mahalanobis"] = mcd.mahalanobis(x_scaled)
    except Exception:
        df["robust_mahalanobis"] = np.nan
    df["boundary_outlier_score"] = (
        df["isolation_score"].rank(pct=True)
        + df["B_event_z"].rank(pct=True)
        + df["robust_mahalanobis"].fillna(0).rank(pct=True)
    )
    top = df.sort_values("boundary_outlier_score", ascending=False).head(max(100, int(0.001 * len(df))))
    top.to_csv(TABLES_DIR / "top_boundary_anomaly_events.csv", index=False)
    print(f"Wrote {len(top)} high-boundary event outliers to {TABLES_DIR / 'top_boundary_anomaly_events.csv'}")


if __name__ == "__main__":
    main()
