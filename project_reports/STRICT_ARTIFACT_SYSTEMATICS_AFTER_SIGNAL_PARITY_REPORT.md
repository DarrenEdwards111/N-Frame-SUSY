# Strict Artefact/Systematics After Signal Parity Report

Date: 2026-06-09

This stress test reruns the high-B_NF versus trace-alignment comparison after excluding obvious provenance and reconstruction artefact candidates.

| stress_test                            |   events_remaining |   high_tail_events |   mean_trace_high |   mean_trace_rest |   mean_diff |   welch_p |   welch_z |   top_source_file_fraction_high_tail |   top_run_fraction_high_tail | status   |
|:---------------------------------------|-------------------:|-------------------:|------------------:|------------------:|------------:|----------:|----------:|-------------------------------------:|-----------------------------:|:---------|
| all_real                               |             761835 |              38092 |           2.13372 |        -0.112302  |     2.24603 |         0 |       inf |                             0.218786 |                     0.180432 | tested   |
| exclude_top_source_file                |             588899 |              29445 |           2.2252  |         0.0706529 |     2.15455 |         0 |       inf |                             0.230328 |                     0.194668 | tested   |
| exclude_top_run                        |             620360 |              31018 |           2.20514 |         0.0331327 |     2.17201 |         0 |       inf |                             0.227481 |                     0.191566 | tested   |
| exclude_top_lumi                       |             753093 |              37655 |           2.13081 |        -0.109828  |     2.24064 |         0 |       inf |                             0.221113 |                     0.17424  | tested   |
| standard_quality_only                  |             761835 |              38092 |           2.13372 |        -0.112302  |     2.24603 |         0 |       inf |                             0.218786 |                     0.180432 | tested   |
| exclude_extreme_N_primary_vertices     |             747333 |              37367 |           2.14921 |        -0.1026    |     2.25181 |         0 |       inf |                             0.220435 |                     0.182434 | tested   |
| exclude_extreme_packed_candidate_count |             746626 |              37332 |           2.15256 |        -0.0998788 |     2.25244 |         0 |       inf |                             0.220829 |                     0.182926 | tested   |
| exclude_extreme_secondary_vertex_count |             757869 |              37894 |           2.11132 |        -0.122093  |     2.23341 |         0 |       inf |                             0.217422 |                     0.175621 | tested   |
| JetHT_only                             |             155004 |               7751 |           2.38601 |         0.78626   |     1.59975 |         0 |       inf |                             0.383434 |                     0.357373 | tested   |
| MET_only                               |             214059 |              10703 |           2.38482 |         0.310268  |     2.07455 |         0 |       inf |                             0.444829 |                     0.444829 | tested   |
| SingleMuon_only                        |             392772 |              19639 |           1.18171 |        -0.659551  |     1.84126 |         0 |       inf |                             0.448903 |                     0.32186  | tested   |