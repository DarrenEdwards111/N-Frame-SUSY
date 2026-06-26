from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "outputs_full_shape_tail_residual_topology_scan/tables/03_full_shape_tail_residual_summary.csv"
OUT = ROOT / "outputs_q99_1to2jet_tail_candidate_replication"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def trial_adjust_z(z: float, n: int) -> float:
    if not np.isfinite(z):
        return np.nan
    p = norm.sf(z)
    p_adj = min(1.0, p * max(n, 1))
    return float(norm.isf(p_adj)) if p_adj < 1 else 0.0


def stouffer(zs: list[float]) -> float:
    vals = np.array([z for z in zs if np.isfinite(z)], dtype=float)
    if len(vals) == 0:
        return np.nan
    return float(vals.sum() / np.sqrt(len(vals)))


def fisher(zs: list[float]) -> float:
    # One-sided normal p-values combined with Fisher, returned as sigma-equivalent.
    from scipy.stats import chi2

    vals = np.array([z for z in zs if np.isfinite(z)], dtype=float)
    if len(vals) == 0:
        return np.nan
    ps = np.clip(norm.sf(vals), 1e-300, 1.0)
    stat = -2 * np.log(ps).sum()
    p = chi2.sf(stat, 2 * len(ps))
    return float(norm.isf(p))


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(IN)
    n_trials = len(df)
    df["tail_99_100_shape_extrapolated_Z_global_trial_adjusted"] = df[
        "tail_99_100_shape_extrapolated_Z_with_shape_uncertainty"
    ].map(lambda z: trial_adjust_z(float(z), n_trials))

    candidate = df[(df["topology_column"].eq("topology_jet_bin")) & (df["topology_value"].eq("1to2jets"))].copy()
    candidate["role"] = candidate["real_sample"].map(
        {
            "Run2016G_main_MET": "development_discovery_sample",
            "Run2016H_expanded_MET": "independent_validation_sample",
            "Run2016H_new_independent_MET": "independent_validation_sample",
            "Run2016H_independent_MET": "subset_crosscheck_inside_Run2016H_expanded",
        }
    )
    cols = [
        "role",
        "real_sample",
        "real_events_in_topology",
        "sideband_80_95_observed_over_expected",
        "tail_95_100_shape_extrapolated_observed_over_expected",
        "tail_95_100_shape_extrapolated_Z_with_shape_uncertainty",
        "tail_99_100_shape_extrapolated_observed_over_expected",
        "tail_99_100_shape_extrapolated_Z_with_shape_uncertainty",
        "tail_99_100_shape_extrapolated_Z_global_trial_adjusted",
        "sideband_log_rms",
    ]
    candidate = candidate[cols].sort_values("role")

    independent = candidate[candidate["role"].isin(["development_discovery_sample", "independent_validation_sample"])].copy()
    validation = candidate[candidate["role"].eq("independent_validation_sample")].copy()
    all_independent_z = independent["tail_99_100_shape_extrapolated_Z_with_shape_uncertainty"].tolist()
    validation_z = validation["tail_99_100_shape_extrapolated_Z_with_shape_uncertainty"].tolist()
    combined = pd.DataFrame(
        [
            {
                "combination": "Run2016G_development_plus_independent_Run2016H_validation_samples",
                "included_samples": ", ".join(independent["real_sample"]),
                "n_samples": len(independent),
                "stouffer_Z": stouffer(all_independent_z),
                "fisher_Z": fisher(all_independent_z),
                "minimum_sample_Z": float(np.min(all_independent_z)),
                "interpretation": "Exploratory combined candidate; not a final discovery statistic because topology was selected after scanning.",
            },
            {
                "combination": "independent_Run2016H_validation_only",
                "included_samples": ", ".join(validation["real_sample"]),
                "n_samples": len(validation),
                "stouffer_Z": stouffer(validation_z),
                "fisher_Z": fisher(validation_z),
                "minimum_sample_Z": float(np.min(validation_z)),
                "interpretation": "Validation-only check after candidate selection in Run2016G.",
            },
        ]
    )

    ranked_q99 = df.sort_values("tail_99_100_shape_extrapolated_Z_with_shape_uncertainty", ascending=False)[
        [
            "real_sample",
            "topology_column",
            "topology_value",
            "real_events_in_topology",
            "tail_99_100_shape_extrapolated_observed_over_expected",
            "tail_99_100_shape_extrapolated_Z_with_shape_uncertainty",
            "tail_99_100_shape_extrapolated_Z_global_trial_adjusted",
            "sideband_80_95_observed_over_expected",
            "sideband_log_rms",
        ]
    ]

    candidate.to_csv(TABLES / "01_q99_1to2jet_candidate_replication.csv", index=False)
    combined.to_csv(TABLES / "02_q99_1to2jet_candidate_combined_significance.csv", index=False)
    ranked_q99.to_csv(TABLES / "03_all_topology_q99_trial_adjusted_ranking.csv", index=False)

    report = f"""# Q99 1-2 Jet Final-Tail Candidate Replication

## Question

After fitting away the broad 50-95% N-Frame score distortion, is there a sharper very-final-tail candidate that replicates?

## Candidate

- Dataset stream: MET
- Topology: 1-2 jets
- Score: `common_missing_resid_visible_only`
- Final tail: 99-100% N-Frame score band inside raw MET bins
- Background model: SM shape corrected by fitted 50-95% sideband trend
- Uncertainty: previous 12.7% replication uncertainty plus sideband-fit residual scatter

## Replication Table

{candidate.to_markdown(index=False)}

## Combined Candidate Significance

{combined.to_markdown(index=False)}

## Interpretation

This is the most promising sharpened trace found in the full-shape scan. It is stronger than the broad 95-100% all-MET excess because it survives an extrapolated sideband-shape correction in the very final 99-100% tail.

However, it is still exploratory. The topology was identified after scanning, and one independent Run2016H sample is weak even though the larger Run2016H expanded sample is strong. The right next step is to freeze this exact Q99 1-2 jet region and test it in a genuinely new era/sample, preferably Run2017/Run2018 MET open data or a newly downloaded disjoint Run2016H/G MET subset.
"""
    (REPORTS / "01_Q99_1TO2JET_FINAL_TAIL_CANDIDATE_REPLICATION_REPORT.md").write_text(report, encoding="utf-8")

    short = f"""# Short Update: Q99 1-2 Jet Candidate

The stricter full-shape analysis found one sharper candidate:

- MET stream
- 1-2 jets
- very final N-Frame tail, 99-100%
- sideband-shape corrected against the 50-95% score trend

Replication table:

{candidate.to_markdown(index=False)}

Combined exploratory candidate significance:

{combined.to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_Q99_1TO2JET_FINAL_TAIL_CANDIDATE.md").write_text(short, encoding="utf-8")

    print("Q99 1-2 JET FINAL-TAIL CANDIDATE REPLICATION COMPLETE")
    print(candidate.to_string(index=False))
    print(combined.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
