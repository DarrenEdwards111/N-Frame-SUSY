# Tri-Aspect Dynamic Boundary Model

## Purpose

Darren's tri-aspect note suggests that the collision boundary should be dynamic rather than a single static observer surface. This run translates that into a testable toy model:

\[
\Omega_0 \rightarrow \Omega_1 \rightarrow \Omega_2 \rightarrow \Omega_T
\]

with three projected aspects:

1. physical projection: missing energy, visible energy, and detector/reconstruction stress;
2. observer projection: missing-energy residual after visible reconstructed structure is modelled;
3. algebraic projection: distance from the low-dimensional SM event manifold fitted by weighted PCA.

The model is dynamic because the MET, HTMHT, JetHT, and SingleMuon contexts are allowed to use different mixtures of the same tri-aspect components. Candidate mixtures are selected on development files and tested on held-out files.

## Split Audit

| era      | primary_dataset   | split       |   source_files |   events |
|:---------|:------------------|:------------|---------------:|---------:|
| Run2015D | HTMHT             | development |              2 |     7641 |
| Run2015D | HTMHT             | validation  |              1 |     6340 |
| Run2015D | JetHT             | development |              2 |     9759 |
| Run2015D | JetHT             | validation  |              1 |     5528 |
| Run2015D | MET               | development |              2 |    12222 |
| Run2015D | MET               | validation  |              1 |     4154 |
| Run2015D | SingleMuon        | development |              2 |    11761 |
| Run2015D | SingleMuon        | validation  |              1 |     6372 |
| Run2016  | MET               | development |              6 |   211330 |
| Run2016  | MET               | validation  |              2 |    35317 |

## Best Held-Out Dynamic Boundary Results

| candidate      | split      | signal_jet_bin   |   Run2016_MET_Z |   Run2015D_MET_Z |   Run2015D_HTMHT_Z |   Run2015D_JetHT_control_Z |   Run2015D_SingleMuon_control_Z |   Run2016_other_jetbin_max_absZ |   Run2015D_dataset_control_max_absZ |   signal_stouffer_Z |   min_signal_Z |   selection_score | passes_trace_breakthrough_screen   |
|:---------------|:-----------|:-----------------|----------------:|-----------------:|-------------------:|---------------------------:|--------------------------------:|--------------------------------:|------------------------------------:|--------------------:|---------------:|------------------:|:-----------------------------------|
| tri_dynamic_02 | validation | 1to2jets         |         4.74372 |          3.91289 |            1.92371 |                    2.99517 |                        0.932407 |                         1.41364 |                             2.99517 |             6.10855 |        1.92371 |          1.92371  | False                              |
| tri_dynamic_00 | validation | 1to2jets         |         4.74372 |          3.91289 |            1.79538 |                    2.99517 |                        0.932407 |                         1.41364 |                             2.99517 |             6.03446 |        1.79538 |          1.79538  | False                              |
| tri_dynamic_05 | validation | 0jet             |        24.7173  |          5.90245 |          nan       |                    3.87592 |                        5.33499  |                         4.82225 |                             5.33499 |            21.6514  |        5.90245 |          1.7452   | False                              |
| tri_dynamic_06 | validation | 0jet             |        24.7173  |          5.90245 |          nan       |                    3.87592 |                        5.33499  |                         4.82225 |                             5.33499 |            21.6514  |        5.90245 |          1.7452   | False                              |
| tri_dynamic_07 | validation | 0jet             |        24.7173  |          5.90245 |          nan       |                    3.87592 |                        5.33499  |                         4.82225 |                             5.33499 |            21.6514  |        5.90245 |          1.7452   | False                              |
| tri_dynamic_01 | validation | 1to2jets         |         4.74372 |          3.91289 |            1.66136 |                    2.99517 |                        0.932407 |                         1.41364 |                             2.99517 |             5.95708 |        1.66136 |          1.66136  | False                              |
| tri_dynamic_03 | validation | 1to2jets         |         4.74372 |          3.91289 |            1.5089  |                    2.99517 |                        0.932407 |                         1.41364 |                             2.99517 |             5.86906 |        1.5089  |          1.5089   | False                              |
| tri_dynamic_09 | validation | 0jet             |        19.9755  |          4.67608 |          nan       |                    3.87592 |                        5.33499  |                         4.03195 |                             5.33499 |            17.4313  |        4.67608 |          1.30913  | False                              |
| tri_dynamic_10 | validation | 0jet             |        19.9755  |          4.67608 |          nan       |                    3.87592 |                        5.33499  |                         4.03195 |                             5.33499 |            17.4313  |        4.67608 |          1.30913  | False                              |
| tri_dynamic_11 | validation | 0jet             |        19.9755  |          4.67608 |          nan       |                    3.87592 |                        5.33499  |                         4.03195 |                             5.33499 |            17.4313  |        4.67608 |          1.30913  | False                              |
| tri_dynamic_08 | validation | 0jet             |        19.9755  |          4.67608 |            2.42199 |                    3.87592 |                        5.33499  |                         4.03195 |                             5.33499 |            15.6309  |        2.42199 |         -0.944958 | False                              |
| tri_dynamic_04 | validation | 0jet             |        24.7173  |          5.90245 |            2.42199 |                    3.87592 |                        5.33499  |                         4.82225 |                             5.33499 |            19.0766  |        2.42199 |         -1.73526  | False                              |

## Best Dynamic Candidate Weights

| candidate      | dataset_context   |   observer_projection |   algebraic_projection |   ordinary_qcd_axis |   physical_projection |   leptonic_control_axis |
|:---------------|:------------------|----------------------:|-----------------------:|--------------------:|----------------------:|------------------------:|
| tri_dynamic_02 | MET               |                  0.8  |                    0   |               -0.2  |                  0    |                    0    |
| tri_dynamic_02 | HTMHT             |                  0.45 |                    0.1 |               -0.1  |                  0.35 |                    0    |
| tri_dynamic_02 | JetHT             |                  0.55 |                    0.1 |               -0.35 |                  0    |                    0    |
| tri_dynamic_02 | SingleMuon        |                  0.55 |                    0.1 |               -0.2  |                  0    |                   -0.15 |

## Readout

- Dynamic models screened: 12
- Dynamic models held out for validation: 12
- Strict trace-breakthrough pass count: 0

## Interpretation

This is a more faithful implementation of Darren's dynamical-boundary idea than the static v5 score. It allows the same underlying N-Frame aspects to reweight by detector/reconstruction context.

If the best dynamic model improves HTMHT transfer while keeping JetHT and SingleMuon controls quiet, that supports the dynamical-boundary direction. If it does not, the bottleneck is still cross-dataset transfer and SM/control robustness rather than lack of boundary flexibility.
