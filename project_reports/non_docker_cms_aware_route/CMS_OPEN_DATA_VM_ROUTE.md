# CMS Open Data VM Route

## Purpose

A CMS Open Data VM is a non-Docker route to a CMS-aware environment. It can provide `cmsRun`, `scram`, CMSSW, FWLite, and the CMS dictionaries needed to unpack MiniAOD objects.

## Why This Helps

Generic uproot can read decomposed numeric leaves such as jets, packed candidates, and vertices. It cannot currently unpack the full CMS object layer in this setup:

- `slimmedMETs`
- `slimmedMuons`
- `slimmedElectrons`
- `EventAuxiliary`
- `TriggerResults`
- b-tag discriminator methods on `pat::Jet`

A CMS Open Data VM should be able to access those through CMSSW/FWLite.

## Local Data Access

The VM would need access to:

```text
D:\cern_open_data\nframe_stage2_real_collision_20gb
```

and to the existing CMSSW extraction package:

```text
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction
```

Depending on the VM software, this can be done with a shared folder or by copying the small extraction package into the VM while mounting/copying the ROOT files.

## Existing Package To Run

Existing package:

```text
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction
```

Inside a CMS-aware environment, run the sample wrapper:

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
cms_jetht_run2016g_collision
cms_singlemuon_run2016g_collision
```

## Recommended First Test

Run only 1000 events from one file in each real sample first. Validate that the CSV contains:

- run/lumi/event
- MET pt/phi
- jets and HT
- muons/electrons
- b-tag counts/discriminator status

Only then run all 9 files.

