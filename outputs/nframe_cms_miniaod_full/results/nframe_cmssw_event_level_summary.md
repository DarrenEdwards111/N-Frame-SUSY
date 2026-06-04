# N-Frame CMSSW Event-Level Summary

## Dataset

- Local data path: `D:\cern_open_data\cms_met_run2016g_miniaod_10gb`
- ROOT files: 6
- Total size: 10.962 GB
- Events processed: 0

## Extraction Status

CMSSW extraction was not completed in this environment.

- event_features.csv: no
- event_features_nframe_scored.csv: no
- MET extracted: not tested
- jets extracted: not tested
- muons/electrons extracted: not tested
- b-tags extracted: not tested

## Boundary Score

`B_event = z(MET_pt) + z(HT) + z(N_jets_30) + z(N_leptons) + z(N_btags_medium) + z(MET_fraction) + z(S_event_proxy)`

Component scores:

- `R_missing = z_MET + z_MET_fraction + high_MET`
- `R_multiplicity = z_Njets + z_Nleptons + z_Nbtags + high_multiplicity`
- `R_reconstruction = z_MET_fraction + z_S_event + z(N_objects)`

## Pseudo Signal Regions

```text
Pseudo signal regions not produced.
```

## Limitations

- No Standard Model background comparison.
- No SUSY claim.
- No hidden-symmetry claim.
- 10 GB MiniAOD subset only.
- MET dataset trigger bias is expected.
- No luminosity or background weighting.

Correct conclusion:

The CMS MiniAOD subset was used to construct event-level N-Frame boundary-access variables from reconstructed event objects only if the CMSSW event files exist above. This demonstrates event-level feasibility but does not constitute a search for supersymmetry or hidden symmetry.
