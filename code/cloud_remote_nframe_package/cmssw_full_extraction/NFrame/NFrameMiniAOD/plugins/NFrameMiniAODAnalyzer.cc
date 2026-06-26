// CMSSW analyzer for CMS MiniAOD event-level N-Frame variables.
// Run inside a compatible CMS Open Data CMSSW release.

#include <algorithm>
#include <cmath>
#include <fstream>
#include <string>
#include <vector>

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Common/interface/TriggerNames.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/Candidate/interface/VertexCompositePtrCandidate.h"
#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"

class NFrameMiniAODAnalyzer : public edm::one::EDAnalyzer<> {
public:
  explicit NFrameMiniAODAnalyzer(const edm::ParameterSet& cfg)
      : mets_(consumes<std::vector<pat::MET>>(cfg.getParameter<edm::InputTag>("mets"))),
        jets_(consumes<std::vector<pat::Jet>>(cfg.getParameter<edm::InputTag>("jets"))),
        muons_(consumes<std::vector<pat::Muon>>(cfg.getParameter<edm::InputTag>("muons"))),
        electrons_(consumes<std::vector<pat::Electron>>(cfg.getParameter<edm::InputTag>("electrons"))),
        vertices_(consumes<std::vector<reco::Vertex>>(cfg.getParameter<edm::InputTag>("vertices"))),
        packedCandidates_(consumes<std::vector<pat::PackedCandidate>>(cfg.getParameter<edm::InputTag>("packedCandidates"))),
        secondaryVertices_(consumes<std::vector<reco::VertexCompositePtrCandidate>>(cfg.getParameter<edm::InputTag>("secondaryVertices"))),
        generatorInfo_(consumes<GenEventInfoProduct>(cfg.getParameter<edm::InputTag>("generatorInfo"))),
        hltResults_(consumes<edm::TriggerResults>(cfg.getParameter<edm::InputTag>("hltResults"))),
        recoResults_(consumes<edm::TriggerResults>(cfg.getParameter<edm::InputTag>("recoResults"))),
        patResults_(consumes<edm::TriggerResults>(cfg.getParameter<edm::InputTag>("patResults"))),
        output_(cfg.getParameter<std::string>("output")),
        btagName_(cfg.getParameter<std::string>("btagDiscriminator")) {}

  void beginJob() override {
    out_.open(output_);
    out_ << "run,lumi,event,MET_pt,MET_phi,MHT_pt,MHT_phi,MHT_over_HT,MET_minus_MHT,"
            "N_jets_all,N_jets_30,N_jets_50,HT,jet_pt_sum,"
            "leading_jet_pt,subleading_jet_pt,N_muons,N_electrons,N_leptons,lepton_pt_sum,leading_muon_pt,"
            "N_btags_loose,N_btags_medium,N_btags_tight,max_btag_discriminator,"
            "N_primary_vertices,packed_candidate_count,secondary_vertex_count,"
            "btag_discriminator_status,vertex_status,packed_candidate_status,secondary_vertex_status,"
            "HLT_MET_paths_any,HLT_HT_paths_any,HLT_Mu_paths_any,HLT_Ele_paths_any,"
            "HLT_PFMET120_PFMHT120_IDTight,HLT_PFMETNoMu120_PFMHTNoMu_IDTight,"
            "HLT_PFMET110_PFMHT110_IDTight,HLT_PFMET170_HBHECleaned,HLT_PFMET170_NotCleaned,"
            "HLT_PFHT800,HLT_PFHT900,HLT_IsoMu20,HLT_IsoMu24,"
            "HLT_IsoTkMu24,HLT_Mu50,"
            "pass_HBHENoiseFilter,pass_HBHENoiseIsoFilter,pass_goodVertices,"
            "pass_EcalDeadCellTriggerPrimitiveFilter,pass_BadPFMuonFilter,"
            "pass_globalSuperTightHalo2016Filter,trigger_filter_extraction_status,"
            "generator_weight,generator_weight_status\n";
  }

