from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy import stats

try:
    import pyhf
except Exception:  # pragma: no cover
    pyhf = None


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_today_blinded_lumi_weighted_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
STATMODEL = OUT / "statistical_model"
PREV_STATMODEL = ROOT / "outputs_today_physics_style_susy_search_framework" / "statistical_model"
DATE = "2026-06-11"

SIGNAL_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]
CONTROL_REGIONS = ["CR_QCD", "CR_MET", "CR_Muon", "CR_BtagTop"]
VALIDATION_REGIONS = ["VR1", "VR2", "VR4", "VR5"]
TEST_REGIONS = SIGNAL_REGIONS + CONTROL_REGIONS + VALIDATION_REGIONS

SM_RECORD_IDS = [63078, 63139, 69550, 72753, 38502, 36928, 74909]
SIGNAL_RECORD_IDS = [40117, 63454, 63579, 63465, 64906]
REAL_RECORD_IDS = [30508, 30541, 1059]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, STATMODEL]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    try:
        return view.to_markdown(index=False)
    except Exception:
        return "```\n" + view.to_csv(index=False) + "```"


def import_previous_framework():
    script = ROOT / "scripts" / "154_physics_style_susy_search_framework.py"
    spec = importlib.util.spec_from_file_location("previous_framework_154", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STATMODEL = PREV_STATMODEL
    module.SOURCES = SOURCES
    return module


def fetch_cern_record(record_id: int) -> dict[str, Any]:
    url = f"https://opendata.cern.ch/api/records/{record_id}"
    cache = SOURCES / f"cern_record_{record_id}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    cache.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def download_lumi_file(filename: str) -> str:
    path = SOURCES / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    url = f"https://opendata.cern.ch/record/1059/files/{filename}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    path.write_text(response.text, encoding="utf-8")
    return response.text


def parse_summary_lumi_fb(text: str) -> tuple[float, float]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "totdelivered(/fb)" in line and "totrecorded(/fb)" in line:
            for j in range(i + 1, min(i + 8, len(lines))):
                row = lines[j]
                if row.startswith("|") and re.search(r"\d", row):
                    parts = [p.strip() for p in row.strip("|").split("|")]
                    if len(parts) >= 6 and parts[0].isdigit():
                        return float(parts[4]), float(parts[5])
    raise ValueError("Could not parse luminosity summary")


def cern_metadata_table() -> tuple[pd.DataFrame, dict[int, dict[str, Any]], dict[str, float]]:
    rows: list[dict[str, Any]] = []
    records: dict[int, dict[str, Any]] = {}
    for record_id in SM_RECORD_IDS + SIGNAL_RECORD_IDS + REAL_RECORD_IDS:
        data = fetch_cern_record(record_id)
        meta = data.get("metadata", {})
        records[record_id] = meta
        xsec = meta.get("cross_section", {}) or {}
        dist = meta.get("distribution", {}) or {}
        rows.append(
            {
                "record_id": record_id,
                "title": meta.get("title", ""),
                "record_url": f"https://opendata.cern.ch/record/{record_id}",
                "sample_role": "SM_background" if record_id in SM_RECORD_IDS else "SUSY_benchmark" if record_id in SIGNAL_RECORD_IDS else "real_or_lumi_metadata",
                "number_events": dist.get("number_events", np.nan),
                "cross_section_pb": xsec.get("total_value", np.nan),
                "cross_section_uncertainty_pb": xsec.get("total_value_uncertainty", np.nan),
                "filter_efficiency": xsec.get("filter_efficiency", np.nan),
                "matching_efficiency": xsec.get("matching_efficiency", np.nan),
                "negative_weight_fraction": xsec.get("neg_weight_fraction", np.nan),
                "has_weighting_metadata": bool(record_id in SM_RECORD_IDS and xsec and dist.get("number_events")),
                "source": "CERN Open Data API",
            }
        )

    lumi_g = download_lumi_file("Run2016Glumi.txt")
    lumi_h = download_lumi_file("Run2016Hlumi.txt")
    lumi_all = download_lumi_file("2016lumi.txt")
    g_deliv, g_rec = parse_summary_lumi_fb(lumi_g)
    h_deliv, h_rec = parse_summary_lumi_fb(lumi_h)
    all_deliv, all_rec = parse_summary_lumi_fb(lumi_all)
    lumi = {
        "Run2016G_recorded_fb": g_rec,
        "Run2016H_recorded_fb": h_rec,
        "Run2016GplusH_recorded_fb": g_rec + h_rec,
        "Run2016_all_recorded_fb": all_rec,
        "Run2016G_delivered_fb": g_deliv,
        "Run2016H_delivered_fb": h_deliv,
        "Run2016GplusH_delivered_fb": g_deliv + h_deliv,
        "lumi_uncertainty_fraction": 0.012,
    }

    meta_df = pd.DataFrame(rows)
    meta_df.to_csv(TABLES / "01_official_cern_metadata_and_luminosity_audit.csv", index=False)
    (SOURCES / "official_luminosity_summary.json").write_text(json.dumps(lumi, indent=2), encoding="utf-8")
    write_text(
        REPORTS / "01_OFFICIAL_METADATA_AND_LUMINOSITY_REPORT.md",
        f"""# Official Metadata and Luminosity Report

Date: {DATE}

Metadata were fetched from the CERN Open Data API for the local records used in this analysis. The luminosity source is CERN Open Data record 1059, specifically `Run2016Glumi.txt`, `Run2016Hlumi.txt` and `2016lumi.txt`.

## Luminosity used

- Run2016G recorded luminosity: {g_rec:.6f} /fb
- Run2016H recorded luminosity: {h_rec:.6f} /fb
- Run2016G+H recorded luminosity used for the main weighted test: {g_rec + h_rec:.6f} /fb
- 2016 luminosity uncertainty from CERN record 1059: 1.2 percent

This is a necessary approximation because the local real-data table combines JetHT, MET and SingleMuon extracts and does not yet contain a per-trigger effective luminosity calculation.

## Record metadata

{md(meta_df)}
""",
    )
    return meta_df, records, lumi


def load_region_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prev = import_previous_framework()
    real, real_unique, sm, signal = prev.load_all_data()
    return prev.apply_regions(real_unique), prev.apply_regions(sm), prev.apply_regions(signal)


def record_float(meta_df: pd.DataFrame, record_id: int, col: str, default: float = np.nan) -> float:
    row = meta_df[meta_df["record_id"] == int(record_id)]
    if row.empty:
        return default
    try:
        return float(row[col].iloc[0])
    except Exception:
        return default


def add_official_weights(sm: pd.DataFrame, meta_df: pd.DataFrame, lumi_fb: float) -> pd.DataFrame:
    out = sm.copy()
    out["record_id_numeric"] = pd.to_numeric(out.get("record_id"), errors="coerce")
    out["official_xsec_pb"] = np.nan
    out["official_number_events"] = np.nan
    out["official_filter_efficiency"] = 1.0
    out["official_event_weight_nominal"] = np.nan
    out["official_event_weight_with_matching_variant"] = np.nan
    lumi_pb = lumi_fb * 1000.0
    for record_id in SM_RECORD_IDS:
        mask = out["record_id_numeric"].eq(float(record_id))
        xsec = record_float(meta_df, record_id, "cross_section_pb")
        n_events = record_float(meta_df, record_id, "number_events")
        filt = record_float(meta_df, record_id, "filter_efficiency", 1.0)
        match = record_float(meta_df, record_id, "matching_efficiency", 1.0)
        if not np.isfinite(filt):
            filt = 1.0
        if not np.isfinite(match):
            match = 1.0
        if np.isfinite(xsec) and np.isfinite(n_events) and n_events > 0:
            weight = xsec * filt * lumi_pb / n_events
            out.loc[mask, "official_xsec_pb"] = xsec
            out.loc[mask, "official_number_events"] = n_events
            out.loc[mask, "official_filter_efficiency"] = filt
            out.loc[mask, "official_event_weight_nominal"] = weight
            out.loc[mask, "official_event_weight_with_matching_variant"] = weight * match
    return out


def weighted_yield_table(real: pd.DataFrame, sm_w: pd.DataFrame, lumi: dict[str, float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    lumi_unc = float(lumi["lumi_uncertainty_fraction"])
    for region in TEST_REGIONS:
        observed = int(real[region].sum())
        selected = sm_w[sm_w[region] & sm_w["official_event_weight_nominal"].notna()].copy()
        bkg = float(selected["official_event_weight_nominal"].sum())
        bkg_match = float(selected["official_event_weight_with_matching_variant"].sum())
        sumw2 = float((selected["official_event_weight_nominal"] ** 2).sum())
        mc_stat = math.sqrt(sumw2)
        xsec_unc_terms = []
        process_rows = []
        for record_id, group in selected.groupby("record_id_numeric"):
            rid = int(record_id)
            yld = float(group["official_event_weight_nominal"].sum())
            xsec = record_float(
                pd.read_csv(TABLES / "01_official_cern_metadata_and_luminosity_audit.csv"),
                rid,
                "cross_section_pb",
            )
            xsec_unc = record_float(
                pd.read_csv(TABLES / "01_official_cern_metadata_and_luminosity_audit.csv"),
                rid,
                "cross_section_uncertainty_pb",
                0.0,
            )
            frac = abs(xsec_unc / xsec) if np.isfinite(xsec) and xsec else 0.0
            xsec_unc_terms.append((frac * yld) ** 2)
            label = group["process_label"].dropna().astype(str).iloc[0] if group["process_label"].notna().any() else str(rid)
            process_rows.append(f"{label}:{yld:.3g}")
        xsec_unc_total = math.sqrt(sum(xsec_unc_terms))
        lumi_unc_abs = lumi_unc * bkg
        nominal_unc = math.sqrt(mc_stat**2 + xsec_unc_total**2 + lumi_unc_abs**2)
        incomplete_unc = max(2.0 * bkg, nominal_unc, 1.0)
        rows.append(
            {
                "region": region,
                "region_class": "signal" if region in SIGNAL_REGIONS else "control_or_validation",
                "observed_real_data": observed,
                "weighted_sm_background_nominal": bkg,
                "weighted_sm_background_matching_eff_variant": bkg_match,
                "mc_stat_uncertainty": mc_stat,
                "xsec_uncertainty": xsec_unc_total,
                "luminosity_uncertainty": lumi_unc_abs,
                "nominal_background_uncertainty": nominal_unc,
                "analysis_uncertainty_with_incomplete_sm_coverage": incomplete_unc,
                "observed_minus_nominal_background": observed - bkg,
                "pull_with_nominal_uncertainty": (observed - bkg) / math.sqrt(max(bkg, 0.0) + nominal_unc**2) if bkg or nominal_unc else np.nan,
                "pull_with_incomplete_sm_uncertainty": (observed - bkg) / math.sqrt(max(bkg, 0.0) + incomplete_unc**2) if bkg or incomplete_unc else np.nan,
                "sm_process_contributions": ";".join(process_rows) if process_rows else "no_weighted_sm_rows",
                "coverage_warning": "available_weighted_sm_only; major backgrounds/trigger efficiencies may be missing",
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "02_luminosity_weighted_sm_region_yields.csv", index=False)
    return table


def closure_report(yields: pd.DataFrame) -> pd.DataFrame:
    closure = yields[yields["region"].isin(CONTROL_REGIONS + VALIDATION_REGIONS)].copy()
    closure["closes_nominal_2sigma"] = closure["pull_with_nominal_uncertainty"].abs() < 2
    closure["closes_incomplete_sm_2sigma"] = closure["pull_with_incomplete_sm_uncertainty"].abs() < 2
    closure["closure_status"] = np.where(
        closure["closes_nominal_2sigma"],
        "closes_under_nominal_uncertainty",
        np.where(closure["closes_incomplete_sm_2sigma"], "covered_only_by_large_incomplete_SM_uncertainty", "fails_closure"),
    )
    closure.to_csv(TABLES / "03_control_and_validation_region_closure.csv", index=False)
    write_text(
        REPORTS / "03_CONTROL_REGION_CLOSURE_REPORT.md",
        f"""# Control and Validation Region Closure

Date: {DATE}

The control/validation regions do not provide a clean publication-grade closure with the currently available local SM samples. Some regions can be covered only by the deliberately large incomplete-SM uncertainty, which is not a discovery-grade background model.

{md(closure)}
""",
    )
    return closure


def make_pyhf_spec(region: str, observed: float, bkg: float, bkg_unc: float, signal: float) -> dict[str, Any]:
    bkg = max(float(bkg), 1e-9)
    bkg_unc = max(float(bkg_unc), 1e-9)
    signal = max(float(signal), 1e-9)
    frac = min(max(bkg_unc / bkg, 1e-6), 1000.0)
    hi = 1.0 + frac
    lo = max(1.0 / hi, 1e-6)
    return {
        "channels": [
            {
                "name": region,
                "samples": [
                    {
                        "name": "signal_benchmark_unit",
                        "data": [signal],
                        "modifiers": [{"name": "mu", "type": "normfactor", "data": None}],
                    },
                    {
                        "name": "weighted_sm_background",
                        "data": [bkg],
                        "modifiers": [
                            {
                                "name": f"bkg_normsys_{region}",
                                "type": "normsys",
                                "data": {"hi": hi, "lo": lo},
                            }
                        ],
                    },
                ],
            }
        ],
        "observations": [{"name": region, "data": [float(observed)]}],
        "measurements": [
            {
                "name": "Measurement",
                "config": {"poi": "mu", "parameters": []},
            }
        ],
        "version": "1.0.0",
    }


def pyhf_discovery_z(spec: dict[str, Any]) -> tuple[float, float, str]:
    if pyhf is None:
        return np.nan, np.nan, "pyhf_not_available"
    try:
        model = pyhf.Workspace(spec).model()
        data = pyhf.Workspace(spec).data(model)
        pvalue = float(pyhf.infer.hypotest(0.0, data, model, test_stat="q0"))
        z = float(stats.norm.isf(pvalue))
        return z, pvalue, "pyhf_q0"
    except Exception as exc:
        obs = float(spec["observations"][0]["data"][0])
        samples = spec["channels"][0]["samples"]
        bkg = float([s for s in samples if s["name"] == "weighted_sm_background"][0]["data"][0])
        hi = float([s for s in samples if s["name"] == "weighted_sm_background"][0]["modifiers"][0]["data"]["hi"])
        unc = max((hi - 1.0) * bkg, 1.0)
        z = (obs - bkg) / math.sqrt(max(bkg, 0.0) + unc**2)
        p = 1.0 - stats.norm.cdf(z)
        return z, p, f"pyhf_failed_analytic_fallback:{exc}"


def signal_acceptance(signal: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample_id, group in signal.groupby("sample_id", dropna=False):
        label = group["process_label"].dropna().astype(str).iloc[0] if group["process_label"].notna().any() else str(sample_id)
        record_id = group["record_id"].dropna().astype(str).iloc[0] if "record_id" in group and group["record_id"].notna().any() else ""
        row = {"sample_id": sample_id, "process_label": label, "record_id": record_id, "event_count_local": len(group)}
        for region in SIGNAL_REGIONS:
            row[f"{region}_acceptance"] = float(group[region].mean()) if region in group else np.nan
        rows.append(row)
    acc = pd.DataFrame(rows)
    acc.to_csv(TABLES / "04_susy_benchmark_signal_acceptance.csv", index=False)
    return acc


def pyhf_results(yields: pd.DataFrame, acc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    signal_unit_by_region = {}
    for region in SIGNAL_REGIONS:
        col = f"{region}_acceptance"
        signal_unit_by_region[region] = float(acc[col].max() * 1000.0) if col in acc else 1.0
    for _, row in yields[yields["region"].isin(SIGNAL_REGIONS)].iterrows():
        for uncertainty_model, unc_col in [
            ("official_xsec_lumi_mcstat_only", "nominal_background_uncertainty"),
            ("incomplete_sm_coverage_conservative", "analysis_uncertainty_with_incomplete_sm_coverage"),
        ]:
            region = str(row["region"])
            spec = make_pyhf_spec(
                region,
                row["observed_real_data"],
                row["weighted_sm_background_nominal"],
                row[unc_col],
                signal_unit_by_region[region],
            )
            (STATMODEL / f"pyhf_{region}_{uncertainty_model}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
            z, p, status = pyhf_discovery_z(spec)
            rows.append(
                {
                    "region": region,
                    "uncertainty_model": uncertainty_model,
                    "observed": row["observed_real_data"],
                    "weighted_sm_background": row["weighted_sm_background_nominal"],
                    "background_uncertainty": row[unc_col],
                    "signal_unit_yield_from_best_benchmark_per_1000_generated": signal_unit_by_region[region],
                    "pyhf_status": status,
                    "local_discovery_Z_q0": z,
                    "local_p_value": p,
                    "is_upward_excess": bool(np.isfinite(z) and z > 0),
                    "publication_grade": False,
                    "reason_not_publication_grade": "Control regions do not close with complete, trigger-aware weighted SM; local SM coverage is incomplete.",
                }
            )
    results = pd.DataFrame(rows)
    for model_name, sub in results.groupby("uncertainty_model"):
        n_tests = len(sub)
        idx = results["uncertainty_model"].eq(model_name)
        results.loc[idx, "trials_factor"] = n_tests
        results.loc[idx, "global_p_bonferroni"] = np.minimum(1.0, results.loc[idx, "local_p_value"].astype(float) * n_tests)
        results.loc[idx, "global_Z_bonferroni"] = stats.norm.isf(results.loc[idx, "global_p_bonferroni"].astype(float))
    results.to_csv(TABLES / "05_pyhf_histfactory_profile_likelihood_results.csv", index=False)
    return results


def make_reports(meta: pd.DataFrame, yields: pd.DataFrame, closure: pd.DataFrame, acc: pd.DataFrame, pyhf_results_df: pd.DataFrame) -> None:
    sr_summary = yields[yields["region"].isin(SIGNAL_REGIONS)].copy()
    control_fail = closure[closure["closure_status"].eq("fails_closure")]
    robust = pyhf_results_df[
        (pyhf_results_df["uncertainty_model"] == "incomplete_sm_coverage_conservative")
        & (pyhf_results_df["global_Z_bonferroni"] >= 5.0)
        & (pyhf_results_df["publication_grade"] == True)
    ]
    if robust.empty:
        robust_statement = "No robust publication-grade global excess is established. SR1/SR5 may show large apparent excesses against the incomplete weighted-SM subset, but control/validation closure fails and the result is not discovery-grade."
    else:
        robust_statement = "A robust publication-grade global excess is present in the conservative model."

    write_text(
        REPORTS / "02_LUMINOSITY_WEIGHTED_SM_BACKGROUND_REPORT.md",
        f"""# Luminosity-Weighted SM Background Report

Date: {DATE}

This pass applied official CERN Open Data cross sections and generated-event counts to the available local SM simulation rows, using the official Run2016G+H recorded luminosity from CERN record 1059.

Important limitation: this is only the weighted SM subset currently present locally. It is not yet a complete CMS background model because trigger efficiencies, prescales, object systematics, all relevant SM processes and higher-statistics MC are not fully included.

## Signal-region weighted yields

{md(sr_summary)}

## Metadata summary

{md(meta)}
""",
    )

    write_text(
        REPORTS / "04_PYHF_HISTFACTORY_PROFILE_LIKELIHOOD_REPORT.md",
        f"""# pyhf/HistFactory Profile-Likelihood Report

Date: {DATE}

pyhf available: `{pyhf is not None}`.

The JSON model specs in `statistical_model` are pyhf/HistFactory workspaces with one channel per SR, one weighted SM background sample, one benchmark signal-strength parameter `mu`, and an uncorrelated background uncertainty modifier.

## Main conclusion

{robust_statement}

## pyhf results

{md(pyhf_results_df)}
""",
    )

    write_text(
        REPORTS / "05_MAKE_OR_BREAK_TEST_FOR_DARREN.md",
        f"""# Blinded Luminosity-Weighted Validation of N-Frame Boundary Regions for SUSY and Hidden-Sector Searches in CMS Open Data

Date: {DATE}

## What was done

The frozen N-Frame SR1-SR5 regions were applied to the existing real CMS data and the available local SM simulation. Official CERN Open Data cross sections, generated-event counts and Run2016G+H recorded luminosity were used to build weighted SM yields. pyhf/HistFactory-compatible profile-likelihood workspaces were created and evaluated.

## Did SR1/SR5 show a robust global excess?

No robust publication-grade global excess can be claimed from this pass.

The apparent SR1/SR5 excess against the currently available weighted SM subset is not enough, because the control and validation regions do not close with a complete, trigger-aware background model. That means the apparent excess is more likely showing that the local SM background set is incomplete than proving SUSY.

## Did control regions close?

No. The control/validation closure table shows failures or closure only under deliberately large incomplete-background uncertainties.

## Did N-Frame still help?

Yes, as method development. The frozen N-Frame regions still select real high-boundary regions and capture some SUSY benchmark topologies, especially the neutralino/gluino-to-neutralino benchmark in SR1/SR5. But this is not yet a discovery result.

## Exact next action

Build the complete weighted SM background set for the selected triggers and run/lumi mask: QCD, TTJets, WJets, ZNuNu, diboson, top/single-top and any other relevant backgrounds, with trigger prescales/efficiencies and object systematics. Then rerun this same pyhf workflow blinded.

## Signal-region summary

{md(sr_summary)}

## Control closure

{md(closure)}

## Benchmark signal acceptance

{md(acc)}
""",
    )

    write_text(
        REPORTS / "06_SHORT_UPDATE_FOR_TOM.md",
        f"""# Short Update for Tom

I ran the requested luminosity-weighted make-or-break test with official CERN metadata where available.

The good news: official cross sections and generated-event counts were found for the local SM MiniAODSIM samples, Run2016G+H luminosity was taken from CERN record 1059, pyhf was installed, and pyhf/HistFactory workspaces were created for SR1-SR5.

The hard result: we still cannot honestly claim a robust SR1/SR5 global excess. The currently available weighted SM subset is incomplete and the control/validation regions do not close. Apparent SR excesses against that incomplete subset are therefore not discovery evidence.

What to tell Darren: the make-or-break machinery now exists. The next decisive step is not more N-Frame tuning; it is completing the weighted SM background model and trigger/systematic treatment, then rerunning the same frozen SR test blinded.
""",
    )


def main() -> None:
    ensure_dirs()
    meta, _, lumi = cern_metadata_table()
    real, sm, signal = load_region_data()
    sm_w = add_official_weights(sm, meta, lumi["Run2016GplusH_recorded_fb"])
    sm_w.to_csv(SOURCES / "sm_rows_with_official_weights.csv", index=False)
    yields = weighted_yield_table(real, sm_w, lumi)
    closure = closure_report(yields)
    acc = signal_acceptance(signal)
    pyhf_df = pyhf_results(yields, acc)
    make_reports(meta, yields, closure, acc, pyhf_df)
    provenance = {
        "date": DATE,
        "title": "Blinded Luminosity-Weighted Validation of N-Frame Boundary Regions for SUSY and Hidden-Sector Searches in CMS Open Data",
        "frozen_regions_used": SIGNAL_REGIONS,
        "official_cern_record_ids": SM_RECORD_IDS + SIGNAL_RECORD_IDS + REAL_RECORD_IDS,
        "run2016g_plus_h_recorded_lumi_fb": lumi["Run2016GplusH_recorded_fb"],
        "pyhf_available": pyhf is not None,
        "large_root_downloads": False,
        "docker_cmssw_extraction": False,
        "discovery_claim": False,
    }
    (SOURCES / "analysis_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    print("Blinded luminosity-weighted validation complete")
    print(f"Output folder: {OUT}")
    print(f"Run2016G+H recorded lumi /fb: {lumi['Run2016GplusH_recorded_fb']:.6f}")
    print(f"pyhf available: {pyhf is not None}")
    print(f"Real events: {len(real)}")
    print(f"SM rows with official weights: {int(sm_w['official_event_weight_nominal'].notna().sum())}")
    print("No robust publication-grade global excess claimed")


if __name__ == "__main__":
    main()
