# Optional Simulation Calibration Appendix

## Status

Skipped for this real-data pass.

## What Was Checked

Existing simulated files were found in:

```text
D:\cern_open_data\nframe_stage2
```

Present files:

- `sms_t5wg_mg1500_mlsp1_signal`, record 63465, one ROOT file
- `susy_htoaa4b_m12_signal`, record 64906, one ROOT file

## Why This Was Skipped

Darren's corrected task was to work from real CMS collision MiniAOD only. The current proper extraction blocker is CMSSW/Docker, not a lack of simulated calibration. Running simulation calibration now would risk distracting from the real-data extraction layer.

Simulation calibration should only be revisited after the same extraction and scoring pipeline works on the real MET, JetHT, and SingleMuon data.

## Interpretation Rule

Any future simulation comparison must be labelled:

```text
Simulation calibration only - not evidence of real SUSY.
```

