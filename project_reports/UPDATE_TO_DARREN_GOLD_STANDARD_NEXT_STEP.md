# Update To Darren: Gold-Standard Next Step

We now have a real-data-only CMS Open Data subset of 20.789 GiB across MET, JetHT, and SingleMuon Run2016G MiniAOD. This satisfies the requested at least 10 GB real-data requirement. I have treated this as the first real-data boundary-estimation layer rather than a SUSY discovery test.

All 9 ROOT files were validated and all 9 opened successfully with uproot. The `Events` tree is visible in every file. A lightweight Python extraction produced 665,902 event rows, but only for visible jet-level features. It extracted jet multiplicity, HT, leading/subleading jet pt, sum jet pt, and related visible-activity variables.

The current fallback boundary score therefore measures visible jet boundary structure only. JetHT is strongly enriched in the high-boundary tail, which is expected because the available score is mainly based on jets and HT:

- JetHT: mean boundary z about 0.998, with 24.48% of events in the global top 5%
- MET: mean boundary z about -0.014, with 2.89% in the global top 5%
- SingleMuon: mean boundary z about -0.278, with 0.80% in the global top 5%

This is a useful pipeline validation, but it is not yet the full N-Frame boundary-stress test. The missing-information and reconstruction-stress components require MET, leptons, b-tags, event IDs, and ideally trigger/quality information. Those require CMSSW extraction from MiniAOD.

The immediate technical blocker is that Docker is installed, but Docker Desktop's Linux engine was not running, and `cmsRun`/`scram` are not available directly in Windows PowerShell. Once Docker Desktop is running, the next step is a 1000-event CMSSW test extraction for one MET file, one JetHT file, and one SingleMuon file. If that validates, we run the full extraction over all 9 files and recompute the boundary score with MET, HT, jets, leptons, and b-tags.

I would not download more data yet. The current 20.789 GiB is enough to validate the real-data extraction and scoring pipeline. More data only becomes useful after the CMSSW layer works.

