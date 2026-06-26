# Real-Only Boundary And Signal-Region Synthesis

Date: 2026-06-08

## What Was Done

This analysis used real CMS Run2016G MiniAOD collision data only. No simulated SUSY samples, simulated records, or simulation labels were used in the main result.

The real-only MiniAOD analysis extracted 150,000 events across MET, JetHT and SingleMuon primary datasets. Boundary parameters were estimated from real event variables: missing energy, visible energy, jet and lepton multiplicity, b-tag structure, primary vertices, packed candidates, secondary vertices and compression-like/reconstruction-complexity proxies.

## Real-Data Boundary Parameters

The hand-defined score shows that the high-boundary tail is not one single variable. The strongest top-tail drivers are combinations of visible energy, missing energy, multiplicity, b-tags and reconstruction complexity.

Top hand-defined driver shifts in the top 1% tail:

| score                     | variable                              |   top01_mean |    rest_mean |   mean_difference |   top01_median |   rest_median |
|:--------------------------|:--------------------------------------|-------------:|-------------:|------------------:|---------------:|--------------:|
| B_boundary_hand_defined_z | HT                                    |   795.707    |  272.685     |         523.022   |     691.996    |    135.312    |
| B_boundary_hand_defined_z | packed_candidate_count                |  1866.54     | 1484.05      |         382.492   |    1853        |   1452        |
| B_boundary_hand_defined_z | MET_pt                                |   110.823    |   50.9996    |          59.8237  |      92.8319   |     37.709    |
| B_boundary_hand_defined_z | secondary_vertex_count                |     7.356    |    1.54801   |           5.80799 |       7        |      1        |
| B_boundary_hand_defined_z | N_primary_vertices                    |    23.6907   |   17.908     |           5.78265 |      23        |     17        |
| B_boundary_hand_defined_z | max_btag_discriminator                |     0.944199 |   -3.5137    |           4.4579  |       0.981012 |      0.55529  |
| B_boundary_hand_defined_z | N_jets_30                             |     5.64333  |    2.18892   |           3.45441 |       6        |      2        |
| B_boundary_hand_defined_z | real_only_unsupervised_boundary_score |     3.25682  |   -0.0328972 |           3.28972 |       3.10707  |     -0.229787 |
| B_boundary_hand_defined_z | B_boundary_hand_defined_z             |     3.04909  |   -0.0307989 |           3.07989 |       2.91865  |     -0.123891 |
| B_boundary_hand_defined_z | N_jets_50                             |     4.24067  |    1.48618   |           2.75449 |       4        |      1        |

PCA axis 1 is mainly loaded by:

| feature                |   loading |   explained_variance_ratio |
|:-----------------------|----------:|---------------------------:|
| N_jets_30              |  0.406486 |                   0.347067 |
| N_jets_50              |  0.399233 |                   0.347067 |
| displacement_proxy_raw |  0.396464 |                   0.347067 |
| secondary_vertex_count |  0.396464 |                   0.347067 |
| log1p_HT               |  0.362808 |                   0.347067 |
| compression_proxy_raw  | -0.260949 |                   0.347067 |
| N_btags_medium         |  0.241093 |                   0.347067 |
| N_btags_tight          |  0.197165 |                   0.347067 |

PCA axis 2 is mainly loaded by:

| feature                |    loading |   explained_variance_ratio |
|:-----------------------|-----------:|---------------------------:|
| N_primary_vertices     |  0.541817  |                    0.18445 |
| packed_candidate_count |  0.52459   |                    0.18445 |
| compression_proxy_raw  |  0.423262  |                    0.18445 |
| log1p_MET_pt           |  0.410363  |                    0.18445 |
| N_leptons              | -0.172824  |                    0.18445 |
| log1p_HT               | -0.119096  |                    0.18445 |
| N_jets_30              | -0.0931087 |                    0.18445 |
| displacement_proxy_raw |  0.0913669 |                    0.18445 |

## Dataset Enrichment

Hand-defined top 5% boundary enrichment:

| sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| cms_met_run2016g_collision        |          0.5024 |            0.333333 |             1.5072 |          3768 |
| cms_jetht_run2016g_collision      |          0.4608 |            0.333333 |             1.3824 |          3456 |
| cms_singlemuon_run2016g_collision |          0.0368 |            0.333333 |             0.1104 |           276 |

Unsupervised top 5% boundary enrichment:

| sample_id                         |   tail_fraction |   baseline_fraction |   enrichment_ratio |   tail_events |
|:----------------------------------|----------------:|--------------------:|-------------------:|--------------:|
| cms_jetht_run2016g_collision      |        0.5312   |            0.333333 |             1.5936 |          3984 |
| cms_met_run2016g_collision        |        0.340133 |            0.333333 |             1.0204 |          2551 |
| cms_singlemuon_run2016g_collision |        0.128667 |            0.333333 |             0.386  |           965 |

## Relation To Earlier Signal-Region Topology Result

The earlier published signal-region table suggested that rare/topology-stressed rows had higher capped topology stress values. That remains a separate, preliminary comparison layer, partly because the signal-region result was influenced by ATLAS-SUSY-2018-42-eff.

The new result is cleaner for Darren's current question because it is based on real CMS MiniAOD only. It shows that high N-Frame boundary-stress conditions can be estimated directly inside real collision events and that the top tails show repeatable structure across independent real CMS primary datasets.

## What Is Still Weak

- Source ROOT file is tracked at sample/log level, not exact per-event file level.
- This is not yet full 20.789 GiB processing.
- No claim is made about SUSY or hidden particles.
- Trigger/filter details are not yet unpacked into named trigger decisions.

## What Would Make It Stronger

- Run the full real-data sample after validating output size and stability.
- Add exact per-event source file provenance to the CMSSW analyzer.
- Add more real CMS records and possibly a parallel NanoAOD validation.
- Compare the high-boundary tail against known CMS object/event-quality filters.
