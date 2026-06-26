# Do We Need More Real Data?

## Short Answer

Not yet. Fix CMSSW extraction before downloading more data.

## Is 20.789 GiB Enough For The Current Extraction/Validation Step?

Yes. The current subset contains 9 real CMS MiniAOD files and produced 665,902 event rows in the Python/uproot fallback. That is enough to validate the pipeline shape and expose the current technical blocker.

## How Many Events Were Extracted?

665,902 event rows were extracted with the Python/uproot fallback.

## Are High-Boundary Tails Sparse?

No, not in the fallback score. The top 5% contains about 33,295 events. However, this is a visible-jet score only, so tail size does not answer the missing-energy/boundary question yet.

## Are Results Stable Across Files?

File-level tables have been written, but stability should be judged after CMSSW extraction because the current score is missing MET, leptons, b-tags, and reconstruction-quality variables.

## Is Another Run2016G File Range Needed?

Not before CMSSW works.

## Should We Expand To 50 GB?

Not yet. If CMSSW extraction works and high-boundary tails are sparse or unstable, then a controlled expansion to 50 GB real collision data would be reasonable.

## Should We Add Another Real Primary Dataset?

Not yet. MET, JetHT, and SingleMuon are already a sensible first cross-check set. Adding more primary datasets before proper extraction would increase complexity without resolving the current blocker.

## Should We Use NanoAOD Instead?

NanoAOD would be much easier for Python extraction and could be useful as a parallel learning path. However, Darren specifically wanted real/raw-ish CMS data, and MiniAOD is the better compromise already downloaded here. NanoAOD should be considered if we need a quick independent validation of the scoring logic.

## Should We Move To RAW/RECO?

Only if detector-level variables are explicitly required. RAW/RECO would be heavier and harder. MiniAOD is the right next layer for MET, jets, leptons, and b-tags.

## Decision

Do not download more now. The correct next action is to start Docker Desktop, enter a compatible CMSSW/Open Data environment, run a 1000-event CMSSW extraction test, and then run the full 9-file extraction if the test passes.

