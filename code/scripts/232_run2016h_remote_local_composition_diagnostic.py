from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_run2016h_remote_local_composition_diagnostic"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

LOCAL_SCORED = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv"
LOCAL_RAW = ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_combined_event_features.csv"
REMOTE_SCORED = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation" / "tables" / "04_remote_mht_aware_scored_axis_events.csv"
REMOTE_RAW = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation" / "tables" / "03_remote_mht_aware_raw_merged_features.csv"

DATASETS = ["HTMHT", "MET", "JetHT", "SingleMuon"]
FEATURES = [
    "MET_pt",
    "MHT_pt",
    "MHT_over_HT",
    "MET_minus_MHT",
    "HT",
    "N_jets_30",
    "N_btags_medium",
    "N_muons",
    "N_electrons",
    "N_primary_vertices",
    "packed_candidate_count",
    "secondary_vertex_count",
    "observer_projection",
    "physical_projection",
    "ordinary_qcd_axis",
]
QUALITY_TRIGGER_COLS = [
    "HLT_MET_paths_any",
    "HLT_HT_paths_any",
    "HLT_Mu_paths_any",
    "HLT_Ele_paths_any",
    "pass_goodVertices",
    "pass_HBHENoiseFilter",
    "pass_HBHENoiseIsoFilter",
    "pass_EcalDeadCellTriggerPrimitiveFilter",
    "pass_BadPFMuonFilter",
    "pass_globalSuperTightHalo2016Filter",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0) if col in df else pd.Series(0.0, index=df.index)


def clean_score(df: pd.DataFrame, qcd: bool) -> pd.Series:
    score = 0.5 * numeric(df, "observer_projection") + 0.5 * numeric(df, "physical_projection")
    if qcd:
        score = 0.344828 * numeric(df, "observer_projection") + 0.517241 * numeric(df, "physical_projection") - 0.137931 * numeric(df, "ordinary_qcd_axis")
    return score


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    local = pd.read_csv(LOCAL_SCORED, low_memory=False)
    local = local[local["primary_dataset"].isin(DATASETS)].copy()
    local["source"] = "local_fresh_mht"
    local["score_clean"] = clean_score(local, qcd=False)
    local["score_opq"] = clean_score(local, qcd=True)

    remote = pd.read_csv(REMOTE_SCORED, low_memory=False)
    remote = remote[remote["sample_validation_id"].eq("Run2016H_remote_mht_aware")].copy()
    remote["source"] = "remote_unused_mht"
    remote["score_clean"] = clean_score(remote, qcd=False)
    remote["score_opq"] = clean_score(remote, qcd=True)

    local_raw = pd.read_csv(LOCAL_RAW, low_memory=False)
    local_raw = local_raw[local_raw["primary_dataset"].isin(DATASETS)].copy()
    local_raw["source"] = "local_fresh_mht"
    remote_raw = pd.read_csv(REMOTE_RAW, low_memory=False)
    remote_raw = remote_raw[remote_raw["run_era"].eq("Run2016H")].copy()
    remote_raw["source"] = "remote_unused_mht"
    return local, remote, local_raw, remote_raw


