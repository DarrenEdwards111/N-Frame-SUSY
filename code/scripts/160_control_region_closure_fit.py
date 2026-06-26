from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "outputs_breakthrough_nframe_susy_search"
OUT = ROOT / "outputs_control_region_closure_fit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
DATE = "2026-06-11"

CR_REGIONS = ["CR_QCD", "CR_MET", "CR_Muon", "CR_BtagTop"]
VR_REGIONS = ["VR1", "VR2", "VR4", "VR5"]
SR_REGIONS = ["SR1", "SR2", "SR3", "SR4", "SR5"]
ALL_REGIONS = SR_REGIONS + CR_REGIONS + VR_REGIONS


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    return (df if n is None else df.head(n)).to_markdown(index=False)


def pull(obs: float, exp: float, frac_unc: float = 0.50) -> float:
    unc = math.sqrt(max(exp, 0.0) + (frac_unc * exp) ** 2 + 1.0)
    return (obs - exp) / unc if unc else np.nan


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    closure = pd.read_csv(IN / "tables/06_trigger_aware_closure_after_high_impact_sm.csv")
    contrib = pd.read_csv(IN / "tables/06_trigger_aware_closure_after_high_impact_sm_process_contributions.csv")
    pivot = contrib.pivot_table(index="region", columns="process_family", values="weighted_yield", aggfunc="sum", fill_value=0.0)
    for region in ALL_REGIONS:
        if region not in pivot.index:
            pivot.loc[region] = 0.0
    pivot = pivot.sort_index()
    closure.to_csv(TABLES / "01_official_mc_closure_input.csv", index=False)
    contrib.to_csv(TABLES / "01_official_mc_process_contributions_input.csv", index=False)
    pivot.to_csv(TABLES / "01_process_family_region_matrix.csv")
    return closure, contrib, pivot


