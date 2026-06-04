# N-Frame Boundary-Selection Reanalysis

## Data Source Summary
This project is configured to start from public HEPData/published signal-region tables, not raw CERN Open Data.

- CMS-SUS-21-007 (CMS), HEPData 10.17182/hepdata.135454.v1, 138 fb^-1 at 13 TeV.
- ATLAS-SUSY-2018-32 (ATLAS), HEPData 10.17182/hepdata.89413.v4, 139 fb^-1 at 13 TeV.

The current processed table contains 5 analyses and 12 signal regions. If only `demo_signal_regions.csv` is present, the numerical results below are a pipeline check, not a physics result.

## Boundary-Access Definition
For each signal region,

`Delta_N = N_obs - N_exp`

`Z = (N_obs - N_exp) / sigma_exp`

`B_access = z(MET) + z(HT_or_meff) + z(N_jets) + z(N_leptons) + z(N_btags) + category_bonus`

Missing kinematic features are set to zero after z-scoring, so absent metadata does not create artificial high or low boundary access. `category_bonus` adds one point for compressed spectra, disappearing tracks, long-lived particles, displaced vertices, high-MET labels, and high-multiplicity labels.

In the N-Frame hypothesis, `B_access` is a proxy for event classes occupying high-boundary-access regimes defined by missing information, event complexity, entropy-like multiplicity, long-lived separation, and reconstruction difficulty.

## Regression Result: Z ~ B_access_z
- Signal regions: 12
- Beta: 0.3370
- Standard error: 0.2395
- OLS p-value: 0.1897
- Bootstrap 95% CI: [-0.1016, 1.1374]
- Permutation p-value: 0.1888
- Spearman rho: 0.4825
- Spearman p-value: 0.1121
- Direction: beta > 0

## Delta_N Regression
- Beta: 1.1007
- OLS p-value: 0.2821
- Bootstrap 95% CI: [-0.5588, 3.6149]
- Permutation p-value: 0.2687

## Interpretation
No evidence for N-Frame boundary-selection.

This is a meta-analysis of signal-region deviations. It does not claim discovery of SUSY, hidden symmetry, or physics beyond the Standard Model.
