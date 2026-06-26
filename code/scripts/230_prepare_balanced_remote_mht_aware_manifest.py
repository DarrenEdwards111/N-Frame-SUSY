from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "cloud_remote_nframe_package"
SOURCE_MANIFEST = PACKAGE / "manifests" / "01_real_cms_miniaod_remote_cloud_manifest.csv"
OUTDIR = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation"
TABLES = OUTDIR / "tables"
MANIFEST_OUT = TABLES / "01_balanced_unused_remote_mht_aware_manifest.csv"
SUMMARY_OUT = TABLES / "00_balanced_manifest_summary.csv"

LOCAL_SOURCES = [
    ROOT / "outputs_mht_proxy_fresh_run2016h_validation" / "sources" / "mht_fresh_run2016h_scored_events.csv",
    ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz",
    ROOT / "outputs_run2015d_frozen_q99_pilot" / "sources" / "run2015d_all_selected_real_events_scored.csv",
    ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_event_features_combined.csv",
]


def used_root_names() -> set[str]:
    names: set[str] = set()
    for path in LOCAL_SOURCES:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path, usecols=lambda c: c in {"source_file", "local_input_path_or_container_path"}, low_memory=False)
        except Exception:
            continue
        for col in df.columns:
            for value in df[col].dropna().astype(str).unique():
                for part in value.replace("|", ";").replace(",", ";").split(";"):
                    part = part.strip()
                    if part.endswith(".root"):
                        names.add(Path(part).name)
    return names


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    used = used_root_names()
    manifest = pd.read_csv(SOURCE_MANIFEST)
    manifest["filename"] = manifest["xrootd_url"].astype(str).map(lambda x: Path(x).name)
    manifest["already_used_locally"] = manifest["filename"].isin(used)
    available = manifest[~manifest["already_used_locally"]].copy()
    available = available.sort_values(["run_era", "primary_dataset", "selection_order", "size_gb"])

    # One file per era/stream per round, interleaved so early partial batches are balanced.
    selected = []
    for rank in range(3):
        for era in ["Run2015D", "Run2016G", "Run2016H"]:
            for dataset in ["HTMHT", "MET", "JetHT", "SingleMuon"]:
                group = available[(available["run_era"].eq(era)) & (available["primary_dataset"].eq(dataset))]
                if len(group) > rank:
                    selected.append(group.iloc[rank])
    out = pd.DataFrame(selected).reset_index(drop=True)
    out["status"] = "pending"
    out["planned_max_events"] = 5000
    out["remote_validation_role"] = "feature_equivalent_mht_aware_validation"
    out["selection_note"] = "interleaved unused file by era and stream; remote XRootD read; compact feature CSV only"
    out.to_csv(MANIFEST_OUT, index=False)

    summary = (
        out.groupby(["run_era", "primary_dataset"], as_index=False)
        .agg(files=("xrootd_url", "count"), total_size_gb=("size_gb", "sum"), planned_events=("planned_max_events", "sum"))
    )
    summary.to_csv(SUMMARY_OUT, index=False)
    print(MANIFEST_OUT)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
