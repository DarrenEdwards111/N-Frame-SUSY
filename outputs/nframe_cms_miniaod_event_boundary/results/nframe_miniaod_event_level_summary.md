# N-Frame Event-Level Boundary-Access Analysis using CMS 2016G MiniAOD

## Data

- Input path: `D:/cern_open_data/cms_met_run2016g_miniaod_10gb`
- ROOT files found: 6
- Total ROOT size: 10.962 GB
- Events processed: 131708

## Extraction Status

A real, testable jet-level event feature table was extracted from CMS MiniAOD with uproot. MET, lepton counts, and true b-tag discriminators remain unavailable in this Python-only EDM readout, so the full event-level N-Frame score still requires the included CMSSW analyzer.

The inspection log is at `results/logs/root_file_structure.txt`.

- Extraction modes: `uproot_edm_partial_jets`
- Score status: `partial_jet_level_real_miniaod`
- Full boundary feature flag: `0`
- Missing MET fraction: 1.000
- Missing lepton-count fraction: 1.000
- Missing b-tag fraction: 1.000

## Variables

Extracted/scored columns:

`event_id, source_file, source_entry, extraction_mode, full_boundary_features_available, jet_only_features_available, MET_pt, MET_phi, N_jets, N_jets_30, N_jets_50, HT, leading_jet_pt, subleading_jet_pt, leading_jet_eta, jet_mass_sum_30, N_leptons, N_muons, N_electrons, N_btags_loose, N_btags_medium, N_btags_tight, N_b_hadron_flavour_proxy, N_PF_candidates, event_weight, missing_MET, missing_leptons, missing_btags, MET_fraction, N_objects, Visible_HT, Nb_missing, S_event_proxy, high_MET, high_multiplicity, R_reconstruction, B_event_jetonly, B_event_jetonly_z, B_event, B_event_z, B_event_status`

## Boundary Score

`MET_fraction = MET_pt / (HT + MET_pt + 1)`

`S_event_proxy = log(1 + N_jets_30 + N_leptons + N_btags_medium)`

`B_event_jetonly = z(HT) + z(N_jets_30) + z(N_jets_50) + z(S_event_proxy)`

`B_event` includes only available extracted components. In the current uproot EDM extraction this is a partial jet-level score because MET, leptons, and true b-tags are not readable from the MiniAOD objects without CMSSW/FWLite.

Missing MET, lepton, and b-tag information is recorded in the feature/status columns rather than silently filled as observed physics.

## Pseudo Signal Regions

```text
     pseudo_signal_region  N_events  mean_MET      mean_HT  mean_Njets  mean_Njets50  mean_B_event_jetonly_z  mean_B_event_z  mean_MET_fraction  mean_S_event_proxy
    JSR1_low_jet_boundary     88710       NaN   194.692757    1.950614      1.578943               -0.314348       -0.317050                NaN            1.050799
           JSR2_medium_HT     35754       NaN   433.713408    3.301281      2.619399                0.514045        0.511379                NaN            1.426927
             JSR3_high_HT      4527       NaN  2455.544026    5.024299      4.271482                1.677374        1.620029                NaN            1.664380
   JSR4_high_HT_high_jets       932       NaN  8515.808480   10.077253      8.500000                4.836949        4.705188                NaN            2.194839
   JSR5_high_jet_boundary      9626       NaN  1332.767670    5.385207      4.223873                1.695923        1.658903                NaN            1.805258
JSR6_extreme_jet_boundary      1023       NaN  7746.904544    9.994135      8.481916                4.720356        4.551801                NaN            2.209123
   JSR7_high_multiplicity       264       NaN 27624.313331   20.026515     17.893939               11.905362       11.625997                NaN            2.772020
      JSR8_many_hard_jets       445       NaN 16763.494350   14.195506     13.395506                8.013839        7.622721                NaN            2.422958
```

## Interpretation

This MiniAOD subset is used to construct event-level N-Frame boundary-access variables directly from reconstructed CMS event objects where possible. The analysis does not test for supersymmetry directly and does not constitute a full CMS search reinterpretation. It demonstrates the feasibility status of computing `B_event` from real event-level data and using it to classify events by missing information, visible activity, multiplicity, and reconstruction complexity.

Do not interpret high-boundary events as SUSY candidates.
