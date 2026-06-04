# Paper-Ready Methods And Results Text

## Methods

We constructed a verified metadata layer for public ATLAS/CMS supersymmetry signal-region tables derived from the SModelS public database and associated public-source pointers. Signal-region yields were retained from the existing public corpus, while kinematic and topology variables were reclassified according to provenance.

Zero percent missing model input values were obtained only after imputation and should not be interpreted as zero percent missing verified metadata. Verified metadata were defined as values extracted directly from HEPData tables, ATLAS/CMS auxiliary material, or explicit paper signal-region definitions. All inferred or imputed values were flagged and analysed separately.

## Verified Versus Imputed Variables

For each signal region and field, the analysis records a value, verification flag, confidence label, source pointer, source text, and match type. HIGH and MEDIUM confidence entries are analysed as verified. LOW confidence entries, including label-only parsing and SModelS proxy values without explicit cut text, are not treated as verified and enter only the verified+imputed sensitivity dataset.

## Statistical Models

The primary verified-only model regresses standardized residuals on `B_access_verified_z` using only complete verified fields. A second verified+imputed model uses verified values where available and flagged proxy values otherwise, with metadata-completeness and imputation-fraction controls.

## Limitations

The automated pass cannot replace manual extraction from every paper table. Null, unstable, or imputation-driven results are interpreted as no robust support. This analysis is exploratory and does not claim evidence for supersymmetry or hidden symmetry.
