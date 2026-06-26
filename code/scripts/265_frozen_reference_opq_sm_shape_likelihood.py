from __future__ import annotations

"""Frozen-reference OPQ calibration and SM-template sideband likelihood.

Unlike the historical rank-tail readout, this script derives all calibrations
and numerical score thresholds once from the original Run2016G reference
sample. Those definitions are then applied unchanged to the held-out real
samples and UL16 simulated templates.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyhf
from scipy.stats import combine_pvalues, norm


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "outputs_run2016g_control_diagnostics" / "tables" / "00_scored_events_for_control_diagnostics.csv.gz"
REAL = ROOT / "outputs_remote_mht_aware_feature_equivalent_validation" / "tables" / "04_remote_mht_aware_scored_axis_events.csv"
SM_EVENTS = ROOT / "outputs_remote_opq_sm_background_build" / "tables" / "07_remote_sm_opq_shape_scored_events.csv"
TIERS = ROOT / "outputs_remote_opq_sm_background_build" / "tables" / "17_exact_hybrid_sm_normalisation_tiers.csv"
OUT = ROOT / "outputs_frozen_reference_opq_sm_shape_likelihood"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
JSON_DIR = OUT / "json"

DATASETS = ["MET", "JetHT", "SingleMuon"]
SAMPLES = [
    "Run2015D_remote_mht_aware_holdout",
    "Run2016H_remote_mht_aware",
    "Run2016G_remote_mht_aware_fresh",
]
BANDS = ["q90_95", "q95_97", "q97_98", "q98_99", "q99_100"]
QUANTILES = [0.90, 0.95, 0.97, 0.98, 0.99, 1.0]
UPPER = BANDS[1:]
REL_SHAPE_UNCS = [0.10, 0.20, 0.30, 0.40, 0.50]
MODES = {
    "exact_completed_only": ["exact_record_sumw"],
    "exact_plus_unit_weight_metadata": ["exact_record_sumw", "metadata_unit_weight_record"],
}


def p_to_z(p: float) -> float:
    return float(norm.isf(float(np.clip(p, np.nextafter(0, 1), 1.0))))


def col(df: pd.DataFrame, name: str, default: float = 0.0) -> np.ndarray:
    if name not in df.columns:
        return np.full(len(df), default, dtype=float)
    return pd.to_numeric(df[name], errors="coerce").fillna(default).to_numpy(float)


def quality(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mask = np.ones(len(out), dtype=bool)
    for name in ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]:
        if name in out.columns:
            mask &= pd.to_numeric(out[name], errors="coerce").fillna(0).eq(1).to_numpy(bool)
    return out.loc[mask].copy()


def prepare(df: pd.DataFrame, dataset_override: str | None = None) -> pd.DataFrame:
    out = df.copy()
    if dataset_override is not None:
        out["primary_dataset"] = dataset_override
    out["primary_dataset"] = out["primary_dataset"].astype(str)
    out["missing_proxy_pt"] = np.where(
        out["primary_dataset"].eq("HTMHT").to_numpy(bool),
        col(out, "MHT_pt"),
        col(out, "MET_pt"),
    )
    out["log_missing"] = np.log1p(np.clip(out["missing_proxy_pt"].to_numpy(float), 0, None))
    out["log_ht"] = np.log1p(np.clip(col(out, "HT"), 0, None))
    out["log_packed"] = np.log1p(np.clip(col(out, "packed_candidate_count"), 0, None))
    out["log_sv"] = np.log1p(np.clip(col(out, "secondary_vertex_count"), 0, None))
    out["n_jets"] = col(out, "N_jets_30")
    out["n_btags"] = col(out, "N_btags_medium")
    out["n_muons"] = col(out, "N_muons")
    out["n_electrons"] = col(out, "N_electrons")
    if "jet_bin" not in out.columns:
        n = out["n_jets"].to_numpy(float)
        out["jet_bin"] = np.select([n <= 0, n <= 2, n <= 4], ["0jet", "1to2jets", "3to4jets"], default="5plusjets")
    out["jet_bin"] = out["jet_bin"].astype(str)
    return out


def fit_reference(reference: pd.DataFrame) -> tuple[dict[str, dict[str, object]], pd.DataFrame]:
    calibrations: dict[str, dict[str, object]] = {}
    threshold_rows: list[dict[str, object]] = []
    for dataset in DATASETS:
        frame = reference[reference["primary_dataset"].eq(dataset)].copy()
        if len(frame) < 500:
            raise RuntimeError(f"Reference sample has too few {dataset} events: {len(frame)}")
        lower = frame["log_missing"].le(frame["log_missing"].quantile(0.95)).to_numpy(bool)
        features = ["log_ht", "n_jets", "n_btags", "n_muons", "n_electrons"]
        x = frame.loc[lower, features].to_numpy(float)
        y = frame.loc[lower, "log_missing"].to_numpy(float)
        beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)
        pred = np.column_stack([np.ones(len(frame)), frame[features].to_numpy(float)]) @ beta
        residual = frame["log_missing"].to_numpy(float) - pred

        values = {
            "log_missing": frame["log_missing"].to_numpy(float),
            "log_ht": frame["log_ht"].to_numpy(float),
            "log_packed": frame["log_packed"].to_numpy(float),
            "log_sv": frame["log_sv"].to_numpy(float),
            "n_jets": frame["n_jets"].to_numpy(float),
            "n_btags": frame["n_btags"].to_numpy(float),
            "residual": residual,
        }
        stats: dict[str, dict[str, float]] = {}
        for name, vals in values.items():
            ref_vals = vals[lower]
            sd = float(np.std(ref_vals))
            stats[name] = {"mean": float(np.mean(ref_vals)), "sd": sd if sd > 1e-9 else 1.0}

        missing_edges = np.unique(np.quantile(frame["missing_proxy_pt"].to_numpy(float), np.linspace(0, 1, 11)))
        if len(missing_edges) < 3:
            raise RuntimeError(f"Reference missing-energy quantiles collapsed for {dataset}")
        calibrations[dataset] = {
            "residual_beta": beta.tolist(),
            "features": features,
            "stats": stats,
            "missing_decile_edges": missing_edges.tolist(),
        }

        scored = apply_calibration(frame, calibrations[dataset])
        deciles = assign_decile(scored["missing_proxy_pt"].to_numpy(float), missing_edges)
        scored["missing_decile_frozen"] = deciles
        for decile, group in scored.groupby("missing_decile_frozen", observed=False):
            if len(group) < 100:
                continue
            edges = np.quantile(group["B_OPQ_frozen_reference"].to_numpy(float), QUANTILES)
            for band, lo, hi in zip(BANDS, edges[:-1], edges[1:]):
                threshold_rows.append(
                    {
                        "primary_dataset": dataset,
                        "missing_decile_frozen": int(decile),
                        "microband": band,
                        "score_low": float(lo),
                        "score_high": float(hi) if band != "q99_100" else np.inf,
                        "reference_events_in_decile": int(len(group)),
                    }
                )
    return calibrations, pd.DataFrame(threshold_rows)


def apply_calibration(frame: pd.DataFrame, calibration: dict[str, object]) -> pd.DataFrame:
    out = frame.copy()
    stats = calibration["stats"]
    features = calibration["features"]
    beta = np.asarray(calibration["residual_beta"], dtype=float)
    pred = np.column_stack([np.ones(len(out)), out[features].to_numpy(float)]) @ beta
    residual = out["log_missing"].to_numpy(float) - pred

    def z(name: str, values: np.ndarray) -> np.ndarray:
        item = stats[name]
        return (values - float(item["mean"])) / float(item["sd"])

    observer = z("residual", residual)
    disp = z("log_sv", out["log_sv"].to_numpy(float)) + 0.05 * z("log_packed", out["log_packed"].to_numpy(float))
    physical = 0.65 * z("log_missing", out["log_missing"].to_numpy(float)) + 0.20 * z("log_ht", out["log_ht"].to_numpy(float)) + 0.15 * disp
    qcd = 0.70 * z("n_jets", out["n_jets"].to_numpy(float)) + 0.30 * z("n_btags", out["n_btags"].to_numpy(float))
    out["observer_projection_frozen_reference"] = observer
    out["physical_projection_frozen_reference"] = physical
    out["ordinary_qcd_axis_frozen_reference"] = qcd
    out["B_OPQ_frozen_reference"] = 0.344828 * observer + 0.517241 * physical - 0.137931 * qcd
    return out


def assign_decile(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
    decile = np.searchsorted(edges[1:-1], values, side="right")
    return np.clip(decile, 0, 9).astype(int)


def tag(frame: pd.DataFrame, calibrations: dict[str, dict[str, object]], thresholds: pd.DataFrame, mc: bool = False) -> pd.DataFrame:
    chunks = []
    for dataset, group in frame.groupby("primary_dataset", sort=False):
        reference_dataset = "MET" if mc else str(dataset)
        if reference_dataset not in calibrations:
            continue
        cal = calibrations[reference_dataset]
        scored = apply_calibration(group, cal)
        scored["missing_decile_frozen"] = assign_decile(
            scored["missing_proxy_pt"].to_numpy(float),
            np.asarray(cal["missing_decile_edges"], dtype=float),
        )
        scored["calibration_dataset"] = reference_dataset
        lookup = thresholds[thresholds["primary_dataset"].eq(reference_dataset)]
        labels = np.full(len(scored), None, dtype=object)
        vals = scored["B_OPQ_frozen_reference"].to_numpy(float)
        for row in lookup.itertuples(index=False):
            hit = scored["missing_decile_frozen"].to_numpy(int) == int(row.missing_decile_frozen)
            labels[hit & (vals >= float(row.score_low)) & (vals < float(row.score_high))] = row.microband
        scored["microband_frozen_reference"] = labels
        chunks.append(scored)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def build_model(observed: dict[str, float], expected: dict[str, float], rel_unc: float) -> tuple[pyhf.Model, list[float]]:
    channels = []
    for band in UPPER:
        exp = max(float(expected[band]), 1e-9)
        channels.append(
            {
                "name": band,
                "samples": [
                    {"name": "opq_trace_excess", "data": [exp], "modifiers": [{"name": "mu_trace", "type": "normfactor", "data": None}]},
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
    model = pyhf.Model({"channels": channels, "parameters": [{"name": "mu_trace", "bounds": [[0.0, 20.0]], "inits": [0.0]}]}, poi_name="mu_trace")
    return model, [float(observed[name]) for name in model.config.channels] + model.config.auxdata


def main() -> None:
    for path in [TABLES, REPORTS, JSON_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    reference = prepare(quality(pd.read_csv(REFERENCE, low_memory=False)))
    calibrations, thresholds = fit_reference(reference)
    (TABLES / "01_frozen_reference_calibration.json").write_text(json.dumps(calibrations, indent=2), encoding="utf-8")
    thresholds.to_csv(TABLES / "02_frozen_reference_microband_thresholds.csv", index=False)

    real_raw = prepare(quality(pd.read_csv(REAL, low_memory=False)))
    real_raw = real_raw[real_raw["sample_validation_id"].isin(SAMPLES) & real_raw["primary_dataset"].isin(DATASETS)].copy()
    real = tag(real_raw, calibrations, thresholds)
    real.to_csv(TABLES / "03_heldout_real_events_frozen_reference_scored.csv", index=False)

    sm_raw = prepare(quality(pd.read_csv(SM_EVENTS, low_memory=False)), dataset_override="MET")
    sm = tag(sm_raw, calibrations, thresholds, mc=True)
    tiers = pd.read_csv(TIERS)
    scale = tiers.set_index("record_id")["base_event_scale_for_generator_weight"].to_dict()
    sm["template_weight"] = pd.to_numeric(sm["generator_weight"], errors="coerce").fillna(0.0) * sm["record_id"].map(scale).fillna(0.0)
    sm.to_csv(TABLES / "04_sm_events_frozen_reference_scored.csv", index=False)

    results = []
    process_rows = []
    event_rows = []
    combined_rows = []
    for mode, allowed in MODES.items():
        selected = sm[sm["record_id"].isin(tiers[tiers["normalisation_tier"].isin(allowed)]["record_id"])].copy()
        selected = selected[selected["microband_frozen_reference"].notna() & (selected["template_weight"] > 0)].copy()
        template = selected.groupby("microband_frozen_reference", as_index=False)["template_weight"].sum().rename(columns={"microband_frozen_reference": "microband", "template_weight": "sm_weight"})
        total = max(float(template["sm_weight"].sum()), 1e-12)
        template["sm_fraction"] = template["sm_weight"] / total
        template.to_csv(TABLES / f"05_{mode}_template.csv", index=False)
        proc = selected.groupby(["process_family", "microband_frozen_reference"], as_index=False)["template_weight"].sum()
        proc.insert(0, "mode", mode)
        process_rows.append(proc.rename(columns={"microband_frozen_reference": "microband", "template_weight": "sm_weight"}))
        ratios = template.set_index("microband")["sm_fraction"].to_dict()
        if any(b not in ratios or ratios[b] <= 0 for b in BANDS):
            continue
        for sample_id, group in real.groupby("sample_validation_id", sort=False):
            trace_group = group[group["primary_dataset"].eq("MET") & group["jet_bin"].eq("0jet")]
            control_group = group[group["primary_dataset"].isin(["JetHT", "SingleMuon"])]
            for region, subset in [("MET_trace", trace_group), ("JetHT_SingleMuon_controls", control_group)]:
                observed = {b: float((subset["microband_frozen_reference"] == b).sum()) for b in BANDS}
                anchor = max(observed["q90_95"], 1e-9)
                expected = {b: anchor * ratios[b] / ratios["q90_95"] for b in BANDS}
                for unc in REL_SHAPE_UNCS:
                    model, data = build_model(observed, expected, unc)
                    p = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0", return_expected=False))
                    fit = pyhf.infer.mle.fit(data, model)
                    params = {name: float(fit[i]) for i, name in enumerate(model.config.par_order)}
                    results.append(
                        {
                            "mode": mode, "sample_validation_id": sample_id, "region": region,
                            "relative_independent_shape_uncertainty": unc,
                            "anchor_q90_95": anchor,
                            "upper_observed": sum(observed[b] for b in UPPER),
                            "upper_expected": sum(expected[b] for b in UPPER),
                            "obs_over_exp_upper": sum(observed[b] for b in UPPER) / max(sum(expected[b] for b in UPPER), 1e-12),
                            "background_only_p": p, "background_only_Z": p_to_z(p),
                            "fit_mu_trace": params.get("mu_trace", np.nan),
                        }
                    )
                    for b in BANDS:
                        event_rows.append({"mode": mode, "sample_validation_id": sample_id, "region": region, "uncertainty": unc, "microband": b, "observed": observed[b], "expected": expected[b]})
                    (JSON_DIR / f"{mode}_{sample_id}_{region}_{unc:.2f}.json").write_text(json.dumps(model.spec, indent=2), encoding="utf-8")
    result_df = pd.DataFrame(results)
    key = result_df[result_df["relative_independent_shape_uncertainty"].eq(0.10)].copy()
    if not key.empty:
        for (mode, region), group in key.groupby(["mode", "region"], sort=False):
            stat, p = combine_pvalues(group["background_only_p"].to_numpy(float), method="fisher")
            combined_rows.append({"mode": mode, "region": region, "sample_count": len(group), "fisher_statistic": stat, "fisher_p": p, "fisher_Z": p_to_z(p), "min_sample_Z": group["background_only_Z"].min(), "max_sample_Z": group["background_only_Z"].max()})
    combined = pd.DataFrame(combined_rows)
    control_diag_rows = []
    if not key.empty:
        for mode, group in key[key["region"].eq("JetHT_SingleMuon_controls")].groupby("mode", sort=False):
            max_z = float(group["background_only_Z"].max())
            control_diag_rows.append(
                {
                    "mode": mode,
                    "max_control_Z": max_z,
                    "controls_closed_at_Z_le_2": bool(max_z <= 2.0),
                    "interpretation": "control_closure_pass" if max_z <= 2.0 else "control_closure_fail",
                }
            )
    control_diag = pd.DataFrame(control_diag_rows)
    pd.concat(process_rows, ignore_index=True).to_csv(TABLES / "06_sm_process_composition_frozen_reference.csv", index=False) if process_rows else pd.DataFrame().to_csv(TABLES / "06_sm_process_composition_frozen_reference.csv", index=False)
    result_df.to_csv(TABLES / "07_frozen_reference_likelihood_summary.csv", index=False)
    pd.DataFrame(event_rows).to_csv(TABLES / "08_frozen_reference_likelihood_channels.csv", index=False)
    key.to_csv(TABLES / "09_frozen_reference_key_10pct_readout.csv", index=False)
    combined.to_csv(TABLES / "10_frozen_reference_combined_readout.csv", index=False)
    control_diag.to_csv(TABLES / "11_frozen_reference_control_closure_diagnostic.csv", index=False)

    report = f"""# Frozen-Reference OPQ SM Shape Likelihood

