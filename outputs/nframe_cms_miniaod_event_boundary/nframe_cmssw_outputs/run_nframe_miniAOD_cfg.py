import glob
import os

import FWCore.ParameterSet.Config as cms


def env_int(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


input_dir = os.environ.get("NFRAME_INPUT_DIR", "/data")
output = os.environ.get("NFRAME_OUTPUT", "event_features.csv")
max_events = env_int("NFRAME_MAXEVENTS", 1000)
btag_name = os.environ.get("NFRAME_BTAG", "pfCombinedInclusiveSecondaryVertexV2BJetTags")

root_files = sorted(glob.glob(os.path.join(input_dir, "*.root")))
if not root_files:
    raise RuntimeError("No ROOT files found in NFRAME_INPUT_DIR=%s" % input_dir)

process = cms.Process("NFRAME")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(max_events))
process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(["file:" + path for path in root_files]),
)

process.nframe = cms.EDAnalyzer(
    "NFrameMiniAODAnalyzer",
    mets=cms.InputTag("slimmedMETs"),
    jets=cms.InputTag("slimmedJets"),
    muons=cms.InputTag("slimmedMuons"),
    electrons=cms.InputTag("slimmedElectrons"),
    btagDiscriminator=cms.string(btag_name),
    output=cms.string(output),
)

process.path = cms.Path(process.nframe)