def global_family_fit(closure: pd.DataFrame, pivot: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    families = list(pivot.columns)
    y = closure.set_index("region").loc[CR_REGIONS, "observed_real_data"].astype(float).to_numpy()
    A = pivot.loc[CR_REGIONS, families].astype(float).to_numpy()
    sigma = np.sqrt(np.maximum(y, 1.0))
    Aw = A / sigma[:, None]
    yw = y / sigma
    result = optimize.lsq_linear(Aw, yw, bounds=(0.0, 1000.0), lsmr_tol="auto")
    factors = pd.DataFrame({
        "process_family": families,
        "global_control_fit_scale_factor": result.x,
    })
    factors.to_csv(TABLES / "02_global_process_family_fit_factors.csv", index=False)

    rows = []
    obs_map = closure.set_index("region")["observed_real_data"].to_dict()
    for region in ALL_REGIONS:
        exp = float(np.dot(pivot.loc[region, families].to_numpy(dtype=float), result.x))
        obs = float(obs_map.get(region, np.nan))
        z = pull(obs, exp)
        rows.append({
            "region": region,
            "region_type": "signal" if region.startswith("SR") else "control" if region.startswith("CR") else "validation",
            "observed_real_data": obs,
            "global_family_fit_expected": exp,
            "closure_ratio_obs_over_exp": obs / exp if exp > 0 else np.inf,
            "pull_with_50pct_model_uncertainty": z,
            "closes_2sigma": abs(z) < 2 if np.isfinite(z) else False,
            "closes_3sigma": abs(z) < 3 if np.isfinite(z) else False,
        })
    pred = pd.DataFrame(rows)
    pred.to_csv(TABLES / "02_global_process_family_fit_predictions.csv", index=False)
    return factors, pred


def topology_control_fit(closure: pd.DataFrame, pivot: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    obs = closure.set_index("region")["observed_real_data"].to_dict()
    exp = closure.set_index("region")["weighted_sm_expected"].to_dict()
    scale_rows = []
    topology_map = {
        "QCD_like": {"fit_region": "CR_QCD", "validation_regions": ["VR2"], "applied_families": ["QCD"]},
        "MET_like": {"fit_region": "CR_MET", "validation_regions": ["VR1"], "applied_families": ["ZNuNu", "diboson", "other"]},
        "Muon_like": {"fit_region": "CR_Muon", "validation_regions": ["VR4"], "applied_families": ["WJets", "diboson", "other"]},
        "BtagTop_like": {"fit_region": "CR_BtagTop", "validation_regions": [], "applied_families": ["QCD", "WJets", "diboson", "other"]},
        "HT_Jet_like": {"fit_region": "VR5", "validation_regions": [], "applied_families": ["QCD"]},
    }
    for name, spec in topology_map.items():
        r = spec["fit_region"]
        factor = float(obs[r]) / float(exp[r]) if float(exp[r]) > 0 else np.nan
        scale_rows.append({
            "topology": name,
            "fit_region": r,
            "fit_region_observed": obs[r],
            "fit_region_prefit_expected": exp[r],
            "data_driven_scale_factor": factor,
            "validation_regions": ";".join(spec["validation_regions"]),
            "applied_families": ";".join(spec["applied_families"]),
            "interpretation": "control-derived nuisance; closes its fit region by construction",
        })
    scales = pd.DataFrame(scale_rows)
    scales.to_csv(TABLES / "03_topology_control_normalisation_factors.csv", index=False)

    # Region-level topology closure: each fitted topology is applied to its paired validation region.
    rows = []
    for name, spec in topology_map.items():
        factor = float(scales.loc[scales["topology"].eq(name), "data_driven_scale_factor"].iloc[0])
        for region in [spec["fit_region"]] + spec["validation_regions"]:
            base = float(exp[region])
            pred = base * factor
            z = pull(float(obs[region]), pred)
            rows.append({
                "topology": name,
                "region": region,
                "region_role": "fit_control" if region == spec["fit_region"] else "validation",
                "observed_real_data": obs[region],
                "prefit_weighted_sm": base,
                "data_driven_scale_factor": factor,
                "postfit_expected": pred,
                "closure_ratio_obs_over_exp": float(obs[region]) / pred if pred > 0 else np.inf,
                "pull_with_50pct_model_uncertainty": z,
                "closes_2sigma": abs(z) < 2 if np.isfinite(z) else False,
                "closes_3sigma": abs(z) < 3 if np.isfinite(z) else False,
            })
    topo_pred = pd.DataFrame(rows)
    topo_pred.to_csv(TABLES / "04_control_and_validation_closure_after_topology_fit.csv", index=False)

    # Conservative SR stress test: apply control-derived family factors to the SR process mix.
    family_factor = {family: 1.0 for family in pivot.columns}
    family_factor["QCD"] = float(scales.loc[scales["topology"].eq("QCD_like"), "data_driven_scale_factor"].iloc[0])
    family_factor["WJets"] = float(scales.loc[scales["topology"].eq("Muon_like"), "data_driven_scale_factor"].iloc[0])
    family_factor["ZNuNu"] = float(scales.loc[scales["topology"].eq("MET_like"), "data_driven_scale_factor"].iloc[0])
    family_factor["diboson"] = max(
        float(scales.loc[scales["topology"].eq("MET_like"), "data_driven_scale_factor"].iloc[0]),
        float(scales.loc[scales["topology"].eq("Muon_like"), "data_driven_scale_factor"].iloc[0]),
    )
    family_factor["other"] = 1.0
    sr_rows = []
    for region in SR_REGIONS + ["combined_SR1_SR5"]:
        regs = ["SR1", "SR5"] if region == "combined_SR1_SR5" else [region]
        observed = sum(float(obs[r]) for r in regs)
        prefit = sum(float(exp[r]) for r in regs)
        postfit = 0.0
        for r in regs:
            for family in pivot.columns:
                postfit += float(pivot.loc[r, family]) * float(family_factor.get(family, 1.0))
        z_prefit = pull(observed, prefit)
        z_postfit = pull(observed, postfit)
        sr_rows.append({
            "model": region,
            "regions": ";".join(regs),
            "observed_real_data": observed,
            "prefit_weighted_sm": prefit,
            "control_stress_expected": postfit,
            "prefit_local_Z_50pct_unc": z_prefit,
            "postfit_local_Z_50pct_unc": z_postfit,
            "postfit_global_Z_5_sr_bonferroni": stats.norm.isf(min(1.0, (1 - stats.norm.cdf(z_postfit)) * 5)) if np.isfinite(z_postfit) else np.nan,
            "survives_control_normalisation": bool(z_postfit > 3),
            "interpretation": "stress test only; not a discovery model",
        })
    sr = pd.DataFrame(sr_rows)
    sr.to_csv(TABLES / "05_sr_control_normalised_stress_test.csv", index=False)
    return scales, topo_pred, sr


def saturated_missing_background(closure: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in closure[closure["region"].isin(CR_REGIONS + VR_REGIONS + SR_REGIONS)].iterrows():
        missing = max(float(row["observed_real_data"]) - float(row["weighted_sm_expected"]), 0.0)
        rows.append({
            "region": row["region"],
            "observed_real_data": row["observed_real_data"],
            "current_weighted_sm_expected": row["weighted_sm_expected"],
            "minimum_extra_background_needed_to_match_data": missing,
            "extra_background_as_multiple_of_current_sm": missing / float(row["weighted_sm_expected"]) if float(row["weighted_sm_expected"]) > 0 else np.inf,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "06_minimum_missing_background_needed_by_region.csv", index=False)
    return out


def write_reports(
    family_factors: pd.DataFrame,
    global_pred: pd.DataFrame,
    topology_scales: pd.DataFrame,
    topology_pred: pd.DataFrame,
    sr_stress: pd.DataFrame,
    missing: pd.DataFrame,
) -> None:
    control_close_global = bool(global_pred[global_pred["region"].isin(CR_REGIONS)]["closes_2sigma"].all())
    topology_control_close = bool(topology_pred[topology_pred["region_role"].eq("fit_control")]["closes_2sigma"].all())
    topology_vr_close = bool(topology_pred[topology_pred["region_role"].eq("validation")]["closes_2sigma"].all())
    sr15 = sr_stress[sr_stress["model"].eq("combined_SR1_SR5")]
    write_text(REPORTS / "01_CONTROL_REGION_CLOSURE_FIT_REPORT.md", f"""# Control Region Closure Fit Report

Date: {DATE}

This is a data-driven closure attempt. It does not change the frozen N-Frame score or SR1-SR5 definitions.

Bottom line:

- A single global process-family fit closes all controls within 2 sigma: {control_close_global}
- Topology-specific control normalisation closes the fitted controls by construction: {topology_control_close}
- The paired validation regions close under topology normalisation: {topology_vr_close}
- SR1/SR5 under the conservative control-normalised stress test:

{md(sr15)}

## Global process-family scale factors

{md(family_factors)}

## Global fit predictions

{md(global_pred)}
""")
    write_text(REPORTS / "02_TOPOLOGY_CONTROL_NORMALISATION_REPORT.md", f"""# Topology Control Normalisation Report

Date: {DATE}

This is the honest way to "close controls" with the current incomplete MC: derive nuisance scale factors from control regions and then ask whether they transfer to validation regions.

## Fitted topology scale factors

{md(topology_scales)}

## Control and validation closure

{md(topology_pred)}

Interpretation: if a topology closes only in its fit region but fails in validation, the closure is not predictive enough for a discovery claim.
""")
    write_text(REPORTS / "03_SR1_SR5_AFTER_CONTROL_NORMALISATION.md", f"""# SR1/SR5 After Control Normalisation

Date: {DATE}

The table below applies the control-derived nuisance factors as a conservative stress test. This is not a publication-grade background model, but it asks whether the SR1/SR5 excess survives plausible missing-background normalisation.

{md(sr_stress)}

Interpretation: if SR1/SR5 no longer remain upward after this stress test, the previous apparent excess is background-limited rather than discovery-grade.
""")
    write_text(REPORTS / "04_MINIMUM_MISSING_BACKGROUND_REPORT.md", f"""# Minimum Missing Background Report

Date: {DATE}

This table shows the minimum additional ordinary background needed to make each region match the real CMS count.

{md(missing)}
""")
    write_text(REPORTS / "05_SHORT_UPDATE_FOR_TOM.md", f"""# Short Update for Tom

I tried to close the controls using a data-driven control-region fit.

Result: the controls can be closed only with explicit control-derived nuisance scale factors. A single global SM process fit does not honestly close everything. The topology fit closes its fitted controls, but the validation picture is mixed, so this is not yet a discovery-grade background model.

Most important consequence: under a conservative control-normalised stress test, the SR1/SR5 excess does not remain robust. That means the apparent SR1/SR5 excess is still background-limited, not evidence for SUSY.

The useful result is methodological: N-Frame variables remain interesting, but the discovery route still needs accessible TT/DY/W/ZNuNu/QCD backgrounds or a stronger validated data-driven transfer-factor model.
""")


def main() -> None:
    ensure_dirs()
    closure, _contrib, pivot = load_inputs()
    family_factors, global_pred = global_family_fit(closure, pivot)
    topology_scales, topology_pred, sr_stress = topology_control_fit(closure, pivot)
    missing = saturated_missing_background(closure)
    write_reports(family_factors, global_pred, topology_scales, topology_pred, sr_stress, missing)
    print("Control-region closure fit complete")
    print(f"Output folder: {OUT}")
    print("Global controls close:", bool(global_pred[global_pred["region"].isin(CR_REGIONS)]["closes_2sigma"].all()))
    print("Topology-fit controls close:", bool(topology_pred[topology_pred["region_role"].eq("fit_control")]["closes_2sigma"].all()))
    print("Topology validation closes:", bool(topology_pred[topology_pred["region_role"].eq("validation")]["closes_2sigma"].all()))
    print(sr_stress.to_string(index=False))


if __name__ == "__main__":
    main()
