from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
INFILE = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz"
OUT = ROOT / "outputs_run2016g_sideband_profile_control_model"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SCORE_COL = "frozen_boundary_score"
BANDS = [
    ("q050_080", 0.50, 0.80, 0.65),
    ("q080_090", 0.80, 0.90, 0.85),
    ("q090_095", 0.90, 0.95, 0.925),
    ("q095_099", 0.95, 0.99, 0.970),
    ("q099_100", 0.99, 1.00, 0.995),
]
FIT_BANDS = ["q050_080", "q080_090", "q090_095", "q095_099"]
SIGNAL_BAND = "q099_100"
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]
REL_UNC_FLOOR = 0.30


def finite_z(obs: float, exp: float, rel_unc: float) -> float:
    if exp <= 0:
        return np.nan
    return float((obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2))


def add_missing_bins_and_score_bands(df: pd.DataFrame) -> pd.DataFrame:
    tagged = []
    band_table = pd.DataFrame(BANDS, columns=["score_band", "q_low", "q_high", "q_mid"])
    for (era, dataset), group in df.groupby(["era", "primary_dataset"], sort=False):
        g = group.copy()
        missing_edges = np.unique(g["missing_proxy_pt"].quantile(np.linspace(0, 1, 11)).to_numpy(float))
        if len(missing_edges) < 3:
            missing_edges = np.array([-np.inf, np.inf])
        else:
            missing_edges[0], missing_edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=missing_edges, labels=False, include_lowest=True)

        score_band = np.full(len(g), None, dtype=object)
        score = g[SCORE_COL].to_numpy(float)
        missing_values = g["missing_bin"].to_numpy()
        for mb in sorted(pd.Series(missing_values).dropna().unique()):
            mask = missing_values == mb
            values = score[mask]
            edges = np.quantile(values, [0.50, 0.80, 0.90, 0.95, 0.99, 1.00])
            edges[0], edges[-1] = -np.inf, np.inf
            for (name, _, _, _), lo, hi in zip(BANDS, edges[:-1], edges[1:]):
                score_band[mask & (score >= lo) & (score < hi)] = name
        g["score_band"] = score_band
        g = g[g["score_band"].notna()].copy()
        g = g.merge(band_table, on="score_band", how="left")
        tagged.append(g)
    return pd.concat(tagged, ignore_index=True)


def count_cells(tagged: pd.DataFrame) -> pd.DataFrame:
    rows = (
        tagged.groupby(["era", "primary_dataset", "jet_bin", "missing_bin", "score_band", "q_low", "q_high", "q_mid"], observed=False)
        .size()
        .reset_index(name="observed")
    )
    full = []
    for (era, dataset, jet, mb), _ in tagged.groupby(["era", "primary_dataset", "jet_bin", "missing_bin"], observed=False):
        for name, lo, hi, mid in BANDS:
            full.append(
                {
                    "era": era,
                    "primary_dataset": dataset,
                    "jet_bin": str(jet),
                    "missing_bin": int(mb),
                    "score_band": name,
                    "q_low": lo,
                    "q_high": hi,
                    "q_mid": mid,
                    "band_width": hi - lo,
                }
            )
    full_df = pd.DataFrame(full)
    out = full_df.merge(
        rows.drop(columns=["q_low", "q_high", "q_mid"]),
        on=["era", "primary_dataset", "jet_bin", "missing_bin", "score_band"],
        how="left",
    )
    out["observed"] = out["observed"].fillna(0).astype(float)
    return out


def poisson_nll(obs: np.ndarray, lam: np.ndarray) -> float:
    lam = np.clip(lam, 1e-9, np.inf)
    return float(np.sum(lam - obs * np.log(lam)))


def fit_exponential(cells: pd.DataFrame) -> tuple[float, float, float, int]:
    fit = cells[cells["score_band"].isin(FIT_BANDS)].copy()
    if fit.empty or fit["observed"].sum() <= 0:
        return np.nan, np.nan, np.nan, 0
    y = fit["observed"].to_numpy(float)
    width = fit["band_width"].to_numpy(float)
    x = fit["q_mid"].to_numpy(float) - 0.90
    start_rate = (y.sum() + 0.5) / (width.sum() + 0.5)
    start = np.array([np.log(max(start_rate, 1e-6)), 0.0])

    def objective(theta: np.ndarray) -> float:
        a, b = theta
        lam = width * np.exp(a + b * x)
        reg = 0.5 * (b / 20.0) ** 2
        return poisson_nll(y, lam) + reg

    res = minimize(objective, start, method="Nelder-Mead", options={"maxiter": 5000})
    a, b = res.x
    pred = width * np.exp(a + b * x)
    resid = np.log((y + 0.5) / (pred + 0.5))
    rms = float(np.sqrt(np.mean(resid**2)))
    return float(a), float(b), rms, int(len(fit))


