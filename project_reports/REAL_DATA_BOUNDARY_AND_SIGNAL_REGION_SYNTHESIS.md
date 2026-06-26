# Real Data Boundary And Signal Region Synthesis

## 1. What The Real CMS Collision Dataset Contains

The current real-data subset contains 9 CMS Run2016G MiniAOD ROOT files, totalling 20.789 GiB:

- MET record 30509: 3 files, 7.467 GiB
- JetHT record 30508: 4 files, 5.857 GiB
- SingleMuon record 30513: 2 files, 7.465 GiB

These are real CMS collision MiniAOD files, not simulated signal samples. They satisfy the requested at least 10 GB real-data requirement.

## 2. What Was Extractable

Python/uproot could open all 9 files and see the `Events` tree in all files. A fallback extraction produced 665,902 event rows.

Extracted variables:

- sample ID and source file
- event index within file
- jet multiplicity
- jets with pt > 30 GeV
- jets with pt > 50 GeV
- HT from jets with pt > 30 GeV
- leading and subleading jet pt
- leading jet eta/phi
- sum jet pt
- jet mass sum
- hadron-flavour proxy where available

Not extracted in the Python fallback:

- MET pt/phi
- run/lumi/event IDs
- muon and electron counts
- b-tag discriminator values
- trigger decisions
- genuine lifetime/displacement variables

CMSSW is still required for the serious event-level boundary model.

## 3. What The N-Frame Boundary Score Measured

The current score is a visible-jet boundary score, not the full N-Frame boundary-stress score.

Available components:

- `R_multiplicity`
- `R_reconstruction`

Unavailable components:

- `R_missing`
- `R_compression_proxy`
- `R_lifetime_proxy`
- `R_displacement_proxy`

Missing components were kept as missing values, not replaced with zero.

## 4. What High-Boundary Real Events Look Like

High-boundary events in this fallback pass are events with high visible jet activity: more selected jets, larger HT, larger sum jet pt, and greater visible reconstruction complexity.

The strongest sample-level separation is JetHT versus the other two samples. That is expected because the current score is mostly jet-based.

## 5. Whether MET, JetHT, And SingleMuon Differ As Expected

Yes, for the limited jet-only score:

| sample | events | mean boundary z | top 10% | top 5% | top 1% | mean HT | mean N jets > 30 |
|---|---:|---:|---:|---:|---:|---:|---:|
| JetHT | 98,145 | 0.998 | 42.50% | 24.48% | 5.08% | 593.887 | 3.564 |
| MET | 227,443 | -0.014 | 7.52% | 2.89% | 0.56% | 199.269 | 1.789 |
| SingleMuon | 340,314 | -0.278 | 2.29% | 0.80% | 0.12% | 97.325 | 1.460 |

JetHT is highly enriched in the top visible-boundary tail. This is compatible with the score definition, but it is not yet evidence of hidden SUSY-like missing structure.

## 6. Relation To Earlier Signal-Region Topology Finding

The earlier signal-region analysis found:

- 752 signal regions
- 73 rare/topology-stressed rows
- 679 nonrare rows
- rare mean abs(Z_capped_3): about 2.0137
- nonrare mean abs(Z_capped_3): about 1.1683
- difference: about 0.8454
- Welch p about 2.23e-8
- effect strongly influenced by ATLAS-SUSY-2018-42-eff
- excluding that block weakens the result

The real-data result is directionally consistent only at a broad level: high-boundary scores identify topology-stressed visible event regions. However, the current event-level score lacks MET and object-level reconstruction variables, so it cannot yet test the missing-information part of Darren's target.

## 7. What Remains Weak

- CMSSW extraction did not run because Docker Desktop's Linux engine was not available.
- MET is unavailable in the fallback table.
- Leptons and b-tags are unavailable in the fallback table.
- There is no direct simulation comparison in this real-data pass.
- The visible-jet tail enrichment is expected for JetHT and therefore not surprising by itself.

## 8. What Would Strengthen The Evidence Next

The next strongest step is to run CMSSW extraction and compute the full event-level boundary score with MET, jets, leptons, b-tags, and event identifiers.

After that:

- test whether high-boundary tails remain structured across files
- test whether MET-driven high-boundary tails differ from JetHT-only visible tails
- compare with published SUSY signal-region anomalies only as a later synthesis layer
- expand data only if high-boundary tails are sparse or unstable

## 9. Falsification Criteria

The N-Frame boundary-trace interpretation would weaken if:

- full CMSSW extraction shows no stable high-boundary tails
- high-boundary regions are fully explained by primary dataset selection alone
- MET, HT, lepton, and b-tag components do not form repeatable patterns across independent files
- larger real-data samples erase the apparent structure
- the event-level real-data structure fails to connect with published signal-region topology stress once dominant outlier blocks are controlled

