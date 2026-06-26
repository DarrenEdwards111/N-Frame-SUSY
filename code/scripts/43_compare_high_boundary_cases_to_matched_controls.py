from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "data" / "processed" / "matched_control"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
FEATURES = [
    "MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "max_btag_discriminator",
    "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count", "compression_proxy_raw",
    "displacement_proxy_raw", "R_missing", "R_visible_energy", "R_multiplicity", "R_btag_structure",
    "R_reconstruction_complexity", "R_compression_proxy", "R_displacement_proxy", "B_boundary_hand_defined_z",
    "real_only_unsupervised_boundary_score", "mc_B_boundary_hand_defined_z", "mc_unsupervised_boundary_score",
]
TRIG = ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"]
FILTERS = ["pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter", "pass_goodVertices", "pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter"]


def load_events(path):
    df = pd.read_csv(path)
    if "real_only_unsupervised_boundary_score" not in df and "trigger_filter_unsupervised_boundary_score" in df:
        df["real_only_unsupervised_boundary_score"] = df["trigger_filter_unsupervised_boundary_score"]
    df["event_uid"] = df["source_file_stem"].astype(str) + ":" + df["run"].astype(str) + ":" + df["lumi"].astype(str) + ":" + df["event"].astype(str)
    return df.set_index("event_uid", drop=False)


def ci_boot(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(42)
    means = [rng.choice(x, size=len(x), replace=True).mean() for _ in range(300)]
    return np.quantile(means, [0.025, 0.975])


def compare(match_file, events):
    m = pd.read_csv(match_file)
    if m.empty:
        return pd.DataFrame(), pd.DataFrame()
    case = events.loc[m.case_event_id].reset_index(drop=True)
    ctrl = events.loc[m.control_event_id].reset_index(drop=True)
    meta = m[["quality_subset", "boundary_score_type", "tail_definition", "case_event_id"]].reset_index(drop=True)
    rows = []
    for feat in [f for f in FEATURES if f in events.columns]:
        diff = pd.to_numeric(case[feat], errors="coerce") - pd.to_numeric(ctrl[feat], errors="coerce")
        diff_by_case = pd.concat([meta["case_event_id"], diff.rename("diff")], axis=1).groupby("case_event_id")["diff"].mean()
        t_p = stats.ttest_1samp(diff_by_case.dropna(), 0).pvalue if diff_by_case.notna().sum() > 2 else np.nan
        try:
            w_p = stats.wilcoxon(diff_by_case.dropna()).pvalue if diff_by_case.notna().sum() > 5 and not np.allclose(diff_by_case.dropna(), 0) else np.nan
        except ValueError:
            w_p = np.nan
        lo, hi = ci_boot(diff_by_case)
        rows.append({
            "match_file": match_file.name, "quality_subset": m.quality_subset.iloc[0],
            "boundary_score_type": m.boundary_score_type.iloc[0], "tail_definition": m.tail_definition.iloc[0],
            "feature": feat, "matched_cases": m.case_event_id.nunique(), "matched_pairs": len(m),
            "case_mean": pd.to_numeric(case[feat], errors="coerce").mean(), "control_mean": pd.to_numeric(ctrl[feat], errors="coerce").mean(),
            "paired_mean_difference": diff_by_case.mean(), "paired_median_difference": diff_by_case.median(),
            "standardised_paired_mean_difference": diff_by_case.mean() / diff_by_case.std(ddof=0) if diff_by_case.std(ddof=0) else np.nan,
            "bootstrap_ci_low": lo, "bootstrap_ci_high": hi, "paired_t_p": t_p, "wilcoxon_p": w_p,
        })
    bal_rows = []
    for col in TRIG + FILTERS + ["same_source_file", "same_run", "same_trigger_combo"]:
        if col in events.columns:
            bal_rows.append({"match_file": match_file.name, "variable": col, "case_mean": case[col].mean(), "control_mean": ctrl[col].mean(), "absolute_difference": abs(case[col].mean() - ctrl[col].mean())})
        elif col in m.columns:
            bal_rows.append({"match_file": match_file.name, "variable": col, "case_mean": 1.0, "control_mean": m[col].mean(), "absolute_difference": abs(1.0 - m[col].mean())})
    return pd.DataFrame(rows), pd.DataFrame(bal_rows)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    event_sets = {
        "standard_quality_clean": load_events(IN / "standard_quality_clean_events_rescored.csv"),
        "relaxed_quality_clean": load_events(IN / "relaxed_quality_clean_events_rescored.csv"),
    }
    diffs, bals = [], []
    for mf in sorted(IN.glob("matched_controls_*.csv")):
        subset = "relaxed_quality_clean" if "relaxed_quality_clean" in mf.name else "standard_quality_clean"
        d, b = compare(mf, event_sets[subset])
        if not d.empty:
            diffs.append(d)
            bals.append(b)
    diff = pd.concat(diffs, ignore_index=True)
    bal = pd.concat(bals, ignore_index=True)
    components = diff[diff.feature.str.startswith("R_") | diff.feature.str.startswith("mc_R_") | diff.feature.str.contains("boundary")]
    diff.to_csv(TABLES / "matched_case_control_feature_differences.csv", index=False)
    components.to_csv(TABLES / "matched_case_control_boundary_component_differences.csv", index=False)
    bal.to_csv(TABLES / "matched_control_balance_diagnostics.csv", index=False)
    strongest = diff[diff.match_file.isin(["matched_controls_hand_top01.csv", "matched_controls_unsup_top01.csv"])].sort_values("standardised_paired_mean_difference", key=lambda s: s.abs(), ascending=False).head(25)
    report = ["# Matched Control Comparison Report", "", "Date: 2026-06-08", "", "Cases were compared with matched controls using paired differences averaged by case event. This is real CMS collision data only.", "", "## Strongest Paired Differences", "", strongest.to_markdown(index=False), "", "## Balance Diagnostics", "", bal.groupby("variable").absolute_difference.mean().reset_index().to_markdown(index=False)]
    (REPORTS / "MATCHED_CONTROL_COMPARISON_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(strongest[["match_file", "feature", "paired_mean_difference", "standardised_paired_mean_difference", "wilcoxon_p"]].to_string(index=False))


if __name__ == "__main__":
    main()
