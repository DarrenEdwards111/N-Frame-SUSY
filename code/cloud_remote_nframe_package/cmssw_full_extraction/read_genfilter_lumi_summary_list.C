#include <fstream>
#include <iostream>
#include <string>

#include "TFile.h"
#include "TSystem.h"
#include "TTree.h"

#include "DataFormats/Common/interface/Wrapper.h"
#include "SimDataFormats/GeneratorProducts/interface/GenFilterInfo.h"

struct GenFilterSummary {
  unsigned long long lumi_entries = 0;
  unsigned long long num_events_total = 0;
  unsigned long long num_events_passed = 0;
  double sum_weights_total = 0.0;
  double sum_weights_passed = 0.0;
  int status = 0;
};

GenFilterSummary read_one_genfilter_lumi_summary(const std::string& input) {
  GenFilterSummary out;
  TFile* file = TFile::Open(input.c_str());
  if (!file || file->IsZombie()) {
    out.status = 1;
    return out;
  }
  TTree* tree = dynamic_cast<TTree*>(file->Get("LuminosityBlocks"));
  if (!tree) {
    out.status = 2;
    file->Close();
    return out;
  }

  edm::Wrapper<GenFilterInfo>* wrapper = nullptr;
  const char* branch_name = "GenFilterInfo_genFilterEfficiencyProducer__GEN.";
  if (tree->SetBranchAddress(branch_name, &wrapper) < 0) {
    out.status = 3;
    file->Close();
    return out;
  }

  const Long64_t entries = tree->GetEntries();
  for (Long64_t i = 0; i < entries; ++i) {
    tree->GetEntry(i);
    if (!wrapper || !wrapper->isPresent()) continue;
    const GenFilterInfo& info = *wrapper->product();
    ++out.lumi_entries;
    out.num_events_total += info.numEventsTotal();
    out.num_events_passed += info.numEventsPassed();
    out.sum_weights_total += info.sumWeights();
    out.sum_weights_passed += info.sumPassWeights();
  }
  file->Close();
  return out;
}

void read_genfilter_lumi_summary_list() {
  const char* input_path = gSystem->Getenv("NFRAME_SUMWEIGHT_LIST");
  const char* output_path = gSystem->Getenv("NFRAME_SUMWEIGHT_OUTPUT");
  if (!input_path || std::string(input_path).empty()) {
    std::cerr << "missing_env,NFRAME_SUMWEIGHT_LIST" << std::endl;
    return;
  }
  if (!output_path || std::string(output_path).empty()) {
    std::cerr << "missing_env,NFRAME_SUMWEIGHT_OUTPUT" << std::endl;
    return;
  }

  std::ifstream in(input_path);
  std::ofstream out(output_path);
  out << "record_id,process_family,file_index,xrootd_url,status,lumi_entries,"
         "num_events_total,num_events_passed,sum_weights_total,sum_weights_passed\n";

  std::string line;
  while (std::getline(in, line)) {
    while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) {
      line.pop_back();
    }
    if (line.empty()) continue;
    const std::size_t p1 = line.find(',');
    const std::size_t p2 = line.find(',', p1 + 1);
    const std::size_t p3 = line.find(',', p2 + 1);
    if (p1 == std::string::npos || p2 == std::string::npos || p3 == std::string::npos) continue;
    const std::string record_id = line.substr(0, p1);
    const std::string family = line.substr(p1 + 1, p2 - p1 - 1);
    const std::string file_index = line.substr(p2 + 1, p3 - p2 - 1);
    std::string url = line.substr(p3 + 1);
    while (!url.empty() && (url.back() == '\r' || url.back() == '\n' || url.back() == ' ')) {
      url.pop_back();
    }

    GenFilterSummary s = read_one_genfilter_lumi_summary(url);
    out << record_id << "," << family << "," << file_index << "," << url << "," << s.status << ","
        << s.lumi_entries << "," << s.num_events_total << "," << s.num_events_passed << ","
        << s.sum_weights_total << "," << s.sum_weights_passed << "\n";
    out.flush();
  }
}
