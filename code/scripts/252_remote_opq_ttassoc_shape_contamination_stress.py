from __future__ import annotations

"""Stress-test the OPQ likelihood against unnormalised TTZ/TTW shape coverage."""

from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
SM_OUT = ROOT / "outputs_remote_opq_sm_background_build"
ROBUST = ROOT / "outputs_opq_remote_three_sample_statistical_robustness"
OUT = ROOT / "outputs_remote_opq_ttassoc_shape_contamination_stress"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

TIERS = SM_OUT / "tables" / "08_remote_sm_normalisation_tiers.csv"
SM_EVENTS = SM_OUT / "tables" / "07_remote_sm_opq_shape_scored_events.csv"
REAL_VECTORS = ROBUST / "tables" / "02_opq_three_sample_microband_vectors.csv"
BANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
UPPER = ["q95_97", "q97_98", "q98_99", "q99_100"]
EDGES = [0.90, 0.95, 0.97, 0.98, 0.99, 1.0]
TTASSOC_FRACTIONS = [0.0, 0.01, 0.05, 0.10, 0.20, 0.50]
REL_UNC = 0.10


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, qs: list[float]) -> np.ndarray:
    order = np.argsort(values)
    x = values[order]
    w = weights[order]
    cdf = np.cumsum(w) / np.sum(w)
    return np.interp(qs, cdf, x)


def band_fractions(values: np.ndarray, weights: np.ndarray, edges: np.ndarray) -> dict[str, float]:
    labels = np.full(len(values), None, dtype=object)
    local_edges = edges.copy()
    local_edges[-1] = np.inf
    for band, lo, hi in zip(BANDS, local_edges[:-1], local_edges[1:]):
        labels[(values >= lo) & (values < hi)] = band
    rows = {}
    total = float(weights[labels != None].sum())  # noqa: E711
    for band in BANDS:
        rows[band] = float(weights[labels == band].sum() / total) if total > 0 else 0.0
    return rows


