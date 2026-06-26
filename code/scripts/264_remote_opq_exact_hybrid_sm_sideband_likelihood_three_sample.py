from __future__ import annotations

"""Three-sample OPQ likelihood using exact/hybrid SM normalisation tiers."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
SM_OUT = ROOT / "outputs_remote_opq_sm_background_build"
ROBUST = ROOT / "outputs_opq_remote_three_sample_statistical_robustness"
OUT = ROOT / "outputs_remote_opq_exact_hybrid_sm_sideband_likelihood_three_sample"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON_DIR = OUT / "json"

TIERS = SM_OUT / "tables" / "17_exact_hybrid_sm_normalisation_tiers.csv"
SM_EVENTS = SM_OUT / "tables" / "07_remote_sm_opq_shape_scored_events.csv"
REAL_VECTORS = ROBUST / "tables" / "02_opq_three_sample_microband_vectors.csv"

BANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
UPPER = ["q95_97", "q97_98", "q98_99", "q99_100"]
EDGES = [0.90, 0.95, 0.97, 0.98, 0.99, 1.0]
REL_SHAPE_UNCS = [0.10, 0.20, 0.30, 0.40, 0.50]
MODES = {
    "exact_completed_only": ["exact_record_sumw"],
    "exact_plus_unit_weight_metadata": ["exact_record_sumw", "metadata_unit_weight_record"],
    "exact_plus_approx_pending": [
        "exact_record_sumw",
        "metadata_unit_weight_record",
        "approx_constant_weight_sumw_pending_exact",
    ],
}


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, qs: list[float]) -> np.ndarray:
    order = np.argsort(values)
    x = values[order]
    w = weights[order]
    cdf = np.cumsum(w) / np.sum(w)
    return np.interp(qs, cdf, x)


def sm_template(mode: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tiers = pd.read_csv(TIERS)
    usable = tiers[tiers["normalisation_tier"].isin(MODES[mode])].copy()
    events = pd.read_csv(SM_EVENTS, low_memory=False)
    events = events[events["record_id"].isin(usable["record_id"])].copy()
    if usable.empty or events.empty:
        return pd.DataFrame(), pd.DataFrame(), usable

    scale = usable.set_index("record_id")["base_event_scale_for_generator_weight"].to_dict()
    events["sm_lumi_weight"] = events["generator_weight"] * events["record_id"].map(scale)
    events = events[np.isfinite(events["sm_lumi_weight"]) & (events["sm_lumi_weight"] > 0)].copy()
    if events.empty:
        return pd.DataFrame(), pd.DataFrame(), usable

    edges = weighted_quantile(events["B_OPQ"].to_numpy(float), events["sm_lumi_weight"].to_numpy(float), EDGES)
    edges[-1] = np.inf
    labels = np.full(len(events), None, dtype=object)
    vals = events["B_OPQ"].to_numpy(float)
    for band, lo, hi in zip(BANDS, edges[:-1], edges[1:]):
        labels[(vals >= lo) & (vals < hi)] = band
    events["microband"] = labels

    total = float(events["sm_lumi_weight"].sum())
    rows = []
    for band in BANDS:
        hit = events[events["microband"].eq(band)]
        weight = float(hit["sm_lumi_weight"].sum()) if not hit.empty else 0.0
        rows.append(
            {
                "mode": mode,
                "microband": band,
                "sm_weight": weight,
                "sm_events": int(len(hit)),
                "sm_fraction_of_total": weight / total if total > 0 else 0.0,
            }
        )

    process = (
        events[events["microband"].notna()]
        .groupby(["process_family", "record_id", "microband"], as_index=False)["sm_lumi_weight"]
        .sum()
        .rename(columns={"sm_lumi_weight": "sm_weight"})
    )
    process.insert(0, "mode", mode)
    return pd.DataFrame(rows), process, usable


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
                        "name": "opq_trace_excess",
                        "data": [exp],
                        "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}],
                    },
                    {
                        "name": "sm_background",
                        "data": [exp],
                        "modifiers": [
                            {"name": f"shape_{band}", "type": "normsys", "data": {"hi": 1 + rel_unc, "lo": max(1 - rel_unc, 1e-6)}},
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
    for path in [TABLES, REPORTS, JSON_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    real = pd.read_csv(REAL_VECTORS)
    all_templates = []
    all_process = []
    all_usable = []
    rows = []
    channel_rows = []

    for mode in MODES:
        template, process, usable = sm_template(mode)
        if not template.empty:
            all_templates.append(template)
        if not process.empty:
            all_process.append(process)
        usable = usable.copy()
        usable.insert(0, "mode", mode)
        all_usable.append(usable)
        if template.empty:
            continue

        base = template.set_index("microband")["sm_weight"].to_dict()
        q90 = max(float(base["q90_95"]), 1e-9)
        template_ratio = {band: float(base[band]) / q90 for band in BANDS}

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
                            "mode": mode,
                            "sample_validation_id": sample_id,
                            "region": region_name,
                            "relative_independent_shape_uncertainty": rel_unc,
                            "sideband_anchor_q90_95": anchor,
                            "upper_observed_total": sum(observed[b] for b in UPPER),
                            "upper_expected_total": sum(expected[b] for b in UPPER),
                            "obs_over_exp_upper": sum(observed[b] for b in UPPER) / max(sum(expected[b] for b in UPPER), 1e-9),
                            "background_only_p": p,
                            "background_only_Z": p_to_z(p),
                            "fit_mu_trace": params.get("mu_trace", np.nan),
                            "normalisation_scope": mode,
                        }
                    )
                    for band in UPPER:
                        channel_rows.append(
                            {
                                "mode": mode,
                                "sample_validation_id": sample_id,
                                "region": region_name,
                                "relative_independent_shape_uncertainty": rel_unc,
                                "microband": band,
                                "observed": observed[band],
                                "expected_from_sm_sideband": expected[band],
                                "obs_over_exp": observed[band] / max(expected[band], 1e-9),
                            }
                        )
                    spec_name = f"{mode}_{sample_id}_{region_name}_unc_{rel_unc:.2f}.json"
                    (JSON_DIR / spec_name).write_text(json.dumps(model.spec, indent=2), encoding="utf-8")

    templates = pd.concat(all_templates, ignore_index=True) if all_templates else pd.DataFrame()
    processes = pd.concat(all_process, ignore_index=True) if all_process else pd.DataFrame()
    usable_records = pd.concat(all_usable, ignore_index=True) if all_usable else pd.DataFrame()
    summary = pd.DataFrame(rows)
    channels = pd.DataFrame(channel_rows)

    combined_rows = []
    if not summary.empty:
        key = summary[summary["relative_independent_shape_uncertainty"].eq(0.10)].copy()
        for (mode, region), group in key.groupby(["mode", "region"], sort=False):
            stat, p = combine_pvalues(group["background_only_p"].to_numpy(float), method="fisher")
            combined_rows.append(
                {
                    "mode": mode,
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
    else:
        key = pd.DataFrame()
    combined = pd.DataFrame(combined_rows)

    templates.to_csv(TABLES / "01_exact_hybrid_sm_opq_microband_template.csv", index=False)
    processes.to_csv(TABLES / "02_exact_hybrid_sm_opq_microband_by_process.csv", index=False)
    usable_records.to_csv(TABLES / "03_exact_hybrid_usable_records.csv", index=False)
    summary.to_csv(TABLES / "04_exact_hybrid_sideband_likelihood_summary.csv", index=False)
    channels.to_csv(TABLES / "05_exact_hybrid_sideband_likelihood_channels.csv", index=False)
    key.to_csv(TABLES / "06_key_10pct_exact_hybrid_likelihood_readout.csv", index=False)
    combined.to_csv(TABLES / "07_combined_10pct_exact_hybrid_likelihood_readout.csv", index=False)

    report = f"""# Three-Sample Exact/Hybrid SM OPQ Sideband Likelihood

