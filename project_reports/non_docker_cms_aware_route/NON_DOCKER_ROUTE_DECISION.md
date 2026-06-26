# Non-Docker Route Decision

## Decision

B. Non-Docker extraction is partially enough.

We can extract useful variables without Docker, but the full N-Frame boundary model still needs a CMS-aware MiniAOD extraction environment.

## Evidence

What works now with generic non-Docker tools:

- All 9 MiniAOD files open with uproot.
- Jets are readable.
- HT and jet multiplicities are extractable.
- Packed PF candidate leaves are readable.
- Vertex leaves are readable.
- Encoded `dxy`/`dz`-like leaves are readable as proxies.
- Improved non-Docker table exists with 665,902 rows.

What does not work in the current local environment:

- PyROOT is not installed.
- FWLite is not available.
- ROOT command-line is not on PATH.
- `cmsRun` is not on PATH.
- `scram` is not on PATH.
- Docker CLI is installed, but Docker Desktop's Linux engine is not running.
- WSL does not currently show a usable installed Linux distribution.

What remains inaccessible through the tested route:

- MET pt/phi
- run/lumi/event IDs
- muon/electron kinematics or counts
- experimental b-tag discriminator values
- named trigger decisions

## Correct Wording

A CMS-aware MiniAOD extraction environment is required. Docker is one practical route, but not the only possible route.

Possible CMS-aware routes:

- CMSSW through Docker, once Docker Desktop is running.
- CMS Open Data VM.
- WSL with CMSSW/ROOT/FWLite configured.
- Separate conda ROOT/PyROOT environment as a test, although local ROOT alone may still lack CMS dictionaries.

## Practical Recommendation

The least invasive next experiment is a separate conda environment called `nframe-root`, not an install into base Anaconda. If that does not provide FWLite/CMS dictionaries, use the prepared CMSSW route through Docker or a CMS Open Data VM.

