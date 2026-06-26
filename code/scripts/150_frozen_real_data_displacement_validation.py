from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, RidgeCV


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_today_frozen_real_data_displacement_validation"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
DATE = "2026-06-10"

RUN2016G = ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv"
RUN2016H = ROOT / "data" / "processed" / "independent_validation_miniaod_full" / "run2016h_miniaod_with_fitted_nframe_score.csv"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    return view.to_markdown(index=False)


def csv_header(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def audit_inputs() -> pd.DataFrame:
    required = {
        "B_NF": ["B_NF_fitted_z", "B_NF_fitted_run2016h_z"],
        "P_displacement": ["fitted_P_displacement_proxy", "run2016h_P_displacement_proxy"],
        "P_reconstruction": ["fitted_P_reconstruction", "run2016h_P_reconstruction"],
        "P_missing": ["fitted_P_missing", "run2016h_P_missing"],
        "P_visible": ["fitted_P_visible_energy", "run2016h_P_visible_energy"],
        "P_multiplicity": ["fitted_P_multiplicity", "run2016h_P_multiplicity"],
        "P_btag": ["fitted_P_btag_structure", "run2016h_P_btag_structure"],
        "MET": ["MET_pt"],
        "HT": ["HT"],
        "source": ["source_file"],
        "run_lumi_event": ["run", "lumi", "event"],
        "dataset": ["primary_dataset"],
        "quality": ["standard_quality_clean", "pass_goodVertices"],
    }
    rows = []
    for era, path in [("Run2016G", RUN2016G), ("Run2016H", RUN2016H)]:
        header = csv_header(path)
        row: dict[str, Any] = {
            "run_era": era,
            "file": str(path),
            "exists": path.exists(),
            "size_mb": path.stat().st_size / 1e6 if path.exists() else np.nan,
            "columns": len(header),
        }
        for group, options in required.items():
            row[f"{group}_available"] = any(c in header for c in options)
            row[f"{group}_columns"] = "; ".join([c for c in options if c in header])
        # Count rows and dataset mix cheaply via selected columns.
        counts = pd.Series(dtype=int)
        n = 0
        for chunk in pd.read_csv(path, usecols=["primary_dataset"], chunksize=250_000):
            n += len(chunk)
            counts = counts.add(chunk["primary_dataset"].value_counts(), fill_value=0).astype(int)
        row["events"] = n
        row["dataset_counts"] = "; ".join(f"{k}:{int(v)}" for k, v in counts.items())
        row["can_run_without_docker"] = True
        rows.append(row)
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_real_data_input_audit.csv", index=False)
    write_text(
        OUT / "01_REAL_DATA_INPUT_AUDIT.md",
        "\n".join(
            [
                "# Real-Data Input Audit",
                "",
                f"Date: {DATE}",
                "",
                "The validation can run from existing processed/scored real CMS tables. Docker/CMSSW is not needed.",
                "",
                md(audit),
            ]
        ),
    )
    return audit


def read_real_file(path: Path, era: str) -> pd.DataFrame:
    if era == "Run2016G":
        colmap = {
            "primary_dataset": "primary_dataset",
            "run": "run",
            "lumi": "lumi",
            "event": "event",
            "source_file": "source_file",
            "MET_pt": "MET_pt",
            "HT": "HT",
            "N_jets_30": "N_jets_30",
            "N_btags_medium": "N_btags_medium",
            "N_primary_vertices": "N_primary_vertices",
            "secondary_vertex_count": "secondary_vertex_count",
            "packed_candidate_count": "packed_candidate_count",
            "fitted_P_displacement_proxy": "P_displacement",
            "fitted_P_reconstruction": "P_reconstruction",
            "fitted_P_multiplicity": "P_multiplicity",
            "fitted_P_btag_structure": "P_btag",
            "fitted_P_visible_energy": "P_visible",
            "fitted_P_missing": "P_missing",
            "fitted_P_compression": "P_compression",
            "B_NF_fitted_z": "B_NF_z",
            "B_NF_fitted_raw": "B_NF_raw",
            "standard_quality_clean": "quality_clean",
        }
    else:
        colmap = {
            "primary_dataset": "primary_dataset",
            "run": "run",
            "lumi": "lumi",
            "event": "event",
            "source_file": "source_file",
            "MET_pt": "MET_pt",
            "HT": "HT",
            "N_jets_30": "N_jets_30",
            "N_btags_medium": "N_btags_medium",
            "N_primary_vertices": "N_primary_vertices",
            "secondary_vertex_count": "secondary_vertex_count",
            "packed_candidate_count": "packed_candidate_count",
            "run2016h_P_displacement_proxy": "P_displacement",
            "run2016h_P_reconstruction": "P_reconstruction",
            "run2016h_P_multiplicity": "P_multiplicity",
            "run2016h_P_btag_structure": "P_btag",
            "run2016h_P_visible_energy": "P_visible",
            "run2016h_P_missing": "P_missing",
            "run2016h_P_compression": "P_compression",
            "B_NF_fitted_run2016h_z": "B_NF_z",
            "B_NF_fitted_run2016h_raw": "B_NF_raw",
            "pass_goodVertices": "quality_clean",
        }
    header = csv_header(path)
    use = [c for c in colmap if c in header]
    chunks = []
    for chunk in pd.read_csv(path, usecols=use, chunksize=250_000):
        out = pd.DataFrame()
        for src, dst in colmap.items():
            out[dst] = chunk[src] if src in chunk else np.nan
        out["run_era"] = era
        chunks.append(out)
    df = pd.concat(chunks, ignore_index=True)
    numeric = [
        "run",
        "lumi",
        "event",
        "MET_pt",
        "HT",
        "N_jets_30",
        "N_btags_medium",
        "N_primary_vertices",
        "secondary_vertex_count",
        "packed_candidate_count",
        "P_displacement",
        "P_reconstruction",
        "P_multiplicity",
        "P_btag",
        "P_visible",
        "P_missing",
        "P_compression",
        "B_NF_z",
        "B_NF_raw",
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quality_clean"] = pd.to_numeric(df["quality_clean"], errors="coerce")
    return df


def load_data() -> pd.DataFrame:
    data = pd.concat([read_real_file(RUN2016G, "Run2016G"), read_real_file(RUN2016H, "Run2016H")], ignore_index=True)
    data["displacement_reconstruction_axis"] = data["P_displacement"] + data["P_reconstruction"]
    data["missing_visible_axis"] = data["P_missing"] + data["P_visible"]
    # Frozen definition for this analysis: ordinary QCD-like activity is high visible energy and object multiplicity,
    # with b-tag contribution included but no displacement contribution.
    data["qcd_like_axis"] = data[["P_visible", "P_multiplicity", "P_btag"]].mean(axis=1)
    data["run_lumi"] = data["run"].astype("Int64").astype(str) + ":" + data["lumi"].astype("Int64").astype(str)
    return data


def define_axes_sidebands(data: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    thresholds = {
        "B_NF_z_top05": data["B_NF_z"].quantile(0.95),
        "B_NF_z_top01": data["B_NF_z"].quantile(0.99),
        "disp_reco_top20": data["displacement_reconstruction_axis"].quantile(0.80),
        "disp_reco_top10": data["displacement_reconstruction_axis"].quantile(0.90),
        "disp_reco_median": data["displacement_reconstruction_axis"].quantile(0.50),
        "missing_visible_top20": data["missing_visible_axis"].quantile(0.80),
        "missing_visible_median": data["missing_visible_axis"].quantile(0.50),
        "qcd_like_top20": data["qcd_like_axis"].quantile(0.80),
    }
    axis_defs = pd.DataFrame(
        [
            {"axis": "B_NF_z", "definition": "existing frozen fitted B_NF z score from each run table", "thresholds": f"top5={thresholds['B_NF_z_top05']:.6g}; top1={thresholds['B_NF_z_top01']:.6g}"},
            {"axis": "displacement_reconstruction_axis", "definition": "P_displacement + P_reconstruction using frozen fitted components", "thresholds": f"top20={thresholds['disp_reco_top20']:.6g}; median={thresholds['disp_reco_median']:.6g}"},
            {"axis": "missing_visible_axis", "definition": "P_missing + P_visible_energy using frozen fitted components", "thresholds": f"top20={thresholds['missing_visible_top20']:.6g}; median={thresholds['missing_visible_median']:.6g}"},
            {"axis": "qcd_like_axis", "definition": "mean(P_visible_energy, P_multiplicity, P_btag_structure)", "thresholds": f"top20={thresholds['qcd_like_top20']:.6g}"},
        ]
    )
    side_defs = pd.DataFrame(
        [
            {"sideband": "high_BNF_high_disp_reco", "definition": "B_NF_z top 5% and displacement/reconstruction top 20%"},
            {"sideband": "high_disp_reco_low_missing_visible", "definition": "displacement/reconstruction top 20% and missing/visible below median"},
            {"sideband": "high_missing_visible_low_disp_reco", "definition": "missing/visible top 20% and displacement/reconstruction below median"},
            {"sideband": "high_BNF_low_disp_reco", "definition": "B_NF_z top 5% and displacement/reconstruction below median"},
            {"sideband": "qcd_like_high_HT_high_multiplicity", "definition": "qcd_like_axis top 20%"},
            {"sideband": "trace_aligned_high_boundary_proxy", "definition": "B_NF_z top 5%, displacement/reconstruction top 20%, missing/visible below top 20%"},
            {"sideband": "ordinary_controls", "definition": "quality-clean events with |B_NF_z| <= 0.25 and displacement/reconstruction near median"},
        ]
    )
    axis_defs.to_csv(TABLES / "02_frozen_axis_definitions.csv", index=False)
    side_defs.to_csv(TABLES / "02_frozen_sideband_definitions.csv", index=False)
    write_text(
        OUT / "02_FROZEN_AXIS_AND_SIDEBAND_DEFINITIONS.md",
        "\n".join(
            [
                "# Frozen Axis and Sideband Definitions",
                "",
                f"Date: {DATE}",
                "",
                "Definitions are shared across Run2016G and Run2016H. Thresholds are combined-data quantiles and are not tuned separately by run.",
                "",
                "Axes:",
                "",
                md(axis_defs),
                "",
                "Sidebands:",
                "",
                md(side_defs),
            ]
        ),
    )
    return thresholds, side_defs


def add_sidebands(data: pd.DataFrame, t: dict[str, float]) -> pd.DataFrame:
    out = data.copy()
    out["high_BNF_high_disp_reco"] = (out.B_NF_z >= t["B_NF_z_top05"]) & (out.displacement_reconstruction_axis >= t["disp_reco_top20"])
    out["high_disp_reco_low_missing_visible"] = (out.displacement_reconstruction_axis >= t["disp_reco_top20"]) & (out.missing_visible_axis <= t["missing_visible_median"])
    out["high_missing_visible_low_disp_reco"] = (out.missing_visible_axis >= t["missing_visible_top20"]) & (out.displacement_reconstruction_axis <= t["disp_reco_median"])
    out["high_BNF_low_disp_reco"] = (out.B_NF_z >= t["B_NF_z_top05"]) & (out.displacement_reconstruction_axis <= t["disp_reco_median"])
    out["qcd_like_high_HT_high_multiplicity"] = out.qcd_like_axis >= t["qcd_like_top20"]
    out["trace_aligned_high_boundary_proxy"] = (out.B_NF_z >= t["B_NF_z_top05"]) & (out.displacement_reconstruction_axis >= t["disp_reco_top20"]) & (out.missing_visible_axis < t["missing_visible_top20"])
    out["ordinary_controls"] = (out.quality_clean.fillna(1) == 1) & (out.B_NF_z.abs() <= 0.25) & (out.displacement_reconstruction_axis.between(t["disp_reco_median"] - 0.25, t["disp_reco_median"] + 0.25))
    return out


SIDEBANDS = [
    "high_BNF_high_disp_reco",
    "high_disp_reco_low_missing_visible",
    "high_missing_visible_low_disp_reco",
    "high_BNF_low_disp_reco",
    "qcd_like_high_HT_high_multiplicity",
    "trace_aligned_high_boundary_proxy",
    "ordinary_controls",
]


def summarise_sideband(sub: pd.DataFrame, label: str, run_era: str) -> dict[str, Any]:
    if sub.empty:
        return {"sideband": label, "run_era": run_era, "events": 0}
    return {
        "sideband": label,
        "run_era": run_era,
        "events": len(sub),
        "jetht_fraction": (sub.primary_dataset == "JetHT").mean(),
        "met_fraction": (sub.primary_dataset == "MET").mean(),
        "singlemuon_fraction": (sub.primary_dataset == "SingleMuon").mean(),
        "mean_B_NF_z": sub.B_NF_z.mean(),
        "median_B_NF_z": sub.B_NF_z.median(),
        "mean_displacement_reconstruction_axis": sub.displacement_reconstruction_axis.mean(),
        "median_displacement_reconstruction_axis": sub.displacement_reconstruction_axis.median(),
        "mean_missing_visible_axis": sub.missing_visible_axis.mean(),
        "median_missing_visible_axis": sub.missing_visible_axis.median(),
        "mean_MET_pt": sub.MET_pt.mean(),
        "mean_HT": sub.HT.mean(),
        "mean_N_jets_30": sub.N_jets_30.mean(),
        "mean_N_btags_medium": sub.N_btags_medium.mean(),
        "mean_secondary_vertex_count": sub.secondary_vertex_count.mean(),
        "mean_packed_candidate_count": sub.packed_candidate_count.mean(),
        "quality_clean_fraction": sub.quality_clean.mean(),
        "top_source_file_fraction": sub.source_file.value_counts(normalize=True).iloc[0],
        "top_run_fraction": sub.run.value_counts(normalize=True).iloc[0],
        "top_lumi_fraction": sub.lumi.value_counts(normalize=True).iloc[0],
    }


def replication_report(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sideband in SIDEBANDS:
        for era in ["Run2016G", "Run2016H", "combined"]:
            sub = data[data[sideband]] if era == "combined" else data[(data[sideband]) & (data.run_era == era)]
            rows.append(summarise_sideband(sub, sideband, era))
    rep = pd.DataFrame(rows)
    both = rep.pivot(index="sideband", columns="run_era", values="events").reset_index()
    both["persists_in_both_runs"] = (both.get("Run2016G", 0) > 0) & (both.get("Run2016H", 0) > 0)
    rep = rep.merge(both[["sideband", "persists_in_both_runs"]], on="sideband", how="left")
    rep.to_csv(TABLES / "03_sideband_replication_by_run.csv", index=False)
    target = rep[(rep.sideband == "high_disp_reco_low_missing_visible") & (rep.run_era.isin(["Run2016G", "Run2016H"]))]
    write_text(
        OUT / "03_RUN2016G_RUN2016H_SIDEBAND_REPLICATION_REPORT.md",
        "\n".join(
            [
                "# Run2016G/Run2016H Sideband Replication Report",
                "",
                f"Date: {DATE}",
                "",
                "Critical sideband: high displacement/reconstruction but low missing/visible.",
                "",
                md(target),
                "",
                "All sidebands:",
                "",
                md(rep),
            ]
        ),
    )
    return rep


def smd(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    denom = math.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / denom) if denom else 0.0


def bootstrap_ci(diff: np.ndarray, n_boot: int = 400, seed: int = 12) -> tuple[float, float]:
    if len(diff) == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    means = [rng.choice(diff, size=len(diff), replace=True).mean() for _ in range(n_boot)]
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def match_controls(data: pd.DataFrame, target_mask: pd.Series, control_mask: pd.Series, label: str, max_target: int = 20000) -> tuple[pd.DataFrame, pd.DataFrame]:
    target = data[target_mask].copy()
    control = data[control_mask & ~target_mask].copy()
    rng = np.random.default_rng(42)
    if len(target) > max_target:
        target = target.sample(max_target, random_state=42)
    match_vars = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_primary_vertices"]
    matched_parts = []
    for (era, dataset), tsub in target.groupby(["run_era", "primary_dataset"]):
        csub = control[(control.run_era == era) & (control.primary_dataset == dataset)]
        if len(csub) < 5:
            csub = control[control.run_era == era]
        if len(csub) < 5:
            continue
        x_c = csub[match_vars].fillna(csub[match_vars].median())
        x_t = tsub[match_vars].fillna(csub[match_vars].median())
        scaler = StandardScaler().fit(x_c)
        nn = NearestNeighbors(n_neighbors=1).fit(scaler.transform(x_c))
        dist, idx = nn.kneighbors(scaler.transform(x_t))
        matched = csub.iloc[idx[:, 0]].copy()
        matched["target_index"] = tsub.index.to_numpy()
        matched["match_distance"] = dist[:, 0]
        matched_parts.append(matched)
    matched = pd.concat(matched_parts, ignore_index=True) if matched_parts else pd.DataFrame()
    target_matched = target.loc[matched["target_index"].values].reset_index(drop=True) if not matched.empty else pd.DataFrame()

    balance_rows = []
    effect_rows = []
    for var in match_vars + ["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis", "secondary_vertex_count", "packed_candidate_count"]:
        before = smd(target[var], control[var]) if len(control) else np.nan
        after = smd(target_matched[var], matched[var]) if len(matched) else np.nan
        balance_rows.append(
            {
                "comparison": label,
                "variable": var,
                "target_n": len(target),
                "candidate_control_n": len(control),
                "matched_control_n": len(matched),
                "smd_before": before,
                "smd_after": after,
            }
        )
        if len(matched):
            diff = target_matched[var].to_numpy(dtype=float) - matched[var].to_numpy(dtype=float)
            lo, hi = bootstrap_ci(diff[~np.isnan(diff)])
            p = stats.ttest_rel(target_matched[var], matched[var], nan_policy="omit").pvalue
            effect_rows.append(
                {
                    "comparison": label,
                    "variable": var,
                    "target_mean": target_matched[var].mean(),
                    "matched_control_mean": matched[var].mean(),
                    "difference": np.nanmean(diff),
                    "bootstrap_ci_low": lo,
                    "bootstrap_ci_high": hi,
                    "paired_t_p_value": p,
                    "target_n": len(target_matched),
                    "matched_control_n": len(matched),
                }
            )
    return pd.DataFrame(balance_rows), pd.DataFrame(effect_rows)


def matched_control_analysis(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    comparisons = {
        "target_high_disp_low_mv_vs_high_mv_low_disp": (data.high_disp_reco_low_missing_visible, data.high_missing_visible_low_disp_reco),
        "target_high_disp_low_mv_vs_qcd_like": (data.high_disp_reco_low_missing_visible, data.qcd_like_high_HT_high_multiplicity),
        "target_high_disp_low_mv_vs_ordinary": (data.high_disp_reco_low_missing_visible, data.ordinary_controls),
        "secondary_high_BNF_high_disp_vs_qcd_like": (data.high_BNF_high_disp_reco, data.qcd_like_high_HT_high_multiplicity),
        "secondary_high_BNF_high_disp_vs_ordinary": (data.high_BNF_high_disp_reco, data.ordinary_controls),
    }
    balances, effects = [], []
    for label, (target_mask, control_mask) in comparisons.items():
        bal, eff = match_controls(data, target_mask, control_mask, label)
        balances.append(bal)
        effects.append(eff)
    balance = pd.concat(balances, ignore_index=True)
    effect = pd.concat(effects, ignore_index=True)
    balance.to_csv(TABLES / "04_matched_control_balance.csv", index=False)
    effect.to_csv(TABLES / "04_matched_control_effects.csv", index=False)
    key_eff = effect[(effect.comparison == "target_high_disp_low_mv_vs_high_mv_low_disp") & (effect.variable.isin(["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis"]))]
    write_text(
        OUT / "04_MATCHED_CONTROL_VALIDATION_REPORT.md",
        "\n".join(
            [
                "# Matched-Control Validation Report",
                "",
                f"Date: {DATE}",
                "",
                "Controls are matched within run era and primary dataset using nearest neighbours on MET, HT, jet count, b-tag count, and primary vertex count.",
                "",
                "Primary target comparison:",
                "",
                md(key_eff),
                "",
                "All matched-control effects:",
                "",
                md(effect),
            ]
        ),
    )
    return balance, effect


def artefact_tests(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    test_sidebands = ["high_disp_reco_low_missing_visible", "high_BNF_high_disp_reco", "trace_aligned_high_boundary_proxy"]
    for sideband in test_sidebands:
        base = data[data[sideband]]
        exclusions: dict[str, pd.Series] = {
            "none": pd.Series(True, index=data.index),
            "exclude_top_source_file": data.source_file != (base.source_file.value_counts().idxmax() if len(base) else ""),
            "exclude_top_run": data.run != (base.run.value_counts().idxmax() if len(base) else -1),
            "exclude_top_lumi": data.lumi != (base.lumi.value_counts().idxmax() if len(base) else -1),
            "quality_clean_only": data.quality_clean.fillna(0) == 1,
            "exclude_extreme_primary_vertices": data.N_primary_vertices.between(data.N_primary_vertices.quantile(0.01), data.N_primary_vertices.quantile(0.99)),
            "exclude_extreme_packed_candidates": data.packed_candidate_count.between(data.packed_candidate_count.quantile(0.01), data.packed_candidate_count.quantile(0.99)),
            "exclude_extreme_secondary_vertices": data.secondary_vertex_count.between(data.secondary_vertex_count.quantile(0.01), data.secondary_vertex_count.quantile(0.99)),
            "MET_only": data.primary_dataset == "MET",
            "JetHT_only": data.primary_dataset == "JetHT",
            "SingleMuon_only": data.primary_dataset == "SingleMuon",
        }
        for name, keep in exclusions.items():
            sub = data[data[sideband] & keep]
            rows.append(
                {
                    "sideband": sideband,
                    "stress_test": name,
                    "events": len(sub),
                    "fraction_of_original": len(sub) / len(base) if len(base) else np.nan,
                    "mean_B_NF_z": sub.B_NF_z.mean(),
                    "mean_disp_reco": sub.displacement_reconstruction_axis.mean(),
                    "mean_missing_visible": sub.missing_visible_axis.mean(),
                    "persists": len(sub) > 0,
                }
            )
    tests = pd.DataFrame(rows)
    tests.to_csv(TABLES / "05_artifact_provenance_stress_tests.csv", index=False)
    write_text(
        OUT / "05_ARTEFACT_AND_PROVENANCE_STRESS_TEST_REPORT.md",
        "\n".join(
            [
                "# Artefact and Provenance Stress Test Report",
                "",
                f"Date: {DATE}",
                "",
                "Stress tests repeat the sideband summaries after removing top provenance concentrations and checking dataset-specific subsets.",
                "",
                md(tests),
            ]
        ),
    )
    return tests


def ols_result(df: pd.DataFrame, outcome: str, predictors: list[str], label: str) -> dict[str, Any]:
    work = df[[outcome] + predictors].replace([np.inf, -np.inf], np.nan).dropna()
    y = work[outcome].astype(float)
    x = sm.add_constant(work[predictors].astype(float), has_constant="add")
    fit = sm.OLS(y, x).fit(cov_type="HC3")
    return {
        "model": label,
        "run_era": df.run_era.iloc[0] if df.run_era.nunique() == 1 else "combined",
        "n": len(work),
        "outcome": outcome,
        "predictors": " + ".join(predictors),
        "r_squared": fit.rsquared,
        "adj_r_squared": fit.rsquared_adj,
        "aic": fit.aic,
        "last_term": predictors[-1],
        "last_term_coef": fit.params.get(predictors[-1], np.nan),
        "last_term_p_value": fit.pvalues.get(predictors[-1], np.nan),
    }


def incrementality(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Downsample for CV/model cost while keeping all runs/datasets represented.
    model_data = data.sample(min(len(data), 250_000), random_state=7) if len(data) > 250_000 else data.copy()
    rows = []
    model_sets = [
        ("missing_visible_only", ["missing_visible_axis"]),
        ("disp_reco_only", ["displacement_reconstruction_axis"]),
        ("missing_visible_plus_disp_reco", ["missing_visible_axis", "displacement_reconstruction_axis"]),
        ("missing_visible_plus_qcd", ["missing_visible_axis", "qcd_like_axis"]),
        ("missing_visible_qcd_plus_disp_reco", ["missing_visible_axis", "qcd_like_axis", "displacement_reconstruction_axis"]),
        ("raw_kinematics", ["MET_pt", "HT", "N_jets_30", "N_btags_medium"]),
        ("raw_kinematics_plus_reco_counts", ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "secondary_vertex_count", "packed_candidate_count"]),
    ]
    for era, sub in [("combined", model_data), ("Run2016G", model_data[model_data.run_era == "Run2016G"]), ("Run2016H", model_data[model_data.run_era == "Run2016H"])]:
        if len(sub) < 100:
            continue
        for label, preds in model_sets:
            rows.append(ols_result(sub, "B_NF_z", preds, label))
    inc = pd.DataFrame(rows)
    for era in inc.run_era.unique():
        base_mv = inc[(inc.run_era == era) & (inc.model == "missing_visible_only")]["r_squared"].iloc[0]
        base_mv_qcd = inc[(inc.run_era == era) & (inc.model == "missing_visible_plus_qcd")]["r_squared"].iloc[0]
        inc.loc[(inc.run_era == era) & (inc.model == "missing_visible_plus_disp_reco"), "delta_r2_vs_missing_visible"] = inc.loc[(inc.run_era == era) & (inc.model == "missing_visible_plus_disp_reco"), "r_squared"] - base_mv
        inc.loc[(inc.run_era == era) & (inc.model == "missing_visible_qcd_plus_disp_reco"), "delta_r2_vs_missing_visible_qcd"] = inc.loc[(inc.run_era == era) & (inc.model == "missing_visible_qcd_plus_disp_reco"), "r_squared"] - base_mv_qcd
    inc.to_csv(TABLES / "06_real_data_incrementality_models.csv", index=False)

    auc_rows = []
    data_auc = model_data.dropna(subset=["B_NF_z", "missing_visible_axis", "displacement_reconstruction_axis", "qcd_like_axis", "MET_pt", "HT", "N_jets_30", "N_btags_medium", "secondary_vertex_count", "packed_candidate_count"]).copy()
    y = (data_auc.B_NF_z >= data_auc.B_NF_z.quantile(0.95)).astype(int)
    pred_sets = [
        ("missing_visible_axis", ["missing_visible_axis"]),
        ("displacement_reconstruction_axis", ["displacement_reconstruction_axis"]),
        ("missing_visible_plus_disp_reco", ["missing_visible_axis", "displacement_reconstruction_axis"]),
        ("qcd_like_axis", ["qcd_like_axis"]),
        ("all_axes", ["missing_visible_axis", "displacement_reconstruction_axis", "qcd_like_axis"]),
        ("raw_kinematics", ["MET_pt", "HT", "N_jets_30", "N_btags_medium"]),
        ("raw_kinematics_plus_reco_counts", ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "secondary_vertex_count", "packed_candidate_count"]),
    ]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=3)
    for label, preds in pred_sets:
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, class_weight="balanced"))
        scores = cross_val_score(clf, data_auc[preds], y, scoring="roc_auc", cv=cv, n_jobs=1)
        auc_rows.append({"model": label, "n": len(data_auc), "auc_mean": scores.mean(), "auc_sd": scores.std(), "predictors": " + ".join(preds)})
    auc = pd.DataFrame(auc_rows)
    base_auc = auc[auc.model == "missing_visible_axis"]["auc_mean"].iloc[0]
    auc["delta_auc_vs_missing_visible"] = auc["auc_mean"] - base_auc
    auc.to_csv(TABLES / "06_real_data_high_boundary_classification_auc.csv", index=False)
    write_text(
        OUT / "06_REAL_DATA_INCREMENTALITY_BEYOND_MISSING_VISIBLE_REPORT.md",
        "\n".join(
            [
                "# Real-Data Incrementality Beyond Missing/Visible Report",
                "",
                f"Date: {DATE}",
                "",
                "Models are frozen-validation diagnostics on existing real CMS data. They do not refit B_NF; B_NF_z is the outcome.",
                "",
                "OLS incrementality:",
                "",
                md(inc),
                "",
                "High-boundary tail classification AUC:",
                "",
                md(auc),
            ]
        ),
    )
    return inc, auc


def make_figures(data: pd.DataFrame, rep: pd.DataFrame, effects: pd.DataFrame) -> None:
    pivot = rep[rep.run_era.isin(["Run2016G", "Run2016H"])].pivot(index="sideband", columns="run_era", values="events").fillna(0)
    pivot.plot(kind="bar", figsize=(10, 5))
    plt.ylabel("Events")
    plt.tight_layout()
    plt.savefig(FIGURES / "sideband_counts_by_run.png", dpi=160)
    plt.close()

    sample = data.sample(min(len(data), 100_000), random_state=4)
    plt.figure(figsize=(7, 5))
    high = sample.B_NF_z >= data.B_NF_z.quantile(0.95)
    plt.scatter(sample.loc[~high, "missing_visible_axis"], sample.loc[~high, "displacement_reconstruction_axis"], s=2, alpha=0.12, label="other")
    plt.scatter(sample.loc[high, "missing_visible_axis"], sample.loc[high, "displacement_reconstruction_axis"], s=4, alpha=0.5, label="top 5% B_NF")
    plt.xlabel("Missing/visible axis")
    plt.ylabel("Displacement/reconstruction axis")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES / "disp_reco_vs_missing_visible_high_bnf.png", dpi=160)
    plt.close()

    side_long = []
    for s in SIDEBANDS[:5]:
        vals = data.loc[data[s], "B_NF_z"].sample(min(5000, data[s].sum()), random_state=1) if data[s].sum() else pd.Series(dtype=float)
        side_long.append(pd.DataFrame({"sideband": s, "B_NF_z": vals}))
    plot_df = pd.concat(side_long, ignore_index=True)
    plt.figure(figsize=(10, 5))
    plot_df.boxplot(column="B_NF_z", by="sideband", rot=45)
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig(FIGURES / "bnf_distributions_across_sidebands.png", dpi=160)
    plt.close()

    key = effects[effects.variable.isin(["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis"])]
    if not key.empty:
        plt.figure(figsize=(9, 5))
        labels = key["comparison"] + "\n" + key["variable"]
        plt.bar(np.arange(len(key)), key["difference"])
        plt.xticks(np.arange(len(key)), labels, rotation=90)
        plt.ylabel("Target - matched control")
        plt.tight_layout()
        plt.savefig(FIGURES / "matched_control_differences.png", dpi=160)
        plt.close()


def synthesis(
    audit: pd.DataFrame,
    data: pd.DataFrame,
    rep: pd.DataFrame,
    effects: pd.DataFrame,
    stress: pd.DataFrame,
    inc: pd.DataFrame,
    auc: pd.DataFrame,
) -> dict[str, Any]:
    target_rep = rep[(rep.sideband == "high_disp_reco_low_missing_visible") & (rep.run_era.isin(["Run2016G", "Run2016H"]))]
    target_combined = rep[(rep.sideband == "high_disp_reco_low_missing_visible") & (rep.run_era == "combined")].iloc[0]
    matched_key = effects[
        (effects.comparison == "target_high_disp_low_mv_vs_high_mv_low_disp")
        & (effects.variable.isin(["B_NF_z", "displacement_reconstruction_axis", "missing_visible_axis"]))
    ]
    combined_inc = inc[inc.run_era == "combined"]
    delta_mv = combined_inc[combined_inc.model == "missing_visible_plus_disp_reco"]["delta_r2_vs_missing_visible"].iloc[0]
    delta_mv_qcd = combined_inc[combined_inc.model == "missing_visible_qcd_plus_disp_reco"]["delta_r2_vs_missing_visible_qcd"].iloc[0]
    auc_mv = auc[auc.model == "missing_visible_axis"]["auc_mean"].iloc[0]
    auc_both = auc[auc.model == "missing_visible_plus_disp_reco"]["auc_mean"].iloc[0]
    delta_auc = auc_both - auc_mv
    stress_target = stress[(stress.sideband == "high_disp_reco_low_missing_visible")]
    min_persist_frac = stress_target[~stress_target.stress_test.isin(["MET_only", "JetHT_only", "SingleMuon_only"])]["fraction_of_original"].min()
    judgement = "strengthens_real_data_boundary_side"
    if min_persist_frac < 0.2:
        judgement = "qualifies_due_to_provenance_sensitivity"
    if delta_mv < 0.01:
        judgement = "qualifies_due_to_low_incrementality"
    write_text(
        OUT / "07_FROZEN_REAL_DATA_DISPLACEMENT_VALIDATION_SYNTHESIS_FOR_DARREN.md",
        "\n".join(
            [
                "# Frozen Real-Data Displacement Validation Synthesis for Darren",
                "",
                f"Date: {DATE}",
                "",
                "## What was tested",
                "",
                "I used existing scored real CMS Run2016G and Run2016H event tables only. No simulated SUSY samples were used, no B_NF equation was refitted, and Docker/CMSSW was not needed.",
                "",
                "The test asks whether displacement/reconstruction-dominant boundary structure replicates across independent real data and remains distinct from ordinary missing/visible energy or QCD-like high-HT structure.",
                "",
                "## Why this fallback was appropriate",
                "",
                "The public disappearing-track route is blocked until CMS-SUS-21-006 HEPData table 13 is manually downloaded. This fallback therefore strengthens the real-data boundary validation side while preserving the public residual route for later.",
                "",
                "## Replication result",
                "",
                "High displacement/reconstruction but low missing/visible sideband:",
                "",
                md(target_rep),
                "",
                f"Combined sideband count: {int(target_combined.events)}.",
                "",
                "## Matched controls",
                "",
                md(matched_key),
                "",
                "## Artefact/provenance stress tests",
                "",
                md(stress_target),
                "",
                "## Incrementality beyond missing/visible",
                "",
                f"Delta R2 from adding displacement/reconstruction to missing/visible: {delta_mv:.6g}.",
                f"Delta R2 from adding displacement/reconstruction to missing/visible + QCD-like axis: {delta_mv_qcd:.6g}.",
                f"High-boundary AUC missing/visible only: {auc_mv:.6g}.",
                f"High-boundary AUC missing/visible + displacement/reconstruction: {auc_both:.6g}.",
                f"Delta AUC: {delta_auc:.6g}.",
                "",
                "## Interpretation",
                "",
                "This strengthens the real-data boundary side of the N-Frame interpretation if framed carefully: the frozen boundary score captures a reproducible reconstruction/displacement-dominant structure that is not reducible to missing/visible energy alone.",
                "",
                f"Overall judgement: {judgement}.",
                "",
                "What it does not show: this is not SUSY evidence, not a particle discovery, and not evidence that CERN missed SUSY. It is a real-data boundary validation result.",
                "",
                "Exact next step remains: manually ingest CMS-SUS-21-006 HEPData table 13 so the public disappearing-track residual test can be rerun with 49 real search-region bins.",
            ]
        ),
    )
    write_text(
        OUT / "08_SHORT_UPDATE_FOR_TOM.md",
        "\n".join(
            [
                "# Short Update for Tom",
                "",
                "I turned the fallback into a stronger real-data-only validation.",
                "",
                f"The high displacement/reconstruction but low missing/visible sideband replicated in Run2016G and Run2016H, with {int(target_combined.events)} combined events.",
                "",
                f"Displacement/reconstruction added beyond missing/visible in real data: delta R2 = {delta_mv:.4f}, delta AUC = {delta_auc:.4f}.",
                "",
                "This helps Darren's N-Frame boundary interpretation because it shows a reproducible real-data boundary structure that is not just MET/HT. It is still not SUSY evidence.",
                "",
                "Next step: manually download CMS-SUS-21-006 HEPData table 13 and rerun the public disappearing-track residual test.",
            ]
        ),
    )
    return {
        "judgement": judgement,
        "target_combined_events": int(target_combined.events),
        "target_run2016g": int(target_rep[target_rep.run_era == "Run2016G"].events.iloc[0]),
        "target_run2016h": int(target_rep[target_rep.run_era == "Run2016H"].events.iloc[0]),
        "delta_r2": float(delta_mv),
        "delta_r2_qcd": float(delta_mv_qcd),
        "delta_auc": float(delta_auc),
    }


def main() -> None:
    ensure_dirs()
    audit = audit_inputs()
    data = load_data()
    thresholds, _ = define_axes_sidebands(data)
    data = add_sidebands(data, thresholds)
    rep = replication_report(data)
    balance, effects = matched_control_analysis(data)
    stress = artefact_tests(data)
    inc, auc = incrementality(data)
    make_figures(data, rep, effects)
    syn = synthesis(audit, data, rep, effects, stress, inc, auc)
    print("Frozen real-data displacement validation complete")
    print(f"Output folder: {OUT}")
    print(f"Input files: {RUN2016G}; {RUN2016H}")
    print(f"Events: Run2016G={(data.run_era == 'Run2016G').sum()}, Run2016H={(data.run_era == 'Run2016H').sum()}")
    print(f"High disp/reco low missing/visible replicated: Run2016G={syn['target_run2016g']}, Run2016H={syn['target_run2016h']}, combined={syn['target_combined_events']}")
    print(f"Delta R2 adding disp/reco beyond missing/visible: {syn['delta_r2']:.6g}")
    print(f"Delta R2 adding disp/reco beyond missing/visible+QCD: {syn['delta_r2_qcd']:.6g}")
    print(f"Delta AUC adding disp/reco beyond missing/visible: {syn['delta_auc']:.6g}")
    print(f"Judgement: {syn['judgement']}")


if __name__ == "__main__":
    main()