## Scope

This reruns the frozen OPQ sideband likelihood using the stricter
normalisation table built from exact `GenFilterInfo` sums where full online
records are complete.

The frozen score is unchanged:

$$B_{{OPQ}} = 0.344828O + 0.517241P - 0.137931Q.$$

## Usable Records

{usable_records.to_markdown(index=False, floatfmt='.6g') if not usable_records.empty else '_No usable records._'}

## Templates

{templates.to_markdown(index=False, floatfmt='.6g') if not templates.empty else '_No template could be built._'}

## Key 10 Percent Readout

{key.to_markdown(index=False, floatfmt='.6g') if not key.empty else '_No likelihood readout produced._'}

## Combined Readout

{combined.to_markdown(index=False, floatfmt='.6g') if not combined.empty else '_No combined readout produced._'}

## Interpretation Rule

`exact_completed_only` is the strictest current readout. The
`exact_plus_unit_weight_metadata` mode adds only records with verified +1
generator weights and official zero negative-weight metadata; it remains
distinct from a complete GenFilterInfo scan. `exact_plus_approx_pending` is a
broader continuity stress test against the earlier approximate model, not a
final publication-grade claim.
"""
    (REPORTS / "11_THREE_SAMPLE_EXACT_HYBRID_SM_SIDEBAND_LIKELIHOOD.md").write_text(report, encoding="utf-8")
    print(combined.to_string(index=False) if not combined.empty else "No likelihood readout produced")
    print(REPORTS / "11_THREE_SAMPLE_EXACT_HYBRID_SM_SIDEBAND_LIKELIHOOD.md")


if __name__ == "__main__":
    main()
