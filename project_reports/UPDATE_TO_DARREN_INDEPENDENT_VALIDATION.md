# Update To Darren: Independent Validation

Date: 2026-06-09

We attempted an independent validation of the fitted N-Frame boundary equation using real CMS Run2016H data only. No simulated or SUSY signal samples were used.

## What happened

The preferred MiniAOD validation files downloaded successfully, but CMSSW extraction could not run because Docker Desktop was not available. We therefore used the fallback NanoAOD route as a quick independent cross-check.

## Result

The NanoAOD validation is weak/partial. JetHT remains enriched and SingleMuon remains depleted, but MET does not remain enriched. Also, NanoAOD lacks the key secondary-vertex/displacement proxy and packed-candidate information from the fitted MiniAOD equation.

## Meaning

This does not invalidate the fitted boundary equation, but it does not strongly validate it either. The fair conclusion is that the independent validation is currently limited by data-tier differences.

## SUSY question

This is not evidence that SUSY was found and not a discovery claim.

## Next step

Start Docker Desktop and rerun the already-downloaded Run2016H MiniAOD extraction. That will test the full fitted boundary equation with the same variable families used in the derivation.