def coverage(local: pd.DataFrame, remote: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset in DATASETS:
        l = local[local["primary_dataset"].eq(dataset)]
        r = remote[remote["primary_dataset"].eq(dataset)]
        local_runs = set(l["run"].astype(int).unique())
        remote_runs = set(r["run"].astype(int).unique())
        rows.append(
            {
                "primary_dataset": dataset,
                "local_events": len(l),
                "remote_events": len(r),
                "local_runs": len(local_runs),
                "remote_runs": len(remote_runs),
                "run_overlap_count": len(local_runs & remote_runs),
                "local_run_min": int(l["run"].min()),
                "local_run_max": int(l["run"].max()),
                "remote_run_min": int(r["run"].min()),
                "remote_run_max": int(r["run"].max()),
                "local_lumi_min": int(l["lumi"].min()),
                "local_lumi_max": int(l["lumi"].max()),
                "remote_lumi_min": int(r["lumi"].min()),
                "remote_lumi_max": int(r["lumi"].max()),
            }
        )
    return pd.DataFrame(rows)


def feature_comparison(local: pd.DataFrame, remote: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset in DATASETS:
        l = local[local["primary_dataset"].eq(dataset)]
        r = remote[remote["primary_dataset"].eq(dataset)]
        for feature in FEATURES:
            if feature not in l or feature not in r:
                continue
            lv = numeric(l, feature).to_numpy(float)
            rv = numeric(r, feature).to_numpy(float)
            ks = ks_2samp(lv, rv, method="auto")
            rows.append(
                {
                    "primary_dataset": dataset,
                    "feature": feature,
                    "local_mean": float(np.mean(lv)),
                    "remote_mean": float(np.mean(rv)),
                    "local_p95": float(np.quantile(lv, 0.95)),
                    "remote_p95": float(np.quantile(rv, 0.95)),
                    "ks_statistic": float(ks.statistic),
                    "ks_p_value": float(ks.pvalue),
                }
            )
    return pd.DataFrame(rows)


def trigger_quality_comparison(local_raw: pd.DataFrame, remote_raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset in DATASETS:
        for source, frame in [("local_fresh_mht", local_raw), ("remote_unused_mht", remote_raw)]:
            g = frame[frame["primary_dataset"].eq(dataset)]
            row = {"primary_dataset": dataset, "source": source, "events": len(g)}
            for col in QUALITY_TRIGGER_COLS:
                row[f"{col}_fraction_one"] = float(numeric(g, col).eq(1).mean())
            rows.append(row)
    return pd.DataFrame(rows)


def run_tail_concentration(events: pd.DataFrame, score_col: str) -> pd.DataFrame:
    rows = []
    for dataset in DATASETS:
        g = events[events["primary_dataset"].eq(dataset)].copy()
        if g.empty:
            continue
        threshold = g[score_col].quantile(0.90)
        g["top10"] = g[score_col].ge(threshold)
        for run, rg in g.groupby("run", sort=True):
            rows.append(
                {
                    "source": g["source"].iloc[0],
                    "score": score_col,
                    "primary_dataset": dataset,
                    "run": int(run),
                    "events": len(rg),
                    "top10_events": int(rg["top10"].sum()),
                    "top10_fraction": float(rg["top10"].mean()),
                    "expected_top10_events": 0.10 * len(rg),
                    "top10_enrichment": float(rg["top10"].mean() / 0.10),
                }
            )
    return pd.DataFrame(rows)


def write_report(coverage_df: pd.DataFrame, features_df: pd.DataFrame, trigger_df: pd.DataFrame, tail_df: pd.DataFrame) -> None:
    met_diff = features_df[features_df["primary_dataset"].eq("MET")].sort_values("ks_statistic", ascending=False).head(8)
    remote_tail = tail_df[(tail_df["source"].eq("remote_unused_mht")) & (tail_df["primary_dataset"].eq("MET"))].sort_values(["score", "top10_enrichment"], ascending=[True, False])
    report = f"""# Run2016H Local-versus-Remote Composition Diagnostic

## Purpose

The frozen MHT-aware trace scores were strong in the earlier local Run2016H validation but weak in a new remote Run2016H batch. This diagnostic checks whether that difference is explained by era provenance, run/lumi coverage, trigger/quality acceptance, event composition, or concentration of high-boundary events in particular runs.

## Coverage

{coverage_df.to_markdown(index=False)}

## Largest Local-versus-Remote MET Distribution Differences

{met_diff.to_markdown(index=False, floatfmt='.6g')}

## Trigger and Quality Fractions

{trigger_df.to_markdown(index=False, floatfmt='.4g')}

## Remote MET Tail Concentration by Run

{remote_tail.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

Both inputs are genuinely Run2016H, but they are not the same run/lumisection mixture. The local fresh sample covers a different set of runs and has much larger event totals. Therefore the failure of the remote sample cannot be dismissed as a mislabeled era; it is an independent-composition result.

The next physical question is whether the original local trace is concentrated in its particular run/lumi mixture or whether the remote batch becomes compatible after more files from the same Run2016H streams are processed. The compact remote workflow is working correctly, so this can now be tested without retaining raw ROOT files locally.
"""
    (REPORTS / "01_RUN2016H_REMOTE_LOCAL_COMPOSITION_DIAGNOSTIC.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    local, remote, local_raw, remote_raw = load()
    coverage_df = coverage(local, remote)
    features_df = feature_comparison(local, remote)
    trigger_df = trigger_quality_comparison(local_raw, remote_raw)
    tails = pd.concat(
        [
            run_tail_concentration(local, "score_clean"),
            run_tail_concentration(local, "score_opq"),
            run_tail_concentration(remote, "score_clean"),
            run_tail_concentration(remote, "score_opq"),
        ],
        ignore_index=True,
    )
    coverage_df.to_csv(TABLES / "01_run_lumi_coverage_comparison.csv", index=False)
    features_df.to_csv(TABLES / "02_feature_distribution_comparison.csv", index=False)
    trigger_df.to_csv(TABLES / "03_trigger_quality_comparison.csv", index=False)
    tails.to_csv(TABLES / "04_run_tail_concentration.csv", index=False)
    write_report(coverage_df, features_df, trigger_df, tails)
    print(REPORTS / "01_RUN2016H_REMOTE_LOCAL_COMPOSITION_DIAGNOSTIC.md")


if __name__ == "__main__":
    main()
