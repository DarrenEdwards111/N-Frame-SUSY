# CMSSW Full MiniAOD Extraction Setup

This folder is the next-step package for the raw CMS data.

It exists because plain Python can only read part of MiniAOD. CMSSW can unpack the real CMS objects:

- `slimmedMETs`
- `slimmedJets`
- `slimmedMuons`
- `slimmedElectrons`
- b-tag discriminator values on jets

That gives the first proper event-level boundary/topology table.

## What Is Already Prepared

Run this from PowerShell to build sample-specific plans from completed downloads:

```powershell
D:\Anaconda\python.exe .\nframe_cms_raw_multi_sample\scripts\04_prepare_cmssw_full_extraction.py
```

It writes:

```text
nframe_cms_raw_multi_sample\results\tables\cmssw_full_extraction_plan.csv
nframe_cms_raw_multi_sample\data\filelists_cmssw\
nframe_cms_raw_multi_sample\cmssw_full_extraction\outputs\
```

## How To Run One Sample In A CMS Container

The exact CMS Open Data image/VM depends on what is installed. The container/VM must have a compatible CMSSW release for UL2016 MiniAODv2.

Inside the container, mount:

- the raw ROOT file directory as `/data`
- this folder as `/work`

Then run:

```bash
export SAMPLE_ID=cms_met_run2016g_collision
export NFRAME_INPUT_DIR=/data
export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}
export NFRAME_TEST_MAXEVENTS=1000
export NFRAME_MAXEVENTS_FULL=-1
bash /work/run_one_sample.sh
```

Expected outputs per sample:

```text
outputs/<sample_id>/event_features_test.csv
outputs/<sample_id>/event_features_test_nframe_scored.csv
outputs/<sample_id>/event_features.csv
outputs/<sample_id>/event_features_nframe_scored.csv
outputs/<sample_id>/event_feature_validation.txt
outputs/<sample_id>/pseudo_signal_regions_from_cmssw.csv
outputs/<sample_id>/cmsrun_test.log
outputs/<sample_id>/cmsrun_full.log
```

## Plain-English Meaning

This is the step that turns raw detector events into a spreadsheet where each row is one event.

For each event it records things like:

- how much missing energy it has,
- how many jets it has,
- how many leptons it has,
- how many b-tagged jets it has,
- how compressed or busy the event looks.

Then we can ask whether the high-boundary/topology events behave like Darren's topology result.