def build_model(observed: dict[str, float], expected: dict[str, float]) -> tuple[pyhf.Model, list[float]]:
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
                        "name": "shape_stressed_background",
                        "data": [exp],
                        "modifiers": [
                            {"name": f"shape_{band}", "type": "normsys", "data": {"hi": 1 + REL_UNC, "lo": 1 - REL_UNC}},
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
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    tiers = pd.read_csv(TIERS)
    events = pd.read_csv(SM_EVENTS, low_memory=False)
    usable = tiers[tiers["normalisation_tier"].eq("approx_constant_weight_sumw")].copy()
    usable = usable[~usable["process_family"].eq("TTAssoc")].copy()
    scale = usable.set_index("record_id")["base_event_scale_for_generator_weight"].to_dict()
    base = events[events["record_id"].isin(usable["record_id"])].copy()
    base["template_weight"] = base["generator_weight"] * base["record_id"].map(scale)
    base = base[np.isfinite(base["template_weight"]) & (base["template_weight"] > 0)].copy()
    edges = weighted_quantile(base["B_OPQ"].to_numpy(float), base["template_weight"].to_numpy(float), EDGES)
    base_frac = band_fractions(base["B_OPQ"].to_numpy(float), base["template_weight"].to_numpy(float), edges)

    ttassoc = events[events["process_family"].eq("TTAssoc")].copy()
    if ttassoc.empty:
        raise RuntimeError("No TTAssoc shape rows found.")
    ttassoc["template_weight"] = pd.to_numeric(ttassoc["generator_weight"], errors="coerce").abs().fillna(0.0)
    ttassoc = ttassoc[ttassoc["template_weight"] > 0].copy()
    ttassoc_frac = band_fractions(ttassoc["B_OPQ"].to_numpy(float), ttassoc["template_weight"].to_numpy(float), edges)

    real = pd.read_csv(REAL_VECTORS)
    per_sample_rows = []
    combined_rows = []
    template_rows = []
    for fraction in TTASSOC_FRACTIONS:
        blend = {band: (1.0 - fraction) * base_frac[band] + fraction * ttassoc_frac[band] for band in BANDS}
        template_rows.append(
            {
                "ttassoc_shape_fraction": fraction,
                **{f"template_fraction_{band}": blend[band] for band in BANDS},
                **{f"base_fraction_{band}": base_frac[band] for band in BANDS},
                **{f"ttassoc_abs_weight_fraction_{band}": ttassoc_frac[band] for band in BANDS},
            }
        )
        q90 = max(blend["q90_95"], 1e-12)
        ratio = {band: blend[band] / q90 for band in BANDS}
        for sample_id, group in real.groupby("sample_validation_id", sort=False):
            for region, count_col in [("MET_trace", "trace_count"), ("JetHT_SingleMuon_controls", "control_count")]:
                observed = {row.microband: float(getattr(row, count_col)) for row in group.itertuples(index=False)}
                anchor = observed["q90_95"]
                expected = {band: anchor * ratio[band] for band in BANDS}
                model, data = build_model(observed, expected)
                p = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
                per_sample_rows.append(
                    {
                        "ttassoc_shape_fraction": fraction,
                        "sample_validation_id": sample_id,
                        "region": region,
                        "sideband_anchor_q90_95": anchor,
                        "upper_observed_total": sum(observed[b] for b in UPPER),
                        "upper_expected_total": sum(expected[b] for b in UPPER),
                        "obs_over_exp_upper": sum(observed[b] for b in UPPER) / max(sum(expected[b] for b in UPPER), 1e-9),
                        "background_only_p": p,
                        "background_only_Z": p_to_z(p),
                    }
                )

    per_sample = pd.DataFrame(per_sample_rows)
    for (fraction, region), group in per_sample.groupby(["ttassoc_shape_fraction", "region"], sort=False):
        stat, p = combine_pvalues(group["background_only_p"].to_numpy(float), method="fisher")
        combined_rows.append(
            {
                "ttassoc_shape_fraction": fraction,
                "region": region,
                "samples_combined": ";".join(group["sample_validation_id"].astype(str)),
                "fisher_statistic": float(stat),
                "fisher_p": float(p),
                "fisher_Z": p_to_z(float(p)),
                "min_sample_Z": float(group["background_only_Z"].min()),
                "max_sample_Z": float(group["background_only_Z"].max()),
                "controls_close_if_control_region": bool(region != "MET_trace" and group["background_only_Z"].abs().max() < 1.0),
            }
        )

    templates = pd.DataFrame(template_rows)
    combined = pd.DataFrame(combined_rows)
    per_sample.to_csv(TABLES / "01_ttassoc_shape_stress_per_sample.csv", index=False)
    combined.to_csv(TABLES / "02_ttassoc_shape_stress_combined.csv", index=False)
    templates.to_csv(TABLES / "03_ttassoc_shape_stress_templates.csv", index=False)

    report = f"""# TTZ/TTW Shape-Contamination Stress Test

## Purpose

The rare TTZ/TTW records were extracted, but they are not luminosity-normalised:
the TTZ records lack usable cross-section fields in the local CERN metadata and
all four TTZ/TTW records have high generator-weight variation. Therefore they
cannot be included in the strict approximate-yield template.

This stress test asks a narrower question: if their OPQ shape is blended into
the SM sideband template at fixed fractions, does the MET trace disappear or do
the controls fail?

## Template Fractions

{templates.to_markdown(index=False, floatfmt='.6g')}

## Combined Readout

{combined.to_markdown(index=False, floatfmt='.6g')}

## Interpretation

This is not a replacement for official TTZ/TTW normalisation. It is a
composition stress test. Fractions at 20 percent and 50 percent are deliberately
large for rare TTZ/TTW backgrounds; they are included to check sensitivity to
the missing normalisation, not to claim those are physical rates.
"""
    (REPORTS / "01_TTASSOC_SHAPE_CONTAMINATION_STRESS.md").write_text(report, encoding="utf-8")
    print(combined.to_string(index=False))
    print(REPORTS / "01_TTASSOC_SHAPE_CONTAMINATION_STRESS.md")


if __name__ == "__main__":
    main()
