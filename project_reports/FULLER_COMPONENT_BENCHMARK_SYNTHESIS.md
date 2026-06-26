# Fuller Component MiniAODSIM Benchmark Synthesis

Date: 2026-06-09

## What was done

We searched CERN Open Data metadata for MiniAODSIM benchmark files, planned a download under the 25 GB cap, downloaded accessible files, ran CMSSW extraction, applied the frozen Run2016G fitted N-Frame equation, and compared the fuller-component results with the earlier reduced benchmark layer.

No B_NF refit was performed. No discovery claim is made. This is not a SUSY classifier.

## Data outcome

- Selected files in plan: 5
- Downloaded or already present files: 3
- Total downloaded bytes: 117571300
- Successful full CMSSW extractions: 3
- Total extracted fuller-component events: 1447
- P_displacement_proxy available through secondary vertices: yes
- P_reconstruction available through packed candidates: yes

## Sample summary

| sample_id              | process_label    | classification   | component_mode   |   events |   mean_BNF |   median_BNF |   mean_displacement |   mean_reconstruction |   mean_missing |   mean_visible |
|:-----------------------|:-----------------|:-----------------|:-----------------|---------:|-----------:|-------------:|--------------------:|----------------------:|---------------:|---------------:|
| qcd_ht1000to1500_63078 | QCD HT1000to1500 | SM_background    | full-component   |      794 |   1.45927  |     1.3467   |            2.53314  |             0.508833  |     -0.0689071 |      3.43985   |
| qcd_ht700to1000_63139  | QCD HT700to1000  | SM_background    | full-component   |      196 |   0.975532 |     0.885344 |            1.87309  |             0.2921    |     -0.316112  |      1.9497    |
| wjetstolnu_69550       | WJetsToLNu       | SM_background    | full-component   |      457 |   0.236943 |     0.13038  |            0.667447 |            -0.0966588 |      0.27745   |     -0.0664587 |

## Key statistical result

| threshold   | signal_sample                | signal_process             | background_sample      | background_process   |   signal_count |   signal_total |   background_count |   background_total |   p_signal |   p_background |   risk_difference |   risk_ratio |   z_one_sided |   p_one_sided |       log10_p |   bonferroni_family_size |   bonferroni_z | remains_5sigma_after_bonferroni   |
|:------------|:-----------------------------|:---------------------------|:-----------------------|:---------------------|---------------:|---------------:|-------------------:|-------------------:|-----------:|---------------:|------------------:|-------------:|--------------:|--------------:|--------------:|-------------------------:|---------------:|:----------------------------------|
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht1000to1500_63078 | QCD HT1000to1500     |            989 |           5000 |                198 |                794 |     0.1978 |     0.24937    |        -0.0515703 |     0.793198 |      -3.34464 |   0.999588    |  -0.000178943 |                       36 |     -inf       | False                             |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | qcd_ht700to1000_63139  | QCD HT700to1000      |            989 |           5000 |                 14 |                196 |     0.1978 |     0.0714286  |         0.126371  |     2.7692   |       4.39727 |   5.48093e-06 |  -5.26115     |                       36 |        3.54365 | False                             |
| q95         | sms_t5wg_mg1500_mlsp1_signal | SMS-T5Wg mGluino1500 mLSP1 | wjetstolnu_69550       | WJetsToLNu           |            989 |           5000 |                  1 |                457 |     0.1978 |     0.00218818 |         0.195612  |    90.3946   |      10.387   |   1.42094e-25 | -24.8474      |                       36 |       10.0394  | True                              |

## Incremental score check

| score                                    |      auc |
|:-----------------------------------------|---------:|
| P_missing_only                           | 0.98219  |
| P_missing_plus_visible                   | 0.918015 |
| P_missing_plus_visible_plus_multiplicity | 0.815377 |
| B_NF_without_displacement_reconstruction | 0.540911 |
| B_NF_fitted                              | 0.413442 |
| B_NF_without_missing                     | 0.338169 |
| P_visible_energy_only                    | 0.320552 |
| P_multiplicity_only                      | 0.306847 |
| P_displacement_plus_reconstruction       | 0.184425 |

## Trace direction

| status   | reason                                                                                                                                   | fallback_available   | fallback_table                                                                                                                       |
|:---------|:-----------------------------------------------------------------------------------------------------------------------------------------|:---------------------|:-------------------------------------------------------------------------------------------------------------------------------------|
| not_run  | No accessible MiniAODSIM signal sample survived download/smoke extraction, so no full-component signal-vs-SM direction could be defined. | True                 | D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\expanded_real_trace_alignment_summary.csv |

## Interpretation

qualified/partial. The fuller-component SM MiniAODSIM extraction worked and confirms that P_displacement_proxy and P_reconstruction can be populated from MiniAOD, but the accessible fuller sample set contains no signal file. High-HT QCD becomes a stronger boundary mimic than SMS-T5Wg in q95/q99 tail tests, so the earlier SUSY-like result is less specific than it looked from the reduced benchmark layer.

## Exact next action

Find an accessible MiniAODSIM signal file, preferably SMS-T5Wg or another high-MET simplified model, and rerun phases 101-108 with at least one signal and the existing high-HT QCD fuller-component backgrounds.