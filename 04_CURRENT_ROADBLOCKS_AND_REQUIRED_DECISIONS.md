# Current Roadblocks and Required Decisions

## Technical roadblocks

1. **No unique collider equation from theory:** the N-Frame books give conceptual boundary/tri-aspect ideas, but no unique function mapping a latent collider state to a numerical detector/reconstruction distribution. New score weights are empirical unless Darren specifies the mapping.
2. **Incomplete SM normalisation:** Z-to-neutrinos and inclusive top need complete accessible records or authoritative `sumGenWeights`; QCD/diboson scans are incomplete.
3. **Control model design:** JetHT and SingleMuon should not be expected to share the MET score shape. They must form process-enriched control channels with documented transfer factors.
4. **Independent data:** new source records/eras/topologies must be allocated before model fitting. Existing 2016 samples have been repeatedly explored.
5. **Insufficient independent benchmark records:** five signal records cannot establish discovery-grade predictive superiority.

## What Darren must specify to make N-Frame falsifiable

1. Latent/bulk state variables relevant to an LHC event.
2. Projection rule from latent state to detector/reconstruction observables.
3. Boundary condition/loss with fixed or explicitly fit-eligible parameters.
4. Directional observable prediction that differs from a Standard Model baseline.
5. Which parameters may be calibrated on development data and which are theory-fixed.

## Required path to a credible collider result

1. Freeze score/calibration/regions on development data.
2. Build process-enriched W, Z-proxy, top and QCD controls plus MET validation/SR channels.
3. Obtain complete signed-weight SM prediction and matched trigger/object selections.
4. Require all control/validation regions to close before reading the held-out MET SR.
5. Evaluate the held-out SR once and account for the exploration trials.

## Required path to credible predictive-superiority evidence

1. Add many independent signal topology records and matched SM records.
2. Freeze the N-Frame construction before new test records are opened.
3. Hold out complete records, not individual events.
4. Compare against strong standard baselines by topology and estimate uncertainty at the record level.