def predict_exp_from_params(a: float, b: float, q_mid: float, width: float) -> float:
    if not np.isfinite(a) or not np.isfinite(b):
        return np.nan
    return float(width * np.exp(a + b * (q_mid - 0.90)))


def build_predictions(cell_counts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Model A: local exponential per dataset/jet/missing decile.
    for key, sub in cell_counts.groupby(["era", "primary_dataset", "jet_bin", "missing_bin"], observed=False, sort=False):
        a, b, rms, n = fit_exponential(sub)
        tail = sub[sub["score_band"].eq(SIGNAL_BAND)].iloc[0]
        rows.append(
            {
                "model": "local_exp_by_dataset_jet_missing",
                "era": key[0],
                "primary_dataset": key[1],
                "jet_bin": key[2],
                "missing_bin": key[3],
                "q99_observed": float(tail["observed"]),
                "q99_expected": predict_exp_from_params(a, b, float(tail["q_mid"]), float(tail["band_width"])),
                "sideband_log_rms": rms,
                "fit_bins": n,
            }
        )

    # Model B: pooled exponential per dataset/jet, preserving missing-bin totals only through observed sideband mix.
    for key, sub in cell_counts.groupby(["era", "primary_dataset", "jet_bin"], observed=False, sort=False):
        pooled = sub.groupby(["score_band", "q_low", "q_high", "q_mid", "band_width"], as_index=False)["observed"].sum()
        a, b, rms, n = fit_exponential(pooled)
        tail = pooled[pooled["score_band"].eq(SIGNAL_BAND)].iloc[0]
        rows.append(
            {
                "model": "pooled_exp_by_dataset_jet",
                "era": key[0],
                "primary_dataset": key[1],
                "jet_bin": key[2],
                "missing_bin": "ALL",
                "q99_observed": float(tail["observed"]),
                "q99_expected": predict_exp_from_params(a, b, float(tail["q_mid"]), float(tail["band_width"])),
                "sideband_log_rms": rms,
                "fit_bins": n,
            }
        )

    # Model C: conservative last-sideband transfer. Expected q99 = q95-99 count * width ratio.
    # This avoids extrapolating a steep fitted slope into the blinded tail.
    for key, sub in cell_counts.groupby(["era", "primary_dataset", "jet_bin"], observed=False, sort=False):
        pooled = sub.groupby(["score_band", "band_width"], as_index=False)["observed"].sum()
        last = pooled[pooled["score_band"].eq("q095_099")]
        tail = pooled[pooled["score_band"].eq(SIGNAL_BAND)]
        if last.empty or tail.empty:
            continue
        last_count = float(last["observed"].iloc[0])
        expected = last_count * (float(tail["band_width"].iloc[0]) / float(last["band_width"].iloc[0]))
        rows.append(
            {
                "model": "conservative_q95_99_width_transfer",
                "era": key[0],
                "primary_dataset": key[1],
                "jet_bin": key[2],
                "missing_bin": "ALL",
                "q99_observed": float(tail["observed"].iloc[0]),
                "q99_expected": expected,
                "sideband_log_rms": 0.0,
                "fit_bins": 1,
            }
        )
    pred = pd.DataFrame(rows)
    pred["relative_uncertainty_used"] = np.sqrt(REL_UNC_FLOOR**2 + pred["sideband_log_rms"].fillna(0.0) ** 2)
    pred["q99_Z"] = [
        finite_z(obs, exp, rel)
        for obs, exp, rel in zip(pred["q99_observed"], pred["q99_expected"], pred["relative_uncertainty_used"])
    ]
    pred["q99_obs_exp"] = pred["q99_observed"] / pred["q99_expected"].replace(0, np.nan)
    return pred


def aggregate_readout(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, g in pred.groupby("model", sort=False):
        agg = []
        for (dataset, jet), sub in g.groupby(["primary_dataset", "jet_bin"], observed=False, sort=False):
            obs = float(sub["q99_observed"].sum())
            exp = float(sub["q99_expected"].sum())
            # Use quadrature of the per-cell/model uncertainty, with a minimum 30%.
            variance = float(np.sum(sub["q99_expected"].fillna(0.0) + (sub["relative_uncertainty_used"].fillna(REL_UNC_FLOOR) * sub["q99_expected"].fillna(0.0)) ** 2))
            z = float((obs - exp) / np.sqrt(max(variance, 1e-12))) if exp > 0 else np.nan
            agg.append(
                {
                    "model": model,
                    "primary_dataset": dataset,
                    "jet_bin": jet,
                    "q99_observed": obs,
                    "q99_expected": exp,
                    "q99_Z": z,
                    "q99_obs_exp": obs / exp if exp > 0 else np.nan,
                }
            )
        agg_df = pd.DataFrame(agg)

        def val(dataset: str, jet: str) -> float:
            row = agg_df[(agg_df["primary_dataset"].eq(dataset)) & (agg_df["jet_bin"].eq(jet))]
            return float(row["q99_Z"].iloc[0]) if not row.empty else np.nan

        controls = agg_df[agg_df["primary_dataset"].isin(["JetHT", "SingleMuon"])]["q99_Z"].dropna().to_numpy(float)
        signals = np.array([x for x in [val("MET", "0jet"), val("HTMHT", "1to2jets")] if np.isfinite(x)])
        rows.append(
            {
                "model": model,
                "MET_0jet_Z": val("MET", "0jet"),
                "HTMHT_1to2jets_Z": val("HTMHT", "1to2jets"),
                "signal_stouffer_Z": float(signals.sum() / np.sqrt(len(signals))) if len(signals) else np.nan,
                "JetHT_1to2jets_Z": val("JetHT", "1to2jets"),
                "SingleMuon_0jet_Z": val("SingleMuon", "0jet"),
                "max_control_absZ": float(np.max(np.abs(controls))) if len(controls) else np.nan,
                "controls_close_under_3sigma": bool(len(controls) and np.max(np.abs(controls)) < 3.0),
                "trace_candidate_survives": bool(len(signals) and np.max(np.abs(controls)) < 3.0 and val("MET", "0jet") > 5.0),
            }
        )
    return pd.DataFrame(rows).sort_values(["controls_close_under_3sigma", "signal_stouffer_Z"], ascending=[False, False])


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not INFILE.exists():
        raise SystemExit(f"Missing scored events: {INFILE}")
    df = pd.read_csv(INFILE, low_memory=False)
    for col in ["missing_proxy_pt", SCORE_COL]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["missing_proxy_pt"].notna() & df[SCORE_COL].notna()].copy()
    df["jet_bin"] = df["jet_bin"].astype(str)

    tagged = add_missing_bins_and_score_bands(df)
    cells = count_cells(tagged)
    predictions = build_predictions(cells)
    readout = aggregate_readout(predictions)

    tagged[["era", "primary_dataset", "run", "lumi", "event", "jet_bin", "missing_bin", "score_band", SCORE_COL, "missing_proxy_pt"]].to_csv(
        TABLES / "00_run2016g_score_sideband_tagged_events_slim.csv.gz",
        index=False,
        compression="gzip",
    )
    cells.to_csv(TABLES / "01_run2016g_score_sideband_cell_counts.csv", index=False)
    predictions.to_csv(TABLES / "02_run2016g_sideband_model_cell_predictions.csv", index=False)
    readout.to_csv(TABLES / "03_run2016g_sideband_profile_readout.csv", index=False)

    best = readout.iloc[0].to_dict() if not readout.empty else {}
    report = f"""# Run2016G Frozen Score Sideband/Profile Control Model

## Purpose

This is the next control-closure step after the basic Q99 test. It keeps the frozen N-Frame score fixed and uses lower score sidebands to predict the blinded Q99 tail.

This is directly related to the Standard Model background problem: the sidebands are a data-driven proxy for the ordinary-background shape. If JetHT and SingleMuon controls close while MET remains high, the trace interpretation becomes stronger. If they do not close, the result is still background-model limited.

## Models Tried

1. `local_exp_by_dataset_jet_missing`: exponential sideband extrapolation separately for each dataset, jet bin, and missing decile.
2. `pooled_exp_by_dataset_jet`: exponential sideband extrapolation pooled over missing deciles for each dataset and jet bin.
3. `conservative_q95_99_width_transfer`: predicts Q99 from the immediately adjacent q95-q99 sideband using only quantile-width scaling.

All models use the fixed bands:

- 50-80%
- 80-90%
- 90-95%
- 95-99%
- 99-100% blinded test band

## Main Readout

{readout.to_markdown(index=False, floatfmt=".3f")}

## Best Available Readout

```text
{best}
```

## Interpretation

Controls are considered closed only if all JetHT and SingleMuon control jet bins are below 3 sigma in absolute value. A trace-candidate pass additionally requires MET 0jet above 5 sigma after controls close.

If no model passes both requirements, the correct conclusion is not that the trace is false. It is that this Run2016G result still needs a stronger background model, ideally combining this data-driven sideband fit with official weighted SM process samples.

## Outputs

- `01_run2016g_score_sideband_cell_counts.csv`
- `02_run2016g_sideband_model_cell_predictions.csv`
- `03_run2016g_sideband_profile_readout.csv`
"""
    (REPORTS / "01_RUN2016G_SIDEBAND_PROFILE_CONTROL_MODEL_REPORT.md").write_text(report, encoding="utf-8")
    print(REPORTS / "01_RUN2016G_SIDEBAND_PROFILE_CONTROL_MODEL_REPORT.md")
    print(readout.to_string(index=False))


if __name__ == "__main__":
    main()
