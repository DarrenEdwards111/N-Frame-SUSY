// Minimal CMSSW analyzer skeleton for CMS MiniAOD event-level N-Frame variables.
// Build inside a compatible CMS Open Data CMSSW release.

#include <cmath>
#include <fstream>
#include <vector>

#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/Electron.h"

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
    out_ << "run,lumi,event,MET_pt,MET_phi,N_jets,N_jets_30,N_jets_50,HT,N_muons,N_electrons,N_leptons,"
            "N_btags_loose,N_btags_medium,N_btags_tight,leading_jet_pt,subleading_jet_pt,jet_pt_sum,lepton_pt_sum\n";
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

    double metPt = mets->empty() ? 0.0 : mets->front().pt();
    double metPhi = mets->empty() ? 0.0 : mets->front().phi();
    int nJets = 0, nJets30 = 0, nJets50 = 0, nbL = 0, nbM = 0, nbT = 0;
    double ht = 0.0, jetPtSum = 0.0, leading = 0.0, subleading = 0.0;
    for (const auto& jet : *jets) {
      if (std::abs(jet.eta()) > 2.4) continue;
      nJets++;
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
      }
      if (jet.pt() > 50.0) nJets50++;
      double csv = jet.bDiscriminator("pfCombinedInclusiveSecondaryVertexV2BJetTags");
      if (csv > 0.5426) nbL++;
      if (csv > 0.8484) nbM++;
      if (csv > 0.9535) nbT++;
    }

    int nMu = 0, nEle = 0;
    double lepPtSum = 0.0;
    for (const auto& mu : *muons) {
      if (mu.pt() > 10.0 && std::abs(mu.eta()) < 2.4) {
        nMu++;
        lepPtSum += mu.pt();
      }
    }
    for (const auto& el : *electrons) {
      if (el.pt() > 10.0 && std::abs(el.eta()) < 2.5) {
        nEle++;
        lepPtSum += el.pt();
      }
    }
    int nLep = nMu + nEle;

    out_ << event.id().run() << "," << event.luminosityBlock() << "," << event.id().event() << ","
         << metPt << "," << metPhi << "," << nJets << "," << nJets30 << "," << nJets50 << ","
         << ht << "," << nMu << "," << nEle << "," << nLep << "," << nbL << "," << nbM << ","
         << nbT << "," << leading << "," << subleading << "," << jetPtSum << "," << lepPtSum << "\n";
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
