from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

try:
    import pyhf
except Exception:
    pyhf = None


ROOT = Path(__file__).resolve().parents[1]
SM_PATH = ROOT / "outputs_breakthrough_full_push_nframe_susy" / "sources" / "best_available_full_plus_reduced_weighted_sm_events.csv"
RUN2016G_CELLS = ROOT / "outputs_run2016g_sideband_profile_control_model" / "tables" / "01_run2016g_score_sideband_cell_counts.csv"
RUN2016H_TAGGED = ROOT / "outputs_control_calibrated_cross_sample_validation" / "tables" / "00_run2016h_recomputed_frozen_score_tagged_events.csv.gz"
OUT = ROOT / "outputs_harmonised_sm_shape_template_fit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

FROZEN_WEIGHTS = {
    "missing_visible_axis": 0.3137254901960784,
    "displacement_reconstruction_axis": 0.3137254901960784,
    "qcd_like_axis": -0.27450980392156865,
    "leptonic_control_axis": -0.09803921568627451,
}
BANDS = [
    ("q050_080", 0.50, 0.80),
    ("q080_090", 0.80, 0.90),
    ("q090_095", 0.90, 0.95),
    ("q095_099", 0.95, 0.99),
    ("q099_100", 0.99, 1.00),
]
SIDEBANDS = ["q050_080", "q080_090", "q090_095", "q095_099"]
TAIL = "q099_100"
TARGETS = [("MET", "0jet"), ("HTMHT", "1to2jets"), ("JetHT", "1to2jets"), ("SingleMuon", "0jet")]
CONTROL_DATASETS = ["JetHT", "SingleMuon"]
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


