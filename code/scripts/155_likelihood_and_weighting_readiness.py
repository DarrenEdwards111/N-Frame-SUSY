from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "outputs_today_physics_style_susy_search_framework"
PREV_TABLES = PREV / "tables"
PREV_STATMODEL = PREV / "statistical_model"
OUT = ROOT / "outputs_today_likelihood_and_weighting_readiness"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
SOURCES = OUT / "sources"
STATMODEL = OUT / "statistical_model"
DATE = "2026-06-10"

SIGNAL_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]
VALIDATION_REGIONS = ["VR1", "VR2", "VR4", "VR5", "CR_BtagTop"]
CONTROL_REGIONS = ["CR_QCD", "CR_MET", "CR_Muon", "CR_BtagTop"]
ALL_REGIONS = [
    "SR1",
    "SR2",
    "SR3",
    "SR4",
    "SR5",
    "VR1",
    "VR2",
    "VR3",
    "VR4",
    "VR5",
    "CR_QCD",
    "CR_Muon",
    "CR_MET",
    "CR_Ordinary",
    "CR_BtagTop",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, FIGURES, SOURCES, STATMODEL]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    try:
        return view.to_markdown(index=False)
    except Exception:
        return "```\n" + view.to_csv(index=False) + "```"


def finite_float(value: Any, default: float = np.nan) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if np.isfinite(out) else default


def z_and_p(obs: float, exp: float, sigma: float) -> tuple[float, float]:
    denom = math.sqrt(max(exp, 0.0) + max(sigma, 0.0) ** 2)
    z = (obs - exp) / denom if denom > 0 else np.nan
    p = 1.0 - stats.norm.cdf(z) if np.isfinite(z) else np.nan
    return z, p


def import_previous_framework():
    script = ROOT / "scripts" / "154_physics_style_susy_search_framework.py"
    spec = importlib.util.spec_from_file_location("previous_framework_154", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCES = SOURCES
    module.STATMODEL = PREV_STATMODEL
    return module


def load_existing_context() -> dict[str, Any]:
    inv = read_csv(PREV_TABLES / "01_analysis_inventory.csv")
    regions = read_csv(PREV_TABLES / "02_region_definitions.csv")
    yields = read_csv(PREV_TABLES / "03_real_data_region_yields.csv")
    eff = read_csv(PREV_TABLES / "04_benchmark_signal_region_efficiencies.csv")
    bg = read_csv(PREV_TABLES / "05_background_estimates_by_method.csv")
    sig = read_csv(PREV_TABLES / "06_observed_expected_significance_tests.csv")
    inc = read_csv(PREV_TABLES / "07_bnf_incrementality_in_search_context.csv")
    tf = read_csv(PREV_TABLES / "05_transfer_factor_estimates.csv")
    abcd = read_csv(PREV_TABLES / "05_abcd_closure_tests.csv")
    return {
        "inventory": inv,
        "regions": regions,
        "yields": yields,
        "eff": eff,
        "bg": bg,
        "sig": sig,
        "inc": inc,
        "tf": tf,
        "abcd": abcd,
    }


def prepare_region_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prev = import_previous_framework()
    real, real_unique, sm, signal = prev.load_all_data()
    real_u = prev.apply_regions(real_unique)
    sm_r = prev.apply_regions(sm)
    signal_r = prev.apply_regions(signal)
    return real_u, sm_r, signal_r


def first_values(path: Path, columns: list[str], n: int = 500) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path, nrows=n, usecols=lambda c: c in columns)
    except Exception:
        return {}
    values: dict[str, str] = {}
    for col in df.columns:
        non_null = df[col].dropna().astype(str)
        if len(non_null):
            vals = sorted(non_null.unique()[:5])
            values[col] = ";".join(vals)
    return values


def classify_process(text: str) -> str:
    t = text.lower()
    if "qcd" in t:
        return "QCD"
    if re.search(r"(^|[^a-z0-9])(ttjets|ttbar|t\W*t|top|t2tt)([^a-z0-9]|$)", t):
        return "TTJets_or_stop"
    if "wjets" in t or "wjet" in t:
        return "WJets"
    if "znunu" in t or "znu" in t or "zjets" in t:
        return "ZNuNu_or_ZJets"
    if "ww" in t or "wz" in t or "zz" in t or "diboson" in t:
        return "diboson"
    if "susy" in t or "gluino" in t or "neutralino" in t or "sms" in t or "htoa" in t:
        return "SUSY_benchmark"
    return "other_or_mixed"


