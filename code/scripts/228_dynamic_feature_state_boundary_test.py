from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MOD = SourceFileLoader("cross_sample", str(ROOT / "scripts" / "226_cross_sample_frozen_trace_validation.py")).load_module()

OUT = ROOT / "outputs_dynamic_feature_state_boundary_test"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def load_events() -> pd.DataFrame:
    frames = []
    for config in MOD.SAMPLES:
        path = Path(config["path"])
        if not path.exists():
            continue
        sample = MOD.load_sample(config)
        sample = MOD.add_missing_deciles(sample)
        sample["feature_state"] = np.where(
            sample["sample_validation_id"].isin(["Run2016G_reference", "Run2016H_fresh_mht"]),
            "mht_aware",
            "met_only_or_recomputed",
        )
        frames.append(sample)
    if not frames:
        raise RuntimeError("No input samples available.")
    return pd.concat(frames, ignore_index=True, sort=False)


def normalise(weights: dict[str, float]) -> dict[str, float]:
    total = sum(abs(v) for v in weights.values())
    if total <= 0:
        return weights
    return {k: v / total for k, v in weights.items()}


def candidate_grid() -> pd.DataFrame:
    rows = []
    fixed = [
        ("clean_op", {"observer_projection": 0.5, "physical_projection": 0.5, "ordinary_qcd_axis": 0.0}),
        (
            "scan_best_opq",
            {"observer_projection": 0.344828, "physical_projection": 0.517241, "ordinary_qcd_axis": -0.137931},
        ),
    ]
    for name, weights in fixed:
        row = {"candidate_id": name, **{c: 0.0 for c in MOD.COMPONENTS}}
        row.update(weights)
        rows.append(row)

    idx = 0
    # Keep this grid intentionally small: it is a feature-state test, not an
    # unconstrained parameter hunt.
    for observer, physical in [(0.65, 0.35), (0.55, 0.45), (0.50, 0.50), (0.45, 0.55), (0.35, 0.65)]:
        for qcd in [0.0, -0.10, -0.20, -0.35]:
                weights = normalise(
                    {
                        "observer_projection": float(observer),
                        "physical_projection": float(physical),
                        "ordinary_qcd_axis": float(qcd),
                    }
                )
                idx += 1
                row = {"candidate_id": f"grid_opq_{idx:04d}", **{c: 0.0 for c in MOD.COMPONENTS}}
                row.update(weights)
                rows.append(row)
    return pd.DataFrame(rows).drop_duplicates(subset=MOD.COMPONENTS).reset_index(drop=True)


def evaluate_all(events: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate in candidates.to_dict("records"):
        tagged = MOD.tag_microbands(events, MOD.score_candidate(events, candidate))
        counts = (
            tagged.groupby(["sample_validation_id", "run_era", "primary_dataset", "jet_bin", "microband"], observed=False)
            .size()
            .reset_index(name="observed")
        )
        for sample_id in sorted(events["sample_validation_id"].unique()):
            trace = MOD.vector(counts, sample_id, [MOD.TRACE_REGION])
            control = MOD.vector(counts, sample_id, MOD.CONTROL_REGIONS)
            metrics = MOD.shape_metrics(trace, control)
            sample = events[events["sample_validation_id"].eq(sample_id)]
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "sample_validation_id": sample_id,
                    "feature_state": str(sample["feature_state"].iloc[0]),
                    **{col: candidate[col] for col in MOD.COMPONENTS},
                    **metrics,
                    "shoulder_above_control": bool(
                        metrics.get("trace_95_99_over_90_95_density_ratio", -np.inf)
                        > metrics.get("control_95_99_over_90_95_density_ratio", np.inf)
                    ),
                }
            )
    return pd.DataFrame(rows)


def score_training(group: pd.DataFrame) -> pd.DataFrame:
    out = []
    for candidate_id, cand in group.groupby("candidate_id", observed=False):
        shoulder_pass = int(cand["shoulder_above_control"].sum())
        min_z = float(cand["shape_Z"].min())
        median_z = float(cand["shape_Z"].median())
        min_shoulder_delta = float(
            (
                cand["trace_95_99_over_90_95_density_ratio"]
                - cand["control_95_99_over_90_95_density_ratio"]
            ).min()
        )
        out.append(
            {
                "candidate_id": candidate_id,
                "training_samples": int(len(cand)),
                "training_shoulder_passes": shoulder_pass,
                "training_min_shape_Z": min_z,
                "training_median_shape_Z": median_z,
                "training_min_shoulder_delta": min_shoulder_delta,
                "training_score": shoulder_pass * 1000 + min(min_z, 20.0) + min_shoulder_delta,
            }
        )
    return pd.DataFrame(out).sort_values(
        ["training_shoulder_passes", "training_min_shape_Z", "training_min_shoulder_delta"],
        ascending=[False, False, False],
    )


