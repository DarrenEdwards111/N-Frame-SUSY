# Real-Only Boundary With Trigger/Filter Synthesis For N-Frame

Date: 2026-06-08

## What changed

We re-ran the real CMS collision extraction with broad trigger and event-quality diagnostics available for every event. The boundary model itself was kept independent of these diagnostics, so the trigger/filter columns are used only to test whether the high-boundary tail looks like physics structure, trigger selection, or a data-quality effect.

## Main result

The current trigger/filter pass classifies the N-Frame interpretation as **qualified rather than strengthened**. The strongest acceptable statement is that the high-boundary tail is structured and reproducible across real samples, but it still needs trigger and provenance controls before it can be interpreted as evidence for a hidden higher-dimensional process.

## Classification table

| score        | tail    | classification                 | reason                                                                   |   top_file_fraction |   top_run_fraction |   top_lumi_bin_fraction |
|:-------------|:--------|:-------------------------------|:-------------------------------------------------------------------------|--------------------:|-------------------:|------------------------:|
| hand_defined | top100  | data-quality/technical concern | One or more quality-filter pass fractions are below 98% in the top tail. |            0.43     |           0.61     |                0.35     |
| hand_defined | top1000 | data-quality/technical concern | One or more quality-filter pass fractions are below 98% in the top tail. |            0.247    |           0.323    |                0.254    |
| hand_defined | top666  | data-quality/technical concern | One or more quality-filter pass fractions are below 98% in the top tail. |            0.252252 |           0.339339 |                0.262763 |
| unsupervised | top100  | data-quality/technical concern | One or more quality-filter pass fractions are below 98% in the top tail. |            0.43     |           0.6      |                0.35     |
| unsupervised | top1000 | data-quality/technical concern | One or more quality-filter pass fractions are below 98% in the top tail. |            0.245    |           0.245    |                0.186    |
| unsupervised | top666  | data-quality/technical concern | One or more quality-filter pass fractions are below 98% in the top tail. |            0.252252 |           0.252252 |                0.21021  |

## Next task

Build a control-matched comparison: compare high-boundary events only against events from the same primary dataset, same trigger category, same run range, and similar pileup/vertex conditions. That is the next step needed to separate N-Frame-like structure from CMS trigger and data-taking structure.