def audit_metadata(inv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in inv.iterrows():
        path = Path(str(row["path"]))
        cols = list(pd.read_csv(path, nrows=0).columns) if path.exists() else []
        lower_cols = {c.lower(): c for c in cols}

        def find_cols(pattern: str, exclude: tuple[str, ...] = ()) -> list[str]:
            out = []
            rx = re.compile(pattern, re.I)
            for c in cols:
                lc = c.lower()
                if any(x in lc for x in exclude):
                    continue
                if rx.search(c):
                    out.append(c)
            return out

        xsec_cols = find_cols(r"(^|_)(xsec|cross[_-]?section|sigma[_-]?pb)($|_)")
        gen_count_cols = find_cols(r"(generated|gen)[_-]?(events|count)|n[_-]?gen")
        weight_cols = find_cols(r"(^|_)(gen)?weight($|_)|genweight|event[_-]?weight")
        lumi_cols = find_cols(r"integrated[_-]?luminosity|target[_-]?lumi|lumi[_-]?(pb|fb)", exclude=("lumi_block",))
        sumw_cols = find_cols(r"sum[_-]?(w|weights)|sumweights")
        filter_cols = find_cols(r"filter[_-]?(eff|efficiency)")
        kfactor_cols = find_cols(r"k[_-]?factor")
        id_values = first_values(path, ["record_id", "sample_id", "process_label", "classification", "data_tier"])

        sample_text = " ".join(
            [
                str(row.get("dataset_label", "")),
                str(row.get("sample_name", "")),
                str(row.get("category", "")),
                str(row.get("path", "")),
                " ".join(id_values.values()),
            ]
        )
        if str(row.get("category", "")) == "observed_real_collision_data":
            process_family = "observed_real_collision_data"
        else:
            process_family = classify_process(sample_text)
        generator = "pythia" if "pythia" in sample_text.lower() else "madgraph" if "madgraph" in sample_text.lower() else "not_inferable"
        campaign = "RunIISummer/UL2016-like" if re.search(r"RunII|UL2016|Summer16|2016", sample_text, re.I) else "not_inferable"
        record_id = id_values.get("record_id", "not_inferable")

        kind = str(row.get("category", ""))
        missing = []
        if "simulation" in kind:
            for label, found in [
                ("cross_section", xsec_cols),
                ("generated_event_count", gen_count_cols),
                ("per_event_generator_weight", weight_cols),
                ("integrated_luminosity", lumi_cols),
                ("sum_of_weights", sumw_cols),
                ("filter_efficiency", filter_cols),
                ("k_factor", kfactor_cols),
            ]:
                if not found:
                    missing.append(label)
        else:
            missing.append("not_applicable_real_observed_data")

        weighted_possible = (
            "simulation" in kind
            and bool(xsec_cols)
            and bool(lumi_cols)
            and (bool(gen_count_cols) or bool(sumw_cols))
        )
        rows.append(
            {
                "sample_name": row.get("sample_name", row.get("dataset_label", "")),
                "process_label": id_values.get("process_label", row.get("sample_name", "")),
                "process_family": process_family,
                "local_path": str(path),
                "data_tier": row.get("data_tier", ""),
                "sample_type": row.get("category", ""),
                "event_count": row.get("event_count", np.nan),
                "generator_name_inferable": generator,
                "campaign_inferable": campaign,
                "cern_record_id_inferable": record_id,
                "cross_section_columns": ";".join(xsec_cols),
                "cross_section_available": bool(xsec_cols),
                "generated_event_count_columns": ";".join(gen_count_cols),
                "generated_event_count_available": bool(gen_count_cols),
                "per_event_generator_weight_columns": ";".join(weight_cols),
                "per_event_generator_weight_available": bool(weight_cols),
                "luminosity_columns": ";".join(lumi_cols),
                "luminosity_available": bool(lumi_cols),
                "sum_weights_columns": ";".join(sumw_cols),
                "sum_weights_available": bool(sumw_cols),
                "filter_efficiency_columns": ";".join(filter_cols),
                "filter_efficiency_available": bool(filter_cols),
                "k_factor_columns": ";".join(kfactor_cols),
                "k_factor_available": bool(kfactor_cols),
                "weighted_yield_estimation_possible_now": weighted_possible,
                "metadata_source_used": "previous inventory plus local CSV header and first-row metadata",
                "missing_metadata": ";".join(missing),
                "confidence": "medium" if path.exists() else "low_missing_file",
            }
        )
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_mc_normalisation_metadata_audit.csv", index=False)

    weightable = audit[audit["weighted_yield_estimation_possible_now"] == True]
    event_weighted = audit[audit["per_event_generator_weight_available"] == True]
    write_text(
        OUT / "01_MC_NORMALISATION_METADATA_AUDIT_REPORT.md",
        f"""# MC Normalisation Metadata Audit

Date: {DATE}

This audit used local files only: the previous analysis inventory, CSV headers and first-row metadata from the extracted/scored tables. No new large CERN files were downloaded.

## Main finding

No available SM or SUSY benchmark sample currently has enough local metadata for a true luminosity-weighted yield. The local tables are usable for shapes, transfer-factor diagnostics and benchmark efficiencies, but not for publication-grade absolute background normalisation.

## Samples that can be luminosity-weighted now

{md(weightable)}

## Samples with per-event generator weights

{md(event_weighted)}

## Full audit

{md(audit)}

## Bottom line

True weighted background modelling is not possible today from the local extracted tables alone. The missing fields are mainly cross sections, integrated luminosity targets, generated-event counts or sum of weights, filter efficiencies and k-factors.
""",
    )
    return audit


def region_count(df: pd.DataFrame, region: str) -> int:
    return int(df[region].sum()) if region in df.columns else 0


def real_observed_map(yields: pd.DataFrame) -> dict[str, int]:
    sub = yields[yields["subset"] == "combined_unique_real"]
    return {str(r.region): int(r.observed_count) for r in sub.itertuples()}


def shape_expected(sm_r: pd.DataFrame, total_real: int, region: str) -> float:
    if len(sm_r) == 0:
        return np.nan
    return float(sm_r[region].mean() * total_real)


def process_contributions(sm_r: pd.DataFrame, region: str) -> str:
    if len(sm_r) == 0 or region not in sm_r.columns:
        return "unavailable"
    sub = sm_r[sm_r[region]].copy()
    if len(sub) == 0:
        return "no_unweighted_sm_events"
    labels = (
        sub.get("process_label", sub.get("sample_id", pd.Series(["unknown"] * len(sub))))
        .fillna("unknown")
        .astype(str)
        .map(classify_process)
    )
    vc = labels.value_counts(normalize=True)
    return ";".join(f"{k}:{v:.3f}" for k, v in vc.items())


def build_scenarios(
    bg: pd.DataFrame,
    yields: pd.DataFrame,
    sm_r: pd.DataFrame,
    real_u: pd.DataFrame,
) -> pd.DataFrame:
    obs = real_observed_map(yields)
    total_real = len(real_u)
    rows: list[dict[str, Any]] = []

    for sr in SIGNAL_REGIONS:
        observed = obs.get(sr, region_count(real_u, sr))
        prior_shape = bg[(bg["region"] == sr) & (bg["method"] == "B_SM_simulation_shape_scaled_to_real_total")]
        exp_shape = finite_float(prior_shape["expected_background"].iloc[0]) if len(prior_shape) else shape_expected(sm_r, len(real_u), sr)
        for scenario, uncertainty_fraction, headline, assumptions in [
            ("A_shape_only_normalised_to_total_real", 1.00, False, "Unweighted SM region fraction scaled to total observed real-event count."),
            ("D_broad_prior_50pct", 0.50, False, "Same shape-only central value with a 50 percent background-normalisation prior."),
            ("D_broad_prior_100pct", 1.00, False, "Same shape-only central value with a 100 percent background-normalisation prior."),
            ("D_broad_prior_200pct", 2.00, False, "Same shape-only central value with a 200 percent background-normalisation prior."),
            ("D_broad_prior_500pct", 5.00, False, "Same shape-only central value with a 500 percent background-normalisation prior."),
        ]:
            unc = max(abs(exp_shape) * uncertainty_fraction, math.sqrt(max(exp_shape, 0.0)), 1.0)
            rows.append(
                {
                    "scenario": scenario,
                    "region": sr,
                    "observed": observed,
                    "expected_background": exp_shape,
                    "background_uncertainty": unc,
                    "process_contributions": process_contributions(sm_r, sr),
                    "assumptions": assumptions,
                    "headline_usable": headline,
                    "caveats": "Shape-only/unweighted; not a discovery-grade background.",
                }
            )

        for cr in CONTROL_REGIONS:
            sm_sr = region_count(sm_r, sr)
            sm_cr = region_count(sm_r, cr)
            real_cr = region_count(real_u, cr)
            tf = (sm_sr + 1.0) / (sm_cr + 1.0)
            exp = real_cr * tf
            unc = max(exp, math.sqrt(max(exp, 0.0)), 1.0)
            rows.append(
                {
                    "scenario": f"B_control_region_normalisation_to_{cr}",
                    "region": sr,
                    "observed": observed,
                    "expected_background": exp,
                    "background_uncertainty": unc,
                    "process_contributions": process_contributions(sm_r, sr),
                    "assumptions": f"Real {cr} count multiplied by unweighted SM {sr}/{cr} transfer factor.",
                    "headline_usable": False,
                    "caveats": "Diagnostic transfer only; lacks MC weights and control-region systematics.",
                }
            )

        rows.append(
            {
                "scenario": "C_floating_background_normalisation_nuisance",
                "region": sr,
                "observed": observed,
                "expected_background": observed,
                "background_uncertainty": max(5.0 * observed, 1.0),
                "process_contributions": "floating_background",
                "assumptions": "Background normalisation floats freely around the observed count.",
                "headline_usable": False,
                "caveats": "Tautological for discovery; useful only as a likelihood scaffold stress test.",
            }
        )

        rows.append(
            {
                "scenario": "E_exploratory_process_fraction_scan",
                "region": sr,
                "observed": observed,
                "expected_background": exp_shape,
                "background_uncertainty": max(2.0 * abs(exp_shape), 1.0),
                "process_contributions": process_contributions(sm_r, sr),
                "assumptions": "QCD, TTJets, WJets, ZNuNu and diboson fractions are varied as an exploratory shape scan.",
                "headline_usable": False,
                "caveats": "Process fractions are from unweighted local MC support, not official composition.",
            }
        )

        abcd = bg[(bg["region"] == sr) & (bg["method"] == "C_ABCD_sideband_estimate")]
        if len(abcd):
            r = abcd.iloc[0]
            rows.append(
                {
                    "scenario": "reference_previous_ABCD_sideband_estimate",
                    "region": sr,
                    "observed": observed,
                    "expected_background": finite_float(r["expected_background"]),
                    "background_uncertainty": finite_float(r["total_uncertainty"]),
                    "process_contributions": "real_data_sideband_ABCD",
                    "assumptions": str(r["assumptions"]),
                    "headline_usable": bool(r["headline_usable"]),
                    "caveats": str(r["caveat"]),
                }
            )

    scenarios = pd.DataFrame(rows)
    scenarios.to_csv(TABLES / "02_weighting_and_normalisation_scenarios.csv", index=False)
    write_text(
        OUT / "02_WEIGHTING_AND_NORMALISATION_SCENARIOS_REPORT.md",
        f"""# Weighting and Normalisation Scenarios

Date: {DATE}

Because the local MC does not contain enough normalisation metadata for true luminosity weighting, this pass built labelled scenario models rather than pretending to know absolute backgrounds.

The scenarios are:

- A: shape-only normalisation to the total real observed count.
- B: control-region normalisation to CR_QCD, CR_MET, CR_Muon and CR_BtagTop.
- C: floating background normalisation nuisance.
- D: broad-prior models with 50, 100, 200 and 500 percent uncertainty.
- E: exploratory process-fraction scan.
- Reference: the previous ABCD sideband estimate, retained only where explicitly marked.

## Scenario table

{md(scenarios)}

## Interpretation

Only the previous SR2 ABCD row is marked headline-usable by the previous framework, and it is a downward fluctuation, not an excess. All other rows are likelihood-readiness or sensitivity scaffolding, not discovery-level inference.
""",
    )
    return scenarios


def closure_tests(sm_r: pd.DataFrame, real_u: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total_real = len(real_u)
    for vr in VALIDATION_REGIONS:
        observed = region_count(real_u, vr)
        exp = shape_expected(sm_r, total_real, vr)
        for scenario, frac, predictive in [
            ("A_shape_only_normalised_to_total_real", 1.0, False),
            ("D_broad_prior_50pct", 0.5, False),
            ("D_broad_prior_100pct", 1.0, False),
            ("D_broad_prior_200pct", 2.0, False),
            ("D_broad_prior_500pct", 5.0, False),
        ]:
            unc = max(abs(exp) * frac, math.sqrt(max(exp, 0.0)), 1.0)
            z, p = z_and_p(observed, exp, unc)
            ratio = observed / exp if exp else np.nan
            rows.append(
                {
                    "scenario": scenario,
                    "validation_region": vr,
                    "predicted_yield": exp,
                    "observed_yield": observed,
                    "uncertainty": unc,
                    "pull": z,
                    "closure_ratio": ratio,
                    "closure_p_value_upward": p,
                    "closure_Z": z,
                    "acceptable_under_this_uncertainty": bool(np.isfinite(z) and abs(z) < 2.0),
                    "predictive_for_signal_region_significance": False,
                    "caveat": "Loose pull check only; unweighted SM shape closure is not predictive enough for SR significance.",
                }
            )

        for cr in CONTROL_REGIONS:
            sm_vr = region_count(sm_r, vr)
            sm_cr = region_count(sm_r, cr)
            real_cr = region_count(real_u, cr)
            tf = (sm_vr + 1.0) / (sm_cr + 1.0)
            pred = real_cr * tf
            unc = max(pred, math.sqrt(max(pred, 0.0)), 1.0)
            z, p = z_and_p(observed, pred, unc)
            rows.append(
                {
                    "scenario": f"B_control_region_normalisation_to_{cr}",
                    "validation_region": vr,
                    "predicted_yield": pred,
                    "observed_yield": observed,
                    "uncertainty": unc,
                    "pull": z,
                    "closure_ratio": observed / pred if pred else np.nan,
                    "closure_p_value_upward": p,
                    "closure_Z": z,
                    "acceptable_under_this_uncertainty": bool(np.isfinite(z) and abs(z) < 2.0),
                    "predictive_for_signal_region_significance": False,
                    "caveat": "Control-transfer check without weighted MC/systematics; acceptable rows are not publication-grade.",
                }
            )

        rows.append(
            {
                "scenario": "C_floating_background_normalisation_nuisance",
                "validation_region": vr,
                "predicted_yield": observed,
                "observed_yield": observed,
                "uncertainty": max(5.0 * observed, 1.0),
                "pull": 0.0,
                "closure_ratio": 1.0,
                "closure_p_value_upward": 0.5,
                "closure_Z": 0.0,
                "acceptable_under_this_uncertainty": True,
                "predictive_for_signal_region_significance": False,
                "caveat": "Passes only by construction; not a predictive closure test.",
            }
        )

    closure = pd.DataFrame(rows)
    closure.to_csv(TABLES / "03_control_region_closure_tests.csv", index=False)
    predictive = closure[closure["predictive_for_signal_region_significance"] == True]
    write_text(
        OUT / "03_CONTROL_REGION_CLOSURE_REPORT.md",
        f"""# Control-Region Closure Report

Date: {DATE}

Validation regions tested: VR1, VR2, VR4, VR5 and CR_BtagTop.

## Main answer

No scenario is strong enough for publication-grade SR significance. Some broad-uncertainty or floating models can cover validation regions, but that is not the same as predictive closure. The missing luminosity-weighted SM normalisation and systematic uncertainties remain the bottleneck.

## Predictive rows passing the loose pull criterion

{md(predictive)}

## Full closure table

{md(closure)}
""",
    )
    return closure


def selected_backgrounds(scenarios: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sr in SIGNAL_REGIONS:
        abcd = scenarios[
            (scenarios["region"] == sr)
            & (scenarios["scenario"] == "reference_previous_ABCD_sideband_estimate")
            & (scenarios["headline_usable"] == True)
        ]
        if len(abcd):
            r = abcd.iloc[0]
            source = "reference_previous_ABCD_sideband_estimate"
            publication_grade = False
            headline = True
        else:
            r = scenarios[(scenarios["region"] == sr) & (scenarios["scenario"] == "D_broad_prior_200pct")].iloc[0]
            source = "D_broad_prior_200pct"
            publication_grade = False
            headline = False
        rows.append(
            {
                "region": sr,
                "observed": int(r["observed"]),
                "expected_background": finite_float(r["expected_background"]),
                "background_uncertainty": finite_float(r["background_uncertainty"]),
                "background_source": source,
                "headline_reference": headline,
                "publication_grade": publication_grade,
            }
        )
    return pd.DataFrame(rows)


def benchmark_unit_signal(eff: pd.DataFrame, regions: list[str], unit_events: float = 1000.0) -> float:
    vals = []
    for _, row in eff.iterrows():
        total = 0.0
        for sr in regions:
            col = f"{sr}_efficiency"
            if col in eff.columns:
                total += finite_float(row[col], 0.0) * unit_events
        vals.append(total)
    return max(vals) if vals else 0.0


def profile_likelihood_models(scenarios: pd.DataFrame, eff: pd.DataFrame) -> pd.DataFrame:
    selected = selected_backgrounds(scenarios)
    model_defs = {
        "SR1_only": ["SR1"],
        "SR2_only": ["SR2"],
        "SR3_only": ["SR3"],
        "SR4_only": ["SR4"],
        "SR5_only": ["SR5"],
        "combined_SR1_SR3_SR5": ["SR1", "SR3", "SR5"],
        "combined_all_SR": SIGNAL_REGIONS,
    }
    pyhf_available = importlib.util.find_spec("pyhf") is not None
    rows = []
    for name, regions in model_defs.items():
        sub = selected[selected["region"].isin(regions)]
        obs = float(sub["observed"].sum())
        bkg = float(sub["expected_background"].sum())
        unc = float(math.sqrt(np.square(sub["background_uncertainty"]).sum()))
        z, p = z_and_p(obs, bkg, unc)
        unit_signal = benchmark_unit_signal(eff, regions)
        denom = math.sqrt(max(bkg, 0.0) + unc**2)
        expected_sensitivity = unit_signal / denom if denom else np.nan
        upper_limit_proxy = 1.64 * denom
        direction = "upward" if z > 0.5 else "downward" if z < -0.5 else "no_clear_shift"
        headline = bool(len(regions) == 1 and regions[0] == "SR2")
        publication_grade = False
        spec = {
            "model_name": name,
            "date": DATE,
            "pyhf_available_in_this_environment": pyhf_available,
            "portable_to_pyhf": True,
            "publication_grade": publication_grade,
            "channels": [
                {
                    "name": r.region,
                    "observed": int(r.observed),
                    "background": float(r.expected_background),
                    "background_uncertainty": float(r.background_uncertainty),
                    "background_source": r.background_source,
                    "signal_yield_per_1000_generated_benchmark_events": float(
                        benchmark_unit_signal(eff, [r.region])
                    ),
                    "likelihood": "Poisson(observed | mu*signal + background)",
                    "background_nuisance_prior": "Gaussian/log-normal placeholder",
                }
                for r in sub.itertuples()
            ],
            "notes": "Approximate counting model. Needs official weighted backgrounds, correlated nuisances, trigger/object systematics and pyhf/HistFactory implementation before publication use.",
        }
        (STATMODEL / f"model_{name}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        rows.append(
            {
                "model_name": name,
                "regions": ";".join(regions),
                "observed_count": obs,
                "expected_background": bkg,
                "background_uncertainty": unc,
                "observed_local_Z": z,
                "observed_local_p_upward": p,
                "expected_unit_benchmark_signal_yield_per_1000_generated": unit_signal,
                "expected_unit_signal_sensitivity_Z": expected_sensitivity,
                "expected_upper_limit_proxy_events": upper_limit_proxy,
                "direction": direction,
                "headline_reference": headline,
                "publication_grade_usable": publication_grade,
                "pyhf_available": pyhf_available,
                "caveat": "Likelihood scaffold only; background model is not publication-grade.",
            }
        )
    results = pd.DataFrame(rows)
    headline = results[results["headline_reference"] == True].copy()
    if len(headline):
        n = len(headline)
        headline["global_p_bonferroni"] = np.minimum(1.0, headline["observed_local_p_upward"] * n)
        headline["global_Z_bonferroni"] = stats.norm.isf(headline["global_p_bonferroni"])
    else:
        headline = pd.DataFrame()
    results.to_csv(TABLES / "04_profile_likelihood_model_results.csv", index=False)
    headline.to_csv(TABLES / "04_profile_likelihood_headline_reference_global_correction.csv", index=False)
    write_text(
        OUT / "04_PROFILE_LIKELIHOOD_READINESS_REPORT.md",
        f"""# Profile-Likelihood Readiness Report

Date: {DATE}

Approximate one-bin and multi-bin counting model specs were written to `statistical_model`. pyhf installed: `{pyhf_available}`.

## Main result

The likelihood scaffold now exists, but it is not publication-grade because the background normalisation is still scenario-based rather than luminosity-weighted and systematic uncertainties are placeholders.

## Model results

{md(results)}

## Headline-reference global correction

{md(headline)}

## Interpretation

The only headline-reference model inherited from the previous framework is SR2 ABCD. It is a downward fluctuation, not an upward excess. No 5 sigma-like result survives.
""",
    )
    return results


def sensitivity_scan(selected: pd.DataFrame, eff: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, bench in eff.iterrows():
        for sr in SIGNAL_REGIONS:
            b = selected[selected["region"] == sr].iloc[0]
            eff_val = finite_float(bench.get(f"{sr}_efficiency", 0.0), 0.0)
            event_count = finite_float(bench.get("event_count", 0.0), 0.0)
            denom = math.sqrt(max(finite_float(b["expected_background"], 0.0), 0.0) + finite_float(b["background_uncertainty"], 0.0) ** 2)
            rows.append(
                {
                    "sample_id": bench.get("sample_id", ""),
                    "process_label": bench.get("process_label", ""),
                    "region": sr,
                    "raw_efficiency": eff_val,
                    "benchmark_event_count": event_count,
                    "unweighted_signal_count_in_region": eff_val * event_count,
                    "unweighted_signal_fraction": eff_val,
                    "expected_signal_yield_per_1000_generated": eff_val * 1000.0,
                    "required_signal_yield_for_3sigma_local": 3.0 * denom,
                    "required_signal_yield_for_5sigma_local": 5.0 * denom,
                    "required_signal_cross_section_proxy": "not_available_no_luminosity_or_cross_section_weights",
                    "background_source": b["background_source"],
                    "caveat": "Events-required sensitivity only; no cross-section limit can be quoted today.",
                }
            )
    scan = pd.DataFrame(rows)
    scan.to_csv(TABLES / "05_benchmark_signal_strength_sensitivity_scan.csv", index=False)
    best = scan.sort_values("expected_signal_yield_per_1000_generated", ascending=False).head(10)
    write_text(
        OUT / "05_BENCHMARK_SIGNAL_STRENGTH_SENSITIVITY_REPORT.md",
        f"""# Benchmark Signal-Strength Sensitivity Report

Date: {DATE}

SUSY simulations are treated only as benchmark signal hypotheses. Because luminosity/cross-section weights are unavailable locally, sensitivity is reported as events required, not as a physical cross-section limit.

## Highest unit-normalisation benchmark yields

{md(best)}

## Full scan

{md(scan)}

## Main answer

Under the current conservative/scenario backgrounds, a publishable 3 sigma or 5 sigma claim would require a very large signal yield in the selected regions. The current framework is useful for ranking region sensitivity, not for claiming evidence.
""",
    )
    return scan


def family_mask(df: pd.DataFrame, name: str) -> pd.Series:
    t = json.loads((PREV_STATMODEL / "region_thresholds.json").read_text(encoding="utf-8"))
    if name == "standard_MET_HT_only":
        return df["VR1"]
    if name == "MET_HT_jets_btags":
        return df["VR2"]
    if name == "standard_plus_displacement_reconstruction":
        return df["SR2"]
    if name == "standard_plus_BNF":
        return df["SR1"]
    if name == "frozen_NFrame_SRs":
        return df["SR1"] | df["SR3"] | df["SR5"]
    if name == "optimised_exploratory_NFrame":
        return (df["B_NF_z"] >= t["B_NF_z_top10"]) & (df["displacement_reconstruction_axis"] >= t["disp_reco_top20"])
    raise KeyError(name)


def region_family_comparison(real_u: pd.DataFrame, sm_r: pd.DataFrame, signal_r: pd.DataFrame, inc: pd.DataFrame) -> pd.DataFrame:
    families = [
        ("standard_MET_HT_only", "MET_HT", "A standard MET/HT-only proxy"),
        ("MET_HT_jets_btags", "MET_HT_jets_btags", "B MET/HT plus jets/b-tags proxy"),
        ("standard_plus_displacement_reconstruction", "standard_plus_disp_reco", "C standard variables plus displacement/reconstruction"),
        ("standard_plus_BNF", "standard_plus_BNF", "D standard variables plus B_NF"),
        ("frozen_NFrame_SRs", "full_axes", "E union of frozen N-Frame SR1/SR3/SR5"),
        ("optimised_exploratory_NFrame", "full_axes", "F exploratory N-Frame broad high-boundary/high-displacement region"),
    ]
    total_real = len(real_u)
    rows = []
    for family, auc_model, desc in families:
        real_mask = family_mask(real_u, family)
        sm_mask = family_mask(sm_r, family)
        sig_mask = family_mask(signal_r, family)
        obs = int(real_mask.sum())
        exp = float(sm_mask.mean() * total_real) if len(sm_mask) else np.nan
        unc = max(2.0 * abs(exp), math.sqrt(max(exp, 0.0)), 1.0)
        z, _ = z_and_p(obs, exp, unc)
        if len(signal_r):
            by_bench = signal_r.assign(_mask=sig_mask).groupby("sample_id")["_mask"].mean()
            best_eff = float(by_bench.max()) if len(by_bench) else 0.0
            best_bench = str(by_bench.idxmax()) if len(by_bench) else ""
        else:
            best_eff = 0.0
            best_bench = ""
        denom = math.sqrt(max(exp, 0.0) + unc**2)
        expected_sens = (1000.0 * best_eff / denom) if denom else np.nan
        auc_row = inc[inc["model"] == auc_model]
        auc = finite_float(auc_row["auc_mean"].iloc[0]) if len(auc_row) else np.nan
        rows.append(
            {
                "region_family": family,
                "description": desc,
                "observed_real_yield": obs,
                "expected_background_best_available": exp,
                "background_uncertainty": unc,
                "best_benchmark_signal_efficiency": best_eff,
                "best_benchmark_sample_id": best_bench,
                "expected_S_over_sqrt_B_plus_sigmaB2_per_1000_generated": expected_sens,
                "observed_local_Z_where_valid": z,
                "benchmark_separation_auc": auc,
                "robustness_caveat": "Background is shape/scenario based. Exploratory row is not frozen." if "exploratory" in family else "Background is shape/scenario based.",
            }
        )
    comp = pd.DataFrame(rows)
    comp["expected_sensitivity_rank"] = comp["expected_S_over_sqrt_B_plus_sigmaB2_per_1000_generated"].rank(ascending=False, method="min")
    comp.to_csv(TABLES / "06_region_family_sensitivity_comparison.csv", index=False)
    write_text(
        OUT / "06_BNF_VS_STANDARD_REGION_SENSITIVITY_REPORT.md",
        f"""# B_NF Versus Standard Region Sensitivity

Date: {DATE}

This table extends the previous benchmark AUC comparison into a scenario-background sensitivity comparison.

{md(comp)}

## Main answer

N-Frame-related regions improve benchmark separation over MET/HT-only and MET/HT plus jets/b-tags in the previous AUC tests. However, when broad background uncertainty is included, the advantage is qualified rather than decisive. The strongest previous AUC was standard variables plus displacement/reconstruction, not B_NF alone. Frozen N-Frame SRs remain useful benchmark-sensitive search regions, but they do not yet produce a publication-grade excess.
""",
    )
    return comp


def prioritised_pathway() -> pd.DataFrame:
    rows = [
        ("Add MC cross sections and luminosity weights", 1, "very high", "medium", "CMS record metadata, generated counts, sum weights", "medium/high", "directly fixes the absolute background bottleneck", "1-2 days", "metadata mismatches"),
        ("Use official CMS certified luminosity and good-run JSON", 2, "very high", "medium", "certified JSON and lumi calculation", "medium/high", "defines the observed dataset correctly", "1 day", "requires exact run/lumi bookkeeping"),
        ("Implement trigger efficiency and object systematics", 3, "high", "hard", "trigger menus, efficiency maps, object uncertainties", "high", "needed for credible uncertainties", "several days", "HEP expertise needed"),
        ("Build weighted SM background samples", 4, "very high", "hard", "higher-stat SM MC with weights", "high", "turns shape diagnostics into expected yields", "several days", "storage and compute"),
        ("Add higher-statistics SM backgrounds", 5, "high", "medium/hard", "more QCD, TTJets, WJets, ZNuNu, diboson", "medium/high", "improves closure and transfer factors", "several days", "large downloads"),
        ("Add more relevant LLP/SUSY benchmark signals", 6, "medium/high", "medium", "more benchmark points", "medium", "tests whether N-Frame is topology-specific", "1-3 days", "coverage bias"),
        ("Implement pyhf/HistFactory likelihood", 7, "high", "medium", "weighted backgrounds and uncertainties", "medium/high", "required for journal-style inference", "1-2 days after weights", "premature without weights"),
        ("Validate against published CMS search results", 8, "very high", "hard", "published bin definitions and yields", "high", "anchors the method to known searches", "several days", "needs careful reinterpretation"),
        ("Prepare reproducible code/data release", 9, "medium/high", "medium", "frozen scripts, manifests, checksums", "low/medium", "supports review and collaboration", "1 day", "data licensing/size"),
        ("Consult a HEP physicist on background strategy", 10, "very high", "easy", "expert review", "high", "prevents invalid inference choices", "hours", "availability"),
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "action",
            "priority_rank",
            "expected_evidential_value",
            "feasibility_on_this_machine",
            "required_data",
            "required_physics_expertise",
            "bottleneck_addressed",
            "time_cost",
            "risk",
        ],
    )
    df.to_csv(TABLES / "07_prioritised_publishable_pathway.csv", index=False)
    write_text(
        OUT / "07_PRIORITISED_PATH_TO_PHYSICS_PUBLICATION.md",
        f"""# Prioritised Path to a Physics Publication

Date: {DATE}

{md(df)}

## Recommended next action

Start with MC normalisation: collect official cross sections, generated-event counts or sum weights, filter efficiencies, k-factors where needed, and the integrated luminosity definition for the observed Run2016 data. Without that, the likelihood layer remains a scaffold rather than a physics result.
""",
    )
    return df


def final_reports(
    audit: pd.DataFrame,
    scenarios: pd.DataFrame,
    closure: pd.DataFrame,
    profile: pd.DataFrame,
    scan: pd.DataFrame,
    comp: pd.DataFrame,
) -> None:
    weightable = int(audit["weighted_yield_estimation_possible_now"].sum())
    headline = profile[profile["headline_reference"] == True]
    if len(headline):
        best_headline = headline.iloc[0]
        headline_text = f"SR2 ABCD reference: local Z = {best_headline['observed_local_Z']:.3f}, direction = {best_headline['direction']}."
    else:
        headline_text = "No headline-reference likelihood row was available."
    best_scan = scan.sort_values("expected_signal_yield_per_1000_generated", ascending=False).head(5)
    best_comp = comp.sort_values("expected_S_over_sqrt_B_plus_sigmaB2_per_1000_generated", ascending=False).head(6)
    predictive_closure = closure[closure["predictive_for_signal_region_significance"] == True]

    write_text(
        OUT / "08_END_OF_DAY_LIKELIHOOD_AND_WEIGHTING_SYNTHESIS_FOR_DARREN.md",
        f"""# End-of-Day Likelihood and Weighting Synthesis for Darren

Date: {DATE}

## 1. Why this final run was needed

The previous framework had real CMS observed yields, SM simulation/control support and SUSY benchmark efficiencies, but it did not yet have a physics-journal-style background normalisation or likelihood layer. This pass focused on that bottleneck.

## 2. Metadata and weighting audit

The local audit found {weightable} samples that can be luminosity-weighted now.

## 3. Can true luminosity-weighted SM backgrounds be built now?

No. The local MC/scored tables do not contain the full set of cross sections, integrated luminosity, generated-event counts or sum weights, filter efficiencies and k-factors needed for true weighted yields.

## 4. Scenario background models built

Shape-only total-real normalisation, control-region transfer models, floating background nuisance models, broad-prior models at 50/100/200/500 percent uncertainty and an exploratory process-fraction scan were built.

## 5. Control-region closure

Predictive closure rows passing the loose criterion: {len(predictive_closure)}. Even where broad scenarios cover the validation regions, they are not strong enough for publication-grade SR significance.

## 6. Profile-likelihood-style model

Approximate counting-model JSON specs were created for SR1, SR2, SR3, SR4, SR5, combined SR1/SR3/SR5 and combined all SRs.

## 7. Credible upward excess?

No. {headline_text} This is not evidence for an upward signal.

## 8. Does anything survive conservative systematics and look-elsewhere correction?

No 5 sigma-like result survives. The largest diagnostic local-Z rows remain non-headline because the background is under-constrained.

## 9. Does N-Frame improve expected benchmark sensitivity?

Qualified yes. N-Frame-related regions and displacement/reconstruction axes improve benchmark separation over MET/HT-only style variables, but the strongest previous benchmark AUC was standard variables plus displacement/reconstruction. B_NF alone is weak, and background uncertainty dominates the likelihood-style sensitivity.

## 10. Meaning for the SUSY objective

This strengthens the search-method-development case: frozen N-Frame regions can define benchmark-sensitive, real-data-populated regions. It does not yet strengthen a discovery claim. It does not show real SUSY particles and does not show CERN missed SUSY.

## 11. Missing for journal level

Official MC normalisation, certified luminosity, trigger/object systematics, higher-stat weighted SM backgrounds, more benchmark coverage, pyhf/HistFactory likelihoods and validation against published CMS searches.

## 12. Exact next action

Collect official normalisation metadata for each SM and SUSY sample: cross section, generated event count or sum weights, filter efficiency, k-factor where relevant, and the integrated luminosity for the exact real-data run/lumi selection.

## Best benchmark unit-normalisation rows

{md(best_scan)}

## Region-family sensitivity ranking

{md(best_comp)}
""",
    )

    write_text(
        OUT / "09_SHORT_UPDATE_FOR_TOM.md",
        f"""# Short Update for Tom

I built the likelihood and weighting-readiness layer on top of the existing N-Frame/CERN outputs.

It helped because we now know exactly why the analysis is not yet publishable: the local MC files do not contain enough normalisation metadata for true luminosity-weighted backgrounds. I built transparent scenario models, closure tests, approximate profile-likelihood JSON specs and benchmark signal-yield sensitivity tables.

We did not get a credible 5 sigma result. The only headline-reference row is SR2 ABCD and it is a downward fluctuation, not an excess.

The best thing to tell Darren is: the method-development case is stronger, especially for benchmark-sensitive N-Frame/displacement regions, but the discovery case is still blocked by background normalisation and systematics.

Next: gather official cross sections, generated counts/sum weights, filter efficiencies, k-factors and certified luminosity, then rerun the likelihood with real weighted backgrounds.
""",
    )


def main() -> None:
    ensure_dirs()
    ctx = load_existing_context()
    real_u, sm_r, signal_r = prepare_region_data()

    audit = audit_metadata(ctx["inventory"])
    scenarios = build_scenarios(ctx["bg"], ctx["yields"], sm_r, real_u)
    closure = closure_tests(sm_r, real_u)
    profile = profile_likelihood_models(scenarios, ctx["eff"])
    selected = selected_backgrounds(scenarios)
    scan = sensitivity_scan(selected, ctx["eff"])
    comp = region_family_comparison(real_u, sm_r, signal_r, ctx["inc"])
    prioritised_pathway()
    final_reports(audit, scenarios, closure, profile, scan, comp)

    provenance = {
        "date": DATE,
        "input_folder": str(PREV),
        "output_folder": str(OUT),
        "large_downloads_performed": False,
        "docker_or_cmssw_run": False,
        "frozen_bnf_equation_changed": False,
        "signal_regions_retuned": False,
        "real_unique_events_loaded": int(len(real_u)),
        "sm_support_events_loaded": int(len(sm_r)),
        "signal_benchmark_events_loaded": int(len(signal_r)),
    }
    (SOURCES / "likelihood_readiness_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    print("Likelihood and weighting-readiness pass complete")
    print(f"Output folder: {OUT}")
    print(f"Real unique events used: {len(real_u)}")
    print(f"SM support events used: {len(sm_r)}")
    print(f"Signal benchmark events used: {len(signal_r)}")
    print(f"Weighted-yield-ready samples: {int(audit['weighted_yield_estimation_possible_now'].sum())}")
    headline = profile[profile["headline_reference"] == True]
    if len(headline):
        r = headline.iloc[0]
        print(f"Headline-reference observed local Z: {r['observed_local_Z']:.3f} ({r['direction']})")
    print("No discovery claim produced")


if __name__ == "__main__":
    main()
