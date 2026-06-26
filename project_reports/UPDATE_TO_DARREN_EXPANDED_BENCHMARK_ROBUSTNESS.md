# Update To Darren: Expanded Benchmark Robustness

Date: 2026-06-09

We did not stop at manual inspection. We broadened the automated benchmark layer with additional WJets, QCD HT bins and a compressed stop-like SUSY benchmark, all treated as benchmark/specificity simulation only.

## Added Samples

| sample_id                            | process_label                             | classification   | data_tier   |   actual_size_bytes |
|:-------------------------------------|:------------------------------------------|:-----------------|:------------|--------------------:|
| wjets_lnu_nanoaodsim_pilot           | WJetsToLNu                                | SM_background    | NANOAODSIM  |           133529187 |
| qcd_ht500to700_nanoaodsim_pilot      | QCD HT500to700                            | SM_background    | NANOAODSIM  |           110734104 |
| qcd_ht1000to1500_nanoaodsim_pilot    | QCD HT1000to1500                          | SM_background    | NANOAODSIM  |            80890335 |
| sms_t2tt_compressed_nanoaodsim_pilot | SMS-T2tt compressed stop mStop300 mLSP290 | signal           | NANOAODSIM  |           108940400 |

## Does The 5 Sigma SMS-T5Wg Result Survive?

| threshold   | signal_sample                | signal_process             | background_sample                 | background_process   |   signal_count |   signal_total |   background_count |   background_total |   p_signal |   p_background |   risk_difference |   risk_ratio |   z_one_sided |   p_one_sided |   log10_p |   bonferroni_family_size |   bonferroni_z | remains_5sigma_after_bonferroni   |
|:------------|:-----------------------------|:---------------------------|:----------------------------------|:---------------------|---------------:|---------------:|-------------------:|-------------------:|-----------:|---------------:|------------------:|-------------:|--------------:|--------------:|----------:|-------------------------:|---------------:|:----------------------------------|
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht1000to1500_nanoaodsim_pilot | QCD HT1000to1500     |            989 |           5000 |               2591 |              33536 |     0.1978 |      0.0772603 |           0.12054 |      2.56018 |       27.3906 |  1.77375e-165 |  -164.751 |                       60 |        27.2409 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | ttjets_nanoaodsim_pilot           | TTJets inclusive     |            989 |           5000 |               2454 |              50000 |     0.1978 |      0.04908   |           0.14872 |      4.03015 |       41.3912 |  0            |  -374.04  |                       60 |        41.2923 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht700to1000_nanoaodsim_pilot  | QCD HT700to1000      |            989 |           5000 |               1223 |              50000 |     0.1978 |      0.02446   |           0.17334 |      8.08667 |       59.4826 |  0            |  -770.48  |                       60 |        59.4138 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht500to700_nanoaodsim_pilot   | QCD HT500to700       |            989 |           5000 |                446 |              50000 |     0.1978 |      0.00892   |           0.18888 |     22.1749  |       79.886  |  0            | -1388.09  |                       60 |        79.8348 | True                              |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | wjets_lnu_nanoaodsim_pilot        | WJetsToLNu           |            989 |           5000 |                  1 |              50000 |     0.1978 |      2e-05     |           0.19778 |   9890       |      100.295  |  0            | -2186.7   |                       60 |       100.254  | True                              |

## Does The Trace Direction Still Appear In Real Data?

| dataset   | bnf_tail   |   high_events |   mean_expanded_trace_high |   mean_expanded_trace_rest |   mean_diff |    welch_p |   welch_z |   fraction_high_above_trace_q90 |   fraction_rest_above_trace_q90 |   enrichment_ratio |
|:----------|:-----------|--------------:|---------------------------:|---------------------------:|------------:|-----------:|----------:|--------------------------------:|--------------------------------:|-------------------:|
| Run2016G  | top01      |          6049 |                    1.95122 |                 -0.0197107 |     1.97093 | 0          |  inf      |                        0.551827 |                       0.0954358 |            5.78218 |
| Run2016H  | top01      |          1570 |                    1.3884  |                 -0.0140265 |     1.40243 | 6.3227e-85 |   19.4928 |                        0.421656 |                       0.0967536 |            4.35804 |
| combined  | top01      |          7619 |                    1.85256 |                 -0.0187143 |     1.87127 | 0          |  inf      |                        0.535897 |                       0.0955973 |            5.60578 |

## Plain English

This remains indirect, model-dependent evidence. It is not direct particle detection and not a discovery claim. The main weakness is that the added samples are small NanoAODSIM reduced-component benchmarks.

## Next Step

Add fuller MiniAODSIM or larger NanoAODSIM W/Z/DY/single-top/diboson backgrounds, then repeat the same frozen-score test.