# Frozen-Reference OPQ SM Shape Likelihood

## Method Correction

All residual fits, feature standardisation constants, missing-energy deciles and
numerical OPQ microband thresholds were fitted once on the original Run2016G
reference sample. They were then applied unchanged to held-out real samples and
to UL16 simulated templates. This avoids recalculating percentile boundaries
within each simulated process, which would make a process-composition test
tautological.

## Combined 10 Percent Readout

| mode                            | region                    |   sample_count |   fisher_statistic |     fisher_p |   fisher_Z |   min_sample_Z |   max_sample_Z |
|:--------------------------------|:--------------------------|---------------:|-------------------:|-------------:|-----------:|---------------:|---------------:|
| exact_completed_only            | MET_trace                 |              3 |           319.605  | 5.13111e-66  |   17.1215  |    4.01759e-05 |       13.8667  |
| exact_completed_only            | JetHT_SingleMuon_controls |              3 |            15.3921 | 0.0174168    |    2.11029 |    0           |        2.28681 |
| exact_plus_unit_weight_metadata | MET_trace                 |              3 |           655.051  | 3.08751e-138 |   24.9996  |    2.34963     |       21.029   |
| exact_plus_unit_weight_metadata | JetHT_SingleMuon_controls |              3 |           105.513  | 1.77025e-20  |    9.20118 |    1.2512      |        7.40639 |

## Control Closure Diagnostic

| mode                            |   max_control_Z | controls_closed_at_Z_le_2   | interpretation       |
|:--------------------------------|----------------:|:----------------------------|:---------------------|
| exact_completed_only            |         2.28681 | False                       | control_closure_fail |
| exact_plus_unit_weight_metadata |         7.40639 | False                       | control_closure_fail |

## Interpretation

This is a corrected SM-template shape test, not an absolute-yield or official
CMS likelihood. It uses sideband anchoring and fixed reference thresholds.
The `exact_completed_only` mode contains full-record GenFilterInfo-normalised
W3Jets and TTW. The unit-weight mode additionally includes records whose
generator weights are verified +1 in the extracted sample and whose official
metadata report zero negative-weight fraction.

The historical rank-tail likelihood should not be used as a discovery-style SM
prediction because it recomputed microband thresholds separately in each MC
template. The fixed-reference test is the relevant diagnostic. A MET trace is
only interpretable as process-specific if the same template closes JetHT and
SingleMuon controls; a failure in this table blocks that interpretation.
