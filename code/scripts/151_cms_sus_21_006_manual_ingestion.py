from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml
from scipy import stats
from statsmodels.tools.sm_exceptions import PerfectSeparationError


ROOT = Path(__file__).resolve().parents[1]
MANUAL_YAML = Path(r"D:\Downs\HEPData-ins2705044-v1-Search_region_bins.yaml")
OUT = ROOT / "outputs_today_cms_sus_21_006_manual_ingestion"
TABLES = OUT / "tables"
SOURCES = OUT / "sources"
FIGURES = OUT / "figures"
PREV_DISP = ROOT / "outputs_today_displaced_llp_signal_region_residuals"
PREV_HIGH = ROOT / "outputs_today_high_value_public_results_and_real_validation"
REAL_VALID = ROOT / "outputs_today_frozen_real_data_displacement_validation"
DATE = "2026-06-10"


PROXY_COLS = [
    "P_missing_proxy",
    "P_visible_energy_proxy",
    "P_multiplicity_proxy",
    "P_btag_proxy",
    "P_displacement_or_longlived_proxy",
    "P_reconstruction_stress_proxy",
    "P_compressed_proxy",
    "P_rare_topology_proxy",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, SOURCES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    return view.to_markdown(index=False)


def value_name(dep: dict[str, Any]) -> str:
    return dep.get("header", {}).get("name", "")


def get_error(entry: dict[str, Any]) -> float:
    for err in entry.get("errors", []) or []:
        if "symerror" in err:
            return float(err["symerror"])
        if "asymerror" in err:
            asym = err["asymerror"]
            plus = abs(float(asym.get("plus", 0)))
            minus = abs(float(asym.get("minus", 0)))
            return (plus + minus) / 2
    return np.nan


def verify_and_copy_yaml() -> tuple[dict[str, Any], pd.DataFrame]:
    exists = MANUAL_YAML.exists()
    parse_ok = False
    y: dict[str, Any] = {}
    error = ""
    if exists:
        try:
            y = yaml.safe_load(MANUAL_YAML.read_text(encoding="utf-8"))
            parse_ok = isinstance(y, dict)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    if exists and parse_ok:
        dest = SOURCES / "HEPData-ins2705044-v1-Search_region_bins.yaml"
        shutil.copyfile(MANUAL_YAML, dest)
        prior_pack = PREV_HIGH / "manual_extraction_pack"
        if prior_pack.exists():
            shutil.copyfile(MANUAL_YAML, prior_pack / "HEPData-ins2705044-v1-Search_region_bins.yaml")

    indep = y.get("independent_variables", []) if parse_ok else []
    dep = y.get("dependent_variables", []) if parse_ok else []
    n_bins = len(indep[0].get("values", [])) if indep else 0
    rows = []
    for kind, variables in [("independent", indep), ("dependent", dep)]:
        for i, var in enumerate(variables):
            vals = var.get("values", [])
            rows.append(
                {
                    "kind": kind,
                    "index": i,
                    "name": value_name(var),
                    "values": len(vals),
                    "first_values": json.dumps(vals[:3]),
                    "has_errors": any("errors" in v for v in vals[:10]),
                    "error_labels": "; ".join(
                        sorted(
                            {
                                e.get("label", "")
                                for v in vals
                                for e in (v.get("errors", []) or [])
                                if e.get("label")
                            }
                        )
                    ),
                }
            )
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "01_manual_yaml_structure_summary.csv", index=False)
    write_text(
        OUT / "01_MANUAL_YAML_VERIFICATION_REPORT.md",
        "\n".join(
            [
                "# Manual YAML Verification Report",
                "",
                f"Date: {DATE}",
                "",
                f"Manual file: `{MANUAL_YAML}`",
                f"File exists: {exists}",
                f"YAML parsing succeeded: {parse_ok}",
                f"Parsing error: {error or 'none'}",
                f"Bins found: {n_bins}",
                "",
                "The table contains one independent variable (`bin value`) and five dependent variables. The observed real-data count is `Number of observed events`; the expected Standard Model background is `Number of background events`; the total uncertainty is the `total uncertainty` error on the background variable.",
                "",
                "The YAML does not include fine category labels for jets, b-tags, leptons, hard MET, or track category. Proxy coding for CMS-SUS-21-006 therefore uses conservative analysis-level disappearing-track scores plus a clearly labelled exploratory bin-order rank.",
                "",
                md(summary),
            ]
        ),
    )
    return y, summary


