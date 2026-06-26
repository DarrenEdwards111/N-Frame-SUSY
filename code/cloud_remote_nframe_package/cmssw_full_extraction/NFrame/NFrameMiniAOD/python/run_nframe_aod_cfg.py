import glob
import os

import FWCore.ParameterSet.Config as cms


def env_int(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


input_dir = os.environ.get("NFRAME_INPUT_DIR", "/data")
input_files_env = os.environ.get("NFRAME_INPUT_FILES", "").strip()
output = os.environ.get("NFRAME_OUTPUT", "event_features.csv")
max_events = env_int("NFRAME_MAXEVENTS", 1000)

if input_files_env:
    root_files = [path.strip() for path in input_files_env.split(",") if path.strip()]
else:
    root_files = sorted(glob.glob(os.path.join(input_dir, "*.root")))
if not root_files:
    raise RuntimeError("No ROOT files found in NFRAME_INPUT_DIR=%s or NFRAME_INPUT_FILES=%s" % (input_dir, input_files_env))

process = cms.Process("NFRAMEAOD")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(max_events))
process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring([path if path.startswith(("root://", "file:")) else "file:" + path for path in root_files]),
)

process.nframe = cms.EDAnalyzer(
    "NFrameAODAnalyzer",
    mets=cms.InputTag("pfMet"),
    jets=cms.InputTag("ak5PFJets"),
    muons=cms.InputTag("muons"),
    electrons=cms.InputTag("gsfElectrons"),
    vertices=cms.InputTag("offlinePrimaryVertices"),
    pfCandidates=cms.InputTag("particleFlow"),
    btagsCombinedSecondaryVertex=cms.InputTag("combinedSecondaryVertexBJetTags"),
    btagsSimpleSecondaryVertexHighEff=cms.InputTag("simpleSecondaryVertexHighEffBJetTags"),
    btagsTrackCountingHighEff=cms.InputTag("trackCountingHighEffBJetTags"),
    v0Kshort=cms.InputTag("generalV0Candidates", "Kshort"),
    v0Lambda=cms.InputTag("generalV0Candidates", "Lambda"),
    v0LambdaBar=cms.InputTag("generalV0Candidates", "LambdaBar"),
    hltResults=cms.InputTag("TriggerResults", "", "HLT"),
    recoResults=cms.InputTag("TriggerResults", "", "RECO"),
    output=cms.string(output),
)

process.path = cms.Path(process.nframe)
