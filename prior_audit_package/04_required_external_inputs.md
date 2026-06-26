# Inputs Still Required for a Credible Claim

## Current hard gaps

1. Full-access Z-to-neutrinos and inclusive-top UL16 MC records or authoritative record-level `sumGenWeights`. Current records in the local manifest expose only partial online files for exact scans.
2. Complete QCD and diboson `GenFilterInfo` scans. The remote campaign has started but remains partial.
3. Stream-specific trigger efficiency information, especially a complete SingleMuon path union/plateau and its data/MC scale factor.
4. A certified-data selection and matched MC object/reconstruction configuration for every control and validation region.
5. An independent held-out dataset/era after the full protocol is frozen.

## What Gemini should not do

- Do not tune OPQ coefficients, quantile edges, jet bins or nuisance widths to force control closure.
- Do not use independent per-sample percentile thresholds as a discovery statistic.
- Do not combine MiniAOD, NanoAOD, AOD or ATLAS Z values into one significance.
- Do not call a control mismatch an N-Frame trace or SUSY evidence.

## Efficient acquisition route

Prefer remote XRootD reads and resumable `LuminosityBlocks/GenFilterInfo` scans for full-online records. If full records are not publicly online, obtain an official generated-event/sumweight source or choose a fully accessible replacement sample and document the coverage change. Avoid downloading the full ROOT corpus locally.