def parse_49bin(y: dict[str, Any]) -> pd.DataFrame:
    indep = y["independent_variables"][0]["values"]
    deps = {value_name(dep): dep["values"] for dep in y["dependent_variables"]}
    bg = deps["Number of background events"]
    obs = deps["Number of observed events"]
    prompt_shower = deps.get("Number of prompt showering events", [{}] * len(indep))
    spurious = deps.get("Number of spurious events", [{}] * len(indep))
    prompt_mip = deps.get("Number of prompt MIP events", [{}] * len(indep))
    rows = []
    for i, bin_entry in enumerate(indep):
        idx = int(bin_entry["value"])
        rows.append(
            {
                "analysis_id": "CMS-SUS-21-006",
                "experiment": "CMS",
                "paper_title_short": "CMS disappearing tracks",
                "year": 2024,
                "table_name": "Search region bins",
                "signal_region": f"SR{idx:02d}",
                "search_region_index": idx,
                "observed": float(obs[i]["value"]),
                "expected": float(bg[i]["value"]),
                "expected_uncertainty": get_error(bg[i]),
                "uncertainty_type": "published total uncertainty on Number of background events",
                "final_state": "disappearing tracks",
                "raw_label": f"Search region bin {idx}",
                "raw_bin_description": f"HEPData table 13 bin value {idx}; category labels not included in YAML",
                "track_category": "",
                "jets_category": "",
                "btag_category": "",
                "lepton_category": "",
                "hard_met_category": "",
                "prompt_showering_background": float(prompt_shower[i].get("value", np.nan)),
                "spurious_background": float(spurious[i].get("value", np.nan)),
                "prompt_mip_background": float(prompt_mip[i].get("value", np.nan)),
                "source_url_or_reference": "https://www.hepdata.net/record/150650; https://doi.org/10.17182/hepdata.144178.v1/t13",
                "extraction_notes": "Parsed from manually downloaded HEPData YAML. Only observed real-data and SM background summary columns used.",
                "extraction_quality": "high for observed/background values; category labels absent from YAML",
                "analysis_group": "displaced_llp",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "02_cms_sus_21_006_49bin_parsed.csv", index=False)
    write_text(
        OUT / "02_CMS_SUS_21_006_49BIN_PARSING_REPORT.md",
        "\n".join(
            [
                "# CMS-SUS-21-006 49-Bin Parsing Report",
                "",
                f"Date: {DATE}",
                "",
                f"Rows parsed: {len(df)}.",
                "",
                "Parsed fields: observed count from `Number of observed events`; expected background from `Number of background events`; uncertainty from its `total uncertainty` symerror.",
                "",
                "Simulated signal-yield and model-limit tables were not used.",
                "",
                "Category limitation: the YAML only gives bin values 1-49 and background component counts. It does not expose the detailed category labels. The main proxy coding therefore treats the disappearing-track topology as an analysis-level feature and treats bin-order tests as exploratory.",
                "",
                md(df.head(10)),
            ]
        ),
    )
    return df


def combine_with_previous(new: pd.DataFrame) -> pd.DataFrame:
    prev = pd.read_csv(PREV_DISP / "tables" / "07_displaced_llp_boundary_proxy_scores.csv")
    for col in prev.columns:
        if col not in new:
            new[col] = np.nan
    for col in new.columns:
        if col not in prev:
            prev[col] = np.nan
    combined = pd.concat([prev, new[prev.columns]], ignore_index=True)
    # Remove residual/proxy scores; recompute from clean raw fields.
    combined.to_csv(TABLES / "03_combined_public_signal_regions_with_cms_sus_21_006.csv", index=False)
    summary = pd.DataFrame(
        [
            {"metric": "total_rows", "value": len(combined)},
            {"metric": "analyses", "value": combined["analysis_id"].nunique()},
            {"metric": "ordinary_jets_met_rows", "value": int((combined["analysis_group"] != "displaced_llp").sum())},
            {"metric": "displaced_llp_disappearing_rows", "value": int((combined["analysis_group"] == "displaced_llp").sum())},
            {"metric": "cms_sus_21_006_rows", "value": int((combined["analysis_id"] == "CMS-SUS-21-006").sum())},
            {"metric": "observed_complete", "value": bool(combined["observed"].notna().all())},
            {"metric": "expected_complete", "value": bool(combined["expected"].notna().all())},
            {"metric": "uncertainty_complete", "value": bool(combined["expected_uncertainty"].notna().all())},
        ]
    )
    write_text(
        OUT / "03_COMBINED_PUBLIC_DATASET_REPORT.md",
        "\n".join(
            [
                "# Combined Public Dataset Report",
                "",
                f"Date: {DATE}",
                "",
                "The previous 180-row public dataset was combined with 49 manually ingested CMS-SUS-21-006 disappearing-track bins.",
                "",
                md(summary),
            ]
        ),
    )
    return combined


def compute_residuals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["observed", "expected", "expected_uncertainty"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["residual"] = out["observed"] - out["expected"]
    out["residual_denominator"] = np.sqrt(np.maximum(out["expected"], 0) + out["expected_uncertainty"].fillna(0) ** 2)
    no_unc = out["expected_uncertainty"].isna()
    out.loc[no_unc, "residual_denominator"] = np.sqrt(np.maximum(out.loc[no_unc, "expected"], 1e-9))
    out["Z_residual"] = out["residual"] / out["residual_denominator"].replace(0, np.nan)
    out["abs_Z_residual"] = out["Z_residual"].abs()
    out["positive_residual"] = out["residual"] > 0
    out["large_upward_fluctuation"] = out["Z_residual"] > 1
    out["upward_fluctuation_p_approx"] = stats.norm.sf(out["Z_residual"])
    out["two_sided_residual_p_approx"] = 2 * stats.norm.sf(out["abs_Z_residual"])
    out.to_csv(TABLES / "04_combined_public_signal_region_residuals.csv", index=False)
    by_analysis = out.groupby("analysis_id").agg(
        rows=("signal_region", "count"),
        positive_residuals=("positive_residual", "sum"),
        mean_signed_Z=("Z_residual", "mean"),
        mean_abs_Z=("abs_Z_residual", "mean"),
        max_signed_Z=("Z_residual", "max"),
        min_signed_Z=("Z_residual", "min"),
    ).reset_index()
    write_text(
        OUT / "04_COMBINED_RESIDUAL_CALCULATION_REPORT.md",
        "\n".join(
            [
                "# Combined Residual Calculation Report",
                "",
                f"Date: {DATE}",
                "",
                "Residuals use observed minus expected, with denominator sqrt(expected + uncertainty^2) where uncertainty is present.",
                "",
                md(by_analysis),
            ]
        ),
    )
    return out


def code_proxies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in PROXY_COLS:
        out[col] = pd.to_numeric(out.get(col, 0.0), errors="coerce").fillna(0.0)

    is_cms_sus = out["analysis_id"] == "CMS-SUS-21-006"
    out.loc[is_cms_sus, "P_displacement_or_longlived_proxy"] = 3.0
    out.loc[is_cms_sus, "P_reconstruction_stress_proxy"] = 3.0
    out.loc[is_cms_sus, "P_rare_topology_proxy"] = 3.0
    out.loc[is_cms_sus, "P_compressed_proxy"] = 2.0
    out.loc[is_cms_sus, "P_missing_proxy"] = 2.0
    out.loc[is_cms_sus, "P_visible_energy_proxy"] = 1.0
    out.loc[is_cms_sus, "P_multiplicity_proxy"] = 1.0
    out.loc[is_cms_sus, "P_btag_proxy"] = 0.0
    out.loc[is_cms_sus, "cms_sus_21_006_bin_order_rank"] = out.loc[is_cms_sus, "search_region_index"].rank(pct=True)
    out["cms_sus_21_006_bin_order_rank"] = out["cms_sus_21_006_bin_order_rank"].fillna(0.0)

    out["Published_BNF_proxy_simple"] = (
        out["P_missing_proxy"]
        + out["P_visible_energy_proxy"]
        + out["P_multiplicity_proxy"]
        + out["P_btag_proxy"]
        + out["P_displacement_or_longlived_proxy"]
        + out["P_reconstruction_stress_proxy"]
        + out["P_compressed_proxy"]
        + out["P_rare_topology_proxy"]
    )
    out["Published_BNF_proxy_weighted"] = (
        0.3566 * out["P_displacement_or_longlived_proxy"]
        + 0.2112 * out["P_reconstruction_stress_proxy"]
        + 0.2019 * out["P_multiplicity_proxy"]
        + 0.0926 * out["P_btag_proxy"]
        + 0.0728 * out["P_visible_energy_proxy"]
        + 0.0595 * out["P_missing_proxy"]
        + 0.0055 * out["P_compressed_proxy"]
    )
    out["Published_BNF_displacement_reconstruction"] = (
        out["P_displacement_or_longlived_proxy"] + out["P_reconstruction_stress_proxy"]
    )
    out["Published_BNF_missing_visible"] = out["P_missing_proxy"] + out["P_visible_energy_proxy"]
    out["Published_hidden_topology_proxy"] = (
        out["P_displacement_or_longlived_proxy"] + out["P_compressed_proxy"] + out["P_rare_topology_proxy"]
    )
    score_cols = [
        "Published_BNF_proxy_simple",
        "Published_BNF_proxy_weighted",
        "Published_BNF_displacement_reconstruction",
        "Published_BNF_missing_visible",
        "Published_hidden_topology_proxy",
    ]
    for col in score_cols:
        out[f"{col}_rank_within_analysis"] = out.groupby("analysis_id")[col].rank(pct=True)
        out[f"{col}_z_within_analysis"] = out.groupby("analysis_id")[col].transform(
            lambda s: (s - s.mean()) / s.std(ddof=0) if len(s) > 1 and s.std(ddof=0) else 0.0
        )
    component_cols = [
        "analysis_id",
        "signal_region",
        "search_region_index",
        "raw_label",
        *PROXY_COLS,
        "cms_sus_21_006_bin_order_rank",
    ]
    out[component_cols].to_csv(TABLES / "05_combined_boundary_proxy_components.csv", index=False)
    out.to_csv(TABLES / "06_combined_boundary_proxy_scores.csv", index=False)
    write_text(
        OUT / "05_BOUNDARY_PROXY_CODING_WITH_CMS_SUS_21_006_REPORT.md",
        "\n".join(
            [
                "# Boundary Proxy Coding With CMS-SUS-21-006",
                "",
                f"Date: {DATE}",
                "",
                "CMS-SUS-21-006 rows were coded with high displacement/long-lived, reconstruction-stress, and rare-topology proxy values because disappearing tracks are explicit long-lived/reconstruction-sensitive signatures.",
                "",
                "The YAML does not include detailed bin category labels, so MET, visible-energy, multiplicity, and b-tag proxies are conservative analysis-level values. Fine-grained bin-index order is included only as `cms_sus_21_006_bin_order_rank` and treated as exploratory, not as part of the frozen B_NF proxy.",
                "",
                md(out[out["analysis_id"] == "CMS-SUS-21-006"][component_cols].head(10)),
            ]
        ),
    )
    write_text(
        OUT / "06_PUBLISHED_BNF_PROXY_WITH_CMS_SUS_21_006_REPORT.md",
        "\n".join(
            [
                "# Published BNF Proxy With CMS-SUS-21-006",
                "",
                f"Date: {DATE}",
                "",
                "These are public signal-region proxies, not event-level B_NF values. The frozen event-level weights are used only to build the weighted proxy from published labels.",
                "",
                md(out.groupby("analysis_id")[score_cols].mean().reset_index()),
            ]
        ),
    )
    return out


def spearman(df: pd.DataFrame, outcome: str, pred: str, label: str) -> dict[str, Any]:
    work = df[[outcome, pred]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < 5 or work[outcome].nunique() < 2 or work[pred].nunique() < 2:
        return {"model": f"spearman_{label}_{outcome}_vs_{pred}", "status": "not_run", "outcome": outcome, "predictors": pred, "n": len(work), "reason": "too few rows or no variation"}
    rho, p = stats.spearmanr(work[pred], work[outcome])
    return {"model": f"spearman_{label}_{outcome}_vs_{pred}", "status": "run", "outcome": outcome, "predictors": pred, "n": len(work), "primary_term": pred, "primary_estimate": rho, "primary_p_value": p, "reason": ""}


def ols(df: pd.DataFrame, outcome: str, preds: list[str], label: str) -> dict[str, Any]:
    work = df[[outcome] + preds].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < len(preds) + 5 or any(work[p].nunique() < 2 for p in preds):
        return {"model": label, "status": "not_run", "outcome": outcome, "predictors": " + ".join(preds), "n": len(work), "reason": "too few rows or no predictor variation"}
    x = sm.add_constant(work[preds].astype(float), has_constant="add")
    y = work[outcome].astype(float)
    fit = sm.OLS(y, x).fit(cov_type="HC3")
    key = preds[-1]
    ci = fit.conf_int()
    return {
        "model": label,
        "status": "run",
        "outcome": outcome,
        "predictors": " + ".join(preds),
        "n": len(work),
        "primary_term": key,
        "primary_estimate": fit.params.get(key, np.nan),
        "primary_p_value": fit.pvalues.get(key, np.nan),
        "primary_ci_low": ci.loc[key, 0] if key in ci.index else np.nan,
        "primary_ci_high": ci.loc[key, 1] if key in ci.index else np.nan,
        "r_squared": fit.rsquared,
        "aic": fit.aic,
        "reason": "",
    }


def logit(df: pd.DataFrame, outcome: str, preds: list[str], label: str) -> dict[str, Any]:
    work = df[[outcome] + preds].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < len(preds) + 10 or work[outcome].nunique() < 2 or any(work[p].nunique() < 2 for p in preds):
        return {"model": label, "status": "not_run", "outcome": outcome, "predictors": " + ".join(preds), "n": len(work), "reason": "too few rows, no class variation, or no predictor variation"}
    x = sm.add_constant(work[preds].astype(float), has_constant="add")
    y = work[outcome].astype(int)
    try:
        fit = sm.Logit(y, x).fit(disp=False, maxiter=200)
    except (PerfectSeparationError, np.linalg.LinAlgError, ValueError) as exc:
        return {"model": label, "status": "not_run", "outcome": outcome, "predictors": " + ".join(preds), "n": len(work), "reason": f"logit failed: {exc}"}
    key = preds[-1]
    ci = fit.conf_int()
    return {
        "model": label,
        "status": "run",
        "outcome": outcome,
        "predictors": " + ".join(preds),
        "n": len(work),
        "primary_term": key,
        "primary_estimate": fit.params.get(key, np.nan),
        "primary_p_value": fit.pvalues.get(key, np.nan),
        "primary_ci_low": ci.loc[key, 0] if key in ci.index else np.nan,
        "primary_ci_high": ci.loc[key, 1] if key in ci.index else np.nan,
        "pseudo_r_squared": fit.prsquared,
        "aic": fit.aic,
        "reason": "",
    }


def bh_adjust(p: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=p.index, dtype=float)
    valid = p.astype(float).dropna().sort_values()
    if valid.empty:
        return out
    adj = valid * len(valid) / np.arange(1, len(valid) + 1)
    adj = adj.iloc[::-1].cummin().iloc[::-1].clip(upper=1)
    out.loc[adj.index] = adj
    return out


def run_models(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictors = [
        "Published_BNF_proxy_weighted",
        "Published_BNF_proxy_simple",
        "Published_BNF_displacement_reconstruction",
        "Published_hidden_topology_proxy",
        "Published_BNF_missing_visible",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
        "cms_sus_21_006_bin_order_rank",
    ]
    groups = {
        "all": df,
        "displaced_llp_only": df[df["analysis_group"] == "displaced_llp"],
        "cms_sus_21_006_only": df[df["analysis_id"] == "CMS-SUS-21-006"],
        "jets_met_comparator": df[df["analysis_group"] != "displaced_llp"],
        "cms_only": df[df["experiment"] == "CMS"],
    }
    rows = []
    for group_name, sub in groups.items():
        for pred in predictors:
            for outcome in ["abs_Z_residual", "Z_residual", "positive_residual", "large_upward_fluctuation"]:
                rows.append(spearman(sub, outcome, pred, group_name))
    rows += [
        ols(df, "abs_Z_residual", ["Published_BNF_proxy_weighted"], "ols_all_absZ_weighted"),
        ols(df, "Z_residual", ["Published_BNF_proxy_weighted"], "ols_all_signedZ_weighted"),
        logit(df, "positive_residual", ["Published_BNF_proxy_weighted"], "logit_all_positive_weighted"),
        ols(df, "Z_residual", ["Published_BNF_displacement_reconstruction"], "ols_all_signedZ_disp_reco"),
        logit(df, "positive_residual", ["Published_BNF_displacement_reconstruction"], "logit_all_positive_disp_reco"),
        ols(df[df["analysis_group"] == "displaced_llp"], "Z_residual", ["Published_BNF_displacement_reconstruction"], "ols_displaced_only_signedZ_disp_reco"),
        ols(df[df["analysis_id"] == "CMS-SUS-21-006"], "Z_residual", ["cms_sus_21_006_bin_order_rank"], "ols_cms_sus_21_006_signedZ_bin_order"),
        logit(df[df["analysis_id"] == "CMS-SUS-21-006"], "positive_residual", ["cms_sus_21_006_bin_order_rank"], "logit_cms_sus_21_006_positive_bin_order"),
    ]
    model_df = pd.DataFrame(rows)
    # BH correction over primary Spearman tests.
    mask = model_df["model"].str.startswith("spearman")
    model_df.loc[mask, "bh_adjusted_p"] = bh_adjust(model_df.loc[mask, "primary_p_value"])
    model_df.to_csv(TABLES / "07_residual_model_results_with_cms_sus_21_006.csv", index=False)

    within = []
    for aid, sub in df.groupby("analysis_id"):
        for pred in [
            "Published_BNF_displacement_reconstruction",
            "Published_BNF_proxy_weighted",
            "Published_hidden_topology_proxy",
            "Published_BNF_missing_visible",
            "cms_sus_21_006_bin_order_rank",
        ]:
            for outcome in ["abs_Z_residual", "Z_residual", "positive_residual"]:
                within.append(spearman(sub, outcome, pred, aid))
    within_df = pd.DataFrame(within)
    within_df.to_csv(TABLES / "07_within_analysis_rank_tests_with_cms_sus_21_006.csv", index=False)

    inc_rows = [
        ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "baseline_absZ_missing_visible"),
        ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"], "augmented_absZ_missing_visible_plus_weighted"),
        ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "P_displacement_or_longlived_proxy", "P_reconstruction_stress_proxy"], "specific_absZ_missing_visible_plus_disp_reco"),
        ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_hidden_topology_proxy"], "hidden_absZ_missing_visible_plus_hidden_topology"),
        ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "baseline_signedZ_missing_visible"),
        ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"], "augmented_signedZ_missing_visible_plus_weighted"),
        ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "P_displacement_or_longlived_proxy", "P_reconstruction_stress_proxy"], "specific_signedZ_missing_visible_plus_disp_reco"),
        ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_hidden_topology_proxy"], "hidden_signedZ_missing_visible_plus_hidden_topology"),
    ]
    inc = pd.DataFrame(inc_rows)
    for outcome_prefix, base_name in [("absZ", "baseline_absZ_missing_visible"), ("signedZ", "baseline_signedZ_missing_visible")]:
        base = inc[inc["model"] == base_name]
        if not base.empty and base.iloc[0].get("status") == "run":
            base_r2 = base.iloc[0].get("r_squared", np.nan)
            base_aic = base.iloc[0].get("aic", np.nan)
            mask2 = inc["model"].str.contains(outcome_prefix, regex=False) & ~inc["model"].eq(base_name)
            inc.loc[mask2, "delta_r_squared_vs_missing_visible"] = inc.loc[mask2, "r_squared"] - base_r2
            inc.loc[mask2, "delta_aic_vs_missing_visible"] = inc.loc[mask2, "aic"] - base_aic
    inc.to_csv(TABLES / "07_incrementality_tests_with_cms_sus_21_006.csv", index=False)

    sens_rows = []
    sens_groups = {
        "all": df,
        "remove_jets_met_comparator": df[df["analysis_group"] == "displaced_llp"],
        "cms_sus_21_006_only": df[df["analysis_id"] == "CMS-SUS-21-006"],
        "displaced_llp_only": df[df["analysis_group"] == "displaced_llp"],
        "expected_at_least_1": df[df["expected"] >= 1],
        "expected_at_least_5": df[df["expected"] >= 5],
    }
    for name, sub in sens_groups.items():
        for pred in ["Published_BNF_proxy_weighted", "Published_BNF_displacement_reconstruction", "Published_hidden_topology_proxy", "cms_sus_21_006_bin_order_rank"]:
            for outcome in ["abs_Z_residual", "Z_residual", "positive_residual"]:
                r = spearman(sub, outcome, pred, name)
                sens_rows.append(
                    {
                        "check": name,
                        "predictor": pred,
                        "outcome": outcome,
                        "n": r.get("n"),
                        "effect": r.get("primary_estimate", np.nan),
                        "p_value": r.get("primary_p_value", np.nan),
                        "bh_adjusted_p": np.nan,
                        "interpretation": r.get("reason", ""),
                    }
                )
    for aid in df["analysis_id"].dropna().unique():
        sub = df[df["analysis_id"] != aid]
        r = spearman(sub, "Z_residual", "Published_BNF_displacement_reconstruction", f"drop_{aid}")
        sens_rows.append({"check": f"leave_one_analysis_out_drop_{aid}", "predictor": "Published_BNF_displacement_reconstruction", "outcome": "Z_residual", "n": r.get("n"), "effect": r.get("primary_estimate", np.nan), "p_value": r.get("primary_p_value", np.nan), "bh_adjusted_p": np.nan, "interpretation": r.get("reason", "")})
    sens = pd.DataFrame(sens_rows)
    sens["bh_adjusted_p"] = bh_adjust(sens["p_value"])
    sens.to_csv(TABLES / "08_sensitivity_and_negative_controls_with_cms_sus_21_006.csv", index=False)

    headline = model_df[model_df["model"].isin([
        "spearman_all_Z_residual_vs_Published_BNF_displacement_reconstruction",
        "spearman_all_positive_residual_vs_Published_BNF_displacement_reconstruction",
        "spearman_displaced_llp_only_Z_residual_vs_Published_BNF_displacement_reconstruction",
        "spearman_displaced_llp_only_positive_residual_vs_Published_BNF_displacement_reconstruction",
        "spearman_cms_sus_21_006_only_Z_residual_vs_cms_sus_21_006_bin_order_rank",
        "spearman_cms_sus_21_006_only_positive_residual_vs_cms_sus_21_006_bin_order_rank",
    ])]
    write_text(
        OUT / "07_PUBLIC_RESIDUAL_MODELLING_WITH_CMS_SUS_21_006_REPORT.md",
        "\n".join(
            [
                "# Public Residual Modelling With CMS-SUS-21-006",
                "",
                f"Date: {DATE}",
                "",
                "The main displacement/reconstruction proxies are constant within CMS-SUS-21-006 because the YAML lacks detailed category labels. Therefore, CMS-SUS-21-006-only proxy tests use bin-order rank as exploratory only.",
                "",
                "Headline tests:",
                "",
                md(headline),
                "",
                "Incrementality:",
                "",
                md(inc),
            ]
        ),
    )
    write_text(
        OUT / "08_SENSITIVITY_WITH_CMS_SUS_21_006_REPORT.md",
        "\n".join(
            [
                "# Sensitivity With CMS-SUS-21-006",
                "",
                f"Date: {DATE}",
                "",
                md(sens),
            ]
        ),
    )
    return model_df, within_df, inc, sens


