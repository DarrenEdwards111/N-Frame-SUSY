# Update To Darren: SUSY Versus SM Background Test

Date: 2026-06-09

## Plain English Summary

We froze the real-data-fitted N-Frame boundary equation and added two Standard Model simulated benchmark backgrounds: inclusive TTJets and high-HT QCD. This is a benchmark/specificity test, not a discovery test.

## q95 Tail Fractions

| sample_id                        | process_label              | classification   | threshold   |   threshold_value |   events |   mean_BNF |   median_BNF |   tail_fraction |   ci_low |   ci_high |
|:---------------------------------|:---------------------------|:-----------------|:------------|------------------:|---------:|-----------:|-------------:|----------------:|---------:|----------:|
| sms_t5wg_mg1500_mlsp1_signal     | SMS-T5Wg mGluino1500 mLSP1 | signal           | q95         |             1.968 |     5000 |  1.6124    |    1.57143   |         0.1978  | 0.186095 | 0.208905  |
| ttjets_nanoaodsim_pilot          | TTJets inclusive           | SM_background    | q95         |             1.968 |    50000 |  0.875909  |    0.830251  |         0.04908 | 0.047199 | 0.050781  |
| qcd_ht700to1000_nanoaodsim_pilot | QCD HT700to1000            | SM_background    | q95         |             1.968 |    50000 |  0.630491  |    0.55262   |         0.02446 | 0.02324  | 0.0257905 |
| susy_htoaa4b_m12_signal          | SUSY HToAA4B mA12          | signal           | q95         |             1.968 |     2394 |  0.0390909 |    0.0403913 |         0       | 0        | 0         |

## Interpretation

SMS-T5Wg remains higher than the tested SM backgrounds in q95 high-boundary occupancy. This strengthens the SUSY-relevance interpretation at benchmark level, while still not making a discovery claim. Positive enrichment here should be described as benchmark-level SUSY-relevant support only, not evidence that SUSY was found in real collision data.

## Next Step

Repeat with more SM backgrounds and, where manageable, MiniAODSIM extraction so the secondary-vertex and reconstruction components match the real-data validation more completely.