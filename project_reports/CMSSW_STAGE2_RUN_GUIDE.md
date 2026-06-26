# CMSSW Stage 2 Run Guide

This guide is for running the full CMS MiniAOD extraction on the five Stage 2 ROOT files.

The lightweight Python/uproot pass already opened the files and extracted jets, but MiniAOD is an EDM format. For proper event-level variables we still need CMSSW to read:

- `slimmedMETs`
- `slimmedJets`
- `slimmedMuons`
- `slimmedElectrons`
- b-tag discriminator values on jets

## Current Local Status

The following commands were checked on the Windows host:

```powershell
where.exe docker
where.exe cmsRun
where.exe scram
```

Result:

```text
docker not found
cmsRun not found
scram not found
```

So CMSSW was **not** run locally in this Codex pass. Docker Desktop or a CMS Open Data VM/container is still required.

## Stage 2 Inputs

Host data folder:

```text
D:\cern_open_data\nframe_stage2
```

CMSSW work package already prepared:

```text
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction
```

Desired Stage 2 CMSSW output folder:

```text
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\cmssw_event_features
```

Run plan:

```text
nframe_cms_stage2_event_boundary\results\tables\cmssw_stage2_run_plan.csv
```

Per-sample filelists:

```text
nframe_cms_stage2_event_boundary\data\cmssw_filelists
```

## What To Install

Use either:

1. Docker Desktop plus a compatible CMS Open Data CMSSW image for UL2016 MiniAODv2, or
2. the CMS Open Data VM with a compatible CMSSW release.

The exact image name depends on the CMS Open Data environment you choose. Replace:

```text
<cms-open-data-cmssw-image>
```

with the actual image.

## One-Sample Docker Command Template

Example for the MET real collision sample:

```powershell
$Image = "<cms-open-data-cmssw-image>"
$Work = "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction"
$Input = "D:\cern_open_data\nframe_stage2\cms_met_run2016g_collision\30509"

docker run --rm -it `
  -v "${Work}:/work" `
  -v "${Input}:/data" `
  -e "SAMPLE_ID=cms_met_run2016g_collision" `
  -e "NFRAME_INPUT_DIR=/data" `
  -e "NFRAME_OUTPUT_DIR=/work/outputs/cms_met_run2016g_collision" `
  -e "NFRAME_TEST_MAXEVENTS=1000" `
  -e "NFRAME_MAXEVENTS_FULL=-1" `
  $Image bash /work/run_one_sample.sh
```

This writes outputs inside the mounted work folder:

```text
nframe_cms_raw_multi_sample\cmssw_full_extraction\outputs\cms_met_run2016g_collision
```

After running, copy the sample output folder to:

```text
nframe_cms_stage2_event_boundary\data\processed\cmssw_event_features\cms_met_run2016g_collision
```

Repeat for each sample in `cmssw_stage2_run_plan.csv`.

## All Samples PowerShell Skeleton

```powershell
$Image = "<cms-open-data-cmssw-image>"
$Repo = "D:\Gamer File\My Work\The PhD\Extra\Nframe"
$Work = "$Repo\nframe_cms_raw_multi_sample\cmssw_full_extraction"
$Plan = Import-Csv "$Repo\nframe_cms_stage2_event_boundary\results\tables\cmssw_stage2_run_plan.csv"

foreach ($Row in $Plan) {
  docker run --rm -it `
    -v "${Work}:/work" `
    -v "$($Row.host_input_dir):/data" `
    -e "SAMPLE_ID=$($Row.sample_id)" `
    -e "NFRAME_INPUT_DIR=/data" `
    -e "NFRAME_OUTPUT_DIR=/work/outputs/$($Row.sample_id)" `
    -e "NFRAME_TEST_MAXEVENTS=1000" `
    -e "NFRAME_MAXEVENTS_FULL=-1" `
    $Image bash /work/run_one_sample.sh
}
```

## What To Do After CMSSW Runs

Copy or move each output folder from:

```text
nframe_cms_raw_multi_sample\cmssw_full_extraction\outputs\<sample_id>
```

to:

```text
nframe_cms_stage2_event_boundary\data\processed\cmssw_event_features\<sample_id>
```

Then run:

```powershell
D:\Anaconda\python.exe .\nframe_cms_stage2_event_boundary\scripts\03_score_event_level_boundary.py
D:\Anaconda\python.exe .\nframe_cms_stage2_event_boundary\scripts\04_fit_event_level_boundary_validation.py
```

The scoring script prefers CMSSW outputs when they exist. If CMSSW outputs are absent, it falls back to the jet-only uproot table.

## Important Scientific Caution

CMSSW extraction is needed before making claims about MET, leptons, b-tags, displacement, or lifetime. The current Python/uproot extraction is useful but incomplete.

