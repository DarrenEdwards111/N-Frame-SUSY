# Is Docker Or CMSSW Actually Required?

## Conclusion

Partially. We can extract some variables without Docker, but not enough for the full N-Frame boundary model.

The strongest evidence from the non-Docker investigation is:

- MiniAOD objects are present in the files.
- Generic Python/uproot can read many decomposed numeric leaves.
- Generic Python/uproot cannot currently read the full CMS EDM objects needed for MET, muons, electrons, event IDs, trigger decisions, or experimental b-tag discriminators.
- PyROOT is not installed in the current Python environment.
- ROOT command line is not available on PATH.

So Docker specifically is not proven to be the only route. However, a CMS-aware extraction route is still needed for the full model. That could be CMSSW in Docker, CMSSW in a VM, FWLite/PyROOT in a suitable ROOT/CMSSW environment, or another CMS-aware MiniAOD reader.

## What Was Found And Readable

Readable with non-Docker uproot:

- jet pt, eta, phi, mass
- jet hadron-flavour proxy
- jet parton-flavour proxy
- packed PF candidate pt-like leaves
- packed PF candidate `dxy`/`dz` encoded leaves
- primary vertex position and quality leaves
- some product-present flags for MET, muons, electrons, triggers, photons, taus, and filters

Not readable as physics quantities with the tested tools:

- MET pt/phi from `slimmedMETs`
- muon counts/kinematics from `slimmedMuons`
- electron counts/kinematics from `slimmedElectrons`
- run/lumi/event IDs from `EventAuxiliary`
- named HLT trigger decisions from `TriggerResults`
- experimental b-tag discriminator values

## Evidence From Readability Tests

The candidate branch test produced:

- `jets`: 7 readable tested candidates
- `packed_candidates`: 7 readable tested candidates
- `vertices`: 5 readable tested candidates
- `met`: only product-present flag readable, not MET pt/phi
- `muons`: only product-present flag readable
- `electrons`: only product-present flag readable
- `event_ids`: not readable through tested uproot path
- `triggers`: product-present flags readable, not named decisions

Detailed table:

```text
results\tables\candidate_branch_read_tests.csv
```

## Practical Decision

Darren is right that Docker may not be necessary for every useful boundary variable. We improved the non-Docker table substantially without Docker.

But for the full requested boundary model, especially the missing-information component, the current evidence says a CMS-aware environment is still needed. That does not have to mean Docker specifically, but it does mean generic uproot alone is not enough.

