# N-Frame Verified Metadata Reanalysis

## Dataset

- Signal regions: 752
- Analyses: 40
- ATLAS rows: 555
- CMS rows: 197

## Metadata Integrity

Zero percent missing model input values were obtained only after imputation and should not be interpreted as zero percent missing verified metadata. Verified metadata were defined as values extracted directly from HEPData tables, ATLAS/CMS auxiliary material, or explicit paper signal-region definitions. All inferred or imputed values were flagged and analysed separately.

The current automated pass uses local SModelS metadata and source/comment text as its verified layer. Label-only values are treated as inferred/proxy values, not verified.

## Core Model Results

- Verified-only pooled `Z ~ B_access_verified_z`: beta=-0.1955, p=0.06874, cluster_p=0.01215, R2=0.02902, n=115
- Verified+imputed pooled `Z ~ B_access_verified_imputed_z`: beta=-0.1337, p=0.2815, cluster_p=0.0006838, R2=0.01326, n=752

Full model tables:

- `results/tables/verified_only_model_results.csv`
- `results/tables/verified_plus_imputed_model_results.csv`
- `results/tables/verified_cross_validation_results.csv`
- `results/tables/verified_key_terms_bootstrap_permutation.csv`

## Cross-Validation

                scheme   n            r2          mae         rmse  correlation_predicted_observed  note               dataset
GroupKFold_by_analysis 115  1.634588e-02     0.822313     1.138490                        0.157479   NaN         verified_only
  ATLAS_train_CMS_test  79 -2.036862e+08 10543.379603 13225.460378                        0.258793   NaN         verified_only
  CMS_train_ATLAS_test  36 -2.676531e-03     1.143938     1.526752                        0.073270   NaN         verified_only
GroupKFold_by_analysis 752 -2.324853e-02     1.672382     2.789863                       -0.128821   NaN verified_plus_imputed
  ATLAS_train_CMS_test 197 -2.076231e-01     1.513264     3.105497                       -0.094630   NaN verified_plus_imputed
  CMS_train_ATLAS_test 555 -3.783983e-03     1.829722     2.738557                       -0.070458   NaN verified_plus_imputed

## Bootstrap And Permutation

dataset                 score                        term   n          beta        ci_low      ci_high  perm_p_two_sided  perm_p_positive
 pooled         verified_only         B_access_verified_z 115     -0.195545     -0.385213    -0.007120          0.064468         0.967516
  ATLAS         verified_only         B_access_verified_z  36 -10693.940277 -79439.472233 36495.092489          0.677661         0.662669
    CMS         verified_only         B_access_verified_z  79     -0.201106     -0.382241    -0.010694          0.023488         0.987006
 pooled verified_plus_imputed B_access_verified_imputed_z 752     -0.078983     -0.157862     0.020276          0.399300         0.801099
  ATLAS verified_plus_imputed B_access_verified_imputed_z 555      0.553596      0.055936     1.014055          0.096952         0.041979
    CMS verified_plus_imputed B_access_verified_imputed_z 197     -0.151882     -0.257906    -0.048890          0.148926         0.972014

## Interpretation

This is a metadata-quality reanalysis, not a tuned signal search. If effects appear only in verified+imputed data, they should be treated as exploratory and metadata-sensitive. If verified-only complete cases are sparse, the correct conclusion is limited verified coverage, not stronger physics evidence.

No SUSY discovery, hidden symmetry proof, or detector-level claim is made.
