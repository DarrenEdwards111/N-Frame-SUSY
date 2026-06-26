# Update To Darren: Trigger/Filter Boundary Check

Date: 2026-06-08

We have moved from a topology-only reproduction into a real-data event-level boundary check with trigger/filter diagnostics.

## Done

- Re-ran real CMS MiniAOD extraction with broad HLT category flags and standard event-quality filter flags.
- Recomputed the N-Frame-style boundary score without using trigger/filter flags as inputs.
- Inspected the top boundary events against trigger category, event-quality filters, file, run, and luminosity-bin concentration.

## Current interpretation

The result is **qualified rather than strengthened**. It remains interesting because the high-boundary tail is structured, but the honest next step is a trigger/run-matched control test before interpreting the tail as anything beyond detector/data-taking structure.

## Next

Construct matched controls within the same CMS dataset and trigger category, then test whether the boundary excess remains after that matching.