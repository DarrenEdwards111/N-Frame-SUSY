# Fuller Component Benchmark Gap Audit

Date: 2026-06-09

## Existing Reports

| report                                                   | exists   |   size_bytes |
|:---------------------------------------------------------|:---------|-------------:|
| EXPANDED_BENCHMARK_AND_TRACE_ROBUSTNESS_SYNTHESIS.md     | True     |        11210 |
| UPDATE_TO_DARREN_EXPANDED_BENCHMARK_ROBUSTNESS.md        | True     |         5591 |
| EXPANDED_BENCHMARK_FIVE_SIGMA_TEST_REPORT.md             | True     |        38471 |
| EXPANDED_REAL_TRACE_ALIGNMENT_REPORT.md                  | True     |         4257 |
| FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md | True     |        44583 |
| REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md                   | True     |        10252 |

## Benchmark Component State

| sample_id                            | process_label                             | classification   | data_tier               |   events |   mean_BNF |   q95_tail_fraction | P_missing   | P_visible_energy   | P_multiplicity   | P_btag_structure   | P_compression   | P_displacement_proxy   | P_reconstruction   | component_mode    | needs_miniaodsim_replacement   |
|:-------------------------------------|:------------------------------------------|:-----------------|:------------------------|---------:|-----------:|--------------------:|:------------|:-------------------|:-----------------|:-------------------|:----------------|:-----------------------|:-------------------|:------------------|:-------------------------------|
| qcd_ht1000to1500_nanoaodsim_pilot    | QCD HT1000to1500                          | SM_background    | NANOAODSIM              |    33536 |  0.976586  |           0.0772603 | available   | available          | available        | available          | available       | available              | reduced            | reduced-component | True                           |
| ttjets_nanoaodsim_pilot              | TTJets inclusive                          | SM_background    | NANOAODSIM              |    50000 |  0.875909  |           0.04908   | available   | available          | available        | available          | available       | available              | reduced            | reduced-component | True                           |
| qcd_ht700to1000_nanoaodsim_pilot     | QCD HT700to1000                           | SM_background    | NANOAODSIM              |    50000 |  0.630491  |           0.02446   | available   | available          | available        | available          | available       | available              | reduced            | reduced-component | True                           |
| qcd_ht500to700_nanoaodsim_pilot      | QCD HT500to700                            | SM_background    | NANOAODSIM              |    50000 |  0.403127  |           0.00892   | available   | available          | available        | available          | available       | available              | reduced            | reduced-component | True                           |
| wjets_lnu_nanoaodsim_pilot           | WJetsToLNu                                | SM_background    | NANOAODSIM              |    50000 | -0.425829  |           2e-05     | available   | available          | available        | available          | available       | available              | reduced            | reduced-component | True                           |
| sms_t5wg_mg1500_mlsp1_signal         | SMS-T5Wg mGluino1500 mLSP1                | signal           | MiniAOD-derived/reduced |     5000 |  1.6124    |           0.1978    | available   | available          | available        | available          | available       | missing                | missing            | reduced-component | True                           |
| sms_t2tt_compressed_nanoaodsim_pilot | SMS-T2tt compressed stop mStop300 mLSP290 | signal           | NANOAODSIM              |    50000 |  0.38747   |           0.0137    | available   | available          | available        | available          | available       | available              | reduced            | reduced-component | True                           |
| susy_htoaa4b_m12_signal              | SUSY HToAA4B mA12                         | signal           | MiniAOD-derived/reduced |     2394 |  0.0390909 |           0         | available   | available          | available        | available          | available       | missing                | missing            | reduced-component | True                           |

## Why This Matters

MiniAODSIM matters because the real-data B_NF model was strongest in reconstruction/displacement-related axes. NanoAODSIM lacks packed_candidate_count, so P_reconstruction is reduced and benchmark comparison is not fully aligned with the real MiniAOD validation.