## Method Correction

All residual fits, feature standardisation constants, missing-energy deciles and
numerical OPQ microband thresholds were fitted once on the original Run2016G
reference sample. They were then applied unchanged to held-out real samples and
to UL16 simulated templates. This avoids recalculating percentile boundaries
within each simulated process, which would make a process-composition test
tautological.

## Combined 10 Percent Readout

{combined.to_markdown(index=False, floatfmt='.6g') if not combined.empty else '_No valid template/readout was produced._'}

## Control Closure Diagnostic

{control_diag.to_markdown(index=False, floatfmt='.6g') if not control_diag.empty else '_No control diagnostic was produced._'}

## Interpretation

This is a corrected SM-template shape test, not an absolute-yield or official
CMS likelihood. It uses sideband anchoring and fixed reference thresholds.
The `exact_completed_only` mode contains full-record GenFilterInfo-normalised
W3Jets and TTW. The unit-weight mode additionally includes records whose
generator weights are verified +1 in the extracted sample and whose official
metadata report zero negative-weight fraction.

The historical rank-tail likelihood should not be used as a discovery-style SM
prediction because it recomputed microband thresholds separately in each MC
template. The fixed-reference test is the relevant diagnostic. A MET trace is
only interpretable as process-specific if the same template closes JetHT and
SingleMuon controls; a failure in this table blocks that interpretation.
"""
    (REPORTS / "01_FROZEN_REFERENCE_OPQ_SM_SHAPE_LIKELIHOOD.md").write_text(report, encoding="utf-8")
    print(combined.to_string(index=False) if not combined.empty else "No valid readout")
    print(REPORTS / "01_FROZEN_REFERENCE_OPQ_SM_SHAPE_LIKELIHOOD.md")


if __name__ == "__main__":
    main()
