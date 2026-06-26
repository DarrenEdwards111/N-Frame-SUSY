# Update To Darren: Top Boundary Event Inspection

Date: 2026-06-08

## What We Did

We used real CMS collision data only. No simulated samples were used.

We inspected the top high-boundary events from the full real-data-only MiniAOD run of 665,902 events.

## What The Top Events Look Like

The top boundary events are not random. They are mainly mixed high-stress events involving:

- high visible activity / JetHT-like structure,
- jet multiplicity,
- b-tags and heavy-flavour-like reconstruction structure,
- secondary-vertex proxy structure,
- packed-candidate/reconstruction complexity,
- some missing-energy and compression-like imbalance.

For the hand-defined top 1000, about 88.7% are visible-energy/JetHT dominant, 87.9% have heavy-flavour/reconstruction flags, and 93.1% have secondary-vertex proxy flags.

## Are They Spread Across Files?

They are not explained by one file alone, but the very top events are concentrated enough by file/run/lumi that we need trigger and data-quality follow-up.

For the hand-defined top 1000:

- top source file: 24.7%
- top run: 32.3%
- top lumi bin: 36.4%

So the answer is: **structured, but not yet cleanly physics-like**.

## Trigger/Filter Information

We tested trigger/filter extraction and it works on a small 1,000-event-per-sample probe. It can extract broad HLT categories and common event-quality flags. But it has not yet been run over the full 665,902 events, so the current full top-event tables do not have full trigger/filter coverage.

## Strongest Honest Claim Now

The strongest honest claim is that real CMS collision data contain a structured high-boundary tail with mixed missing-energy, visible-energy, multiplicity, b-tag, secondary-vertex proxy and reconstruction-complexity stress. This is a real-data N-Frame follow-up region.

It is not evidence that SUSY was found. It is not a discovery claim.

## Next Step

The next step is to re-run the full file-by-file extraction with the trigger/filter columns enabled, then check whether the strongest top-boundary events pass standard event-quality filters and whether the run/lumi concentration is trigger/data-quality driven.
