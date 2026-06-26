# Existing CMSSW Package Audit

## Package Location

```text
D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_raw_multi_sample\cmssw_full_extraction
```

## Important Files

- `run_one_sample.sh`
- `README.md`
- `compute_full_event_score.py`
- `validate_and_make_pseudo_regions.py`
- `NFrame/NFrameMiniAOD/plugins/NFrameMiniAODAnalyzer.cc`
- `NFrame/NFrameMiniAOD/plugins/BuildFile.xml`
- `NFrame/NFrameMiniAOD/python/run_nframe_miniAOD_cfg.py`

## Wrapper Behaviour

`run_one_sample.sh` expects to be run inside a valid CMSSW environment where `CMSSW_BASE` is already set.

It then:

1. Enters `${CMSSW_BASE}/src`.
2. Copies the local NFrame analyzer/plugin files into the CMSSW source tree.
3. Runs `scram b`.
4. Runs a test extraction using `cmsRun`.
5. Scores the test output.
6. Runs a full extraction using `cmsRun`.
7. Scores and validates the full output.

## Expected Environment Variables

- `SAMPLE_ID`
- `NFRAME_INPUT_DIR`
- `NFRAME_OUTPUT_DIR`
- `NFRAME_TEST_MAXEVENTS`
- `NFRAME_MAXEVENTS_FULL`
- `NFRAME_BTAG`

## Current Config Behaviour

`run_nframe_miniAOD_cfg.py` searches:

```python
glob.glob(os.path.join(input_dir, "*.root"))
```

That means `NFRAME_INPUT_DIR` must point directly at a directory containing ROOT files. For this real-data folder, suitable container paths are:

```text
/data/cms_met_run2016g_collision/30509
/data/cms_jetht_run2016g_collision/30508
/data/cms_singlemuon_run2016g_collision/30513
```

Using only `/data` will not work unless the config is changed to search recursively.

## Analyzer Outputs

The analyzer writes:

- `run`
- `lumi`
- `event`
- `MET_pt`
- `MET_phi`
- `N_jets_all`
- `N_jets_30`
- `N_jets_50`
- `HT`
- `jet_pt_sum`
- `leading_jet_pt`
- `subleading_jet_pt`
- `N_muons`
- `N_electrons`
- `N_leptons`
- `lepton_pt_sum`
- `N_btags_loose`
- `N_btags_medium`
- `N_btags_tight`
- `btag_discriminator_status`

## Fit To Current Real Samples

The wrapper is compatible with the three current sample IDs as long as `SAMPLE_ID` and `NFRAME_INPUT_DIR` are set correctly:

- `cms_met_run2016g_collision`
- `cms_jetht_run2016g_collision`
- `cms_singlemuon_run2016g_collision`

## Caution

The wrapper currently runs both test and full extraction in one call. For a safe 100-event or 1000-event gate, call it with:

```bash
export NFRAME_TEST_MAXEVENTS=100
export NFRAME_MAXEVENTS_FULL=0
```

or create a small test-only wrapper before running full extraction.

