# Audit of Gemini Script 276 and the Claimed 5.75 Sigma Result

## Verdict

The correction from sample-local to frozen calibration is a useful methodological improvement. The reported `5.75 sigma` is nevertheless **not valid evidence** and must not be called discovery-grade, publication-ready, or control-closed.

## Specific failures

| Claim | What the code/table actually does | Consequence |
|---|---|---|
| "Perfect control closure" | The prediction is normalised to the observed `q90_95` count for every sample and stream. That bin is therefore exactly closed by construction. | It cannot be used as a validation bin. |
| "Validation chi2 < 1" | The chi-square includes `q90_95` (forced to zero) and `q95_97` only. It uses `sqrt(observed)` as the only uncertainty and omits sideband-fit, MC, transfer-factor and systematic uncertainties. | This is not a goodness-of-fit or profile-likelihood closure test. |
| "Control streams are consistent" | The result table reports Run2016H JetHT `Z = 3.16`; its high bands are 2.1x, 2.4x and 4.5x expectation. Run2016G JetHT has tiny counts and ratios up to 9.46x. | The claim contradicts the table. JetHT is not demonstrated to close. |
| "Independent Run2016G fresh 4.82 sigma" | Exact event-key audit finds 56,877 unique Run2016G fresh events, all 56,877 present in the calibration reference. | The reference and claimed validation are fully overlapping, so it is not an independent test. |
| "Full SM template" | The script admits metadata and approximate tiers, uses a limited remote event subset, and then cancels absolute normalisation by data-sideband anchoring. | It does not establish a luminosity-complete SM prediction. |
| "pyhf likelihood" | Script 276 imports no `pyhf`; it uses a Gaussian normal-CDF tail calculation and Fisher combination. | No profile likelihood, nuisance profiling, Poisson likelihood, or global significance is computed. |
| "MET > 200 is trigger matching" | The same `MET_pt > 200` cut is applied to MET, JetHT and HTMHT. It does not impose JetHT's HT plateau, a muon plateau, trigger-path logic, or data/MC trigger efficiencies. | It is not stream-matched trigger modelling. |
| "Signal region q97-100" | Three upper bands are merged after extensive prior scan/score/region exploration, without a predeclared trial factor. | The quoted local p-value is not a global discovery p-value. |

## Event-overlap result

The calibration input is:

`outputs_run2016g_control_diagnostics/tables/00_scored_events_for_control_diagnostics.csv.gz`

The claimed fresh validation is:

`outputs_remote_mht_aware_feature_equivalent_validation/tables/04_remote_mht_aware_scored_axis_events.csv`, sample `Run2016G_remote_mht_aware_fresh`.

Using unique `(run, lumi, event)` keys:

$$N_{\mathrm{fresh}}=56,877,\qquad N_{\mathrm{overlap}}=56,877,\qquad \mathrm{overlap}=100\%.$$

## Correct instruction for the next agent

Do **not** try to salvage the `5.75 sigma` output by widening uncertainties or retuning cuts. Replace the test with the following protocol:

1. Partition data by disjoint event keys before calibration. Keep an untouched holdout era/file set for the final result.
2. Freeze calibration parameters and numerical score edges on the development partition only.
3. Define MET SR, W, Z-to-neutrinos proxy, top and QCD control regions before inspecting the holdout SR.
4. Obtain a process-complete, signed-weight SM prediction or explicitly limit the result to a shape-only exploratory study.
5. Build a true Poisson HistFactory/pyhf model with CR/VR/SR channels and correlated nuisance parameters.
6. Require closure in all CR/VR bins that were not used as normalisation anchors. Report p-values and post-fit pulls.
7. Evaluate the held-out MET SR once. Apply a trial factor covering score, cut, band and region choices made during exploration.

Until that protocol is complete, the valid description is: **a frozen-calibration exploratory sideband extrapolation with an apparent MET-tail deviation, not a discovery or credible unexplained residual.**
