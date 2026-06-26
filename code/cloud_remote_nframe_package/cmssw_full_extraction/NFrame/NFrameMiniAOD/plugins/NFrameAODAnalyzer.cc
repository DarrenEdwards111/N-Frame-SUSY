// Reduced AOD analyzer for older CMS Open Data eras.

#include <algorithm>
#include <cmath>
#include <fstream>
#include <string>
#include <vector>

#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/BTauReco/interface/JetTag.h"
#include "DataFormats/Candidate/interface/VertexCompositeCandidate.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/JetReco/interface/PFJet.h"
#include "DataFormats/METReco/interface/PFMET.h"
#include "DataFormats/MuonReco/interface/Muon.h"
#include "DataFormats/ParticleFlowCandidate/interface/PFCandidate.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "FWCore/Common/interface/TriggerNames.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"

class NFrameAODAnalyzer : public edm::one::EDAnalyzer<> {
public:
  explicit NFrameAODAnalyzer(const edm::ParameterSet& cfg)
      : mets_(consumes<std::vector<reco::PFMET>>(cfg.getParameter<edm::InputTag>("mets"))),
        jets_(consumes<std::vector<reco::PFJet>>(cfg.getParameter<edm::InputTag>("jets"))),
        muons_(consumes<std::vector<reco::Muon>>(cfg.getParameter<edm::InputTag>("muons"))),
        electrons_(consumes<std::vector<reco::GsfElectron>>(cfg.getParameter<edm::InputTag>("electrons"))),
        vertices_(consumes<std::vector<reco::Vertex>>(cfg.getParameter<edm::InputTag>("vertices"))),
        pfCandidates_(consumes<std::vector<reco::PFCandidate>>(cfg.getParameter<edm::InputTag>("pfCandidates"))),
        btagsCombinedSecondaryVertex_(consumes<reco::JetTagCollection>(cfg.getParameter<edm::InputTag>("btagsCombinedSecondaryVertex"))),
        btagsSimpleSecondaryVertexHighEff_(consumes<reco::JetTagCollection>(cfg.getParameter<edm::InputTag>("btagsSimpleSecondaryVertexHighEff"))),
        btagsTrackCountingHighEff_(consumes<reco::JetTagCollection>(cfg.getParameter<edm::InputTag>("btagsTrackCountingHighEff"))),
        v0Kshort_(consumes<std::vector<reco::VertexCompositeCandidate>>(cfg.getParameter<edm::InputTag>("v0Kshort"))),
        v0Lambda_(consumes<std::vector<reco::VertexCompositeCandidate>>(cfg.getParameter<edm::InputTag>("v0Lambda"))),
        v0LambdaBar_(consumes<std::vector<reco::VertexCompositeCandidate>>(cfg.getParameter<edm::InputTag>("v0LambdaBar"))),
        hltResults_(consumes<edm::TriggerResults>(cfg.getParameter<edm::InputTag>("hltResults"))),
        recoResults_(consumes<edm::TriggerResults>(cfg.getParameter<edm::InputTag>("recoResults"))),
        output_(cfg.getParameter<std::string>("output")) {}

  void beginJob() override {
    out_.open(output_);
    out_ << "run,lumi,event,MET_pt,MET_phi,MHT_pt,MHT_phi,MHT_over_HT,MET_minus_MHT,"
            "N_jets_all,N_jets_30,N_jets_50,HT,jet_pt_sum,"
            "leading_jet_pt,subleading_jet_pt,N_muons,N_electrons,N_leptons,lepton_pt_sum,"
            "N_btags_loose,N_btags_medium,N_btags_tight,max_btag_discriminator,"
            "N_primary_vertices,packed_candidate_count,secondary_vertex_count,"
            "btag_discriminator_status,vertex_status,packed_candidate_status,secondary_vertex_status,"
            "HLT_MET_paths_any,HLT_HT_paths_any,HLT_Mu_paths_any,HLT_Ele_paths_any,"
            "pass_HBHENoiseFilter,pass_HBHENoiseIsoFilter,pass_goodVertices,"
            "pass_EcalDeadCellTriggerPrimitiveFilter,pass_BadPFMuonFilter,"
            "pass_globalSuperTightHalo2016Filter,trigger_filter_extraction_status,"
            "generator_weight,generator_weight_status\n";
  }

