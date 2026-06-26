# ATLAS Open Data Q99 1-2 Jet N-Frame Analogue

## Purpose

Test whether the CMS frozen Q99 1-2 jet missing-vs-visible boundary trace has an independent-detector analogue in public ATLAS 13 TeV Open Data.

## Important Difference From CMS

This is not an exact CMS MiniAOD replication. ATLAS Open Data 2020 is provided as preselected flat ROOT ntuples. This run uses the public exactly-one-lepton ATLAS collection because it has real data, MET, jets, leptons, b-tag information and matching SM MC.

## Inputs

Record: CERN Open Data ATLAS record 15001

| role      | family    |   files |       gb |   events |
|:----------|:----------|--------:|---------:|---------:|
| real_data | real_data |       1 | 1.58114  |        1 |
| sm_mc     | Wjets     |      15 | 5.5968   |       15 |
| sm_mc     | Zjets     |       9 | 0.877757 |        9 |
| sm_mc     | diboson   |       5 | 2.22064  |        5 |
| sm_mc     | top       |       3 | 0.63761  |        3 |

## Frozen Analogue Rule

- ATLAS real data, `data_A.1lep.root`
- 1-2 jets with pT > 30 GeV
- missing-vs-visible residual score: residual of log(MET) after HT, jet count, b-tags, lepton count and leading lepton pT
- raw-MET-binned score bands
- signal band: top 1%, q99-100
- sideband-shape correction fitted from 50-95%
- jet-bin controls: 0 jet, 3-4 jets, 5+ jets

## Result

| jet_bin   | usable   |   real_events |   sideband_80_95_observed |   sideband_80_95_expected_official |   sideband_80_95_obs_exp |   q99_observed |   q99_expected_shape |   q99_obs_exp |   sideband_log_rms |   relative_uncertainty_used |     q99_Z |
|:----------|:---------|--------------:|--------------------------:|-----------------------------------:|-------------------------:|---------------:|---------------------:|--------------:|-------------------:|----------------------------:|----------:|
| 0jet      | True     |       7050055 |               1.36274e+06 |                        1.04694e+06 |                  1.30163 |         771125 |          1.79749e+06 |      0.429001 |           0.221629 |                    0.372987 | -1.53088  |
| 1to2jets  | True     |       2560282 |          338333           |                   228367           |                  1.48153 |             19 |         32.5229      |      0.584203 |           0.429783 |                    0.524131 | -0.752321 |
| 3to4jets  | True     |        167033 |           51263           |                    28649.6         |                  1.78931 |             37 |         98.5072      |      0.375607 |           0.21129  |                    0.366938 | -1.6409   |
| 5plusjets | True     |         19039 |           11139           |                    10113.4         |                  1.10141 |            282 |        197.91        |      1.42489  |           0.313931 |                    0.434226 |  0.965644 |

## Interpretation

This is an ATLAS analogue check, not a final discovery test. A positive q99 result in the 1-2 jet bin with non-discovery controls would support detector-independent behaviour. A null or control-dominated result would mean the CMS trace does not simply transfer to this ATLAS preselected channel.