  void analyze(const edm::Event& event, const edm::EventSetup&) override {
    edm::Handle<std::vector<pat::MET>> mets;
    edm::Handle<std::vector<pat::Jet>> jets;
    edm::Handle<std::vector<pat::Muon>> muons;
    edm::Handle<std::vector<pat::Electron>> electrons;
    edm::Handle<std::vector<reco::Vertex>> vertices;
    edm::Handle<std::vector<pat::PackedCandidate>> packedCandidates;
    edm::Handle<std::vector<reco::VertexCompositePtrCandidate>> secondaryVertices;
    edm::Handle<GenEventInfoProduct> generatorInfo;
    edm::Handle<edm::TriggerResults> hltResults;
    edm::Handle<edm::TriggerResults> recoResults;
    edm::Handle<edm::TriggerResults> patResults;
    event.getByToken(mets_, mets);
    event.getByToken(jets_, jets);
    event.getByToken(muons_, muons);
    event.getByToken(electrons_, electrons);
    event.getByToken(vertices_, vertices);
    event.getByToken(packedCandidates_, packedCandidates);
    event.getByToken(secondaryVertices_, secondaryVertices);
    event.getByToken(generatorInfo_, generatorInfo);
    event.getByToken(hltResults_, hltResults);
    event.getByToken(recoResults_, recoResults);
    event.getByToken(patResults_, patResults);

    const double metPt = mets.isValid() && !mets->empty() ? mets->front().pt() : 0.0;
    const double metPhi = mets.isValid() && !mets->empty() ? mets->front().phi() : 0.0;

    int nJetsAll = 0;
    int nJets30 = 0;
    int nJets50 = 0;
    int nbLoose = 0;
    int nbMedium = 0;
    int nbTight = 0;
    int btagStatus = 1;
    double maxBtag = -999.0;
    double ht = 0.0;
    double jetPtSum = 0.0;
    double leading = 0.0;
    double subleading = 0.0;
    double mhtPx = 0.0;
    double mhtPy = 0.0;

    if (jets.isValid()) {
      for (const auto& jet : *jets) {
        if (std::abs(jet.eta()) > 2.4) continue;
        nJetsAll++;
        jetPtSum += jet.pt();
        if (jet.pt() > leading) {
          subleading = leading;
          leading = jet.pt();
        } else if (jet.pt() > subleading) {
          subleading = jet.pt();
        }
        if (jet.pt() > 30.0) {
          nJets30++;
          ht += jet.pt();
          mhtPx -= jet.pt() * std::cos(jet.phi());
          mhtPy -= jet.pt() * std::sin(jet.phi());
        }
        if (jet.pt() > 50.0) nJets50++;

        double btag = -999.0;
        try {
          btag = jet.bDiscriminator(btagName_);
          if (btag > maxBtag) maxBtag = btag;
        } catch (...) {
          btagStatus = 0;
        }
        if (btag > 0.5426) nbLoose++;
        if (btag > 0.8484) nbMedium++;
        if (btag > 0.9535) nbTight++;
      }
    }
    const double mhtPt = std::sqrt(mhtPx * mhtPx + mhtPy * mhtPy);
    const double mhtPhi = std::atan2(mhtPy, mhtPx);
    const double mhtOverHt = ht > 0.0 ? mhtPt / ht : 0.0;
    const double metMinusMht = metPt - mhtPt;

    int nMuons = 0;
    int nElectrons = 0;
    double leptonPtSum = 0.0;
    double leadingMuonPt = 0.0;
    if (muons.isValid()) {
      for (const auto& mu : *muons) {
        if (mu.pt() > 10.0 && std::abs(mu.eta()) < 2.4) {
          nMuons++;
          leptonPtSum += mu.pt();
          if (mu.pt() > leadingMuonPt) leadingMuonPt = mu.pt();
        }
      }
    }
    if (electrons.isValid()) {
      for (const auto& el : *electrons) {
        if (el.pt() > 10.0 && std::abs(el.eta()) < 2.5) {
          nElectrons++;
          leptonPtSum += el.pt();
        }
      }
    }
    const int nLeptons = nMuons + nElectrons;

    const int vertexStatus = vertices.isValid() ? 1 : 0;
    const int packedCandidateStatus = packedCandidates.isValid() ? 1 : 0;
    const int secondaryVertexStatus = secondaryVertices.isValid() ? 1 : 0;
    const unsigned int nPrimaryVertices = vertices.isValid() ? vertices->size() : 0;
    const unsigned int nPackedCandidates = packedCandidates.isValid() ? packedCandidates->size() : 0;
    const unsigned int nSecondaryVertices = secondaryVertices.isValid() ? secondaryVertices->size() : 0;
    const int generatorWeightStatus = generatorInfo.isValid() ? 1 : 0;
    const double generatorWeight = generatorInfo.isValid() ? generatorInfo->weight() : 1.0;

    int hltMET = 0;
    int hltHT = 0;
    int hltMu = 0;
    int hltEle = 0;
    int hltMet120 = 0;
    int hltMetNoMu120 = 0;
    int hltMet110 = 0;
    int hltMet170Cleaned = 0;
    int hltMet170NotCleaned = 0;
    int hltPfht800 = 0;
    int hltPfht900 = 0;
    int hltIsoMu20 = 0;
    int hltIsoMu24 = 0;
    int hltIsoTkMu24 = 0;
    int hltMu50 = 0;
    int passHBHENoise = -1;
    int passHBHENoiseIso = -1;
    int passGoodVertices = -1;
    int passEcalDeadCell = -1;
    int passBadPFMuon = -1;
    int passGlobalHalo = -1;
    int triggerStatus = 0;

    auto scanTriggerBits = [&](const edm::Handle<edm::TriggerResults>& results, bool scanHlt) {
      if (!results.isValid()) return;
      triggerStatus = 1;
      const edm::TriggerNames& names = event.triggerNames(*results);
      for (unsigned int i = 0; i < results->size(); ++i) {
        const std::string name = names.triggerName(i);
        const bool accepted = results->accept(i);
        if (!accepted) continue;
        if (scanHlt) {
          if (name.find("MET") != std::string::npos || name.find("PFMET") != std::string::npos) hltMET = 1;
          if (name.find("HT") != std::string::npos || name.find("PFHT") != std::string::npos) hltHT = 1;
          if (name.find("Mu") != std::string::npos || name.find("IsoMu") != std::string::npos) hltMu = 1;
          if (name.find("Ele") != std::string::npos || name.find("Photon") != std::string::npos) hltEle = 1;
          if (name.find("HLT_PFMET120_PFMHT120_IDTight") == 0) hltMet120 = 1;
          if (name.find("HLT_PFMETNoMu120_PFMHTNoMu_IDTight") == 0) hltMetNoMu120 = 1;
          if (name.find("HLT_PFMET110_PFMHT110_IDTight") == 0) hltMet110 = 1;
          if (name.find("HLT_PFMET170_HBHECleaned") == 0) hltMet170Cleaned = 1;
          if (name.find("HLT_PFMET170_NotCleaned") == 0) hltMet170NotCleaned = 1;
          if (name.find("HLT_PFHT800") == 0) hltPfht800 = 1;
          if (name.find("HLT_PFHT900") == 0) hltPfht900 = 1;
          if (name.find("HLT_IsoMu20") == 0) hltIsoMu20 = 1;
          if (name.find("HLT_IsoMu24") == 0) hltIsoMu24 = 1;
          if (name.find("HLT_IsoTkMu24") == 0) hltIsoTkMu24 = 1;
          if (name.find("HLT_Mu50") == 0) hltMu50 = 1;
        }
        if (name.find("HBHENoiseFilter") != std::string::npos) passHBHENoise = 1;
        if (name.find("HBHENoiseIsoFilter") != std::string::npos) passHBHENoiseIso = 1;
        if (name.find("goodVertices") != std::string::npos) passGoodVertices = 1;
        if (name.find("EcalDeadCellTriggerPrimitiveFilter") != std::string::npos) passEcalDeadCell = 1;
        if (name.find("BadPFMuonFilter") != std::string::npos) passBadPFMuon = 1;
        if (name.find("globalSuperTightHalo2016Filter") != std::string::npos) passGlobalHalo = 1;
      }
    };
    scanTriggerBits(hltResults, true);
    scanTriggerBits(recoResults, false);
    scanTriggerBits(patResults, false);

    out_ << event.id().run() << "," << event.luminosityBlock() << "," << event.id().event() << ","
         << metPt << "," << metPhi << "," << mhtPt << "," << mhtPhi << "," << mhtOverHt << "," << metMinusMht << ","
         << nJetsAll << "," << nJets30 << "," << nJets50 << ","
         << ht << "," << jetPtSum << "," << leading << "," << subleading << ","
         << nMuons << "," << nElectrons << "," << nLeptons << "," << leptonPtSum << "," << leadingMuonPt << ","
         << nbLoose << "," << nbMedium << "," << nbTight << "," << maxBtag << ","
         << nPrimaryVertices << "," << nPackedCandidates << "," << nSecondaryVertices << ","
         << btagStatus << "," << vertexStatus << "," << packedCandidateStatus << "," << secondaryVertexStatus << ","
         << hltMET << "," << hltHT << "," << hltMu << "," << hltEle << ","
         << hltMet120 << "," << hltMetNoMu120 << "," << hltMet110 << ","
         << hltMet170Cleaned << "," << hltMet170NotCleaned << "," << hltPfht800 << "," << hltPfht900 << ","
         << hltIsoMu20 << "," << hltIsoMu24 << "," << hltIsoTkMu24 << "," << hltMu50 << ","
         << passHBHENoise << "," << passHBHENoiseIso << "," << passGoodVertices << ","
         << passEcalDeadCell << "," << passBadPFMuon << "," << passGlobalHalo << ","
         << triggerStatus << "," << generatorWeight << "," << generatorWeightStatus << "\n";
  }

  void endJob() override { out_.close(); }

private:
  edm::EDGetTokenT<std::vector<pat::MET>> mets_;
  edm::EDGetTokenT<std::vector<pat::Jet>> jets_;
  edm::EDGetTokenT<std::vector<pat::Muon>> muons_;
  edm::EDGetTokenT<std::vector<pat::Electron>> electrons_;
  edm::EDGetTokenT<std::vector<reco::Vertex>> vertices_;
  edm::EDGetTokenT<std::vector<pat::PackedCandidate>> packedCandidates_;
  edm::EDGetTokenT<std::vector<reco::VertexCompositePtrCandidate>> secondaryVertices_;
  edm::EDGetTokenT<GenEventInfoProduct> generatorInfo_;
  edm::EDGetTokenT<edm::TriggerResults> hltResults_;
  edm::EDGetTokenT<edm::TriggerResults> recoResults_;
  edm::EDGetTokenT<edm::TriggerResults> patResults_;
  std::string output_;
  std::string btagName_;
  std::ofstream out_;
};

DEFINE_FWK_MODULE(NFrameMiniAODAnalyzer);