def make_figures(df: pd.DataFrame) -> None:
    cms = df[df["analysis_id"] == "CMS-SUS-21-006"].copy()
    if not cms.empty:
        plt.figure(figsize=(7, 4))
        plt.bar(cms["search_region_index"], cms["Z_residual"])
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xlabel("CMS-SUS-21-006 search-region bin")
        plt.ylabel("Signed residual Z")
        plt.tight_layout()
        plt.savefig(FIGURES / "cms_sus_21_006_signed_residual_by_bin.png", dpi=160)
        plt.close()

    plt.figure(figsize=(7, 5))
    colours = np.where(df["analysis_id"].eq("CMS-SUS-21-006"), "tab:red", np.where(df["analysis_group"].eq("displaced_llp"), "tab:orange", "tab:blue"))
    plt.scatter(df["Published_BNF_displacement_reconstruction"], df["Z_residual"], c=colours, alpha=0.75)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Published displacement/reconstruction proxy")
    plt.ylabel("Signed residual Z")
    plt.tight_layout()
    plt.savefig(FIGURES / "combined_disp_reco_proxy_vs_signed_residual.png", dpi=160)
    plt.close()


def integrated_reports(df: pd.DataFrame, model_df: pd.DataFrame, inc: pd.DataFrame, sens: pd.DataFrame) -> dict[str, Any]:
    cms = df[df["analysis_id"] == "CMS-SUS-21-006"]
    disp = df[df["analysis_group"] == "displaced_llp"]
    def get(model: str, field: str) -> float:
        row = model_df[model_df["model"] == model]
        return float(row.iloc[0].get(field, np.nan)) if not row.empty else np.nan

    cms_bin_signed = get("spearman_cms_sus_21_006_only_Z_residual_vs_cms_sus_21_006_bin_order_rank", "primary_estimate")
    cms_bin_signed_p = get("spearman_cms_sus_21_006_only_Z_residual_vs_cms_sus_21_006_bin_order_rank", "primary_p_value")
    cms_bin_pos = get("spearman_cms_sus_21_006_only_positive_residual_vs_cms_sus_21_006_bin_order_rank", "primary_estimate")
    cms_bin_pos_p = get("spearman_cms_sus_21_006_only_positive_residual_vs_cms_sus_21_006_bin_order_rank", "primary_p_value")
    disp_signed = get("spearman_displaced_llp_only_Z_residual_vs_Published_BNF_displacement_reconstruction", "primary_estimate")
    disp_signed_p = get("spearman_displaced_llp_only_Z_residual_vs_Published_BNF_displacement_reconstruction", "primary_p_value")
    disp_pos = get("spearman_displaced_llp_only_positive_residual_vs_Published_BNF_displacement_reconstruction", "primary_estimate")
    disp_pos_p = get("spearman_displaced_llp_only_positive_residual_vs_Published_BNF_displacement_reconstruction", "primary_p_value")
    signed_aug = inc[inc["model"] == "specific_signedZ_missing_visible_plus_disp_reco"]
    delta_signed = float(signed_aug.iloc[0].get("delta_r_squared_vs_missing_visible", np.nan)) if not signed_aug.empty else np.nan

    real_summary = ""
    real_report = REAL_VALID / "07_FROZEN_REAL_DATA_DISPLACEMENT_VALIDATION_SYNTHESIS_FOR_DARREN.md"
    if real_report.exists():
        real_summary = "Real-data sideband validation already found that high displacement/reconstruction but low missing/visible structure replicated across Run2016G and Run2016H, combined n = 14,797, with delta R2 about 0.476 and delta AUC about 0.125. This remains a real-data boundary validation result, not SUSY evidence."

    if not np.isnan(cms_bin_signed_p) and cms_bin_signed_p < 0.05 and cms_bin_signed > 0:
        judgement = "strengthens_with_caveats"
        interp = "CMS-SUS-21-006 shows an exploratory positive signed-residual alignment with bin order, while the combined displacement-aware public dataset is now much less underpowered. Because detailed category labels are absent, this is suggestive rather than decisive."
    elif cms["Z_residual"].mean() > 0 and cms["positive_residual"].mean() > 0.5:
        judgement = "qualifies_mixed"
        interp = "CMS-SUS-21-006 adds many disappearing-track rows with a mild positive residual tendency, but the available YAML lacks category labels, so it does not prove a fine-grained displacement/reconstruction proxy relationship."
    else:
        judgement = "qualifies_or_weakens_public_bridge"
        interp = "CMS-SUS-21-006 does not show a strong public disappearing-track residual bridge using the available YAML fields, though the real-data boundary validation remains useful."

    cms_summary = pd.DataFrame(
        [
            {
                "rows": len(cms),
                "positive_residuals": int(cms["positive_residual"].sum()),
                "positive_fraction": cms["positive_residual"].mean(),
                "mean_signed_Z": cms["Z_residual"].mean(),
                "mean_abs_Z": cms["abs_Z_residual"].mean(),
                "max_signed_Z": cms["Z_residual"].max(),
                "min_signed_Z": cms["Z_residual"].min(),
            }
        ]
    )
    write_text(
        OUT / "09_INTEGRATED_PUBLIC_AND_REAL_DATA_SYNTHESIS_FOR_DARREN.md",
        "\n".join(
            [
                "# Integrated Public and Real-Data Synthesis for Darren",
                "",
                f"Date: {DATE}",
                "",
                "## Manual CMS-SUS-21-006 ingestion",
                "",
                "The manually downloaded HEPData YAML was successfully parsed. It added 49 disappearing-track search-region bins with observed real-data counts, expected SM background counts, and total background uncertainties.",
                "",
                md(cms_summary),
                "",
                "## Public residual result",
                "",
                f"CMS-SUS-21-006 exploratory bin-order vs signed residual: rho = {cms_bin_signed:.4g}, p = {cms_bin_signed_p:.4g}.",
                f"CMS-SUS-21-006 exploratory bin-order vs positive residual: rho = {cms_bin_pos:.4g}, p = {cms_bin_pos_p:.4g}.",
                f"All displaced/LLP rows displacement/reconstruction vs signed residual: rho = {disp_signed:.4g}, p = {disp_signed_p:.4g}.",
                f"All displaced/LLP rows displacement/reconstruction vs positive residual: rho = {disp_pos:.4g}, p = {disp_pos_p:.4g}.",
                f"Signed-residual delta R2 adding displacement/reconstruction beyond missing/visible: {delta_signed:.4g}.",
                "",
                "Important limitation: the YAML exposes bin numbers but not detailed category labels. Therefore, the CMS-SUS-21-006-only tests are bin-order exploratory tests, not definitive category-level topology tests.",
                "",
                "## Real-data sideband validation",
                "",
                real_summary,
                "",
                "## Interpretation",
                "",
                interp,
                "",
                f"Overall judgement: {judgement}.",
                "",
                "This is not a SUSY discovery claim and not proof that CERN missed SUSY. It is a public disappearing-track residual test paired with real-data boundary validation.",
                "",
                "## Exact next action",
                "",
                "Get or reconstruct the CMS-SUS-21-006 category map for bins 1-49. With real category labels, rerun the same residual model using proper per-bin jets/b-tags/leptons/hard-MET/track-category proxies instead of the current analysis-level proxy plus exploratory bin order.",
            ]
        ),
    )
    write_text(
        OUT / "10_SHORT_UPDATE_FOR_TOM.md",
        "\n".join(
            [
                "# Short Update for Tom",
                "",
                "The manually downloaded CMS-SUS-21-006 HEPData YAML worked. I parsed all 49 disappearing-track search-region bins and added them to the public residual model.",
                "",
                f"CMS-SUS-21-006 has {int(cms['positive_residual'].sum())} positive residual bins out of {len(cms)}, with mean signed Z = {cms['Z_residual'].mean():.3f}.",
                "",
                "The main caveat is that the YAML only gives bin numbers, not the full category labels. So the disappearing-track topology is coded at analysis level, and bin-order tests are exploratory.",
                "",
                f"Overall: {interp}",
                "",
                "What to tell Darren: the public disappearing-track residual layer is now no longer blocked, but the next improvement is to get the bin-category map so we can test proper per-bin boundary proxies.",
            ]
        ),
    )
    return {
        "judgement": judgement,
        "cms_rows": len(cms),
        "total_rows": len(df),
        "disp_rows": len(disp),
        "cms_positive": int(cms["positive_residual"].sum()),
        "cms_mean_signed_z": float(cms["Z_residual"].mean()),
        "cms_bin_signed": cms_bin_signed,
        "cms_bin_signed_p": cms_bin_signed_p,
        "delta_signed": delta_signed,
    }


