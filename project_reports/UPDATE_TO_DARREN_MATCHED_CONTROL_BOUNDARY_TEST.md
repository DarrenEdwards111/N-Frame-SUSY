# Update To Darren: Matched-Control Boundary Test

Date: 2026-06-08

## What we used

We used real CMS collision data only: 665,902 MiniAOD events from MET, JetHT and SingleMuon samples. No simulated samples were used.

## Why matched controls were needed

The earlier boundary tail was interesting but partly confounded by run/lumi concentration and quality-filter warnings. Matched controls test whether the same high-boundary events remain unusual when compared against nearby ordinary events from the same CMS context.

## What we matched on

Controls were matched on primary dataset, source file, run where possible, broad HLT trigger category, primary-vertex count, packed-candidate load and luminosity context. In the standard-clean analysis we matched every requested case with 5 controls on average.

## Result

After matching, the high-boundary events still differ from controls. The strongest surviving differences are reconstruction complexity, secondary-vertex proxy, jet/multiplicity structure, b-tag structure, visible energy and missing energy. Compression-like imbalance is weak after matching.

## What this means

This strengthens the claim that the boundary score is not only a simple trigger or data-quality artefact. However, the evidence is still qualified because the surviving structure looks strongly tied to reconstruction/event-topology stress.

## SUSY question

This is not direct evidence of SUSY and does not show that SUSY particles were found. The most cautious wording is that the result is trace-compatible with Darren?s boundary idea, but currently better described as a real-data boundary-stress region needing further parameter fitting.

## Next step

Use the matched case-control differences to fit N-Frame parameters, focusing first on reconstruction complexity, secondary-vertex proxy, b-tag structure, multiplicity, visible energy and missing energy.