def leave_one_out(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature_state, state_df in results.groupby("feature_state", observed=False):
        samples = sorted(state_df["sample_validation_id"].unique())
        for holdout in samples:
            train = state_df[~state_df["sample_validation_id"].eq(holdout)]
            test = state_df[state_df["sample_validation_id"].eq(holdout)]
            if train.empty or test.empty:
                continue
            ranked = score_training(train)
            chosen_id = str(ranked.iloc[0]["candidate_id"])
            chosen_train = ranked.iloc[0].to_dict()
            chosen_test = test[test["candidate_id"].eq(chosen_id)].iloc[0].to_dict()
            rows.append(
                {
                    "feature_state": feature_state,
                    "holdout_sample": holdout,
                    "chosen_candidate_id": chosen_id,
                    **{f"train_{k}": v for k, v in chosen_train.items() if k != "candidate_id"},
                    "holdout_shape_Z": chosen_test["shape_Z"],
                    "holdout_shoulder_Z": chosen_test["shoulder_Z"],
                    "holdout_trace_95_99_over_90_95_density_ratio": chosen_test[
                        "trace_95_99_over_90_95_density_ratio"
                    ],
                    "holdout_control_95_99_over_90_95_density_ratio": chosen_test[
                        "control_95_99_over_90_95_density_ratio"
                    ],
                    "holdout_shoulder_above_control": chosen_test["shoulder_above_control"],
                    **{col: chosen_test[col] for col in MOD.COMPONENTS},
                }
            )
    return pd.DataFrame(rows)


def state_winners(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature_state, state_df in results.groupby("feature_state", observed=False):
        ranked = score_training(state_df)
        best_id = str(ranked.iloc[0]["candidate_id"])
        best = state_df[state_df["candidate_id"].eq(best_id)].copy()
        row = ranked.iloc[0].to_dict()
        row["feature_state"] = feature_state
        for col in MOD.COMPONENTS:
            row[col] = float(best[col].iloc[0])
        rows.append(row)
    return pd.DataFrame(rows)


def write_report(results: pd.DataFrame, loo: pd.DataFrame, winners: pd.DataFrame) -> None:
    fixed = results[results["candidate_id"].isin(["clean_op", "scan_best_opq"])].copy()
    report = f"""# Dynamic Feature-State Boundary Test

## Purpose

This is the first explicit test of Darren's dynamical-boundary idea against the current blocker. Instead of assuming one static score works identically across all detector/feature states, the script separates samples into:

- `mht_aware`: samples with the richer MHT-aware boundary feature set.
- `met_only_or_recomputed`: samples where axes had to be recomputed from a reduced MET-only MiniAOD-style feature set.

The test then asks whether a feature-state-specific N-Frame boundary can be learned on one sample and predict the held-out sample inside the same feature state.

## Fixed Baseline Scores

{fixed[["candidate_id", "sample_validation_id", "feature_state", "shape_Z", "shoulder_Z", "trace_95_99_over_90_95_density_ratio", "control_95_99_over_90_95_density_ratio", "shoulder_above_control"]].to_markdown(index=False, floatfmt=".6g")}

## Feature-State Winners

{winners.to_markdown(index=False, floatfmt=".6g")}

## Leave-One-Sample-Out Dynamic Boundary Test

{loo.to_markdown(index=False, floatfmt=".6g")}

## Interpretation

This is not a discovery claim. It is a blocker-resolution test. A positive result would mean the boundary can be made feature-state dependent without simply tuning to the weak sample. A negative or mixed result means the next required step is not more weighting, but feature-equivalent extraction: all samples need the same MHT-aware variables before a universal or dynamical boundary claim is publishable.

For Darren's framing, the useful question is whether $\\Omega(t, s)$ depends on detector/feature state $s$. This script turns that into a concrete test by allowing the $[O, P, Q]$ projection to vary by feature state while preserving held-out validation.
"""
    (REPORTS / "01_DYNAMIC_FEATURE_STATE_BOUNDARY_TEST.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    events = load_events()
    candidates = candidate_grid()
    candidates.to_csv(TABLES / "00_dynamic_candidate_grid.csv", index=False)
    results = evaluate_all(events, candidates)
    loo = leave_one_out(results)
    winners = state_winners(results)
    results.to_csv(TABLES / "01_all_dynamic_candidate_sample_results.csv", index=False)
    winners.to_csv(TABLES / "02_feature_state_winners.csv", index=False)
    loo.to_csv(TABLES / "03_leave_one_sample_out_dynamic_test.csv", index=False)
    write_report(results, loo, winners)
    print(REPORTS / "01_DYNAMIC_FEATURE_STATE_BOUNDARY_TEST.md")
    print(loo.to_string(index=False))


if __name__ == "__main__":
    main()
