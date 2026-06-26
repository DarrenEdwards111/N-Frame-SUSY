# Fuller Component MiniAODSIM Feature Extraction Report

Date: 2026-06-09

Full extraction used maxEvents=50000 per selected MiniAODSIM file and preserved exact file provenance.

## Extraction Status

| mode   | sample_slug            |   record_id | process_label    | classification   |   max_events | status   |   events_written | output_csv                                                                                                                                                            | log_path                                                                                                                        |   returncode |
|:-------|:-----------------------|------------:|:-----------------|:-----------------|-------------:|:---------|-----------------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------|-------------:|
| full   | qcd_ht1000to1500_63078 |       63078 | QCD HT1000to1500 | SM_background    |        50000 | success  |              794 | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\fuller_component_benchmarks\full\qcd_ht1000to1500_63078_event_features.csv | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\logs\fuller_full_qcd_ht1000to1500_63078.log |            0 |
| full   | qcd_ht700to1000_63139  |       63139 | QCD HT700to1000  | SM_background    |        50000 | success  |              196 | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\fuller_component_benchmarks\full\qcd_ht700to1000_63139_event_features.csv  | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\logs\fuller_full_qcd_ht700to1000_63139.log  |            0 |
| full   | wjetstolnu_69550       |       69550 | WJetsToLNu       | SM_background    |        50000 | success  |              457 | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\fuller_component_benchmarks\full\wjetstolnu_69550_event_features.csv       | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\logs\fuller_full_wjetstolnu_69550.log       |            0 |

## Feature Availability

| sample_id              | process_label    | classification   |   events | has_secondary_vertex_count   | has_packed_candidate_count   | has_met_ht   |
|:-----------------------|:-----------------|:-----------------|---------:|:-----------------------------|:-----------------------------|:-------------|
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    |      794 | True                         | True                         | True         |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    |      196 | True                         | True                         | True         |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    |      457 | True                         | True                         | True         |

Combined output: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\fuller_component_benchmarks\fuller_component_benchmark_event_features.csv`