  void analyze(const edm::Event& event, const edm::EventSetup&) override {
    edm::Handle<std::vector<reco::PFMET>> mets;
    edm::Handle<std::vector<reco::PFJet>> jets;
    edm::Handle<std::vector<reco::Muon>> muons;
    edm::Handle<std::vector<reco::GsfElectron>> electrons;
    edm::Handle<std::vector<reco::Vertex>> vertices;
    edm::Handle<std::vector<reco::PFCandidate>> pfCandidates;
    edm::Handle<reco::JetTagCollection> btagsCombinedSecondaryVertex;
    edm::Handle<reco::JetTagCollection> btagsSimpleSecondaryVertexHighEff;
    edm::Handle<reco::JetTagCollection> btagsTrackCountingHighEff;
    edm::Handle<std::vector<reco::VertexCompositeCandidate>> v0Kshort;
    edm::Handle<std::vector<reco::VertexCompositeCandidate>> v0Lambda;
    edm::Handle<std::vector<reco::VertexCompositeCandidate>> v0LambdaBar;
    edm::Handle<edm::TriggerResults> hltResults;
    edm::Handle<edm::TriggerResults> recoResults;
    event.getByToken(mets_, mets);
    event.getByToken(jets_, jets);
    event.getByToken(muons_, muons);
    event.getByToken(electrons_, electrons);
    event.getByToken(vertices_, vertices);
    event.getByToken(pfCandidates_, pfCandidates);
    event.getByToken(btagsCombinedSecondaryVertex_, btagsCombinedSecondaryVertex);
    event.getByToken(btagsSimpleSecondaryVertexHighEff_, btagsSimpleSecondaryVertexHighEff);
    event.getByToken(btagsTrackCountingHighEff_, btagsTrackCountingHighEff);
    event.getByToken(v0Kshort_, v0Kshort);
    event.getByToken(v0Lambda_, v0Lambda);
    event.getByToken(v0LambdaBar_, v0LambdaBar);
    event.getByToken(hltResults_, hltResults);
    event.getByToken(recoResults_, recoResults);

    const double metPt = mets.isValid() && !mets->empty() ? mets->front().pt() : 0.0;
    const double metPhi = mets.isValid() && !mets->empty() ? mets->front().phi() : 0.0;

    int nJetsAll = 0;
    int nJets30 = 0;
    int nJets50 = 0;
    double ht = 0.0;
    double jetPtSum = 0.0;
    double leading = 0.0;
    double subleading = 0.0;
    double mhtPx = 0.0;
    double mhtPy = 0.0;
    if (jets.isValid()) {
      for (const auto& jet : *jets) {
        if (std::abs(jet.eta()) > 2.4) continue;
        ++nJetsAll;
        jetPtSum += jet.pt();
        if (jet.pt() > leading) {
          subleading = leading;
          leading = jet.pt();
        } else if (jet.pt() > subleading) {
          subleading = jet.pt();
        }
        if (jet.pt() > 30.0) {
          ++nJets30;
          ht += jet.pt();
          mhtPx -= jet.pt() * std::cos(jet.phi());
          mhtPy -= jet.pt() * std::sin(jet.phi());
        }
        if (jet.pt() > 50.0) ++nJets50;
      }
    }
    const double mhtPt = std::sqrt(mhtPx * mhtPx + mhtPy * mhtPy);
    const double mhtPhi = std::atan2(mhtPy, mhtPx);
    const double mhtOverHt = ht > 0.0 ? mhtPt / ht : 0.0;
    const double metMinusMht = metPt - mhtPt;

    int nMuons = 0;
    int nElectrons = 0;
    double leptonPtSum = 0.0;
    if (muons.isValid()) {
      for (const auto& mu : *muons) {
        if (mu.pt() > 10.0 && std::abs(mu.eta()) < 2.4) {
          ++nMuons;
          leptonPtSum += mu.pt();
        }
      }
    }
    if (electrons.isValid()) {
      for (const auto& el : *electrons) {
        if (el.pt() > 10.0 && std::abs(el.eta()) < 2.5) {
          ++nElectrons;
          leptonPtSum += el.pt();
        }
      }
    }
    const int nLeptons = nMuons + nElectrons;

    const int vertexStatus = vertices.isValid() ? 1 : 0;
    const int packedCandidateStatus = pfCandidates.isValid() ? 1 : 0;
    const unsigned int nPrimaryVertices = vertices.isValid() ? vertices->size() : 0;
    const unsigned int nPackedCandidates = pfCandidates.isValid() ? pfCandidates->size() : 0;
    const unsigned int nKshort = v0Kshort.isValid() ? v0Kshort->size() : 0;
    const unsigned int nLambda = v0Lambda.isValid() ? v0Lambda->size() : 0;
    const unsigned int nLambdaBar = v0LambdaBar.isValid() ? v0LambdaBar->size() : 0;
    const unsigned int nSecondaryVertices = nKshort + nLambda + nLambdaBar;
    const int secondaryVertexStatus = (v0Kshort.isValid() || v0Lambda.isValid() || v0LambdaBar.isValid()) ? 1 : 0;

    int nbLoose = 0;
    int nbMedium = 0;
    int nbTight = 0;
    int btagStatus = 0;
    double maxBtag = -999.0;
    auto scanBTags = [&](const edm::Handle<reco::JetTagCollection>& tags) {
      if (!tags.isValid()) return false;
      for (const auto& tag : *tags) {
        const reco::JetBaseRef jetRef = tag.first;
        if (jetRef.isNull()) continue;
        const reco::Jet& jet = *jetRef;
        if (std::abs(jet.eta()) > 2.4 || jet.pt() <= 30.0) continue;
        const double btag = tag.second;
        if (btag > maxBtag) maxBtag = btag;
        if (btag > 0.244) ++nbLoose;
        if (btag > 0.679) ++nbMedium;
        if (btag > 0.898) ++nbTight;
      }
      return true;
    };
    if (scanBTags(btagsCombinedSecondaryVertex)) {
      btagStatus = 1;
    } else if (scanBTags(btagsSimpleSecondaryVertexHighEff)) {
      btagStatus = 2;
    } else if (scanBTags(btagsTrackCountingHighEff)) {
      btagStatus = 3;
    }

    int hltMET = 0;
    int hltHT = 0;
    int hltMu = 0;
    int hltEle = 0;
    int passGoodVertices = vertexStatus && nPrimaryVertices > 0 ? 1 : 0;
    int triggerStatus = 0;
    auto scanTriggerBits = [&](const edm::Handle<edm::TriggerResults>& results, bool scanHlt) {
      if (!results.isValid()) return;
      triggerStatus = 1;
      const edm::TriggerNames& names = event.triggerNames(*results);
      for (unsigned int i = 0; i < results->size(); ++i) {
        if (!results->accept(i)) continue;
        const std::string name = names.triggerName(i);
        if (scanHlt) {
          if (name.find("MET") != std::string::npos || name.find("PFMET") != std::string::npos) hltMET = 1;
          if (name.find("HT") != std::string::npos || name.find("PFHT") != std::string::npos || name.find("Jet") != std::string::npos) hltHT = 1;
          if (name.find("Mu") != std::string::npos || name.find("IsoMu") != std::string::npos) hltMu = 1;
          if (name.find("Ele") != std::string::npos || name.find("Photon") != std::string::npos) hltEle = 1;
        }
      }
    };
    scanTriggerBits(hltResults, true);
    scanTriggerBits(recoResults, false);

    out_ << event.id().run() << "," << event.luminosityBlock() << "," << event.id().event() << ","
         << metPt << "," << metPhi << "," << mhtPt << "," << mhtPhi << "," << mhtOverHt << "," << metMinusMht << ","
         << nJetsAll << "," << nJets30 << "," << nJets50 << ","
         << ht << "," << jetPtSum << "," << leading << "," << subleading << ","
         << nMuons << "," << nElectrons << "," << nLeptons << "," << leptonPtSum << ","
         << nbLoose << "," << nbMedium << "," << nbTight << "," << maxBtag << ","
         << nPrimaryVertices << "," << nPackedCandidates << "," << nSecondaryVertices << ","
         << btagStatus << "," << vertexStatus << "," << packedCandidateStatus << "," << secondaryVertexStatus << ","
         << hltMET << "," << hltHT << "," << hltMu << "," << hltEle << ","
         << 1 << "," << 1 << "," << passGoodVertices << ","
         << 1 << "," << 1 << "," << 1 << "," << triggerStatus << ","
         << 1.0 << "," << 0 << "\n";
  }

