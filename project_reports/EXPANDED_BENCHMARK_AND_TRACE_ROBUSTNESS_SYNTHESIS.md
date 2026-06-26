# Expanded Benchmark And Trace Robustness Synthesis

Date: 2026-06-09

## New Samples Added

| sample_id                            | process_label                             | classification   | data_tier   |   actual_size_bytes |
|:-------------------------------------|:------------------------------------------|:-----------------|:------------|--------------------:|
| wjets_lnu_nanoaodsim_pilot           | WJetsToLNu                                | SM_background    | NANOAODSIM  |           133529187 |
| qcd_ht500to700_nanoaodsim_pilot      | QCD HT500to700                            | SM_background    | NANOAODSIM  |           110734104 |
| qcd_ht1000to1500_nanoaodsim_pilot    | QCD HT1000to1500                          | SM_background    | NANOAODSIM  |            80890335 |
| sms_t2tt_compressed_nanoaodsim_pilot | SMS-T2tt compressed stop mStop300 mLSP290 | signal           | NANOAODSIM  |           108940400 |

Total new download size: 0.404 GiB.

## Expanded BNF Summary

| sample_id                            | process_label                             | classification   |   events |   mean_BNF |   median_BNF |
|:-------------------------------------|:------------------------------------------|:-----------------|---------:|-----------:|-------------:|
| qcd_ht1000to1500_nanoaodsim_pilot    | QCD HT1000to1500                          | SM_background    |    33536 |  0.976586  |    0.890743  |
| qcd_ht500to700_nanoaodsim_pilot      | QCD HT500to700                            | SM_background    |    50000 |  0.403127  |    0.322978  |
| qcd_ht700to1000_nanoaodsim_pilot     | QCD HT700to1000                           | SM_background    |    50000 |  0.630491  |    0.55262   |
| sms_t2tt_compressed_nanoaodsim_pilot | SMS-T2tt compressed stop mStop300 mLSP290 | signal           |    50000 |  0.38747   |    0.280366  |
| sms_t5wg_mg1500_mlsp1_signal         | SMS-T5Wg mGluino1500 mLSP1                | signal           |     5000 |  1.6124    |    1.57143   |
| susy_htoaa4b_m12_signal              | SUSY HToAA4B mA12                         | signal           |     2394 |  0.0390909 |    0.0403913 |
| ttjets_nanoaodsim_pilot              | TTJets inclusive                          | SM_background    |    50000 |  0.875909  |    0.830251  |
| wjets_lnu_nanoaodsim_pilot           | WJetsToLNu                                | SM_background    |    50000 | -0.425829  |   -0.478634  |

## SMS-T5Wg q95 Corrected Tests

| threshold   | signal_sample                | signal_process             | background_sample                 | background_process   |   signal_count |   signal_total |   background_count |   background_total |   p_signal |   p_background |   risk_difference |   risk_ratio |   z_one_sided |   p_one_sided |   log10_p |   bonferroni_family_size |   bonferroni_z | remains_5sigma_after_bonferroni   |
|:------------|:-----------------------------|:---------------------------|:----------------------------------|:---------------------|---------------:|---------------:|-------------------:|-------------------:|-----------:|---------------:|------------------:|-------------:|--------------:|--------------:|----------:|-------------------------:|---------------:|:----------------------------------|
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht1000to1500_nanoaodsim_pilot | QCD HT1000to1500     |            989 |           5000 |               2591 |              33536 |     0.1978 |      0.0772603 |           0.12054 |      2.56018 |       27.3906 |  1.77375e-165 |  -164.751 |                       60 |        27.2409 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | ttjets_nanoaodsim_pilot           | TTJets inclusive     |            989 |           5000 |               2454 |              50000 |     0.1978 |      0.04908   |           0.14872 |      4.03015 |       41.3912 |  0            |  -374.04  |                       60 |        41.2923 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht700to1000_nanoaodsim_pilot  | QCD HT700to1000      |            989 |           5000 |               1223 |              50000 |     0.1978 |      0.02446   |           0.17334 |      8.08667 |       59.4826 |  0            |  -770.48  |                       60 |        59.4138 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht500to700_nanoaodsim_pilot   | QCD HT500to700       |            989 |           5000 |                446 |              50000 |     0.1978 |      0.00892   |           0.18888 |     22.1749  |       79.886  |  0            | -1388.09  |                       60 |        79.8348 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | wjets_lnu_nanoaodsim_pilot        | WJetsToLNu           |            989 |           5000 |                  1 |              50000 |     0.1978 |      2e-05     |           0.19778 |   9890       |      100.295  |  0            | -2186.7   |                       60 |       100.254  | True                              |

## Incremental Test

Median B_NF AUC across expanded comparisons: 0.483. Median missing+visible+multiplicity AUC: 0.895. If the latter is higher, the separation remains largely MET/HT/multiplicity driven.

