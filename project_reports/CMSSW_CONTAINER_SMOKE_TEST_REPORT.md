# CMSSW Container Smoke Test Report

## Status

The CMSSW container smoke test was not run.

## Reason

The correct CMS Open Data image could not be pulled because Docker's internal storage failed during the image download.

Observed Docker error:

```text
input/output error
```

Drive status showed:

```text
C: free = 0 bytes
```

Docker image listing also failed after the interrupted pull, which suggests Docker's local layer store needs attention before more container work.

## Smoke Test That Should Run After Docker Storage Is Fixed

Use the selected image:

```text
cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700
```

Mounts:

```powershell
-v "D:\cern_open_data\nframe_stage2_real_collision_20gb:/data"
-v "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction:/work"
-v "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_outputs:/outputs"
```

Minimal command:

```powershell
docker run --rm `
  -v "D:\cern_open_data\nframe_stage2_real_collision_20gb:/data" `
  -v "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction:/work" `
  -v "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_outputs:/outputs" `
  cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700 `
  /bin/bash -lc "ls /data && ls /work && command -v cmsRun && command -v scram && cmsRun --help | head"
```

## Log

The failed image-selection and Docker state logs are in:

```text
results\logs\cms_docker_image_tests.log
results\logs\docker_status_after_fix.log
```

