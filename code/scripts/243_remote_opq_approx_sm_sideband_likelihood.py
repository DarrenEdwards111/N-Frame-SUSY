from __future__ import annotations

"""Approximate process-aware OPQ sideband likelihood.

This is a stress test, not an official CMS inference. It uses only records in
the `approx_constant_weight_sumw` tier and excludes shape-only records.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
SM_OUT = ROOT / "outputs_remote_opq_sm_background_build"
ROBUST = ROOT / "outputs_opq_remote_holdout_statistical_robustness"
OUT = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

TIERS = SM_OUT / "tables" / "08_remote_sm_normalisation_tiers.csv"
SM_EVENTS = SM_OUT / "tables" / "07_remote_sm_opq_shape_scored_events.csv"
REAL_VECTORS = ROBUST / "tables" / "02_opq_heldout_microband_vectors.csv"
BANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
UPPER = ["q95_97", "q97_98", "q98_99", "q99_100"]
EDGES = [0.90, 0.95, 0.97, 0.98, 0.99, 1.0]
REL_SHAPE_UNCS = [0.10, 0.20, 0.30, 0.40, 0.50]


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, qs: list[float]) -> np.ndarray:
    order = np.argsort(values)
    x = values[order]
    w = weights[order]
    cdf = np.cumsum(w) / np.sum(w)
    return np.interp(qs, cdf, x)


def sm_template() -> tuple[pd.DataFrame, pd.DataFrame]:
    tiers = pd.read_csv(TIERS)
    usable = tiers[tiers["normalisation_tier"].eq("approx_constant_weight_sumw")].copy()
    events = pd.read_csv(SM_EVENTS, low_memory=False)
    events = events[events["record_id"].isin(usable["record_id"])].copy()
    scale = usable.set_index("record_id")["base_event_scale_for_generator_weight"].to_dict()
    events["approx_lumi_weight"] = events["generator_weight"] * events["record_id"].map(scale)
    events = events[np.isfinite(events["approx_lumi_weight"]) & (events["approx_lumi_weight"] > 0)].copy()
    edges = weighted_quantile(events["B_OPQ"].to_numpy(float), events["approx_lumi_weight"].to_numpy(float), EDGES)
    edges[-1] = np.inf
    labels = np.full(len(events), None, dtype=object)
    vals = events["B_OPQ"].to_numpy(float)
    for band, lo, hi in zip(BANDS, edges[:-1], edges[1:]):
        labels[(vals >= lo) & (vals < hi)] = band
    events["microband"] = labels
    band_weights = (
        events[events["microband"].notna()]
        .groupby("microband", as_index=False)["approx_lumi_weight"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "sm_weight", "count": "sm_events"})
    )
    rows = []
    total = float(events["approx_lumi_weight"].sum())
    for band in BANDS:
        hit = band_weights[band_weights["microband"].eq(band)]
        rows.append(
            {
                "microband": band,
                "sm_weight": float(hit["sm_weight"].iloc[0]) if not hit.empty else 0.0,
                "sm_events": int(hit["sm_events"].iloc[0]) if not hit.empty else 0,
                "sm_fraction_of_total": (float(hit["sm_weight"].iloc[0]) / total) if not hit.empty and total > 0 else 0.0,
            }
        )
    process = (
        events[events["microband"].notna()]
        .groupby(["process_family", "microband"], as_index=False)["approx_lumi_weight"]
        .sum()
        .rename(columns={"approx_lumi_weight": "sm_weight"})
    )
    return pd.DataFrame(rows), process


def build_model(observed: dict[str, float], expected: dict[str, float], rel_unc: float) -> tuple[pyhf.Model, list[float]]:
    channels = []
    observations = {}
    for band in UPPER:
        obs = float(observed[band])
        exp = max(float(expected[band]), 1e-9)
        observations[band] = obs
        channels.append(
            {
                "name": band,
                "samples": [
                    {
                        "name": "opq_excess",
                        "data": [exp],
                        "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}],
                    },
                    {
                        "name": "approx_sm_background",
                        "data": [exp],
                        "modifiers": [
                            {"name": f"shape_{band}", "type": "normsys", "data": {"hi": 1 + rel_unc, "lo": max(1 - rel_unc, 1e-6)}},
                            {"name": f"stat_{band}", "type": "staterror", "data": [float(max(np.sqrt(exp), 1.0))]},
                        ],
                    },
                ],
            }
        )
    model = pyhf.Model({"channels": channels, "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}]}, poi_name="mu_trace")
    data = [observations[name] for name in model.config.channels] + model.config.auxdata
    return model, data


def main() -> None:
    for path in [TABLES, REPORTS, JSON]:
        path.mkdir(parents=True, exist_ok=True)
    template, process = sm_template()
    template.to_csv(TABLES / "01_approx_sm_opq_microband_template.csv", index=False)
    process.to_csv(TABLES / "02_approx_sm_opq_microband_by_process.csv", index=False)
    real = pd.read_csv(REAL_VECTORS)
    base = template.set_index("microband")["sm_weight"].to_dict()
    q90 = max(base["q90_95"], 1e-9)
    template_ratio = {band: base[band] / q90 for band in BANDS}

    rows = []
    channel_rows = []
    for sample_id, group in real.groupby("sample_validation_id", sort=False):
        for region_name, count_col in [("MET_trace", "trace_count"), ("JetHT_SingleMuon_controls", "control_count")]:
            observed = {row.microband: float(getattr(row, count_col)) for row in group.itertuples(index=False)}
            anchor = observed["q90_95"]
            expected = {band: anchor * template_ratio[band] for band in BANDS}
            for rel_unc in REL_SHAPE_UNCS:
                model, data = build_model(observed, expected, rel_unc)
                p = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
                fit = pyhf.infer.mle.fit(data, model)
                params = {name: float(fit[i]) for i, name in enumerate(model.config.par_order)}
                rows.append(
                    {
                        "sample_validation_id": sample_id,
                        "region": region_name,
                        "relative_independent_shape_uncertainty": rel_unc,
                        "sideband_anchor_q90_95": anchor,
                        "upper_observed_total": sum(observed[b] for b in UPPER),
                        "upper_expected_total": sum(expected[b] for b in UPPER),
                        "obs_over_exp_upper": sum(observed[b] for b in UPPER) / max(sum(expected[b] for b in UPPER), 1e-9),
                        "background_only_p": p,
                        "background_only_Z": p_to_z(p),
                        "fit_mu_excess": params.get("mu_trace", np.nan),
                        "normalisation_scope": "approx_constant_weight_records_only",
                    }
                )
                for band in UPPER:
                    channel_rows.append(
                        {
                            "sample_validation_id": sample_id,
                            "region": region_name,
                            "relative_independent_shape_uncertainty": rel_unc,
                            "microband": band,
                            "observed": observed[band],
                            "expected_from_approx_sm_sideband": expected[band],
                            "obs_over_exp": observed[band] / max(expected[band], 1e-9),
                        }
                    )
                (JSON / f"{sample_id}_{region_name}_unc_{rel_unc:.2f}.json").write_text(json.dumps(model.spec, indent=2), encoding="utf-8")

    summary = pd.DataFrame(rows)
    channels = pd.DataFrame(channel_rows)
    summary.to_csv(TABLES / "03_approx_sm_sideband_likelihood_summary.csv", index=False)
    channels.to_csv(TABLES / "04_approx_sm_sideband_likelihood_channels.csv", index=False)

    report = f"""# Approximate Process-Aware SM OPQ Sideband Likelihood

## Scope

This is a stress test using only MC records in the
`approx_constant_weight_sumw` tier. ZNuNu records are not used for approximate
yield inference because the selected generator weights are too sparse/variable.

The likelihood is sideband-normalised: q90-95 in the real data anchors the
background normalisation, and the approximate SM template predicts q95-100.
MET trace and JetHT/SingleMuon controls are tested separately.

## Approximate SM Template

{template.to_markdown(index=False, floatfmt='.6g')}

## Summary

{summary.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

This is stronger than a pure data-vs-data shape comparison because the upper
tail is predicted from a process-aware SM template. It is still not official
CMS-grade: exact record-level sum-of-generator-weights and full process
coverage are missing, and ZNuNu is excluded from approximate yield use.

The useful readout is whether the MET trace remains more discrepant than the
controls after the same approximate SM sideband transfer. If controls are also
large, the model is still not specific enough; if controls close and MET stays
high, that is movement toward Darren's boundary-trace claim.
"""
    (REPORTS / "05_APPROX_REMOTE_OPQ_SM_SIDEBAND_LIKELIHOOD.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(REPORTS / "05_APPROX_REMOTE_OPQ_SM_SIDEBAND_LIKELIHOOD.md")


if __name__ == "__main__":
    main()
