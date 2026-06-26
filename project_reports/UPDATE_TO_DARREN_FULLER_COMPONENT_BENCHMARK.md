# Update to Darren: Fuller Component MiniAODSIM Benchmark

Date: 2026-06-09

## Stage 1: What we added

We moved from reduced NanoAOD-style benchmark checks to MiniAODSIM files where packed candidates and secondary vertices are available. This lets us test the fitted N-Frame equation with fuller versions of P_reconstruction and P_displacement_proxy.

## Stage 2: What worked

CMSSW extraction succeeded for QCD HT1000to1500, QCD HT700to1000, and WJetsToLNu, giving 1447 fuller-component simulated background events. All successful samples had secondary-vertex and packed-candidate information.

## Stage 3: Main finding

The high-HT QCD MiniAODSIM sample is a strong boundary mimic. Its q95 and q99 boundary-tail fractions are higher than the earlier SMS-T5Wg benchmark, so the previous signal-like tail result is not specific to SUSY-like samples.

## Stage 4: What failed

The planned SingleTop and compressed T2tt files were listed in the metadata but were missing at the advertised CERN EOS paths. Because no MiniAODSIM signal file survived download, we could not build a true fuller-component signal-vs-background trace direction.

## Stage 5: Interpretation

This qualifies the N-Frame interpretation rather than strengthens it unambiguously. It supports the idea that the fitted boundary finds unusual high-energy/high-complexity event structure, but it also shows that Standard Model high-HT QCD can occupy the same boundary region.

## Next task

Locate an accessible MiniAODSIM signal sample and repeat the fuller-component benchmark against the existing high-HT QCD fuller backgrounds.