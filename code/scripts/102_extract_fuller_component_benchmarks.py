from __future__ import annotations

import pandas as pd

from fuller_component_common import DATE, OUT, REPORTS, TABLES, read_plan, run_cmssw


def main() -> None:
    manifest_path = TABLES / "fuller_component_download_manifest.csv"
    smoke_path = TABLES / "fuller_component_smoke_extraction_summary.csv"
    if not manifest_path.exists() or not smoke_path.exists():
        raise SystemExit("Run script 101 first; manifest or smoke summary is missing.")
    manifest = pd.read_csv(manifest_path)
    smoke = pd.read_csv(smoke_path)
    successful = smoke[smoke["status"].eq("success")]["sample_slug"].tolist()
    candidates = manifest[manifest["sample_slug"].isin(successful)].merge(read_plan(), on=["sample_slug", "record_id"], suffixes=("", "_plan"))
    rows = []
    for _, row in candidates.iterrows():
        rows.append(run_cmssw(row, "full", 50000))
        pd.DataFrame(rows).to_csv(TABLES / "fuller_component_full_extraction_summary.csv", index=False)
    status = pd.DataFrame(rows)
    frames = [pd.read_csv(p) for p in status[status["status"].eq("success")]["output_csv"]]
    combined = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    combined_path = OUT / "fuller_component_benchmark_event_features.csv"
    combined.to_csv(combined_path, index=False)
    availability = []
    for _, g in (combined.groupby("sample_id") if not combined.empty else []):
        availability.append({
            "sample_id": g["sample_id"].iloc[0],
            "process_label": g["process_label"].iloc[0],
            "classification": g["classification"].iloc[0],
            "events": len(g),
            "has_secondary_vertex_count": "secondary_vertex_count" in g.columns,
            "has_packed_candidate_count": "packed_candidate_count" in g.columns,
            "has_met_ht": {"MET_pt", "HT"}.issubset(g.columns),
        })
    avail = pd.DataFrame(availability)
    avail.to_csv(TABLES / "fuller_component_feature_availability.csv", index=False)
    report = [
        "# Fuller Component MiniAODSIM Feature Extraction Report",
        "",
        f"Date: {DATE}",
        "",
        "Full extraction used maxEvents=50000 per selected MiniAODSIM file and preserved exact file provenance.",
        "",
        "## Extraction Status",
        "",
        status.to_markdown(index=False) if not status.empty else "No full extractions were attempted.",
        "",
        "## Feature Availability",
        "",
        avail.to_markdown(index=False) if not avail.empty else "No successful full feature files were created.",
        "",
        f"Combined output: `{combined_path}`",
    ]
    (REPORTS / "FULLER_COMPONENT_FEATURE_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(status.to_string(index=False) if not status.empty else "No full extractions attempted.")


if __name__ == "__main__":
    main()
