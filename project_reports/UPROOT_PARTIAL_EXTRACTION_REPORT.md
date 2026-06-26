# Uproot Partial Extraction Report

## Summary

The Python/uproot fallback extracted 665,902 event rows from 9 ROOT files.

What was extractable: jet four-vector leaves from MiniAOD (`pt`, `eta`, `phi`, mass), jet multiplicity, HT from jets with pt > 30 GeV, leading/subleading jet pt, sum jet pt, object multiplicity based on selected jets, and a hadron-flavour proxy where the MiniAOD leaf was readable.

What was not extractable honestly with this lightweight path: run/lumi/event IDs, MET pt/phi, muon/electron counts, b-tag discriminators, trigger decisions, lifetime/displacement variables.

This output is useful for a limited real-data boundary dry run based on visible jet activity only. It is not sufficient for a serious N-Frame boundary analysis because the missing-information component requires MET, and the reconstruction-complexity components need leptons, b-tags, triggers, and quality information. CMSSW remains required for the proper analysis layer.

## Per-File Status

| sample_id                         | primary_dataset   | source_file                               | status                      |   events_extracted | available_features                                        | unavailable_features                                                                                        | error   |
|:----------------------------------|:------------------|:------------------------------------------|:----------------------------|-------------------:|:----------------------------------------------------------|:------------------------------------------------------------------------------------------------------------|:--------|
| cms_jetht_run2016g_collision      | JetHT             | 0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root | extracted_visible_jets_only |              61353 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_jetht_run2016g_collision      | JetHT             | 35017A26-8C9D-204D-92B6-3ABFBBD4ADF3.root | extracted_visible_jets_only |              17433 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_jetht_run2016g_collision      | JetHT             | 94C50CE8-43B0-AF4D-A8AE-BE0C7EC09B80.root | extracted_visible_jets_only |               2937 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_jetht_run2016g_collision      | JetHT             | EF857ADB-D98F-3F4A-A847-C8AC759ED9B3.root | extracted_visible_jets_only |              16422 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_met_run2016g_collision        | MET               | 020ADD62-87D5-4B43-BAAD-C77C83D5FF8F.root | extracted_visible_jets_only |              85149 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_met_run2016g_collision        | MET               | 0313FB78-4AB7-024F-9BAF-454665B7A5FF.root | extracted_visible_jets_only |             113601 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_met_run2016g_collision        | MET               | 0E1A8650-EA73-264D-8BA5-92902470681F.root | extracted_visible_jets_only |              28693 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_singlemuon_run2016g_collision | SingleMuon        | 001FDE5F-A989-2F48-A280-D4D0F7766D95.root | extracted_visible_jets_only |             172994 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
| cms_singlemuon_run2016g_collision | SingleMuon        | 080625AC-04AC-BC49-B816-7FF6BB62AAC0.root | extracted_visible_jets_only |             167320 | jets;HT;jet_multiplicity;jet_phi_eta;hadron_flavour_proxy | run/lumi/event;MET_pt;MET_phi;muons;electrons;btag_discriminator;trigger_decisions;lifetime_or_displacement |         |