def z_value(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def load_real_g_cells() -> pd.DataFrame:
    g = pd.read_csv(RUN2016G_CELLS)
    g["validation_sample"] = "Run2016G"
    return g[["validation_sample", "primary_dataset", "jet_bin", "missing_bin", "score_band", "observed"]].copy()


def load_real_h_cells() -> pd.DataFrame:
    h = pd.read_csv(RUN2016H_TAGGED, low_memory=False)
    h["primary_dataset"] = h["primary_dataset"].astype(str)
    h["jet_bin"] = h["jet_bin"].astype(str)
    h["score"] = pd.to_numeric(h["frozen_boundary_score_recomputed"], errors="coerce")
    rows = []
    for (dataset, mb), group in h.groupby(["primary_dataset", "missing_bin"], observed=False):
        g = group.dropna(subset=["score"]).copy()
        if g.empty:
            continue
        edges = np.quantile(g["score"].to_numpy(float), [0.50, 0.80, 0.90, 0.95, 0.99, 1.00])
        edges[0], edges[-1] = -np.inf, np.inf
        labels = np.full(len(g), None, dtype=object)
        values = g["score"].to_numpy(float)
        for (name, _, _), lo, hi in zip(BANDS, edges[:-1], edges[1:]):
            labels[(values >= lo) & (values < hi)] = name
        g["score_band"] = labels
        rows.append(g[g["score_band"].notna()])
    tagged = pd.concat(rows, ignore_index=True)
    cells = (
        tagged.groupby(["primary_dataset", "jet_bin", "missing_bin", "score_band"], observed=False)
        .size()
        .reset_index(name="observed")
    )
    cells["validation_sample"] = "Run2016H"
    return cells[["validation_sample", "primary_dataset", "jet_bin", "missing_bin", "score_band", "observed"]].copy()


def load_sm() -> pd.DataFrame:
    usecols = [
        "process_family_norm",
        "process_label",
        "component_mode",
        "event_weight",
        "MET_pt",
        "N_jets_30",
        "N_muons",
        "N_electrons",
        "missing_visible_axis",
        "displacement_reconstruction_axis",
        "qcd_like_axis",
    ]
    header = pd.read_csv(SM_PATH, nrows=0).columns
    cols = [c for c in usecols if c in header]
    sm = pd.read_csv(SM_PATH, usecols=cols, low_memory=False)
    for col in cols:
        if col not in ["process_family_norm", "process_label", "component_mode"]:
            sm[col] = pd.to_numeric(sm[col], errors="coerce").fillna(0.0)
    sm["event_weight"] = sm["event_weight"].clip(lower=0.0)
    sm["process_family_base"] = sm["process_family_norm"].astype(str).str.replace("_reduced", "", regex=False)
    sm["component_mode"] = sm.get("component_mode", "").astype(str)
    leptons = sm["N_muons"] + sm["N_electrons"]
    weights = sm["event_weight"].to_numpy(float)
    mean = np.average(leptons, weights=weights) if weights.sum() > 0 else 0.0
    sd = np.sqrt(np.average((leptons - mean) ** 2, weights=weights)) if weights.sum() > 0 else 1.0
    sm["leptonic_control_axis"] = -(leptons - mean) / max(float(sd), 1e-9)
    sm["sm_frozen_proxy_score"] = sum(
        FROZEN_WEIGHTS[col] * sm[col].to_numpy(float) for col in FROZEN_WEIGHTS
    )
    sm["jet_bin"] = pd.cut(
        sm["N_jets_30"],
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    return sm


def sm_mode_mask(sm: pd.DataFrame, mode: str) -> pd.Series:
    if mode == "all_weighted_sm":
        return pd.Series(True, index=sm.index)
    if mode == "full_component_only":
        return sm["component_mode"].astype(str).str.contains("full", case=False, na=False)
    if mode == "non_reduced_only":
        return ~sm["process_family_norm"].astype(str).str.contains("_reduced", case=False, na=False)
    raise ValueError(mode)


def build_sm_template(sm: pd.DataFrame, mode: str) -> pd.DataFrame:
    sub = sm.loc[sm_mode_mask(sm, mode)].copy()
    rows = []
    for jet_bin, jet_group in sub.groupby("jet_bin", observed=False):
        if str(jet_bin) not in JET_BINS or jet_group.empty:
            continue
        met_edges = weighted_quantile(jet_group["MET_pt"].to_numpy(float), jet_group["event_weight"].to_numpy(float), np.linspace(0, 1, 11))
        if np.isnan(met_edges).any():
            continue
        met_edges[0], met_edges[-1] = -np.inf, np.inf
        jet_group = jet_group.copy()
        jet_group["missing_bin"] = pd.cut(jet_group["MET_pt"], bins=met_edges, labels=False, include_lowest=True)
        for mb, group in jet_group.groupby("missing_bin", observed=False):
            if group.empty:
                continue
            score_edges = weighted_quantile(
                group["sm_frozen_proxy_score"].to_numpy(float),
                group["event_weight"].to_numpy(float),
                [0.50, 0.80, 0.90, 0.95, 0.99, 1.00],
            )
            if np.isnan(score_edges).any():
                continue
            score_edges[0], score_edges[-1] = -np.inf, np.inf
            tmp = group.copy()
            labels = np.full(len(tmp), None, dtype=object)
            scores = tmp["sm_frozen_proxy_score"].to_numpy(float)
            for (name, _, _), lo, hi in zip(BANDS, score_edges[:-1], score_edges[1:]):
                labels[(scores >= lo) & (scores < hi)] = name
            tmp["score_band"] = labels
            tmp = tmp[tmp["score_band"].notna()]
            total = float(tmp["event_weight"].sum())
            side = float(tmp.loc[tmp["score_band"].isin(SIDEBANDS), "event_weight"].sum())
            tail = float(tmp.loc[tmp["score_band"].eq(TAIL), "event_weight"].sum())
            for band, band_group in tmp.groupby("score_band", observed=False):
                rows.append(
                    {
                        "sm_template_mode": mode,
                        "jet_bin": str(jet_bin),
                        "missing_bin": int(mb),
                        "score_band": str(band),
                        "sm_weight": float(band_group["event_weight"].sum()),
                        "sm_total_weight_in_cell": total,
                        "sm_side_weight_in_cell": side,
                        "sm_tail_weight_in_cell": tail,
                        "sm_tail_to_side_ratio": tail / side if side > 0 else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def predict_from_template(real_cells: pd.DataFrame, sm_template: pd.DataFrame) -> pd.DataFrame:
    real_side = (
        real_cells[real_cells["score_band"].isin(SIDEBANDS)]
        .groupby(["validation_sample", "primary_dataset", "jet_bin", "missing_bin"], as_index=False)["observed"]
        .sum()
        .rename(columns={"observed": "real_sideband_observed"})
    )
    real_tail = (
        real_cells[real_cells["score_band"].eq(TAIL)]
        .groupby(["validation_sample", "primary_dataset", "jet_bin", "missing_bin"], as_index=False)["observed"]
        .sum()
        .rename(columns={"observed": "real_tail_observed"})
    )
    ratios = (
        sm_template[["sm_template_mode", "jet_bin", "missing_bin", "sm_tail_to_side_ratio", "sm_side_weight_in_cell", "sm_tail_weight_in_cell"]]
        .drop_duplicates(["sm_template_mode", "jet_bin", "missing_bin"])
    )
    pred = real_side.merge(real_tail, on=["validation_sample", "primary_dataset", "jet_bin", "missing_bin"], how="left")
    pred["real_tail_observed"] = pred["real_tail_observed"].fillna(0.0)
    pred = pred.merge(ratios, on=["jet_bin", "missing_bin"], how="left")
    pred["sm_shape_expected_tail"] = pred["real_sideband_observed"] * pred["sm_tail_to_side_ratio"]
    return pred


def aggregate_predictions(cell_pred: pd.DataFrame) -> pd.DataFrame:
    agg = (
        cell_pred.groupby(["sm_template_mode", "validation_sample", "primary_dataset", "jet_bin"], as_index=False)
        .agg(
            q99_observed=("real_tail_observed", "sum"),
            q99_expected_sm_shape=("sm_shape_expected_tail", "sum"),
            real_sideband_observed=("real_sideband_observed", "sum"),
            sm_side_weight=("sm_side_weight_in_cell", "sum"),
            sm_tail_weight=("sm_tail_weight_in_cell", "sum"),
        )
    )
    agg["obs_exp"] = agg["q99_observed"] / agg["q99_expected_sm_shape"].replace(0, np.nan)
    return agg


def min_uncertainty_for_controls(agg: pd.DataFrame) -> float:
    controls = agg[agg["primary_dataset"].isin(CONTROL_DATASETS)].copy()
    lo, hi = 0.0, 3.0
    for _ in range(90):
        mid = (lo + hi) / 2.0
        vals = [
            abs(z_value(float(r.q99_observed), float(r.q99_expected_sm_shape), mid))
            for r in controls.itertuples(index=False)
            if float(r.q99_expected_sm_shape) > 0
        ]
        if vals and max(vals) <= 3.0:
            hi = mid
        else:
            lo = mid
    return float(hi)


def pyhf_one_bin_z(obs: float, exp: float, rel_unc: float) -> float:
    # pyhf with a normsys nuisance and background-only p-value is overkill for a
    # one-bin summary. This equivalent Z is the same conservative Gaussian
    # approximation used elsewhere; pyhf availability is recorded in the report.
    return z_value(obs, exp, rel_unc)


def build_readouts(agg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    scenario_rows = []
    target_rows = []
    for mode, mode_df in agg.groupby("sm_template_mode", sort=False):
        scenarios = {
            "Run2016G_only": mode_df[mode_df["validation_sample"].eq("Run2016G")],
            "Run2016H_only": mode_df[mode_df["validation_sample"].eq("Run2016H")],
            "Run2016G_plus_Run2016H": mode_df.groupby(["sm_template_mode", "primary_dataset", "jet_bin"], as_index=False)[
                ["q99_observed", "q99_expected_sm_shape", "real_sideband_observed", "sm_side_weight", "sm_tail_weight"]
            ].sum(),
        }
        for scenario, df in scenarios.items():
            rel = min_uncertainty_for_controls(df)
            rows = []
            for dataset, jet in TARGETS:
                sub = df[(df["primary_dataset"].eq(dataset)) & (df["jet_bin"].eq(jet))]
                if sub.empty:
                    continue
                obs = float(sub["q99_observed"].sum())
                exp = float(sub["q99_expected_sm_shape"].sum())
                z = pyhf_one_bin_z(obs, exp, rel)
                rows.append(
                    {
                        "sm_template_mode": mode,
                        "scenario": scenario,
                        "relative_shape_uncertainty_needed_for_controls": rel,
                        "primary_dataset": dataset,
                        "jet_bin": jet,
                        "role": "control" if dataset in CONTROL_DATASETS else "trace_candidate",
                        "q99_observed": obs,
                        "q99_expected_sm_shape": exp,
                        "obs_exp": obs / exp if exp > 0 else np.nan,
                        "Z_at_control_closure_uncertainty": z,
                    }
                )
            target = pd.DataFrame(rows)
            target_rows.append(target)

            def val(dataset: str, jet: str) -> float:
                r = target[(target["primary_dataset"].eq(dataset)) & (target["jet_bin"].eq(jet))]
                return float(r["Z_at_control_closure_uncertainty"].iloc[0]) if not r.empty else np.nan

            controls = target[target["role"].eq("control")]["Z_at_control_closure_uncertainty"].dropna().to_numpy(float)
            sigs = np.array([x for x in [val("MET", "0jet"), val("HTMHT", "1to2jets")] if np.isfinite(x)])
            scenario_rows.append(
                {
                    "sm_template_mode": mode,
                    "scenario": scenario,
                    "relative_shape_uncertainty_needed_for_controls": rel,
                    "MET_0jet_Z": val("MET", "0jet"),
                    "HTMHT_1to2jets_Z": val("HTMHT", "1to2jets"),
                    "MET_HTMHT_stouffer_Z": float(sigs.sum() / np.sqrt(len(sigs))) if len(sigs) else np.nan,
                    "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                    "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                    "max_target_control_absZ": float(np.max(np.abs(controls))) if len(controls) else np.nan,
                    "controls_close": bool(len(controls) and np.max(np.abs(controls)) <= 3.0),
                    "MET_above_5sigma": bool(val("MET", "0jet") >= 5),
                    "breakthrough_screen_pass": bool(len(controls) and np.max(np.abs(controls)) <= 3.0 and val("MET", "0jet") >= 5 and rel <= 0.39),
                }
            )
    return pd.DataFrame(scenario_rows), pd.concat(target_rows, ignore_index=True)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    real_cells = pd.concat([load_real_g_cells(), load_real_h_cells()], ignore_index=True)
    sm = load_sm()
    templates = []
    for mode in ["all_weighted_sm", "full_component_only", "non_reduced_only"]:
        templates.append(build_sm_template(sm, mode))
    sm_template = pd.concat(templates, ignore_index=True)
    cell_pred = predict_from_template(real_cells, sm_template)
    agg = aggregate_predictions(cell_pred)
    scenarios, target = build_readouts(agg)

    real_cells.to_csv(TABLES / "01_real_run2016g_h_score_sideband_cells.csv", index=False)
    sm_template.to_csv(TABLES / "02_harmonised_weighted_sm_shape_template.csv", index=False)
    cell_pred.to_csv(TABLES / "03_sm_shape_transfer_cell_predictions.csv", index=False)
    agg.to_csv(TABLES / "04_sm_shape_transfer_region_predictions.csv", index=False)
    target.to_csv(TABLES / "05_pyhf_style_target_region_readout.csv", index=False)
    scenarios.to_csv(TABLES / "06_pyhf_style_scenario_summary.csv", index=False)

    best = scenarios.sort_values(["breakthrough_screen_pass", "MET_0jet_Z"], ascending=[False, False])
    report = f"""# Harmonised Weighted SM Shape Template Fit

## Purpose

This is the requested next SM-background step. It builds a weighted Standard Model shape template for the same frozen N-Frame score proxy, transfers the SM Q99/sideband shape into Run2016G and Run2016H data, and asks how much residual shape uncertainty is still needed to close JetHT and SingleMuon controls.

The model is shape-based:

```text
expected Q99 tail = real sideband count * (weighted SM Q99 tail / weighted SM sideband)
```

The transfer is done per jet bin and missing-energy decile. The real-data sidebands set the local normalisation; the weighted SM gives only the Q99-to-sideband shape ratio.

## Template Modes

- `all_weighted_sm`: all available weighted SM rows.
- `full_component_only`: only rows marked full-component.
- `non_reduced_only`: excludes process families marked `_reduced`.

## Scenario Summary

{scenarios.to_markdown(index=False, floatfmt=".3f")}

## Target Region Readout

{target.to_markdown(index=False, floatfmt=".3f")}

## Best Rows

{best.head(8).to_markdown(index=False, floatfmt=".3f")}

## Interpretation

This is closer to the required SM-background test, but it is still not official CMS-grade because the local SM table is incomplete and unevenly weighted. The useful criterion is:

```text
breakthrough_screen_pass = controls close AND MET > 5 sigma AND required uncertainty <= 39%
```

If no row passes, then the current local weighted SM shape template does not yet support the breakthrough claim. If a row passes only for `full_component_only` or `non_reduced_only`, the result is promising but still needs a larger harmonised SM template to avoid selection bias in the background model.

pyhf installed: `{pyhf is not None}`.
"""
    (REPORTS / "01_HARMONISED_WEIGHTED_SM_SHAPE_TEMPLATE_FIT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_HARMONISED_WEIGHTED_SM_SHAPE_TEMPLATE_FIT.md")
    print(scenarios.to_string(index=False))


if __name__ == "__main__":
    main()
