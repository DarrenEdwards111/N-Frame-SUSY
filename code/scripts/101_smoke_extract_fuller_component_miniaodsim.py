from __future__ import annotations

import pandas as pd

from fuller_component_common import DATE, REPORTS, TABLES, download_selected_files, run_cmssw


def main() -> None:
    manifest = download_selected_files()
    ok = manifest[manifest["download_status"].isin(["already_present", "downloaded"])]
    rows = []
    for _, row in ok.iterrows():
        rows.append(run_cmssw(row, "smoke", 1000))
        pd.DataFrame(rows).to_csv(TABLES / "fuller_component_smoke_extraction_summary.csv", index=False)
    summary = pd.DataFrame(rows)
    validations = []
    for _, row in summary[summary["status"].eq("success")].iterrows():
        df = pd.read_csv(row["output_csv"], nrows=1005)
        validations.append({
            "sample_slug": row["sample_slug"],
            "rows": len(pd.read_csv(row["output_csv"], usecols=["event"])),
            "has_secondary_vertex_count": "secondary_vertex_count" in df.columns,
            "has_packed_candidate_count": "packed_candidate_count" in df.columns,
            "has_met_ht": {"MET_pt", "HT"}.issubset(df.columns),
        })
    validation = pd.DataFrame(validations)
    validation.to_csv(TABLES / "fuller_component_smoke_feature_validation.csv", index=False)
    report = [
        "# Fuller Component MiniAODSIM Smoke Extraction Report",
        "",
        f"Date: {DATE}",
        "",
        "This smoke test used selected real-CMS-open-data MiniAODSIM files only. It did not refit B_NF.",
        "",
        "## Download Manifest",
        "",
        manifest.to_markdown(index=False),
        "",
        "## Smoke Extraction",
        "",
        summary.to_markdown(index=False) if not summary.empty else "No successful downloads were available for smoke extraction.",
        "",
        "## Feature Validation",
        "",
        validation.to_markdown(index=False) if not validation.empty else "No smoke feature files were created.",
    ]
    (REPORTS / "FULLER_COMPONENT_SMOKE_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False) if not summary.empty else "No smoke extractions attempted.")


if __name__ == "__main__":
    main()
