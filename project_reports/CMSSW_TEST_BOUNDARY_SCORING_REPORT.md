# CMSSW Test Boundary Scoring Report

## Status

Not run.

## Reason

No CMSSW test event-feature CSV was produced because the selected CMS Open Data image could not be pulled. Docker storage failed with input/output errors during the image download, and the C: drive had 0 bytes free.

## Next Step

Repair/free Docker storage, pull `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700`, run the smoke test, then run the 100-event extraction gate.
