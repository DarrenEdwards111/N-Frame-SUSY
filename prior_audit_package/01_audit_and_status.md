# Audit and Current Status

## Invalidated headline claims

### CMS `7.76 sigma`

The script `264_remote_opq_exact_hybrid_sm_sideband_likelihood_three_sample.py` computes weighted quantile microbands separately in the MC template, anchors the template to the real-data 90-95% band, and tests the remaining relative shape. This is not an absolute SM yield prediction in a fixed physical score region. The strict exact-only component contains W3Jets and two TT-associated records, not complete Z-to-neutrinos, inclusive top, QCD and diboson coverage.

### ATLAS `10.80 sigma`

The ATLAS value was selected after inspecting four score variants on the same data. The chosen model's 1-2-jet 80-95% sideband has observed/expected `0.1549`, so the adjacent control region is not closed. The model uses a limited five-sample W/single-top set and takes absolute MC weights. It is exploratory only.

## Corrected CMS diagnostics

| Test | Control result | Consequence |
|---|---:|---|
| Frozen reference, exact-only | maximum control Z = 2.29 | fails stated closure threshold |
| Frozen reference, expanded metadata | maximum control Z = 7.41 | strong failure |
| Process-mixture transfer | 38.47, 19.69, 31.04 control Z | invalid MET transfer |
| Stream-matched plateau transfer | 14.62, 38.47, 31.27 control Z | trigger/offline cuts alone do not solve mismatch |

## Defensible present conclusion

OPQ-style scores show interesting high-tail differences across CMS Open Data streams. The present analysis does not isolate those differences from incomplete SM process modelling, trigger/reconstruction differences, or data/MC selection mismatch.
