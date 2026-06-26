from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

ROWS = [
    ("P_displacement_proxy", "secondary_vertex_count", "required_for_full_score", "slimmedSecondaryVertices", "not generally available in NanoAOD", "No", "Proxy only; not proof of displaced particles."),
    ("P_displacement_proxy", "displacement_proxy_raw", "derived", "derived from secondary_vertex_count", "not generally available", "No", "Reduced score needed if unavailable."),
    ("P_reconstruction", "packed_candidate_count", "required_for_full_score", "packedPFCandidates", "not stored as direct NanoAOD branch", "Approximate only", "NanoAOD can use object counts/PV as reduced reconstruction proxy."),
    ("P_reconstruction", "N_primary_vertices", "required", "offlineSlimmedPrimaryVertices", "PV_npvs", "Yes", "Pileup/reconstruction-load proxy."),
    ("P_reconstruction", "secondary_vertex_count", "required_for_full_score", "slimmedSecondaryVertices", "not generally available", "No", "Shared with displacement proxy."),
    ("P_multiplicity", "N_jets_30", "required", "slimmedJets", "Jet_pt", "Yes", "Computed from jets with pt > 30."),
    ("P_multiplicity", "N_jets_50", "required", "slimmedJets", "Jet_pt", "Yes", "Computed from jets with pt > 50."),
    ("P_multiplicity", "N_leptons", "required", "slimmedMuons/slimmedElectrons", "Muon_pt/Electron_pt", "Yes", "Computed count."),
    ("P_btag_structure", "N_btags_medium", "required", "slimmedJets b discriminator", "Jet_btagDeepB or Jet_btagDeepFlavB", "Approximate", "Working point must be documented."),
    ("P_btag_structure", "N_btags_tight", "required", "slimmedJets b discriminator", "Jet_btagDeepB or Jet_btagDeepFlavB", "Approximate", "Working point must be documented."),
    ("P_btag_structure", "max_btag_discriminator", "required", "slimmedJets b discriminator", "Jet_btagDeepB or Jet_btagDeepFlavB", "Yes", "Branch name differs by NanoAOD version."),
    ("P_visible_energy", "HT", "required", "derived from jets", "derived from Jet_pt", "Yes", "Use selected jets."),
    ("P_visible_energy", "leading_jet_pt", "required", "slimmedJets", "Jet_pt", "Yes", "Leading selected jet."),
    ("P_visible_energy", "subleading_jet_pt", "optional", "slimmedJets", "Jet_pt", "Yes", "Subleading selected jet."),
    ("P_missing", "MET_pt", "required", "slimmedMETs", "MET_pt", "Yes", "Direct missing transverse momentum."),
    ("P_compression", "compression_proxy_raw", "secondary", "derived from MET and visible activity", "derived from MET_pt and HT/leading jet", "Yes", "Weak fitted component; secondary."),
]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        ROWS,
        columns=[
            "parameter_family", "variable", "status", "miniaod_availability",
            "nanoaod_likely_equivalent", "nanoaod_approximation_acceptable", "notes",
        ],
    )
    df.to_csv(TABLES / "fitted_boundary_required_variables.csv", index=False)
    report = [
        "# Validation Requirements For Fitted N-Frame Boundary",
        "",
        "Date: 2026-06-09",
        "",
        "The fitted boundary can be tested most directly on MiniAOD because MiniAOD contains the secondary-vertex and packed-candidate information used by the dominant fitted parameters. NanoAOD is useful as a faster cross-check, but would be a reduced or approximate validation because some dominant components are missing or approximated.",
        "",
        df.to_markdown(index=False),
    ]
    (REPORTS / "VALIDATION_REQUIREMENTS_FOR_FITTED_NFRAME_BOUNDARY.md").write_text("\n".join(report), encoding="utf-8")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