def main() -> None:
    ensure_dirs()
    y, _ = verify_and_copy_yaml()
    parsed = parse_49bin(y)
    combined = combine_with_previous(parsed)
    residuals = compute_residuals(combined)
    scored = code_proxies(residuals)
    model_df, within_df, inc, sens = run_models(scored)
    make_figures(scored)
    result = integrated_reports(scored, model_df, inc, sens)
    print("CMS-SUS-21-006 manual ingestion complete")
    print(f"Output folder: {OUT}")
    print(f"Manual YAML found and parsed: {MANUAL_YAML.exists()}")
    print(f"CMS-SUS-21-006 rows ingested: {result['cms_rows']}")
    print(f"Total public rows: {result['total_rows']}")
    print(f"Displaced/LLP/disappearing rows: {result['disp_rows']}")
    print(f"CMS-SUS-21-006 positive residuals: {result['cms_positive']}/{result['cms_rows']}")
    print(f"CMS-SUS-21-006 mean signed Z: {result['cms_mean_signed_z']:.6g}")
    print(f"CMS-SUS-21-006 bin-order signed rho: {result['cms_bin_signed']:.6g}, p={result['cms_bin_signed_p']:.6g}")
    print(f"Signed residual delta R2 beyond missing/visible: {result['delta_signed']:.6g}")
    print(f"Judgement: {result['judgement']}")


if __name__ == "__main__":
    main()
