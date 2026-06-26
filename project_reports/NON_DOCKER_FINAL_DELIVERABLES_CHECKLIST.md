# Non-Docker Final Deliverables Checklist

## 1. Scripts Created

- `scripts/05_deep_miniaod_branch_inventory.py`
- `scripts/06_search_miniaod_candidate_objects.py`
- `scripts/07_test_read_candidate_miniaod_branches.py`
- `scripts/08_non_docker_feature_extraction_attempts.py`
- `scripts/09_extract_real_collision_non_docker_features.py`
- `scripts/10_score_real_collision_boundary_improved_non_docker.py`
- `scripts/11_analyse_improved_real_collision_boundary.py`

## 2. Branches/Objects Found

Found candidate branches/objects for:

- EventAuxiliary
- slimmedMETs
- slimmedJets
- slimmedMuons
- slimmedElectrons
- slimmedPhotons
- slimmedTaus
- TriggerResults
- packedPFCandidates
- offlineSlimmedPrimaryVertices
- slimmedSecondaryVertices
- lostTracks
- filter/noise/beam-halo related products

## 3. Whether MET Was Found And Readable

MET was found by name as `patMETs_slimmedMETs__PAT`, but MET pt/phi were not readable with the tested generic uproot route. Only the product-present flag was readable.

## 4. Whether Muons/Electrons Were Found And Readable

Muon and electron objects were found by name, but their kinematics/counts were not readable with the tested generic uproot route. Product-present flags were readable.

## 5. Whether B-Tags Were Found And Readable

Experimental b-tag discriminators were not cleanly extracted. Jet hadron-flavour and parton-flavour leaves were readable and can be used only as labelled proxies, not as measured b-tags.

## 6. Whether Event IDs Were Found And Readable

`EventAuxiliary` was found but failed generic uproot deserialisation. Run/lumi/event IDs were not extracted.

## 7. Whether Triggers/Filters Were Found And Readable

Trigger and filter products were found. Product-present flags were readable, but named HLT decisions and interpreted filter decisions were not extracted.

## 8. Whether Improved Non-Docker Event Features Were Extracted

Yes. Output:

```text
data\processed\real_collision_20gb_non_docker_event_features.csv
```

Rows: 665,902.

## 9. Whether The Boundary Score Improved Beyond Jet/HT

Yes. The improved score includes packed-candidate and primary-vertex complexity plus an encoded displacement-like proxy. It still does not include true MET.

## 10. Whether Docker/CMSSW Is Genuinely Required

Docker specifically is not proven to be required. A CMS-aware extraction route is still required for the full model unless PyROOT/FWLite or another local CMS-aware route can read the CMS EDM objects.

## 11. Main Cautious Result

The improved non-Docker analysis finds repeatable high-boundary structure using visible activity, packed-candidate/vertex complexity, and encoded displacement-like proxies; JetHT remains enriched, and MET becomes enriched in the top 5% tail, but true missing-energy boundary stress cannot be tested until MET pt/phi are extracted.

## 12. Exact Next Command

Check whether conda can see ROOT/PyROOT:

```powershell
D:\Anaconda\python.exe -c "import ROOT; print(ROOT.gROOT.GetVersion())"
```

If that still fails, the next decision is whether to install conda ROOT/FWLite or use the already prepared CMSSW route.

