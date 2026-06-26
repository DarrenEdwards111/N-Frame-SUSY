# Stage 2 Synthesis With Signal-Region Results

## 1. What Was Downloaded

Five CMS Open Data ROOT files were found under:

```text
D:\cern_open_data\nframe_stage2
```

They cover three real 2016 CMS collision control samples and two official CMS simulated SUSY-like signal samples.

## 2. Real Collision Data Versus Simulated Signal Data

Real collision controls:

- `cms_met_run2016g_collision`, record 30509
- `cms_jetht_run2016g_collision`, record 30508
- `cms_singlemuon_run2016g_collision`, record 30513

Official simulated signal samples:

- `sms_t5wg_mg1500_mlsp1_signal`, record 63465
- `susy_htoaa4b_m12_signal`, record 64906

## 3. What Python/uproot Could Extract

Python/uproot successfully opened all five files and found `Events` trees.

Event counts:

- JetHT: 17,433
- MET: 85,149
- SingleMuon: 172,994
- T5Wg signal: 30,214
- HToAA4B signal: 2,394

Total extracted partial event rows:

```text
308,184
```

The direct MiniAOD extraction was partial. It extracted jet-level variables:

- number of jets with pT > 30
- number of jets with pT > 50
- HT from selected jets
- leading jet pT
- subleading jet pT
- jet mass sum

MET, leptons, ordinary b-tags, displacement, and lifetime variables were not available through this lightweight route.

## 4. Whether CMSSW Was Needed And Whether It Ran

CMSSW is still needed for the full boundary model, because MiniAOD stores the important CMS objects in EDM format.

Needed objects:

- `slimmedMETs`
- `slimmedJets`
- `slimmedMuons`
- `slimmedElectrons`
- b-tag discriminator values on jets

CMSSW did not run locally in this pass. The Windows host did not have:

```text
docker
cmsRun
scram
```

A full run guide was created at:

```text
nframe_cms_stage2_event_boundary\reports\CMSSW_STAGE2_RUN_GUIDE.md
```

## 5. Event-Level Boundary Variables Computed

Because only jets were available, the current Stage 2 boundary score is a partial event-level score.

Computed:

- `R_multiplicity`: jet/object multiplicity stress
- `R_reconstruction`: HT, leading-jet, b-tag/lepton placeholders where available
- `B_boundary_equal_weight`
- `B_boundary_equal_weight_z`

Unavailable and explicitly marked missing:

- `R_missing`
- `R_compression_proxy`
- `R_lifetime_proxy`
- `R_displacement_proxy`

This means the current result is a **jet/reconstruction-only validation**, not the full N-Frame boundary model.

## 6. Did Simulated SUSY-Like Samples Have Higher Boundary Scores?

Yes for T5Wg. No clear general yes for HToAA4B.

Mean event-level boundary score z:

| sample | type | mean score z | global top 5% |
|---|---|---:|---:|
| `cms_jetht_run2016g_collision` | real | 0.6884 | 0.56% |
| `cms_met_run2016g_collision` | real | -0.1925 | 0.06% |
| `cms_singlemuon_run2016g_collision` | real | -0.3426 | 0.01% |
| `sms_t5wg_mg1500_mlsp1_signal` | simulated signal | 2.1195 | 50.43% |
| `susy_htoaa4b_m12_signal` | simulated signal | -0.1549 | 0.04% |

T5Wg was strongly higher than all three real collision controls:

- versus MET: mean difference 2.3120, Cohen's d 2.998
- versus JetHT: mean difference 1.4311, Cohen's d 2.434
- versus SingleMuon: mean difference 2.4621, Cohen's d 4.364

HToAA4B did not behave like the hard jet-rich T5Wg sample:

- very similar to MET by mean score
- lower than JetHT
- somewhat higher than SingleMuon

This is consistent with the earlier suspicion that HToAA4B needs b-tags, substructure, or CMSSW-level features.

## 7. Link To The Prior Signal-Region Result

The prior public ATLAS/CMS signal-region result found that rare/topology-stressed regions had larger anomaly magnitudes:

- rare mean `abs(Z_capped_3)`: 2.0137
- nonrare mean `abs(Z_capped_3)`: 1.1683
- p-value: 2.23e-8

Stage 2 aligns with that result in a limited way:

- The known hard SUSY-like T5Wg simulated sample is strongly high in event-level boundary score.
- That supports the idea that the boundary score can identify SUSY-like event structures.
- But because the current extraction is jet-only, this does not test missing-energy, lifetime, displacement, or compression properly.

## 8. What Remains Weak

Important weaknesses:

- The simulated signal data are not real observed SUSY.
- This cannot show that CERN missed SUSY.
- This cannot prove higher dimensions or an N-Frame boundary.
- Python/uproot extraction was incomplete.
- HToAA4B did not separate with the jet-only score.
- The full theory-relevant variables need CMSSW.

## 9. What Should Be Done Next

Next technical step:

1. Install Docker Desktop or use a CMS Open Data VM.
2. Run the prepared CMSSW extraction package.
3. Re-score events using MET, leptons, b-tags, and any available reconstruction variables.
4. Re-run the Stage 2 event-level validation.
5. Only after that, apply the fitted model back to real collision data alone and look for high-boundary tails.

## Required Caution Statements

The simulated signal data are not evidence of real observed SUSY.

This cannot show that CERN missed SUSY.

This can test whether N-Frame boundary variables identify known SUSY-like event structures.

The stronger later test would apply the fitted boundary model to real collision data only and look for high-boundary anomalies.

