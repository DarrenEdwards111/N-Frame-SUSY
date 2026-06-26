# Current CMS New-Era Remote Availability Audit

## Scope

This audit checked the CERN Open Data metadata API at `2026-06-22T08:56:23.359441+00:00` for real CMS
Run2017 and Run2018 MiniAOD records matching the four streams required by the
feature-equivalent N-Frame validation: MET, HTMHT, JetHT, and SingleMuon.

No event file was downloaded. A non-empty usable-record result would be the
only condition required to proceed to a remote XRootD/CMSSW extraction.

## Result

No matching real Run2017/Run2018 CMS MiniAOD stream was exposed by the CERN Open Data API in this audit.

| audit_utc                        | run_era   | primary_dataset   | exact_query                    |   exact_hit_count | broad_query         |   broad_hit_count |   usable_real_miniaod_record_count | remote_feature_equivalent_validation_available   |
|:---------------------------------|:----------|:------------------|:-------------------------------|------------------:|:--------------------|------------------:|-----------------------------------:|:-------------------------------------------------|
| 2026-06-22T08:56:23.359441+00:00 | Run2017   | MET               | CMS MET Run2017 MINIAOD        |                 0 | CMS Run2017 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2017   | HTMHT             | CMS HTMHT Run2017 MINIAOD      |                 0 | CMS Run2017 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2017   | JetHT             | CMS JetHT Run2017 MINIAOD      |                 0 | CMS Run2017 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2017   | SingleMuon        | CMS SingleMuon Run2017 MINIAOD |                 0 | CMS Run2017 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2018   | MET               | CMS MET Run2018 MINIAOD        |                 0 | CMS Run2018 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2018   | HTMHT             | CMS HTMHT Run2018 MINIAOD      |                 0 | CMS Run2018 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2018   | JetHT             | CMS JetHT Run2018 MINIAOD      |                 0 | CMS Run2018 MINIAOD |                 0 |                                  0 | False                                            |
| 2026-06-22T08:56:23.359441+00:00 | Run2018   | SingleMuon        | CMS SingleMuon Run2018 MINIAOD |                 0 | CMS Run2018 MINIAOD |                 0 |                                  0 | False                                            |

## Interpretation

This is an availability result, not a physics result. It means the next truly
new-era CMS validation cannot currently be executed from this portal route.
The completed Run2015D and Run2016H remote validations remain useful independent
real-data checks, but they are not a replacement for a Run2017/2018 validation.
