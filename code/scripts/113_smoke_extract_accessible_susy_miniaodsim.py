from __future__ import annotations

import pandas as pd

from susy_signal_common import DATE, REPORTS, TABLES, download_plan_files, run_cmssw_signal


REQUIRED = [
    "MET_pt", "MET_phi", "HT", "N_jets_30", "N_jets_50", "leading_jet_pt", "subleading_jet_pt",
    "N_muons", "N_electrons", "N_leptons", "N_btags_medium", "N_btags_tight", "max_btag_discriminator",
    "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count",
]


def main() -> None:
    manifest = download_plan_files()
    ok = manifest[manifest["download_status"].isin(["already_present", "downloaded"])]
    rows = []
    for _, row in ok.iterrows():
        rows.append(run_cmssw_signal(row, "smoke", 1000))
        pd.DataFrame(rows).to_csv(TABLES / "accessible_susy_signal_smoke_extraction_summary.csv", index=False)
    summary = pd.DataFrame(rows)
    validations = []
    for _, row in summary[summary["status"].eq("success")].iterrows():
        df = pd.read_csv(row["output_csv"], nrows=1005)
        validations.append({
            "sample_id": row["sample_id"],
            "rows": len(pd.read_csv(row["output_csv"], usecols=["event"])),
            "missing_required_columns": ";".join([c for c in REQUIRED if c not in df.columns]),
            "P_displacement_proxy_available": "secondary_vertex_count" in df.columns,
            "P_reconstruction_available": "packed_candidate_count" in df.columns,
            "P_missing_available": "MET_pt" in df.columns,
            "P_visible_energy_available": {"HT", "leading_jet_pt", "subleading_jet_pt"}.issubset(df.columns),
            "P_multiplicity_available": {"N_jets_30", "N_jets_50", "N_leptons"}.issubset(df.columns),
            "P_btag_structure_available": {"N_btags_medium", "N_btags_tight", "max_btag_discriminator"}.issubset(df.columns),
            "P_compression_available": {"MET_pt", "HT", "leading_jet_pt"}.issubset(df.columns),
        })
    validation = pd.DataFrame(validations)
    validation.to_csv(TABLES / "accessible_susy_signal_smoke_feature_validation.csv", index=False)
    report = [
        "# Accessible SUSY MiniAODSIM Smoke Extraction Report",
        "",
        f"Date: {DATE}",
        "",
        "Downloaded selected verified MiniAODSIM signal files and ran maxEvents=1000 smoke extraction through the existing CMSSW/Docker route.",
        "",
        "## Download Manifest",
        "",
        manifest.to_markdown(index=False),
        "",
        "## Smoke Extraction",
        "",
        summary.to_markdown(index=False) if not summary.empty else "No smoke extraction was attempted.",
        "",
        "## Feature Validation",
        "",
        validation.to_markdown(index=False) if not validation.empty else "No smoke feature validation was possible.",
    ]
    (REPORTS / "ACCESSIBLE_SUSY_SIGNAL_SMOKE_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False) if not summary.empty else "No smoke extraction attempted.")


if __name__ == "__main__":
    main()
