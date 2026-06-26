# Non-Docker Extraction Strategy Report

## Route Results

- Route A - uproot direct arrays: readable groups include jets=7, packed_candidates=7, vertices=5.
- Route B - uproot branch/leaf decomposition: promising for jet leaves, packed-candidate dxy/dz leaves, and primary-vertex leaves.
- Route C - PyROOT availability: import ROOT failed: ModuleNotFoundError("No module named 'ROOT'")
- Route D - conda ROOT suggestion: PyROOT is not installed in the current Python environment. Conda ROOT could be tried later as a non-Docker route, but it was not installed automatically.
- Route E - ROOT command line: ROOT command not found on PATH

## Candidate Readability Summary

| candidate_group    |   tested |   readable |   extractable |
|:-------------------|---------:|-----------:|--------------:|
| electrons          |        4 |          1 |             1 |
| event_ids          |        1 |          0 |             0 |
| filters_quality    |        6 |          4 |             4 |
| jets               |        8 |          7 |             7 |
| met                |        4 |          1 |             1 |
| muons              |        4 |          1 |             1 |
| packed_candidates  |        7 |          7 |             7 |
| photons            |        3 |          1 |             1 |
| secondary_vertices |        3 |          1 |             1 |
| taus               |        3 |          1 |             1 |
| triggers           |        7 |          2 |             2 |
| vertices           |        5 |          5 |             5 |

## Answers

1. Can we extract MET without Docker?

   Current evidence: no. `slimmedMETs` exists, but generic uproot only read the product-present flag, not MET pt/phi.

2. Can we extract muons/electrons without Docker?

   Current evidence: no. `slimmedMuons` and `slimmedElectrons` exist, but generic uproot only read product-present flags, not pt/eta/counts.

3. Can we extract b-tags without Docker?

   Current evidence: partially. Jet hadron/parton flavour leaves and some user-float structures are readable, but an experimental b-tag discriminator was not identified as a clean scalar branch. Hadron flavour can be labelled as a proxy only, not as a measured b-tag.

4. Can we extract run/lumi/event without Docker?

   Current evidence: no. `EventAuxiliary` exists but failed generic uproot deserialisation in the tested environment.

5. Can we extract triggers/filters without Docker?

   Current evidence: partially. Trigger/filter products are visible and present flags are readable, but trigger decisions were not extracted as named decisions. Some filter/noise object branches are visible but not yet physics-ready.

6. Can we construct the full N-Frame boundary score without Docker?

   Current evidence: no. We can improve the visible/reconstruction side using jets, packed-candidate displacement-like leaves, and vertex complexity, but the full score needs MET and event IDs.

7. If not, exactly what remains inaccessible?

   MET pt/phi, muon/electron kinematics or counts, experimental b-tag discriminators, run/lumi/event IDs, named trigger decisions, and CMS-interpreted filter decisions remain inaccessible with the tested non-Docker tools.
