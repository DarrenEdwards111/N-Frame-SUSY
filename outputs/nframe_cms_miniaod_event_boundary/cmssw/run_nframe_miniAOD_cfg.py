import FWCore.ParameterSet.Config as cms

process = cms.Process("NFRAME")
process.load("FWCore.MessageService.MessageLogger_cfi")

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(10000))
process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(
        "file:D:/cern_open_data/cms_met_run2016g_miniaod_10gb/0438B51F-9A50-8642-9963-CDB942DD12D9.root"
    ),
)

process.nframe = cms.EDAnalyzer(
    "NFrameMiniAODAnalyzer",
    mets=cms.InputTag("slimmedMETs"),
    jets=cms.InputTag("slimmedJets"),
    muons=cms.InputTag("slimmedMuons"),
    electrons=cms.InputTag("slimmedElectrons"),
    output=cms.string("event_features.csv"),
)

process.path = cms.Path(process.nframe)
