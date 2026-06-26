# Candidate Branch Readability Report

## Test Scope

Tested candidate branches on one representative real CMS MiniAOD file:

`D:\cern_open_data\nframe_stage2_real_collision_20gb\cms_jetht_run2016g_collision\30508\0002568B-EAD1-4949-B6FB-4E3C6B61FEFF.root`

Each candidate was read for the first 100 events using uproot exact branch reads or wildcard/filter reads.

## Summary

| candidate_group    |   tested |   readable |   potentially_extractable |
|:-------------------|---------:|-----------:|--------------------------:|
| electrons          |        4 |          1 |                         1 |
| event_ids          |        1 |          0 |                         0 |
| filters_quality    |        6 |          4 |                         4 |
| jets               |        8 |          7 |                         7 |
| met                |        4 |          1 |                         1 |
| muons              |        4 |          1 |                         1 |
| packed_candidates  |        7 |          7 |                         7 |
| photons            |        3 |          1 |                         1 |
| secondary_vertices |        3 |          1 |                         1 |
| taus               |        3 |          1 |                         1 |
| triggers           |        7 |          2 |                         2 |
| vertices           |        5 |          5 |                         5 |

## Interpretation

Readable groups with simple numeric jagged leaves can support non-Docker extraction. Object-only CMS EDM branches may be present by name but still not useful if generic uproot cannot deserialize them into physics quantities.

Detailed results are in:

`D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\candidate_branch_read_tests.csv`
