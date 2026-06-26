# CMSSW Real Collision 20GB Run Guide

## What This Step Is For

The 20.789 GiB dataset is real CMS Run2016G MiniAOD collision data. Python/uproot can read some visible jet leaves, but proper MiniAOD physics extraction should be done with CMSSW.

CMSSW is needed for:

- MET pt and phi from `slimmedMETs`
- jets from `slimmedJets`
- muons from `slimmedMuons`
- electrons from `slimmedElectrons`
- b-tag discriminator values
- event identifiers: run, lumi, event
- trigger and reconstruction-quality information if added later

## Current Local Paths

Project folder:

```powershell
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary
```

Real CMS data folder:

```powershell
D:\cern_open_data\nframe_stage2_real_collision_20gb
```

Real-data filelists:

```powershell
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\filelists_real_collision_20gb
```

Existing CMSSW extraction package to reuse:

```powershell
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction
```

## Check Docker

Run this in PowerShell:

```powershell
docker --version
docker info
```

If `docker --version` works but `docker info` fails with a pipe or daemon error, open Docker Desktop and wait until it says the Linux engine is running.

## Enter A CMS Open Data / CMSSW Environment

The local Windows shell does not have `cmsRun` or `scram`. Those normally run inside a CMS Open Data VM/container.

Use a compatible CMS Open Data image/environment for UL2016 MiniAODv2. Once Docker Desktop is running, the container must mount:

- the data directory as `/data`
- the existing CMSSW extraction package as `/work`

Example shape of the command:

```powershell
docker run --rm -it `
  -v "D:\cern_open_data\nframe_stage2_real_collision_20gb:/data" `
  -v "D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction:/work" `
  <CMS_OPEN_DATA_IMAGE_FOR_UL2016_MINIAOD> `
  /bin/bash
```

Replace `<CMS_OPEN_DATA_IMAGE_FOR_UL2016_MINIAOD>` with the actual CMS Open Data image Darren or CMS documentation specifies for UL2016 MiniAODv2.

## Run A Small Test First

Inside the container:

```bash
cd /work
export SAMPLE_ID=cms_met_run2016g_collision
export NFRAME_INPUT_DIR=/data
export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}
export NFRAME_TEST_MAXEVENTS=1000
export NFRAME_MAXEVENTS_FULL=-1
bash /work/run_one_sample.sh
```

Repeat for:

```bash
export SAMPLE_ID=cms_jetht_run2016g_collision
bash /work/run_one_sample.sh

export SAMPLE_ID=cms_singlemuon_run2016g_collision
bash /work/run_one_sample.sh
```

## Expected Test Outputs

For each sample:

```text
outputs/<sample_id>/event_features_test.csv
outputs/<sample_id>/cmsrun_test.log
```

The test CSV should be non-empty and should include at least:

- `run`
- `lumi`
- `event`
- `MET_pt`
- `MET_phi`
- `N_jets_30`
- `N_jets_50`
- `HT`
- `leading_jet_pt`
- `subleading_jet_pt`
- `N_muons`
- `N_electrons`
- `N_btags_medium`

## Run Full Extraction Only After The Test Works

Inside the same container:

```bash
cd /work

export SAMPLE_ID=cms_met_run2016g_collision
export NFRAME_INPUT_DIR=/data
export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}
export NFRAME_MAXEVENTS_FULL=-1
bash /work/run_one_sample.sh

export SAMPLE_ID=cms_jetht_run2016g_collision
export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}
bash /work/run_one_sample.sh

export SAMPLE_ID=cms_singlemuon_run2016g_collision
export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}
bash /work/run_one_sample.sh
```

## Important Interpretation Rule

If CMSSW extraction has not run, do not treat the Python/uproot jet-only table as the full boundary model. It is a useful fallback for visible-activity structure, but the proper boundary-stress model needs MET and reconstruction variables from CMSSW.

