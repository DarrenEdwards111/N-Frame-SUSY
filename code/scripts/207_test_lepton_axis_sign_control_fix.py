from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INFILE = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz"
OUT = ROOT / "outputs_run2016g_control_diagnostics"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

LEPTON_WEIGHT = -0.09803921568627451


def finite_z(observed: float, expected: float, rel_unc: float = 0.30) -> float:
    if expected <= 0:
        return np.nan
    return float((observed - expected) / np.sqrt(expected + (rel_unc * expected) ** 2))


def add_score_variants(df: pd.DataFrame) -> pd.DataFrame:
    g = df.copy()
    lepton_axis = pd.to_numeric(g["leptonic_control_axis"], errors="coerce").fillna(0.0)

    # The stored axis is -z(N_leptons). With the frozen negative weight, high-lepton
    # events are boosted. These variants test sign handling without refitting weights.
    g["score_frozen_original"] = pd.to_numeric(g["frozen_boundary_score"], errors="coerce")
    g["score_lepton_axis_removed"] = g["score_frozen_original"] - LEPTON_WEIGHT * lepton_axis
    g["score_lepton_axis_sign_corrected"] = g["score_frozen_original"] - (2.0 * LEPTON_WEIGHT * lepton_axis)
    return g


def assign_q99_by_missing_decile(df: pd.DataFrame, score_col: str) -> pd.DataFrame:
    tagged = []
    for (_, dataset), group in df.groupby(["era", "primary_dataset"], sort=False):
        g = group.copy()
        edges = np.unique(g["missing_proxy_pt"].quantile(np.linspace(0, 1, 11)).to_numpy(float))
        if len(edges) < 3:
            edges = np.array([-np.inf, np.inf])
        else:
            edges[0], edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=edges, labels=False, include_lowest=True)
        thresholds = g.groupby("missing_bin", observed=False)[score_col].quantile(0.99)
        g["q99_tail"] = g[score_col] >= g["missing_bin"].map(thresholds).astype(float)
        g["expected_tail_fraction"] = g.groupby("missing_bin", observed=False)["q99_tail"].transform("mean")
        g["score_variant"] = score_col
        tagged.append(g)
    return pd.concat(tagged, ignore_index=True)


def stage_table(tagged: pd.DataFrame, score_col: str) -> pd.DataFrame:
    rows = []
    for (era, dataset, jet), sub in tagged.groupby(["era", "primary_dataset", "jet_bin"], observed=False, sort=False):
        observed = int(sub["q99_tail"].sum())
        expected = float(sub["expected_tail_fraction"].sum())
        rows.append(
            {
                "score_variant": score_col,
                "era": era,
                "primary_dataset": dataset,
                "jet_bin": str(jet),
                "events": len(sub),
                "q99_observed": observed,
                "q99_expected": expected,
                "q99_obs_exp": observed / expected if expected > 0 else np.nan,
                "q99_Z_relunc30": finite_z(observed, expected),
            }
        )
    return pd.DataFrame(rows)


def compact_readout(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant, g in table.groupby("score_variant", sort=False):
        def val(dataset: str, jet: str) -> float:
            row = g[(g["primary_dataset"].eq(dataset)) & (g["jet_bin"].eq(jet))]
            return float(row["q99_Z_relunc30"].iloc[0]) if not row.empty else np.nan

        control_vals = []
        for dataset in ["JetHT", "SingleMuon"]:
            for jet in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
                x = val(dataset, jet)
                if np.isfinite(x):
                    control_vals.append(x)
        signal = np.array([x for x in [val("MET", "0jet"), val("HTMHT", "1to2jets")] if np.isfinite(x)])
        rows.append(
            {
                "score_variant": variant,
                "MET_0jet_Z": val("MET", "0jet"),
                "HTMHT_1to2jets_Z": val("HTMHT", "1to2jets"),
                "signal_stouffer_Z": float(signal.sum() / np.sqrt(len(signal))) if len(signal) else np.nan,
                "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                "max_control_absZ": float(np.max(np.abs(control_vals))) if control_vals else np.nan,
                "controls_close_under_3sigma": bool(control_vals and np.max(np.abs(control_vals)) < 3.0),
            }
        )
    return pd.DataFrame(rows).sort_values("max_control_absZ")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not INFILE.exists():
        raise SystemExit(f"Missing scored diagnostic table: {INFILE}")

    df = add_score_variants(pd.read_csv(INFILE, low_memory=False))
    score_cols = [
        "score_frozen_original",
        "score_lepton_axis_removed",
        "score_lepton_axis_sign_corrected",
    ]
    tables = []
    for score_col in score_cols:
        tagged = assign_q99_by_missing_decile(df, score_col)
        tables.append(stage_table(tagged, score_col))
    table = pd.concat(tables, ignore_index=True)
    readout = compact_readout(table)

    table.to_csv(TABLES / "05_lepton_axis_sign_variant_stage_table.csv", index=False)
    readout.to_csv(TABLES / "06_lepton_axis_sign_variant_readout.csv", index=False)

    report = f"""# Run2016G Lepton Axis Sign Diagnostic

## Purpose

This test checks a possible sign-convention problem in the frozen N-Frame score. The stored lepton axis is:

```text
leptonic_control_axis = -z(N_muons + N_electrons)
```

The frozen weight on that stored axis is negative:

```text
w_lepton = {LEPTON_WEIGHT}
```

That means high-lepton events receive a positive score contribution. This can excite the SingleMuon control sample. The variants below do not refit any N-Frame weights; they only test whether the intended lepton-control sign was implemented consistently.

## Score Variants

- `score_frozen_original`: original frozen score.
- `score_lepton_axis_removed`: removes the lepton-axis contribution.
- `score_lepton_axis_sign_corrected`: flips only the lepton-axis sign while keeping the same absolute weight.

## Main Readout

{readout.to_markdown(index=False, floatfmt=".3f")}

## Interpretation

If the sign-corrected variant keeps MET/HTMHT high while lowering SingleMuon, then the control issue is partly an implementation/sign convention problem rather than a physics effect. If JetHT remains high, a separate hadronic-control/background-shape issue still remains.
"""
    (REPORTS / "02_LEPTON_AXIS_SIGN_DIAGNOSTIC_REPORT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "02_LEPTON_AXIS_SIGN_DIAGNOSTIC_REPORT.md")
    print(readout.to_string(index=False))


if __name__ == "__main__":
    main()
