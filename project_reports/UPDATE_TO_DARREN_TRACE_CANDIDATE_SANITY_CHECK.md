# Update To Darren: Trace Candidate Sanity Check

Date: 2026-06-09

We avoided relying on Tom manually inspecting event displays and ran an automated sanity check on the top real trace candidates.

## What We Found

| candidate_set   | primary_category                     |   events |   total |   fraction |
|:----------------|:-------------------------------------|---------:|--------:|-----------:|
| combined        | likely_SM_top_heavy_flavour_like     |       10 |     100 |       0.1  |
| combined        | trace_compatible_follow_up_candidate |        6 |     100 |       0.06 |
| combined        | trace_direction_aligned_but_SM_like  |       82 |     100 |       0.82 |
| combined        | unclear_follow_up_needed             |        2 |     100 |       0.02 |

In the combined top-100 list, 6 events are trace-compatible follow-up candidates by the conservative automated rules. Most are trace-direction aligned but still SM-like or provenance-caveated.

## Quality And Controls

Available quality-filter failures: 0. Matched-control comparison shows the candidates are not ordinary within nearby real-data context: they have higher B_NF, higher trace score, higher MET/HT, more secondary-vertex structure, and are closer to the SMS trace centroid than their controls.

## What This Means

This is still not direct particle detection. It is an automated sanity layer supporting boundary-stress trace dynamics for a small follow-up subset, while qualifying the broader set as mostly SM-like/provenance-caveated.

## Next Step

Have someone with physics expertise inspect the 6 combined follow-up candidates and the top-25 plain-English cards, especially source/run/lumi concentration and ordinary SM explanations.