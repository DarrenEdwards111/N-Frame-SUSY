# Audit of Gemini Script 277 and the 0.77 Sigma Null Result

## Verdict

Script `277_data_driven_pyhf_fit.py` is a substantial improvement over the earlier 7.76 and 5.75 sigma analyses. It uses a disjoint Run2016G reference and Run2016H holdout, fixed reference-derived score boundaries, and a real `pyhf` Poisson model. Its central finding is therefore important:

> Under this particular cross-era data-driven OPQ-shape model, Run2016H does not show a significant upper-tail excess: reported local Z is 0.77.

That makes the earlier discovery-style claims untenable. It does **not** make the analysis fully publication-grade or establish a validated SM background model.

## What is sound

- The reference and Run2016H holdout are disjoint by run, unlike the invalid Run2016G "fresh" claim in script 276.
- Calibration and score boundaries are derived on the reference then applied unchanged to the holdout.
- The final result is null rather than selected for a favourable excess.
- The output is consistent internally: 35 upper-band events are compared with a post-fit expectation of 31.72, yielding a small local deviation.

## Remaining limitations

| Item | What script 277 does | Why it prevents a final physics claim |
|---|---|---|
| Background normalisation | `mu_bkg` is profiled using all five MET bins, including the three bins it calls signal. | The reported q90-95/q95-97 pulls are post-fit checks, not independent validation. A control-only fit must be frozen before reading the upper bins. |
| Control regions | One MET channel only; no W, Z proxy, top or QCD channels. | It measures cross-era shape consistency, not a process-resolved SM prediction. |
| Shape uncertainty | A fixed 5% `histosys` variation is inserted without derivation. | There is no documented transfer uncertainty between 2016G and 2016H. |
| Trigger/object equivalence | Offline MET > 200 and some quality flags are used, but no exact HLT requirement or trigger-efficiency correction is applied in the SR mask. | The test is not a complete trigger-matched CMS selection. |
| Quality filtering | Calibration uses five filters; the final SR mask uses only three. | Selection is internally inconsistent. |
| Limits | No signal MC template, acceptance, efficiency, luminosity model or signal systematic is present. | It cannot set SUSY or generic cross-section limits. |
| Global interpretation | The score, thresholds, regions and prior scans were explored repeatedly. | The 0.77 is a model-specific local compatibility result, not a final global analysis statistic. |

## Correct wording

Use:

> A fixed-calibration, data-driven cross-era comparison of the selected MET shape found no statistically significant Run2016H upper-tail deviation relative to the Run2016G reference (local Z approximately 0.8 under the stated model).

Do not use:

- "perfect control closure";
- "fully publication-grade";
- "validated Standard Model background";
- "exclusion limits";
- any SUSY/hidden-sector inference from this result.

## Next valid test

1. Fit normalisation only in a predeclared control band such as q90-95.
2. Use q95-97 as a true validation band, excluded from the normalisation fit.
3. Freeze the transfer uncertainty from an independent era/file split or a bootstrap of reference files.
4. Predict q97-100 without allowing those bins to alter the background normalisation.
5. Report the result as a cross-era shape test until a process-resolved W/Z/top/QCD likelihood is available.

If that control-only prediction also gives a null result, it reinforces the conclusion that the current data do not support an N-Frame boundary-trace anomaly. If it does not, the discrepancy must be treated as a transfer-modelling issue before any physics interpretation.
