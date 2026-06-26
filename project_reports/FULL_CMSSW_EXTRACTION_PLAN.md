# Full CMSSW Extraction Plan

## Status

Full extraction is not ready to run.

## Gate Conditions

Before full extraction over all 9 ROOT files, we need:

1. Docker storage repaired.
2. `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700` pulled successfully.
3. Container smoke test passes.
4. 100-event extraction passes for MET, JetHT, and SingleMuon.
5. 1000-event extraction passes for MET, JetHT, and SingleMuon.

## Expected Inputs

Use sample-specific input directories:

```text
/data/cms_met_run2016g_collision/30509
/data/cms_jetht_run2016g_collision/30508
/data/cms_singlemuon_run2016g_collision/30513
```

## Runtime/Output Estimate

The current data volume is 20.789 GiB and 665,902 events were visible through uproot. CMSSW full extraction should be expected to take materially longer than the Python fallback because it loads CMS dictionaries and event objects. A safe initial expectation is tens of minutes rather than seconds, depending on Docker disk performance.

The CSV output should be much smaller than the ROOT input, likely hundreds of MB or less, but this should be confirmed after the 1000-event test.

## Decision

Do not run full extraction until the user confirms after the 1000-event test validates.

