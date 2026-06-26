from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "outputs_sm_process_composition_sideband_fit/tables/02_sideband_fit_signal_predictions.csv"
OUT = ROOT / "outputs_adjacent_sideband_shape_nuisance_stress"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def z_with_rel_uncertainty(obs: float, exp: float, rel_unc: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel_unc * exp) ** 2, 1e-12)))


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(IN)
    rows = []
    for _, row in df.iterrows():
        obs = float(row["signal_tail_95_100_observed"])
        exp = float(row["signal_tail_95_100_expected"])
        high_oe = float(row["control_high_80_95_observed_over_expected"])
        all_oe = float(row["control_all_0_95_observed_over_expected"])
        for correction_name, multiplier in [
            ("none_process_fit_only", 1.0),
            ("adjacent_high_sideband_forced_closed", high_oe),
            ("all_control_sidebands_forced_closed", all_oe),
        ]:
            corrected_exp = exp * multiplier
            out = {
                "real_sample": row["real_sample"],
                "fit_scenario": row["fit_scenario"],
                "shape_correction": correction_name,
                "shape_multiplier": multiplier,
                "observed": obs,
                "expected_before_shape_correction": exp,
                "expected_after_shape_correction": corrected_exp,
                "observed_over_expected_after_shape_correction": obs / corrected_exp if corrected_exp > 0 else np.inf,
            }
            for rel_unc in [0.127, 0.20, 0.30]:
                out[f"Z_with_{int(rel_unc * 1000) / 10:g}pct_uncertainty"] = z_with_rel_uncertainty(obs, corrected_exp, rel_unc)
            rows.append(out)

    stress = pd.DataFrame(rows)
    stress.to_csv(TABLES / "01_adjacent_sideband_shape_nuisance_stress.csv", index=False)

    main = stress[
        stress["fit_scenario"].eq("sideband_fit_3x_family_bounds")
        & stress["shape_correction"].isin(["none_process_fit_only", "adjacent_high_sideband_forced_closed"])
    ].copy()
    main.to_csv(TABLES / "02_main_3x_process_fit_with_adjacent_shape_stress.csv", index=False)

    report = f"""# Adjacent-Sideband Shape-Nuisance Stress Test

## Question

If the high-score control sideband does not close, can we treat that as a residual SM background-shape nuisance and force it to close? If yes, does the strict MET top-tail still remain discovery-level?

## Method

Input: process-composition sideband fit from `scripts/171_sm_process_composition_sideband_fit.py`.

Stress correction:

- `none_process_fit_only`: use the sideband-fitted SM mixture directly.
- `adjacent_high_sideband_forced_closed`: multiply the predicted signal-tail background by the observed/expected ratio in the adjacent 80-95% sideband.
- `all_control_sidebands_forced_closed`: multiply by the observed/expected ratio over the full 0-95% sideband.

The adjacent high-sideband correction is the important conservative test because it asks whether a smooth unresolved background-shape mismatch immediately below the signal tail could explain the apparent top-tail excess.

## Main 3x-Bounded Process-Fit Result

{main.to_markdown(index=False)}

## Interpretation

If the `adjacent_high_sideband_forced_closed` rows remain above 5 sigma at 12.7% uncertainty, the signal tail is stronger than the adjacent sideband mismatch alone.

If they fall below 5 sigma, then the current evidence is not yet discovery-grade under this stricter background-shape nuisance. That would mean the project needs a better SM shape model or independent control data before making a discovery-level claim.
"""
    (REPORTS / "01_ADJACENT_SIDEBAND_SHAPE_NUISANCE_STRESS_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Adjacent-Sideband Shape Stress

We took the process-composition-fitted SM background and applied an extra conservative correction that forces the adjacent 80-95% score sideband to close. Then we retested the strict 95-100% MET boundary tail.

Main result:

{main.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_ADJACENT_SIDEBAND_SHAPE_STRESS.md").write_text(short, encoding="utf-8")

    print("ADJACENT SIDEBAND SHAPE-NUISANCE STRESS COMPLETE")
    print(main.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
