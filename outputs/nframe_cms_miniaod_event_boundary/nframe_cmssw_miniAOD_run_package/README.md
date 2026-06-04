# N-Frame CMSSW MiniAOD Extraction Package

This package extracts event-level variables from CMS MiniAOD inside a compatible CMS Open Data CMSSW container.

It is not a SUSY search and does not compare to Standard Model expected backgrounds.

## Container Sketch

```bash
docker run -it --rm \
  -v D:/cern_open_data/cms_met_run2016g_miniaod_10gb:/data \
  -v <this_package_path>:/work \
  <cms-open-data-cmssw-image> /bin/bash
```

Inside the container:

```bash
cd "$CMSSW_BASE/src"
bash /work/run_cmssw_extraction.sh
```

Expected outputs:

- `event_features_test.csv`
- `event_features_test_nframe_scored.csv`
- `event_features.csv`
- `event_features_nframe_scored.csv`

If `slimmedMETs` or `slimmedJets` are not found, run:

```bash
edmDumpEventContent file:/data/<file.root> | grep -i met
edmDumpEventContent file:/data/<file.root> | grep -i jet
```

Then edit `NFrame/NFrameMiniAOD/python/run_nframe_miniAOD_cfg.py`.
