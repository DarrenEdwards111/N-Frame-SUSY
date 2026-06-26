# Update To Darren: CMS-Aware Route Check

We have enough real CMS data for the next test: 20.789 GiB of real Run2016G MiniAOD across MET, JetHT, and SingleMuon. The limiting factor is not data volume. It is whether the MiniAOD objects can be unpacked into MET, leptons, b-tags, triggers, and event identifiers.

Because you suggested Docker may not be necessary, I tested the local non-Docker CMS-aware route.

## What Already Works Without Docker

Generic Python/uproot can open all 9 files and extract 665,902 real event rows.

It can read:

- jets
- HT
- jet multiplicity
- packed PF candidate complexity
- vertex complexity
- encoded `dxy`/`dz`-like leaves as displacement-like proxies

That gives a useful partial boundary model, and it improved the earlier jet-only result.

## What Does Not Currently Work Without A CMS-Aware Environment

The files contain the expected objects by name, but the current generic tools cannot unpack them as physics quantities:

- MET pt/phi from `slimmedMETs`
- run/lumi/event from `EventAuxiliary`
- muon/electron counts and kinematics
- named trigger decisions
- experimental b-tag discriminator values

I also checked the local environment:

- PyROOT is not installed.
- FWLite is not available.
- ROOT command-line is not available.
- `cmsRun` and `scram` are not available.
- Docker is installed, but Docker Desktop's Linux engine is not running.
- WSL is not currently set up with a usable Linux distribution.

## Conclusion

Docker itself is not proven to be strictly required. The accurate conclusion is:

> A CMS-aware MiniAOD extraction environment is required. Docker is one route, but not the only possible route.

The next low-risk non-Docker test would be a separate conda ROOT environment, not modifying base Anaconda. However, local ROOT alone may still not include CMS FWLite dictionaries, so the CMS Open Data VM or CMSSW route may still be needed.

## Next Practical Step

Try a separate `nframe-root` conda environment only if we are happy to spend the setup time and disk space. If that fails to expose FWLite/CMS dictionaries, use the prepared CMSSW extraction package through Docker or a CMS Open Data VM.