  void endJob() override { out_.close(); }

private:
  edm::EDGetTokenT<std::vector<reco::PFMET>> mets_;
  edm::EDGetTokenT<std::vector<reco::PFJet>> jets_;
  edm::EDGetTokenT<std::vector<reco::Muon>> muons_;
  edm::EDGetTokenT<std::vector<reco::GsfElectron>> electrons_;
  edm::EDGetTokenT<std::vector<reco::Vertex>> vertices_;
  edm::EDGetTokenT<std::vector<reco::PFCandidate>> pfCandidates_;
  edm::EDGetTokenT<reco::JetTagCollection> btagsCombinedSecondaryVertex_;
  edm::EDGetTokenT<reco::JetTagCollection> btagsSimpleSecondaryVertexHighEff_;
  edm::EDGetTokenT<reco::JetTagCollection> btagsTrackCountingHighEff_;
  edm::EDGetTokenT<std::vector<reco::VertexCompositeCandidate>> v0Kshort_;
  edm::EDGetTokenT<std::vector<reco::VertexCompositeCandidate>> v0Lambda_;
  edm::EDGetTokenT<std::vector<reco::VertexCompositeCandidate>> v0LambdaBar_;
  edm::EDGetTokenT<edm::TriggerResults> hltResults_;
  edm::EDGetTokenT<edm::TriggerResults> recoResults_;
  std::string output_;
  std::ofstream out_;
};

DEFINE_FWK_MODULE(NFrameAODAnalyzer);
