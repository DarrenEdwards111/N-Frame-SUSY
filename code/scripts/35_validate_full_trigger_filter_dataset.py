from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

TRIGGER_FILTER_COLS = [
    "HLT_MET_paths_any",
    "HLT_HT_paths_any",
    "HLT_Mu_paths_any",
    "HLT_Ele_paths_any",
    "pass_HBHENoiseFilter",
    "pass_HBHENoiseIsoFilter",
    "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter",
    "pass_BadPFMuonFilter",
    "pass_globalSuperTightHalo2016Filter",
    "trigger_filter_extraction_status",
]

REQUIRED_PHYSICS_COLS = [
    "run",
    "lumi",
    "event",
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_leptons",
    "N_btags_medium",
    "N_primary_vertices",
    "packed_candidate_count",
    "secondary_vertex_count",
    "primary_dataset",
    "sample_id",
    "source_file",
]

INPUTS = {
    "trigger_filter_5k": ROOT
    / "data"
    / "processed"
    / "cmssw_real_only_trigger_filter_5k_by_file"
    / "real_only_trigger_filter_5k_combined.csv",
    "trigger_filter_full": ROOT
    / "data"
    / "processed"
    / "cmssw_real_only_trigger_filter_full"
    / "real_only_full_event_features_with_trigger_filter.csv",
}


def validate(label: str, path: Path) -> tuple[pd.DataFrame, list[str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    rows = []
    messages = []
    missing_cols = [c for c in REQUIRED_PHYSICS_COLS + TRIGGER_FILTER_COLS if c not in df.columns]
    if missing_cols:
        messages.append(f"Missing columns: {', '.join(missing_cols)}")

    id_cols = [c for c in ["run", "lumi", "event", "source_file"] if c in df.columns]
    duplicate_fraction = df.duplicated(id_cols).mean() if id_cols else None
    simulated_fraction = pd.to_numeric(df.get("is_simulated", pd.Series([0] * len(df))), errors="coerce").fillna(0).mean()
    real_fraction = pd.to_numeric(df.get("is_real_collision", pd.Series([1] * len(df))), errors="coerce").fillna(1).mean()

    rows.append(
        {
            "dataset": label,
            "check": "rows",
            "value": len(df),
            "status": "pass" if len(df) > 0 else "fail",
        }
    )
    rows.append(
        {
            "dataset": label,
            "check": "missing_required_columns",
            "value": len(missing_cols),
            "status": "pass" if not missing_cols else "fail",
        }
    )
    rows.append(
        {
            "dataset": label,
            "check": "duplicate_run_lumi_event_source_file_fraction",
            "value": duplicate_fraction,
            "status": "pass" if duplicate_fraction == 0 else "warn",
        }
    )
    rows.append(
        {
            "dataset": label,
            "check": "simulated_fraction",
            "value": simulated_fraction,
            "status": "pass" if simulated_fraction == 0 else "fail",
        }
    )
    rows.append(
        {
            "dataset": label,
            "check": "real_collision_fraction",
            "value": real_fraction,
            "status": "pass" if real_fraction == 1 else "warn",
        }
    )

    for col in TRIGGER_FILTER_COLS:
        if col not in df:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        rows.append(
            {
                "dataset": label,
                "check": f"{col}_non_null_fraction",
                "value": s.notna().mean(),
                "status": "pass" if s.notna().mean() > 0.999 else "warn",
            }
        )
        rows.append(
            {
                "dataset": label,
                "check": f"{col}_mean",
                "value": s.mean(),
                "status": "info",
            }
        )

    by_file = df.groupby(["primary_dataset", "sample_id", "source_file"], as_index=False).agg(
        events=("event", "count"),
        trigger_filter_status_mean=("trigger_filter_extraction_status", "mean"),
        hlt_met_fraction=("HLT_MET_paths_any", "mean"),
        hlt_ht_fraction=("HLT_HT_paths_any", "mean"),
        hlt_mu_fraction=("HLT_Mu_paths_any", "mean"),
        hlt_ele_fraction=("HLT_Ele_paths_any", "mean"),
        good_vertices_fraction=("pass_goodVertices", "mean"),
        hbhe_noise_fraction=("pass_HBHENoiseFilter", "mean"),
        hbhe_iso_fraction=("pass_HBHENoiseIsoFilter", "mean"),
        bad_pf_muon_fraction=("pass_BadPFMuonFilter", "mean"),
        halo_filter_fraction=("pass_globalSuperTightHalo2016Filter", "mean"),
    )
    by_file.insert(0, "dataset", label)
    return pd.concat([pd.DataFrame(rows), by_file], axis=0, ignore_index=True), messages


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    label = "trigger_filter_full" if INPUTS["trigger_filter_full"].exists() else "trigger_filter_5k"
    path = INPUTS[label]
    validation, messages = validate(label, path)
    validation_path = TABLES / f"{label}_validation_by_file.csv"
    validation.to_csv(validation_path, index=False)

    checks = validation[validation["check"].notna()].copy()
    by_file = validation[validation["events"].notna()].copy()
    report_name = "FULL_TRIGGER_FILTER_VALIDATION_REPORT.md" if label == "trigger_filter_full" else "TRIGGER_FILTER_5K_VALIDATION_REPORT.md"
    title = "Full Trigger/Filter Validation Report" if label == "trigger_filter_full" else "Trigger/Filter 5k Validation Report"
    report = [
        f"# {title}",
        "",
        "Date: 2026-06-08",
        "",
        "This validates real CMS collision MiniAOD outputs produced by the patched CMSSW analyser. No simulated events are used.",
        "",
        f"Input: `{path}`",
        "",
        "## Machine Checks",
        "",
        checks.to_markdown(index=False),
        "",
        "## Per-File Coverage",
        "",
        by_file.to_markdown(index=False),
    ]
    if messages:
        report.extend(["", "## Warnings", "", *[f"- {m}" for m in messages]])
    (REPORTS / report_name).write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {validation_path}")
    print(f"Wrote {REPORTS / report_name}")
    print(checks.to_string(index=False))


if __name__ == "__main__":
    main()
