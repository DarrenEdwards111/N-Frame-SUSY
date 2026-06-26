# Remote XRootD MiniAODSIM Processing

This folder contains helper scripts for processing CERN Open Data ROOT files by remote `root://` URL through the existing CMSSW/Docker MiniAOD feature extractor.

The manifest schema is:

`dataset_label,record_id,process_family,primary_dataset,run_era,data_tier,xrootd_url,file_index,planned_max_events,status,output_path,notes`

The existing CMSSW config has been patched so local paths are prefixed with `file:`, while `root://...` and `file:...` paths are passed through unchanged.

Typical usage:

```powershell
python scripts\remote_xrootd\build_xrootd_manifest.py --candidates outputs_breakthrough_full_push_nframe_susy\tables\04_cern_record_search_and_xrootd_manifest_candidates.csv --out outputs_breakthrough_full_push_nframe_susy\remote_xrootd\manifest_priority1_top_dy_w_z_qcd.csv
python scripts\remote_xrootd\smoke_test_xrootd_file.py --url root://eospublic.cern.ch//eos/opendata/cms/...root --record-id 63094 --process-family QCD
python scripts\remote_xrootd\run_remote_miniaod_batch.py --manifest outputs_breakthrough_full_push_nframe_susy\remote_xrootd\manifest_priority1_top_dy_w_z_qcd.csv
python scripts\remote_xrootd\merge_remote_batch_outputs.py --ledger outputs_breakthrough_full_push_nframe_susy\remote_xrootd\remote_processing_ledger.csv
```
