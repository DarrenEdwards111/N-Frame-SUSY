# CMSSW Extraction Status Report

## Status

CMSSW extraction was not run in this session.

## Availability Checks Attempted

PowerShell command:

```powershell
docker --version
```

Result:

```text
Docker version 29.5.2, build 79eb04c
```

PowerShell command:

```powershell
docker info --format '{{.ServerVersion}}'
```

Result:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running
```

PowerShell command:

```powershell
cmsRun --help
```

Result:

```text
cmsRun is not recognised in the Windows PowerShell environment.
```

PowerShell command:

```powershell
scram --help
```

Result:

```text
scram is not recognised in the Windows PowerShell environment.
```

## Meaning

Docker is installed, but Docker Desktop's Linux engine was not running, so a CMS Open Data container could not be started. `cmsRun` and `scram` are also not available directly in Windows PowerShell, which is expected unless a CMS environment has already been entered.

## What Was Still Completed

- All 9 real CMS MiniAOD ROOT files were validated.
- All 9 files opened with uproot.
- `Events` trees were visible in all 9 files.
- A Python/uproot fallback extracted visible jet-level event features from the real data.

## What Must Happen Next

1. Open Docker Desktop.
2. Wait until the Linux engine is running.
3. Use a CMS Open Data-compatible CMSSW image/environment for UL2016 MiniAODv2.
4. Mount the real data folder and the existing CMSSW extraction package.
5. Run a 1000-event test extraction for MET, JetHT, and SingleMuon.
6. Only after the test validates, run the full 9-file extraction.

## Current Limitation

Until CMSSW runs, the proper N-Frame components involving MET, leptons, b-tags, triggers, and reconstruction-quality variables remain unavailable. The current analysis can only score visible jet-activity boundary structure from the Python/uproot fallback.

