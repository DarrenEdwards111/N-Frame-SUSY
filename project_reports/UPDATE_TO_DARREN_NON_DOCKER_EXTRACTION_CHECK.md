# Update To Darren: Non-Docker Extraction Check

We have 20.789 GiB of real CMS Run2016G collision MiniAOD across MET, JetHT, and SingleMuon. The first fallback extraction opened all 9 files and produced 665,902 event rows, but only with jet-level features.

Because you suggested Docker may not be necessary, I ran a deeper non-Docker extraction investigation before going back to CMSSW/Docker.

## What We Found

The MiniAOD files do contain the expected CMS objects by name:

- `slimmedMETs`
- `slimmedJets`
- `slimmedMuons`
- `slimmedElectrons`
- trigger products
- packed PF candidates
- primary vertices
- secondary-vertex/track/displacement-related candidates

Generic Python/uproot can read several decomposed numeric leaves:

- jet pt, eta, phi, mass
- jet hadron/parton flavour proxies
- packed PF candidate leaves, including encoded `dxy` and `dz`
- primary vertex position and quality leaves

Using those, I built an improved non-Docker event table with 665,902 rows and 41 columns. I then rescored the boundary model using available components.

## What Still Could Not Be Extracted Without A CMS-Aware Route

With the tools tested, the following are present but not accessible as usable physics quantities:

- MET pt/phi
- run/lumi/event IDs
- muon and electron counts/kinematics
- experimental b-tag discriminator values
- named trigger decisions

This does not prove they are impossible to extract without Docker. It means they were not accessible with generic uproot, and PyROOT/ROOT are not installed in the current environment.

## Improved Boundary Result

The improved non-Docker score now uses:

- multiplicity
- visible reconstruction complexity
- packed-candidate/vertex complexity
- an encoded displacement-like proxy from packed-candidate `dxy`/`dz`

It still does not include the true missing-information component, because MET is not readable in this route.

Top 5% boundary tail:

- JetHT: 16,672 events observed versus 4,907 expected
- MET: 15,702 events observed versus 11,372 expected
- SingleMuon: 922 events observed versus 17,016 expected

This is more interesting than the pure jet-only fallback because MET events are also enriched in the improved high-boundary tail. But it is still not a full SUSY or missing-information result because actual MET pt is missing.

## Practical Next Step

Docker itself is not the point. The point is a CMS-aware MiniAOD extraction route.

The next practical step is one of:

1. Try installing/using PyROOT or FWLite in a compatible conda/ROOT environment as a non-Docker route.
2. Use CMSSW through Docker or a CMS Open Data VM if that is faster.

Based on the evidence so far, generic uproot alone is not enough for the full N-Frame boundary model.

