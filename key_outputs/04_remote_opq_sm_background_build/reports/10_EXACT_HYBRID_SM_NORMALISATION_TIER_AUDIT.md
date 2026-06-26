# Exact/Hybrid SM Normalisation Tier Audit

## Purpose

This table upgrades the previous approximate SM normalisation layer by using
the resumable `GenFilterInfo` sumweight production when, and only when, a full
online record has successful exact rows.

## Exact Coverage Status

|   record_id | process_family   |   online_file_count |   planned_exact_files |   exact_successful_files | exact_complete_full_online   | normalisation_tier                        |   normalisation_denominator |   base_event_scale_for_generator_weight |
|------------:|:-----------------|--------------------:|----------------------:|-------------------------:|:-----------------------------|:------------------------------------------|----------------------------:|----------------------------------------:|
|       69746 | WJets            |                   1 |                     1 |                        0 | False                        | approx_constant_weight_sumw_pending_exact |                 9.91423e+12 |                             3.57596e-05 |
|       69548 | WJets            |                 288 |                   288 |                      288 | True                         | exact_record_sumw                         |                 1.88875e+07 |                             0.0713998   |
|       74907 | ZNuNu            |                   1 |                     1 |                        0 | False                        | shape_only_not_normalised                 |               nan           |                           nan           |
|       74909 | ZNuNu            |                   1 |                     1 |                        0 | False                        | shape_only_not_normalised                 |               nan           |                           nan           |
|       63118 | QCD              |                 562 |                   562 |                        0 | False                        | metadata_unit_weight_record               |                 4.68635e+07 |                            11.3491      |
|       63126 | QCD              |                1143 |                  1143 |                        0 | False                        | metadata_unit_weight_record               |                 5.29165e+07 |                             0.939467    |
|       63102 | QCD              |                 163 |                   163 |                      110 | False                        | metadata_unit_weight_record               |                 4.868e+06   |                             0.00738245  |
|       72753 | diboson          |                 106 |                   106 |                        0 | False                        | metadata_unit_weight_record               |                 7.584e+06   |                             0.0595244   |
|       75592 | diboson          |                  29 |                    29 |                        0 | False                        | metadata_unit_weight_record               |                 1.151e+06   |                             0.171912    |
|       74893 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 7.08322e+06 |                             0.0615821   |
|       74897 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 6.81411e+06 |                             0.0175528   |
|       74901 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 6.11405e+06 |                             0.00265604  |
|       74903 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 1.88167e+06 |                             0.00209704  |
|       74905 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |            633500           |                             0.00278473  |
|       74895 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |            115609           |                             0.00353503  |
|       74899 | ZNuNu            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |            110461           |                             8.32487e-05 |
|       67710 | TTTop            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 6.04513e+06 |                             0.000165968 |
|       67722 | TTTop            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 5.77937e+06 |                             0.000237459 |
|       67726 | TTTop            |                   1 |                     0 |                        0 | False                        | metadata_unit_weight_record               |                 7.41083e+06 |                             0.000190146 |
|       68205 | TTAssoc          |                   1 |                     1 |                        0 | False                        | shape_only_not_normalised                 |               nan           |                           nan           |
|       68196 | TTAssoc          |                   1 |                     1 |                        0 | False                        | shape_only_not_normalised                 |               nan           |                           nan           |
|       68072 | TTAssoc          |                  77 |                    77 |                       77 | True                         | exact_record_sumw                         |                 1.11315e+06 |                             0.00189912  |
|       68082 | TTAssoc          |                  14 |                    14 |                       14 | True                         | exact_record_sumw                         |            209107           |                             0.0205624   |

## Tier Summary

| normalisation_tier                        | process_family   |   records |
|:------------------------------------------|:-----------------|----------:|
| approx_constant_weight_sumw_pending_exact | WJets            |         1 |
| exact_record_sumw                         | TTAssoc          |         2 |
| exact_record_sumw                         | WJets            |         1 |
| metadata_unit_weight_record               | QCD              |         3 |
| metadata_unit_weight_record               | TTTop            |         3 |
| metadata_unit_weight_record               | ZNuNu            |         7 |
| metadata_unit_weight_record               | diboson          |         2 |
| shape_only_not_normalised                 | TTAssoc          |         2 |
| shape_only_not_normalised                 | ZNuNu            |         2 |

## Interpretation

`exact_record_sumw` is the tier needed for a publication-grade luminosity
normalisation component for that record. `approx_constant_weight_sumw_pending_exact`
is still a stress-test tier, not final evidence, because it relies on metadata
generated-event counts and selected generator-weight stability rather than the
full record-level generator-weight sum.

`metadata_unit_weight_record` is an intermediate, explicitly non-GenFilterInfo
tier. It is permitted only where the extracted generator weights are all
exactly +1, the selected variance is zero, the official negative-weight
fraction is zero, and the record supplies a generated-event count. This makes
the generator-weight denominator equal to the official generated-event count
under the stated unit-weight condition, but it remains distinct from a
full-file `GenFilterInfo` scan.