## Expanded Trace Direction

| direction                      | component        |   raw_contrast |   unit_weight |   signal_mean |   background_mean |
|:-------------------------------|:-----------------|---------------:|--------------:|--------------:|------------------:|
| sms_t5wg_vs_expanded_pooled_sm | P_missing        |      10.0037   |     0.895125  |      9.82685  |         -0.176869 |
| sms_t5wg_vs_expanded_pooled_sm | P_visible_energy |       4.22652  |     0.378186  |      5.28199  |          1.05546  |
| sms_t5wg_vs_expanded_pooled_sm | P_multiplicity   |       2.61162  |     0.233685  |      3.06615  |          0.454538 |
| sms_t5wg_vs_expanded_pooled_sm | P_btag_structure |       0.178169 |     0.0159424 |      0.353516 |          0.175347 |
| sms_t5wg_vs_expanded_pooled_sm | P_compression    |       0.328507 |     0.0293945 |     -1.56647  |         -1.89498  |

## Real Data Expanded Trace Alignment

| dataset   | bnf_tail   |   high_events |   mean_expanded_trace_high |   mean_expanded_trace_rest |   mean_diff |      welch_p |   welch_z |   fraction_high_above_trace_q90 |   fraction_rest_above_trace_q90 |   enrichment_ratio |
|:----------|:-----------|--------------:|---------------------------:|---------------------------:|------------:|-------------:|----------:|--------------------------------:|--------------------------------:|-------------------:|
| Run2016G  | top05      |         30243 |                    1.55983 |                -0.0820961  |     1.64192 | 0            | inf       |                        0.435175 |                       0.0823592 |            5.28387 |
| Run2016G  | top01      |          6049 |                    1.95122 |                -0.0197107  |     1.97093 | 0            | inf       |                        0.551827 |                       0.0954358 |            5.78218 |
| Run2016G  | top001     |           605 |                    2.52014 |                -0.00252325 |     2.52266 | 5.28481e-164 |  27.2666  |                        0.684298 |                       0.099415  |            6.88324 |
| Run2016H  | top05      |          7849 |                    1.0275  |                -0.0540809  |     1.08158 | 0            | inf       |                        0.324627 |                       0.0881805 |            3.6814  |
| Run2016H  | top01      |          1570 |                    1.3884  |                -0.0140265  |     1.40243 | 6.3227e-85   |  19.4928  |                        0.421656 |                       0.0967536 |            4.35804 |
| Run2016H  | top001     |           157 |                    2.34181 |                -0.00234453 |     2.34416 | 1.27435e-05  |   4.21044 |                        0.528662 |                       0.099574  |            5.30924 |
| combined  | top05      |         38092 |                    1.45396 |                -0.0765249  |     1.53049 | 0            | inf       |                        0.41636  |                       0.08335   |            4.99532 |
| combined  | top01      |          7619 |                    1.85256 |                -0.0187143  |     1.87127 | 0            | inf       |                        0.535897 |                       0.0955973 |            5.60578 |
| combined  | top001     |           762 |                    2.53115 |                -0.00253423 |     2.53368 | 8.39888e-76  |  18.3867  |                        0.665354 |                       0.0994346 |            6.69138 |

## Mimicry Distances

| comparison                                       | other_classification   |   euclidean_distance |   cosine_similarity | components_compared                                                      |
|:-------------------------------------------------|:-----------------------|---------------------:|--------------------:|:-------------------------------------------------------------------------|
| SMS-T5Wg vs qcd_ht1000to1500_nanoaodsim_pilot    | SM_background          |             16.4742  |            0.380684 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs qcd_ht500to700_nanoaodsim_pilot      | SM_background          |             17.3418  |            0.204879 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs qcd_ht700to1000_nanoaodsim_pilot     | SM_background          |             16.9532  |            0.30119  | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs sms_t2tt_compressed_nanoaodsim_pilot | signal                 |              6.05307 |            0.977019 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs ttjets_nanoaodsim_pilot              | SM_background          |             16.588   |            0.385145 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |
| SMS-T5Wg vs wjets_lnu_nanoaodsim_pilot           | SM_background          |             18.6168  |           -0.161361 | P_missing;P_visible_energy;P_multiplicity;P_btag_structure;P_compression |

## Interpretation

The expanded automated layer strengthens Darren's disappearance-trace interpretation in a qualified way. SMS-T5Wg remains benchmark-enriched if the q95 rows above remain above 5 sigma after correction. The result is still indirect, model-dependent benchmark enrichment and real-data trace-direction alignment, not direct particle detection.

## Remaining Weaknesses

The expansion used small NanoAODSIM files, so component availability is still reduced. W/Z/DY/single-top/diboson coverage is still incomplete, and published signal-region overlap remains missing.