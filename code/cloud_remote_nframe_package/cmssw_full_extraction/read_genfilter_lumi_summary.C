#include <iostream>
#include <string>

#include "TFile.h"
#include "TTree.h"

#include "DataFormats/Common/interface/Wrapper.h"
#include "SimDataFormats/GeneratorProducts/interface/GenFilterInfo.h"

void read_genfilter_lumi_summary(const char* input) {
  TFile* file = TFile::Open(input);
  if (!file || file->IsZombie()) {
    std::cerr << "open_failed," << input << std::endl;
    return;
  }
  TTree* tree = dynamic_cast<TTree*>(file->Get("LuminosityBlocks"));
  if (!tree) {
    std::cerr << "missing_luminosityblocks," << input << std::endl;
    file->Close();
    return;
  }

  edm::Wrapper<GenFilterInfo>* wrapper = nullptr;
  const char* branch_name = "GenFilterInfo_genFilterEfficiencyProducer__GEN.";
  if (tree->SetBranchAddress(branch_name, &wrapper) < 0) {
    std::cerr << "missing_genfilter_branch," << input << std::endl;
    file->Close();
    return;
  }

  unsigned long long lumi_entries = 0;
  unsigned long long num_events_total = 0;
  unsigned long long num_events_passed = 0;
  double sum_weights_total = 0.0;
  double sum_weights_passed = 0.0;

  const Long64_t entries = tree->GetEntries();
  for (Long64_t i = 0; i < entries; ++i) {
    tree->GetEntry(i);
    if (!wrapper || !wrapper->isPresent()) continue;
    const GenFilterInfo& info = *wrapper->product();
    ++lumi_entries;
    num_events_total += info.numEventsTotal();
    num_events_passed += info.numEventsPassed();
    sum_weights_total += info.sumWeights();
    sum_weights_passed += info.sumPassWeights();
  }

  std::cout << "input,lumi_entries,num_events_total,num_events_passed,sum_weights_total,sum_weights_passed" << std::endl;
  std::cout << input << "," << lumi_entries << "," << num_events_total << "," << num_events_passed << ","
            << sum_weights_total << "," << sum_weights_passed << std::endl;
  file->Close();
}
