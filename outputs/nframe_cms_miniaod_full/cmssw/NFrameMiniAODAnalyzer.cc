// CMSSW analyzer for CMS MiniAOD event-level N-Frame variables.

#include <cmath>
#include <fstream>
#include <string>
#include <vector>

#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"

class NFrameMiniAODAnalyzer : public edm::one::EDAnalyzer<> {
public:
  explicit NFrameMiniAODAnalyzer(const edm::ParameterSet& cfg)
      : mets_(consumes<std::vector<pat::MET>>(cfg.getParameter<edm::InputTag>("mets"))),
        jets_(consumes<std::vector<pat::Jet>>(cfg.getParameter<edm::InputTag>("jets"))),
        muons_(consumes<std::vector<pat::Muon>>(cfg.getParameter<edm::InputTag>("muons"))),
        electrons_(consumes<std::vector<pat::Electron>>(cfg.getParameter<edm::InputTag>("electrons"))),
        output_(cfg.getParameter<std::string>("output")) {}

  void beginJob() override {
    out_.open(output_);
    out_ << "run,lumi,event,MET_pt,MET_phi,N_jets_all,N_jets_30,N_jets_50,HT,jet_pt_sum,"
            "leading_jet_pt,subleading_jet_pt,leading_jet_eta,subleading_jet_eta,jet_mass_sum_30,"
            "N_muons,N_electrons,N_leptons,lepton_pt_sum,N_btags_loose,N_btags_medium,N_btags_tight,"
            "MET_fraction,N_objects,S_event_proxy,high_MET,high_multiplicity,B_event_raw_notes\n";
  }

  void analyze(const edm::Event& event, const edm::EventSetup&) override {
    edm::Handle<std::vector<pat::MET>> mets;
    edm::Handle<std::vector<pat::Jet>> jets;
    edm::Handle<std::vector<pat::Muon>> muons;
    edm::Handle<std::vector<pat::Electron>> electrons;
    event.getByToken(mets_, mets);
    event.getByToken(jets_, jets);
    event.getByToken(muons_, muons);
    event.getByToken(electrons_, electrons);

    const double metPt = (mets.isValid() && !mets->empty()) ? mets->front().pt() : 0.0;
    const double metPhi = (mets.isValid() && !mets->empty()) ? mets->front().phi() : 0.0;

    int nJetsAll = 0, nJets30 = 0, nJets50 = 0;
    int nbLoose = 0, nbMedium = 0, nbTight = 0;
    double ht = 0.0, jetPtSum = 0.0, leadingPt = 0.0, subleadingPt = 0.0;
    double leadingEta = 0.0, subleadingEta = 0.0, jetMassSum30 = 0.0;
    bool btagOk = true;

    if (jets.isValid()) {
      for (const auto& jet : *jets) {
        if (std::abs(jet.eta()) > 2.4) continue;
        nJetsAll++;
        jetPtSum += jet.pt();
        if (jet.pt() > leadingPt) {
          subleadingPt = leadingPt;
          subleadingEta = leadingEta;
          leadingPt = jet.pt();
          leadingEta = jet.eta();
        } else if (jet.pt() > subleadingPt) {
          subleadingPt = jet.pt();
          subleadingEta = jet.eta();
        }
        if (jet.pt() > 30.0) {
          nJets30++;
          ht += jet.pt();
          jetMassSum30 += jet.mass();
        }
        if (jet.pt() > 50.0) nJets50++;

        double btag = -999.0;
        try {
          btag = jet.bDiscriminator("pfCombinedInclusiveSecondaryVertexV2BJetTags");
        } catch (...) {
          try {
            btag = jet.bDiscriminator("pfCombinedSecondaryVertexV2BJetTags");
          } catch (...) {
            btagOk = false;
          }
        }
        if (btag > 0.5426) nbLoose++;
        if (btag > 0.8484) nbMedium++;
        if (btag > 0.9535) nbTight++;
      }
    }

    int nMuons = 0, nElectrons = 0;
    double leptonPtSum = 0.0;
    if (muons.isValid()) {
      for (const auto& mu : *muons) {
        if (mu.pt() > 10.0 && std::abs(mu.eta()) < 2.4) {
          nMuons++;
          leptonPtSum += mu.pt();
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
    const double metFraction = metPt / (ht + metPt + 1.0);
    const int nObjects = nJets30 + nLeptons + nbMedium;
    const double sEventProxy = std::log1p(static_cast<double>(nObjects));
    const int highMET = metPt >= 250.0 ? 1 : 0;
    const int highMultiplicity = nJets30 >= 6 ? 1 : 0;
    const std::string notes = btagOk ? "ok" : "btag_discriminator_unresolved";

    out_ << event.id().run() << "," << event.luminosityBlock() << "," << event.id().event() << ","
         << metPt << "," << metPhi << "," << nJetsAll << "," << nJets30 << "," << nJets50 << ","
         << ht << "," << jetPtSum << "," << leadingPt << "," << subleadingPt << ","
         << leadingEta << "," << subleadingEta << "," << jetMassSum30 << ","
         << nMuons << "," << nElectrons << "," << nLeptons << "," << leptonPtSum << ","
         << nbLoose << "," << nbMedium << "," << nbTight << ","
         << metFraction << "," << nObjects << "," << sEventProxy << "," << highMET << ","
         << highMultiplicity << "," << notes << "\n";
  }

  void endJob() override { out_.close(); }

private:
  edm::EDGetTokenT<std::vector<pat::MET>> mets_;
  edm::EDGetTokenT<std::vector<pat::Jet>> jets_;
  edm::EDGetTokenT<std::vector<pat::Muon>> muons_;
  edm::EDGetTokenT<std::vector<pat::Electron>> electrons_;
  std::string output_;
  std::ofstream out_;
};

DEFINE_FWK_MODULE(NFrameMiniAODAnalyzer);
