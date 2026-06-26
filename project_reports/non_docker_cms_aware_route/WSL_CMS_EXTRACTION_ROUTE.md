# WSL CMS Extraction Route

## Current Status

`wsl.exe` exists, but the checks did not show a usable installed Linux distribution.

Observed:

```powershell
wsl --status
wsl -l -v
```

The commands returned WSL usage/help-style output rather than a list of usable distributions. That means WSL may be available as a Windows feature, but Ubuntu or another Linux distribution is not currently configured for this workflow.

## What A Working WSL Route Would Need

A usable WSL route needs:

- Ubuntu or another Linux distribution installed.
- D: drive mounted under `/mnt/d`.
- Access to the project folder:

```bash
/mnt/d/Gamer\ File/My\ Work/The\ PhD/Extra/Nframe
```

- Access to the real CMS data folder:

```bash
/mnt/d/cern_open_data/nframe_stage2_real_collision_20gb
```

- Python/ROOT/FWLite or a CMS Open Data-compatible CMSSW environment inside Linux.

## Checks To Run Later

From PowerShell:

```powershell
wsl -l -v
wsl -d Ubuntu -- bash -lc "ls /mnt/d && python3 --version"
wsl -d Ubuntu -- bash -lc "which root || true; which cmsRun || true; which scram || true"
```

If Docker Desktop WSL integration is enabled later:

```powershell
wsl -d Ubuntu -- bash -lc "docker --version && docker info"
```

## Recommendation

WSL is promising only after a Linux distribution is installed and verified. It may be more reliable than native Windows ROOT for CMS software, but it is still a setup step rather than an immediate extraction route in the current environment.

