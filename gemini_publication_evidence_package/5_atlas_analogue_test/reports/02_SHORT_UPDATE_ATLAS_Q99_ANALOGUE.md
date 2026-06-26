# Short Update: ATLAS Q99 Analogue

We tested an ATLAS Open Data analogue of the frozen CMS Q99 1-2 jet N-Frame boundary trace.

Result:

| jet_bin   | usable   |   real_events |   sideband_80_95_observed |   sideband_80_95_expected_official |   sideband_80_95_obs_exp |   q99_observed |   q99_expected_shape |   q99_obs_exp |   sideband_log_rms |   relative_uncertainty_used |     q99_Z |
|:----------|:---------|--------------:|--------------------------:|-----------------------------------:|-------------------------:|---------------:|---------------------:|--------------:|-------------------:|----------------------------:|----------:|
| 0jet      | True     |       7050055 |               1.36274e+06 |                        1.04694e+06 |                  1.30163 |         771125 |          1.79749e+06 |      0.429001 |           0.221629 |                    0.372987 | -1.53088  |
| 1to2jets  | True     |       2560282 |          338333           |                   228367           |                  1.48153 |             19 |         32.5229      |      0.584203 |           0.429783 |                    0.524131 | -0.752321 |
| 3to4jets  | True     |        167033 |           51263           |                    28649.6         |                  1.78931 |             37 |         98.5072      |      0.375607 |           0.21129  |                    0.366938 | -1.6409   |
| 5plusjets | True     |         19039 |           11139           |                    10113.4         |                  1.10141 |            282 |        197.91        |      1.42489  |           0.313931 |                    0.434226 |  0.965644 |

This is not exact CMS replication because ATLAS Open Data uses preselected flat ntuples, here the exactly-one-lepton channel.
