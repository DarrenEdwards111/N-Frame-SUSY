# Control-Closure Reconstruction Specification

## Objective

Build a single predeclared profile likelihood that tests a fixed N-Frame score only after all control and validation regions are described by the same process-complete model.

The frozen score can remain

$$B_{OPQ}=0.344828O+0.517241P-0.137931Q,$$

but its numerical bin edges must be fixed once from a development dataset and applied identically to data and MC. Do not rank each input sample independently.

## The required model structure

JetHT and SingleMuon must not be required to reproduce the MET tail directly. They are distinct channels that constrain particular processes through transfer factors.

| Channel | Primary purpose | Typical required selection | Main constrained processes |
|---|---|---|---|
| MET SR | Blinded target | MET trigger plateau, lepton veto, fixed jet/b-tag/OPQ bins | summed prediction |
| MET validation bands | Shape validation | same as SR, lower frozen OPQ bands | all MET backgrounds |
| SingleMuon W CR | W normalisation/shape | one tight muon, transverse-mass window, matching muon trigger plateau | W+jets |
| Dilepton or photon Z CR | Z-to-neutrinos transfer | Z to mu-mu/e-e or photon plus jets, recoil matched to MET SR | Z-to-neutrinos |
| b-tag top CR | Top transfer | one lepton and one or more b tags, top-like mass or transverse mass | ttbar and single top |
| Low-DPhi/JetHT QCD CR | Multijet transfer | failed Delta-phi or dedicated prescaled hadronic selection | QCD/mismeasurement |

Each CR must have an MC transfer factor into the appropriate MET SR bin:

$$T_{p,r,b}=\frac{N^{MC}_{p,\mathrm{SR},b}}{N^{MC}_{p,\mathrm{CR},b}},$$

and the predicted yield is constrained by the observed control count, not by assuming another stream has the same score-tail shape.

## Required process model

For every region $r$ and frozen score bin $b$:

$$N^{SM}_{r,b}=\mathcal{L}\sum_p \sigma_p\epsilon_{p,r,b}
\frac{\sum_{i\in p,r,b}w_i}{\sum_{i\in p}w_i}.$$

Required $p$ families:

- Z-to-neutrinos + jets, binned consistently without double counting;
- W+jets;
- inclusive ttbar plus single top;
- diboson;
- QCD/multijet;
- rare top-associated and electroweak processes where non-negligible.

Use signed generator weights. Never discard negative-weight events.

## Non-negotiable data/MC equivalence checks

1. Certified luminosity JSON and run/lumi filtering for collision data.
2. Identical event-quality filters in data and MC where defined; document non-applicable filters.
3. Stream-specific trigger plateaus derived from exact trigger paths, plus data/MC efficiency scale factors and uncertainties.
4. Identical jet, lepton, b-tag, MET and overlap-removal definitions.
5. Fixed numerical OPQ boundaries, not per-dataset quantiles.
6. Data/MC comparisons of all pre-score inputs in every CR and validation band.

## Likelihood implementation

Use HistFactory/pyhf channels for all CR, VR and SR bins. Include correlated nuisance parameters for:

- luminosity;
- cross sections and generator-scale/PDF modelling;
- finite MC statistics;
- trigger efficiency;
- jet energy scale/resolution and unclustered MET;
- lepton and b-tag efficiencies;
- QCD transfer factor;
- Z/W/top process-transfer factors.

The SR must remain blinded until the post-fit model passes all CR and VR acceptance tests.

## Closure acceptance tests

Before unblinding the SR:

1. Every CR/VR has a post-fit goodness-of-fit p-value at least 0.05, with no predeclared exception.
2. No individual bin has a residual exceeding 3 standard deviations after the full correlated model.
3. Nuisance pulls are physically credible and constraints are not pathological.
4. Leave-one-era-out closure succeeds: construct on one era, validate on another.
5. Injection tests recover a known synthetic signal without bias.

Only then may the frozen MET SR p-value be converted to a local and trial-corrected global Z.

## Interpretation rule

If the CR/VR model closes and a held-out SR residual remains, the result is a credible unexplained collider-data residual. It is still not proof of SUSY or bulk-space particles without further experimental cross-checks. If CR/VR closure fails, report a background/reconstruction modelling limitation, not an anomaly.
