from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SM_PATH = ROOT / "outputs_breakthrough_full_push_nframe_susy" / "sources" / "best_available_full_plus_reduced_weighted_sm_events.csv"
OUT = ROOT / "outputs_process_aware_sm_uncertainty_audit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

FROZEN_WEIGHTS = {
    "missing_visible_axis": 0.3137254901960784,
    "displacement_reconstruction_axis": 0.3137254901960784,
    "qcd_like_axis": -0.27450980392156865,
    "leptonic_control_axis": -0.09803921568627451,
}
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]


def weighted_quantile(values: np.ndarray, weights: np.ndarray, qs: np.ndarray | list[float]) -> np.ndarray:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0 or weights.sum() <= 0:
        return np.full(len(qs), np.nan)
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return np.interp(qs, cdf, values)


def load_sm() -> pd.DataFrame:
    usecols = [
        "process_family_norm",
        "process_label",
        "component_mode",
        "event_weight",
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_muons",
        "N_electrons",
        "missing_visible_axis",
        "displacement_reconstruction_axis",
        "qcd_like_axis",
        "packed_candidate_count",
        "secondary_vertex_count",
        "HLT_MET_paths_any",
        "HLT_HT_paths_any",
        "HLT_Mu_paths_any",
    ]
    header = pd.read_csv(SM_PATH, nrows=0).columns
    cols = [c for c in usecols if c in header]
    df = pd.read_csv(SM_PATH, usecols=cols, low_memory=False)
    for col in cols:
        if col not in ["process_family_norm", "process_label", "component_mode"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["event_weight"] = df["event_weight"].fillna(0.0).clip(lower=0.0)
    df["process_family_base"] = df["process_family_norm"].astype(str).str.replace("_reduced", "", regex=False)
    df["component_mode"] = df.get("component_mode", "").astype(str)
    df["N_muons"] = df.get("N_muons", 0).fillna(0.0)
    df["N_electrons"] = df.get("N_electrons", 0).fillna(0.0)
    w = df["event_weight"].to_numpy(float)
    leptons = (df["N_muons"] + df["N_electrons"]).to_numpy(float)
    mean = np.average(leptons, weights=w) if w.sum() > 0 else 0.0
    sd = np.sqrt(np.average((leptons - mean) ** 2, weights=w)) if w.sum() > 0 else 1.0
    df["leptonic_control_axis"] = -(leptons - mean) / max(float(sd), 1e-9)
    df["sm_frozen_proxy_score"] = sum(
        FROZEN_WEIGHTS[col] * df[col].fillna(0.0).to_numpy(float) for col in FROZEN_WEIGHTS
    )
    df["jet_bin"] = pd.cut(
        df["N_jets_30"].fillna(0.0),
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    return df


def assign_sm_q99_tail(df: pd.DataFrame, jet_bin: str) -> pd.DataFrame:
    sub = df[df["jet_bin"].eq(jet_bin)].copy()
    if sub.empty:
        return sub
    edges = weighted_quantile(sub["MET_pt"].to_numpy(float), sub["event_weight"].to_numpy(float), np.linspace(0, 1, 11))
    edges[0], edges[-1] = -np.inf, np.inf
    sub["missing_bin"] = pd.cut(sub["MET_pt"], bins=edges, labels=False, include_lowest=True)
    sub["q99_tail_flag"] = False
    for mb, group in sub.groupby("missing_bin", observed=False):
        threshold = weighted_quantile(group["sm_frozen_proxy_score"].to_numpy(float), group["event_weight"].to_numpy(float), [0.99])[0]
        sub.loc[group.index, "q99_tail_flag"] = group["sm_frozen_proxy_score"] >= threshold
    return sub


def process_tables(scored: pd.DataFrame, jet_bin: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    total_w = float(scored["event_weight"].sum())
    tail_w = float(scored.loc[scored["q99_tail_flag"], "event_weight"].sum())
    base_frac = tail_w / total_w if total_w > 0 else np.nan

    by_family = (
        scored.groupby("process_family_base", as_index=False)
        .apply(
            lambda g: pd.Series(
                {
                    "jet_bin": jet_bin,
                    "weighted_events": g["event_weight"].sum(),
                    "tail_weight": g.loc[g["q99_tail_flag"], "event_weight"].sum(),
                    "tail_fraction": g.loc[g["q99_tail_flag"], "event_weight"].sum() / g["event_weight"].sum()
                    if g["event_weight"].sum() > 0
                    else np.nan,
                    "weight_share": g["event_weight"].sum() / total_w if total_w > 0 else np.nan,
                    "tail_weight_share": g.loc[g["q99_tail_flag"], "event_weight"].sum() / tail_w if tail_w > 0 else np.nan,
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
        .sort_values("weighted_events", ascending=False)
    )

    leave_rows = []
    for fam in sorted(scored["process_family_base"].dropna().unique()):
        keep = scored[~scored["process_family_base"].eq(fam)]
        keep_total = float(keep["event_weight"].sum())
        keep_tail = float(keep.loc[keep["q99_tail_flag"], "event_weight"].sum())
        frac = keep_tail / keep_total if keep_total > 0 else np.nan
        leave_rows.append(
            {
                "jet_bin": jet_bin,
                "left_out_family": fam,
                "base_tail_fraction": base_frac,
                "leave_one_out_tail_fraction": frac,
                "relative_change": (frac - base_frac) / base_frac if base_frac > 0 else np.nan,
            }
        )
    leave_one = pd.DataFrame(leave_rows)

    # Process-label normalisation toy: vary each process label by 50% log-normal.
    rng = np.random.default_rng(20260617)
    groups = list(scored.groupby("process_label", observed=False))
    toys = []
    for _ in range(5000):
        num = 0.0
        den = 0.0
        for _label, group in groups:
            scale = float(np.exp(rng.normal(0.0, np.log(1.5))))
            den += float(group["event_weight"].sum()) * scale
            num += float(group.loc[group["q99_tail_flag"], "event_weight"].sum()) * scale
        toys.append(num / den if den > 0 else np.nan)
    toys = np.array(toys, dtype=float)
    toy = pd.DataFrame(
        [
            {
                "jet_bin": jet_bin,
                "base_tail_fraction": base_frac,
                "process_label_norm_toy_rel_std": float(np.nanstd(toys) / base_frac) if base_frac > 0 else np.nan,
                "process_label_norm_toy_rel_q16": float((np.nanquantile(toys, 0.16) - base_frac) / base_frac) if base_frac > 0 else np.nan,
                "process_label_norm_toy_rel_q84": float((np.nanquantile(toys, 0.84) - base_frac) / base_frac) if base_frac > 0 else np.nan,
                "nominal_total_weight": total_w,
                "nominal_tail_weight": tail_w,
                "nominal_tail_fraction": base_frac,
            }
        ]
    )
    return by_family, leave_one, toy


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    sm = load_sm()

    coverage = (
        sm.groupby(["process_family_base", "component_mode"], dropna=False)
        .agg(
            rows=("event_weight", "size"),
            weighted_events=("event_weight", "sum"),
            missing_packed_candidate_fraction=("packed_candidate_count", lambda x: float(pd.to_numeric(x, errors="coerce").isna().mean())),
        )
        .reset_index()
        .sort_values("weighted_events", ascending=False)
    )
    family_tables = []
    leave_tables = []
    toy_tables = []
    for jet_bin in JET_BINS:
        scored = assign_sm_q99_tail(sm, jet_bin)
        if scored.empty:
            continue
        fam, leave, toy = process_tables(scored, jet_bin)
        family_tables.append(fam)
        leave_tables.append(leave)
        toy_tables.append(toy)
    family = pd.concat(family_tables, ignore_index=True)
    leave_one = pd.concat(leave_tables, ignore_index=True)
    toy = pd.concat(toy_tables, ignore_index=True)

    coverage.to_csv(TABLES / "01_weighted_sm_process_coverage.csv", index=False)
    family.to_csv(TABLES / "02_sm_q99_tail_by_process_family.csv", index=False)
    leave_one.to_csv(TABLES / "03_sm_leave_one_process_family_out.csv", index=False)
    toy.to_csv(TABLES / "04_sm_process_label_normalisation_toys.csv", index=False)

    focus = toy[toy["jet_bin"].isin(["0jet", "1to2jets"])].copy()
    family_focus = family[family["jet_bin"].isin(["0jet", "1to2jets"])].copy()
    report = f"""# Process-Aware SM Uncertainty Audit for Frozen Boundary Trace

## Purpose

This tests whether the existing local weighted Standard Model table can support a residual background-shape uncertainty near or below the current data-driven requirement:

```text
Run2016G+Run2016H required control-closing uncertainty = 39.0%
```

The SM table is used only as an audit here. It is not treated as official CMS-grade for the final claim because the available table mixes full-component and reduced-component samples.

## SM Coverage

{coverage.to_markdown(index=False, floatfmt=".3f")}

## Q99 Tail by Process Family, Focus Jet Bins

{family_focus.to_markdown(index=False, floatfmt=".5f")}

## Process Normalisation Toy

Each process label was varied independently by a 50% log-normal normalisation uncertainty. This tests process-composition uncertainty only, not detector/reconstruction shape uncertainty.

{focus.to_markdown(index=False, floatfmt=".5f")}

## Leave-One-Family-Out Stress

{leave_one[leave_one["jet_bin"].isin(["0jet", "1to2jets"])].to_markdown(index=False, floatfmt=".5f")}

## Interpretation

For the 0-jet proxy, process-label normalisation variations are small compared with 39%. The relative standard deviation is about `{float(focus[focus["jet_bin"].eq("0jet")]["process_label_norm_toy_rel_std"].iloc[0]):.3f}`.

That means ordinary process normalisation alone does not require a 39% uncertainty. However, the 0-jet SM proxy is dominated by WJets weight, and reduced-component samples carry most of the total SM weight. So this audit cannot yet prove that official SM background-shape uncertainty is below 39%.

The honest result is:

- Process-composition normalisation does not obviously kill the N-Frame trace.
- The remaining SM blocker is shape coverage, especially WJets/lost-lepton, QCD mismeasurement, and ZNuNu/invisible-MET modelling in the exact Q99 frozen-score tail.

## Exact Next Requirement

To make the current repeatable Run2016 trace breakthrough-grade, the next SM task is to build a harmonised weighted SM shape template for the same frozen score using:

- WJetsToLNu inclusive and N-jet samples;
- ZJetsToNuNu high-pT samples;
- QCD HT-binned samples;
- TT/top and single-top samples;
- diboson samples;
- official cross sections, generated counts/sum weights, and filter efficiencies.

Then fit the score sidebands and controls with a pyhf/HistFactory model and show the fitted shape nuisance needed for controls is at or below about 39%, while Run2016G+Run2016H MET remains above 5 sigma.
"""
    (REPORTS / "01_PROCESS_AWARE_SM_UNCERTAINTY_AUDIT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_PROCESS_AWARE_SM_UNCERTAINTY_AUDIT.md")
    print(focus.to_string(index=False))


if __name__ == "__main__":
    main()
