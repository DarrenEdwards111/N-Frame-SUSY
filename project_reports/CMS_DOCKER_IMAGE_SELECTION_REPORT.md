# CMS Docker Image Selection Report

## Target Data

The downloaded files are real CMS Run2016G UL2016 MiniAODv2 files. The relevant CMSSW release indicated by the earlier record context is `CMSSW_10_6_30`.

## Best-Matching Image

The best-matching official CMS Open Data image is:

```text
cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700
```

This is the image listed by Docker Hub for `CMSSW_10_6_30` with `slc7_amd64_gcc700`, and it is also the image used in the CERN Open Data Docker guide for CMSSW 10_6_30.

## Candidate Images Tested

Results were written to:

```text
results\tables\cms_docker_image_tests.csv
results\logs\cms_docker_image_tests.log
```

Images attempted:

- `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700`
- `cmsopendata/cmssw_10_6_30`
- `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest`
- `cmssw/cc7`
- `cmssw/cms`

## What Happened

The first and most relevant image pull started, but failed inside Docker's containerd storage:

```text
failed to copy: failed to send write: write /var/lib/desktop-containerd/.../data: input/output error
```

After that, subsequent image pulls failed with Docker metadata write errors:

```text
write /var/lib/desktop-containerd/daemon/io.containerd.metadata.v1.bolt/meta.db: input/output error
```

Docker image listing and disk-use commands also started failing with an input/output error on an expected blob.

## Local Disk/Docker State

PowerShell drive check showed:

```text
C: free = 0 bytes
D: free = about 43.4 GB
G: free = about 14.7 GB
```

Docker's root directory is reported as:

```text
/var/lib/docker
```

Under Docker Desktop on Windows, that storage is normally backed by Docker Desktop's internal Linux disk image, commonly stored under the Windows user profile on C:. The zero free space on C: is therefore the likely immediate blocker.

## Conclusion

The image selection is clear, but the image could not be installed because Docker's storage became unhealthy during the large image pull. This is an environment/disk-space issue, not evidence that the CMS image or extraction package is wrong.

Recommended image after Docker storage is repaired:

```powershell
docker pull cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700
```

