#include "TSystem.h"

#include "read_genfilter_lumi_summary.C"

void read_genfilter_lumi_summary_env() {
  const char* input = gSystem->Getenv("NFRAME_SUMWEIGHT_INPUT");
  if (!input || std::string(input).empty()) {
    std::cerr << "missing_env,NFRAME_SUMWEIGHT_INPUT" << std::endl;
    return;
  }
  read_genfilter_lumi_summary(input);
}
