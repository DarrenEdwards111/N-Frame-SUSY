# Exact GenFilter Sumweight File Plan

## Purpose

This plan targets exact `GenFilterInfo` sums from the `LuminosityBlocks` tree.
Records with full online file coverage can be promoted to full-record exact
normalisation after the ROOT macro completes.

## Summary

|   record_id | process_family   | mode                     | record_complete_online   |   files |   all_file_count |   online_file_count |
|------------:|:-----------------|:-------------------------|:-------------------------|--------:|-----------------:|--------------------:|
|       63102 | QCD              | full_online_exact_target | True                     |     163 |              163 |                 163 |
|       63118 | QCD              | full_online_exact_target | True                     |     562 |              562 |                 562 |
|       63126 | QCD              | full_online_exact_target | True                     |    1143 |             1143 |                1143 |
|       68072 | TTAssoc          | full_online_exact_target | True                     |      77 |               77 |                  77 |
|       68082 | TTAssoc          | full_online_exact_target | True                     |      14 |               14 |                  14 |
|       69548 | WJets            | full_online_exact_target | True                     |     288 |              288 |                 288 |
|       72753 | diboson          | full_online_exact_target | True                     |     106 |              106 |                 106 |
|       75592 | diboson          | full_online_exact_target | True                     |      29 |               29 |                  29 |
|       68196 | TTAssoc          | partial_online_probe     | False                    |       1 |              558 |                   1 |
|       68205 | TTAssoc          | partial_online_probe     | False                    |       1 |              878 |                   1 |
|       69746 | WJets            | partial_online_probe     | False                    |       1 |              945 |                   1 |
|       74907 | ZNuNu            | partial_online_probe     | False                    |       1 |              176 |                   1 |
|       74909 | ZNuNu            | partial_online_probe     | False                    |       1 |               83 |                   1 |

## Interpretation

`full_online_exact_target` records can be summed over every online file because
the CERN record exposes the full file set online. `partial_online_probe` records
are probes only; they document the gap but cannot be used as full-record exact
normalisation unless the missing files or official sumweights are obtained.
