# Remote OPQ Process-Aware SM Shape Layer

## Scope

The frozen score is evaluated as a within-process shape diagnostic:

$$B_{OPQ} = 0.344828O + 0.517241P - 0.137931Q.$$

Every row comes from remote CMS UL16 MiniAODSIM extraction with valid generator
weight information. The q99 threshold is calculated separately for each record,
so the table measures tail occupancy and event composition, not a cross-section
weighted prediction for CMS data.

## Summary

|   record_id | process_family   |   quality_events |   B_OPQ_q99_threshold_within_record |   B_OPQ_q99_events |   B_OPQ_q99_fraction |   generator_weight_sum_selected |   mean_MET_pt |   mean_HT |   mean_Njets30 | shape_only   | absolute_yield_interpretation                               |
|------------:|:-----------------|-----------------:|------------------------------------:|-------------------:|---------------------:|--------------------------------:|--------------:|----------:|---------------:|:-------------|:------------------------------------------------------------|
|       69548 | WJets            |            14996 |                             1.66679 |                150 |            0.0100027 |                 13795.1         |       53.8299 |  118.331  |       1.83716  | True         | not permitted without record-level sum of generator weights |
|       69746 | WJets            |             4997 |                             1.37805 |                 50 |            0.010006  |                     5.98653e+08 |       36.4902 |   25.9818 |       0.542726 | True         | not permitted without record-level sum of generator weights |
|       74907 | ZNuNu            |              560 |                             1.63543 |                  6 |            0.0107143 |                    29.6818      |      132.806  |  159.12   |       1.66429  | True         | not permitted without record-level sum of generator weights |
|       74909 | ZNuNu            |               66 |                             2.60154 |                  1 |            0.0151515 |                     3.40909     |      270.502  |  336.844  |       2        | True         | not permitted without record-level sum of generator weights |
|       63118 | QCD              |            14996 |                             1.41809 |                150 |            0.0100027 |                 14996           |       30.997  |  284.05   |       2.87443  | True         | not permitted without record-level sum of generator weights |
|       63126 | QCD              |            14995 |                             1.46434 |                150 |            0.0100033 |                 14995           |       35.7454 |  500.311  |       3.41047  | True         | not permitted without record-level sum of generator weights |
|       63102 | QCD              |            14987 |                             1.80871 |                150 |            0.0100087 |                 14987           |       77.8213 | 2318.49   |       4.35237  | True         | not permitted without record-level sum of generator weights |
|       72753 | diboson          |            14984 |                             1.79861 |                150 |            0.0100107 |                 14984           |       43.6341 |  122.574  |       1.92425  | True         | not permitted without record-level sum of generator weights |
|       75592 | diboson          |            14994 |                             1.8744  |                150 |            0.010004  |                 14994           |       41.5515 |  123.827  |       1.93604  | True         | not permitted without record-level sum of generator weights |
|       74893 | ZNuNu            |             4999 |                             1.25741 |                 50 |            0.010002  |                  4999           |       80.6786 |   96.9333 |       1.43689  | True         | not permitted without record-level sum of generator weights |
|       74897 | ZNuNu            |             4993 |                             1.4325  |                 50 |            0.010014  |                  4993           |      112.628  |  213.508  |       2.23913  | True         | not permitted without record-level sum of generator weights |
|       74901 | ZNuNu            |             4998 |                             1.53039 |                 50 |            0.010004  |                  4998           |      149.212  |  421.177  |       2.9878   | True         | not permitted without record-level sum of generator weights |
|       74903 | ZNuNu            |             4998 |                             1.67601 |                 50 |            0.010004  |                  4998           |      171.459  |  633.23   |       3.36955  | True         | not permitted without record-level sum of generator weights |
|       74905 | ZNuNu            |             4374 |                             1.80368 |                 44 |            0.0100594 |                  4374           |      190.074  |  903.227  |       3.65501  | True         | not permitted without record-level sum of generator weights |
|       74895 | ZNuNu            |             1248 |                             1.7361  |                 13 |            0.0104167 |                  1248           |      229.1    | 1449.12   |       3.89423  | True         | not permitted without record-level sum of generator weights |
|       74899 | ZNuNu            |             4999 |                             1.76106 |                 50 |            0.010002  |                  4999           |      279.507  | 2896.83   |       4.15603  | True         | not permitted without record-level sum of generator weights |
|       67710 | TTTop            |             3557 |                             2.40687 |                 36 |            0.0101209 |                  3557           |      195.204  |  427.535  |       3.98116  | True         | not permitted without record-level sum of generator weights |
|       67722 | TTTop            |             4998 |                             2.52863 |                 50 |            0.010004  |                  4998           |      201.058  |  458.839  |       4.37655  | True         | not permitted without record-level sum of generator weights |
|       67726 | TTTop            |              773 |                             2.42852 |                  8 |            0.0103493 |                   773           |      207.401  |  471.269  |       4.41915  | True         | not permitted without record-level sum of generator weights |
|       68205 | TTAssoc          |             4993 |                             1.81695 |                 50 |            0.010014  |                  2358.46        |       64.3424 |  540.108  |       5.83136  | True         | not permitted without record-level sum of generator weights |
|       68196 | TTAssoc          |             4998 |                             1.64863 |                 50 |            0.010004  |                   380.031       |       70.7726 |  536.275  |       5.85134  | True         | not permitted without record-level sum of generator weights |
|       68072 | TTAssoc          |             4994 |                             1.69033 |                 50 |            0.010012  |                  1657.84        |       98.6824 |  498.839  |       5.11394  | True         | not permitted without record-level sum of generator weights |
|       68082 | TTAssoc          |             2079 |                             1.82965 |                 21 |            0.010101  |                  1382.49        |       70.2844 |  566.481  |       5.7191   | True         | not permitted without record-level sum of generator weights |

## Interpretation

This creates the process-aware SM shape layer required for the next sideband
fit. It is intentionally not converted into predicted yields until record-level
sum-of-generator-weight provenance is supplied. That avoids the earlier error
of treating a limited file subset as a complete luminosity-normalised sample.
