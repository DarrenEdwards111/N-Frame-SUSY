# Cloud Remote N-Frame Runbook

This runbook is for running the CMS Open Data N-Frame extraction without storing large ROOT files on the local D: drive.

## What This Does

The cloud route reads CERN Open Data files by remote `root://` or HTTP URL, extracts compact N-Frame event-feature CSV files, and keeps only those compact outputs. The raw CERN ROOT files are not permanently downloaded to the laptop.

This is not magic zero-data analysis: the cloud machine still reads bytes from CERN. The efficiency gain is that the laptop does not become the storage warehouse.

## Recommended Setup

Use a Linux cloud VM with:

- Docker installed.
- At least 4 vCPUs.
- 16 GB RAM or more.
- 100 GB temporary disk for logs, CMSSW scratch, and feature CSVs.
- Outbound network access to `eospublic.cern.ch`.

For MiniAOD, prefer a cloud VM over Google Colab because the current extractor uses the CMS Open Data CMSSW Docker image.

## Repository Pieces Needed

Copy this package to the cloud VM:

- `cloud_remote_nframe_package/cmssw_full_extraction`
- `cloud_remote_nframe_package/scripts/remote_xrootd`
- `cloud_remote_nframe_package/manifests`
- `cloud_remote_nframe_package/CLOUD_REMOTE_NFRAME_RUNBOOK.md`

The package intentionally excludes large local ROOT files and previous local extraction outputs.

## Smoke Test

From inside the unpacked package on the cloud VM:

```bash
cd cloud_remote_nframe_package
export NFRAME_CMSSW_WORK="$PWD/cmssw_full_extraction"
export NFRAME_REMOTE_OUT="$PWD/outputs_breakthrough_full_push_nframe_susy"
python scripts/remote_xrootd/smoke_test_xrootd_file.py \
  --url 'root://eospublic.cern.ch//eos/opendata/cms/mc/RunIISummer20UL16MiniAODv2/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/MINIAODSIM/106X_mcRun2_asymptotic_v17-v1/70000/028D83BD-509A-6845-BB42-081E49BBAE26.root' \
  --record-id 63094 \
  --process-family QCD \
  --max-events 100
```

Expected result:

- Docker starts `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700`.
- CMSSW reads the remote ROOT URL.
- A small `event_features.csv` appears under `cmssw_full_extraction/outputs/...`.

## Batch Run

After the smoke test:

```bash
export NFRAME_CMSSW_WORK="$PWD/cmssw_full_extraction"
export NFRAME_REMOTE_OUT="$PWD/outputs_breakthrough_full_push_nframe_susy"
python scripts/remote_xrootd/run_remote_miniaod_batch.py \
  --manifest manifests/manifest_priority1_top_dy_w_z_qcd.csv \
  --limit 3
```

Then merge completed feature files:

```bash
export NFRAME_CMSSW_WORK="$PWD/cmssw_full_extraction"
export NFRAME_REMOTE_OUT="$PWD/outputs_breakthrough_full_push_nframe_susy"
python scripts/remote_xrootd/merge_remote_batch_outputs.py \
  --ledger outputs_breakthrough_full_push_nframe_susy/remote_xrootd/remote_processing_ledger.csv \
  --out outputs_breakthrough_full_push_nframe_susy/features/remote_miniaod_features_merged.csv
```

Only the merged feature CSV needs to come back to the local project.

## What To Send Back

Bring back:

- `remote_processing_ledger.csv`
- merged feature CSV/parquet files
- logs for failed records
- any generated validation reports

Do not bring back raw ROOT files.

## Current Caveat

Earlier XRootD work found that some Open Data records advertise files that are not accessible through the tested endpoint. The workflow must therefore keep a ledger of accessible and failed URLs. Failed records are not a physics result; they are an infrastructure/access result.

## Relationship To Darren's Request

This satisfies the efficient-analysis point:

- CERN data are read remotely.
- N-Frame features are extracted in cloud/remote compute.
- Local storage only keeps compact event tables and reports.

The scientific requirement does not change: the final claim still needs independent real-data validation and clean controls.
