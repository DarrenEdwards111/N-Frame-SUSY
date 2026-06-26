# Boundary Scoring Report

## Input

Used `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\real_collision_20gb_uproot_partial_event_features.csv`.

## What Was Computed

The current score uses only available real-data event features. In this run, the Python/uproot fallback provides visible jet activity, so `R_multiplicity` and `R_reconstruction` are available.

`R_missing`, `R_compression_proxy`, `R_lifetime_proxy`, and `R_displacement_proxy` are unavailable because the required MET or genuine displacement/lifetime variables were not extracted. They were kept as missing values, not replaced with zero.

## Main Limitation

This is not the full N-Frame boundary model. It is a visible-jet boundary dry run on real collision data. CMSSW is still required for the proper boundary-stress model.

## Output

- Scored events: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\data\processed\real_collision_20gb_event_features_scored.csv`
- Component availability: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\boundary_component_availability.csv`
- Component summary by sample: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\tables\boundary_component_summary_by_sample.csv`
