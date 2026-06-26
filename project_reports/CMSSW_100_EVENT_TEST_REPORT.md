# CMSSW 100-Event Test Report

## Status

Not run.

## Reason

The selected CMSSW Docker image could not be pulled because Docker storage failed with input/output errors during the image download. The 100-event extraction gate depends on a working CMSSW container.

## Next Requirement

Free/repair Docker storage, then rerun the image pull and smoke test before attempting a 100-event extraction.

