# N-Frame CMS MiniAOD Full Event Extraction

This project is for extracting event-level N-Frame boundary-access variables from the local CMS Run2016G MiniAOD subset.

Local data path:

`D:/cern_open_data/cms_met_run2016g_miniaod_10gb`

The full extraction requires a compatible CMS Open Data CMSSW Docker/container or VM. Plain Python/uproot cannot read all MiniAOD EDM objects needed for MET, leptons, and b-tags.

Scientific scope: this is event-feature extraction and boundary-score construction only. It is not a SUSY search, not a hidden-symmetry claim, and not a Standard Model background comparison.

