from __future__ import annotations

"""Three-sample approximate process-aware OPQ sideband likelihood.

This keeps the previous approximate SM model and changes only the real-data
validation vectors so Run2016G fresh remote data is included in the formal
readout.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
SM_OUT = ROOT / "outputs_remote_opq_sm_background_build"
ROBUST = ROOT / "outputs_opq_remote_three_sample_statistical_robustness"
OUT = ROOT / "outputs_remote_opq_approx_sm_sideband_likelihood_three_sample"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON = OUT / "json"

TIERS = SM_OUT / "tables" / "08_remote_sm_normalisation_tiers.csv"
SM_EVENTS = SM_OUT / "tables" / "07_remote_sm_opq_shape_scored_events.csv"
REAL_VECTORS = ROBUST / "tables" / "02_opq_three_sample_microband_vectors.csv"
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
                            {
                                "name": f"shape_{band}",
                                "type": "normsys",
                                "data": {"hi": 1 + rel_unc, "lo": max(1 - rel_unc, 1e-6)},
                            },
                            {"name": f"stat_{band}", "type": "staterror", "data": [float(max(np.sqrt(exp), 1.0))]},
                        ],
                    },
                ],
            }
        )
    model = pyhf.Model(
        {"channels": channels, "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}]},
        poi_name="mu_trace",
    )
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
                spec_name = f"{sample_id}_{region_name}_unc_{rel_unc:.2f}.json"
                (JSON / spec_name).write_text(json.dumps(model.spec, indent=2), encoding="utf-8")

    summary = pd.DataFrame(rows)
    channels = pd.DataFrame(channel_rows)
    combined_rows = []
    key = summary[summary["relative_independent_shape_uncertainty"].eq(0.10)].copy()
    for region, group in key.groupby("region", sort=False):
        stat, p = combine_pvalues(group["background_only_p"].to_numpy(float), method="fisher")
        combined_rows.append(
            {
                "region": region,
                "samples_combined": ";".join(group["sample_validation_id"].astype(str)),
                "sample_count": int(group["sample_validation_id"].nunique()),
                "fisher_statistic": float(stat),
                "fisher_p": float(p),
                "fisher_Z": p_to_z(float(p)),
                "min_sample_Z": float(group["background_only_Z"].min()),
                "max_sample_Z": float(group["background_only_Z"].max()),
                "controls_close_if_control_region": bool(region != "MET_trace" and group["background_only_Z"].abs().max() < 1.0),
            }
        )
    combined = pd.DataFrame(combined_rows)

    summary.to_csv(TABLES / "03_approx_sm_sideband_likelihood_summary.csv", index=False)
    channels.to_csv(TABLES / "04_approx_sm_sideband_likelihood_channels.csv", index=False)
    key.to_csv(TABLES / "05_key_10pct_likelihood_readout.csv", index=False)
    combined.to_csv(TABLES / "06_combined_10pct_likelihood_readout.csv", index=False)

    report = f"""# Three-Sample Approximate Process-Aware SM OPQ Sideband Likelihood

## Scope

This reruns the same approximate process-aware SM sideband likelihood after
adding the fresh Run2016G remote validation sample. The OPQ score was unchanged:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

The likelihood remains approximate because exact full-record
sum-of-generator-weights were not available from the CERN record JSON. It uses
records in the `approx_constant_weight_sumw` tier and keeps independent
microband shape uncertainties.

## Approximate SM Template

{template.to_markdown(index=False, floatfmt='.6g')}

## Key 10 Percent Shape-Uncertainty Readout

{key.to_markdown(index=False, floatfmt='.6g')}

## Combined 10 Percent Readout

{combined.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

The fresh Run2016G sample keeps the same MET-trace direction but is weaker than
Run2015D and Run2016H. At the combined level, MET remains discrepant while
JetHT/SingleMuon controls close under the same approximate sideband transfer.

This is stronger multisample support for the N-Frame boundary-trace pattern,
but it is still not official CMS discovery-grade because exact MC sum-weights
and a full CMS systematic model are not closed.
"""
    (REPORTS / "01_THREE_SAMPLE_APPROX_REMOTE_OPQ_SM_SIDEBAND_LIKELIHOOD.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(combined.to_string(index=False))
    print(REPORTS / "01_THREE_SAMPLE_APPROX_REMOTE_OPQ_SM_SIDEBAND_LIKELIHOOD.md")


if __name__ == "__main__":
    main()
