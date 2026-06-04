#!/usr/bin/env bash
set -euo pipefail

if [ -z "${CMSSW_BASE:-}" ]; then
  echo "CMSSW_BASE is empty. Start inside a CMS Open Data CMSSW container first." >&2
  exit 2
fi

cd "$CMSSW_BASE/src"
mkdir -p NFrame/NFrameMiniAOD/plugins NFrame/NFrameMiniAOD/python NFrame/NFrameMiniAOD/test
cp /work/NFrame/NFrameMiniAOD/plugins/NFrameMiniAODAnalyzer.cc NFrame/NFrameMiniAOD/plugins/
cp /work/NFrame/NFrameMiniAOD/plugins/BuildFile.xml NFrame/NFrameMiniAOD/plugins/
cp /work/NFrame/NFrameMiniAOD/python/run_nframe_miniAOD_cfg.py NFrame/NFrameMiniAOD/python/
cp /work/NFrame/NFrameMiniAOD/python/run_nframe_miniAOD_cfg.py ./run_nframe_miniAOD_cfg.py
cp /work/compute_full_event_score.py ./compute_full_event_score.py

scram b

export NFRAME_INPUT_DIR="${NFRAME_INPUT_DIR:-/data}"
export NFRAME_OUTPUT="${NFRAME_TEST_OUTPUT:-event_features_test.csv}"
export NFRAME_MAXEVENTS="${NFRAME_TEST_MAXEVENTS:-1000}"
cmsRun run_nframe_miniAOD_cfg.py 2>&1 | tee cmsrun_test.log
python3 compute_full_event_score.py event_features_test.csv event_features_test_nframe_scored.csv

export NFRAME_OUTPUT="${NFRAME_OUTPUT_FULL:-event_features.csv}"
export NFRAME_MAXEVENTS="${NFRAME_MAXEVENTS_FULL:--1}"
cmsRun run_nframe_miniAOD_cfg.py 2>&1 | tee cmsrun_full.log
python3 compute_full_event_score.py event_features.csv event_features_nframe_scored.csv
