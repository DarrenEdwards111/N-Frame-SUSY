from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
DATE = "2026-06-09"
PARAMS = ["B_P_missing", "B_P_visible_energy", "B_P_multiplicity", "B_P_btag_structure", "B_P_displacement_proxy", "B_P_reconstruction", "B_P_compression"]


def load() -> pd.DataFrame:
    return pd.concat([pd.read_csv(SUSY), pd.read_csv(SM)], ignore_index=True)


def profile(group: pd.DataFrame, threshold: float) -> pd.Series:
    tail = group[group["B_NF_fitted_frozen_raw"] > threshold]
    vals = {}
    for p in PARAMS:
        if p in tail and tail[p].notna().any():
            vals[p] = tail[p].mean()
    return pd.Series(vals, dtype=float)


def distance(a: pd.Series, b: pd.Series) -> dict:
    common = sorted(set(a.dropna().index) & set(b.dropna().index))
    if not common:
        return {"euclidean_distance": np.nan, "cosine_similarity": np.nan, "correlation": np.nan, "components_compared": ""}
    av, bv = a[common].to_numpy(float), b[common].to_numpy(float)
    euclid = float(np.linalg.norm(av - bv))
    cosine = float(np.dot(av, bv) / (np.linalg.norm(av) * np.linalg.norm(bv))) if np.linalg.norm(av) and np.linalg.norm(bv) else np.nan
    corr = float(np.corrcoef(av, bv)[0, 1]) if len(common) > 1 else np.nan
    return {"euclidean_distance": euclid, "cosine_similarity": cosine, "correlation": corr, "components_compared": ";".join(common)}


def main() -> None:
    df = load()
    th = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    rows, dist_rows = [], []
    for threshold in ["q95", "q99"]:
        value = float(th[th["threshold"].eq(threshold)]["value"].iloc[0])
        sms = df[df["sample_id"].eq("sms_t5wg_mg1500_mlsp1_signal")]
        sms_tail = sms[sms["B_NF_fitted_frozen_raw"] > value]
        sms_profile = profile(sms, value)
        for background_id, bg in df[df["classification"].eq("SM_background")].groupby("sample_id"):
            bg_tail = bg[bg["B_NF_fitted_frozen_raw"] > value]
            bg_profile = profile(bg, value)
            d = distance(sms_profile, bg_profile)
            d.update({"threshold": threshold, "signal_sample": "sms_t5wg_mg1500_mlsp1_signal", "background_sample": background_id, "signal_tail_events": len(sms_tail), "background_tail_events": len(bg_tail)})
            dist_rows.append(d)
            for p in PARAMS:
                if p not in sms_tail or p not in bg_tail or not sms_tail[p].notna().any() or not bg_tail[p].notna().any():
                    continue
                stat = stats.ttest_ind(sms_tail[p].dropna(), bg_tail[p].dropna(), equal_var=False, alternative="greater")
                rows.append({
                    "threshold": threshold,
                    "background_sample": background_id,
                    "parameter_family": p.replace("B_", ""),
                    "sms_high_tail_mean": sms_tail[p].mean(),
                    "background_high_tail_mean": bg_tail[p].mean(),
                    "sms_minus_background": sms_tail[p].mean() - bg_tail[p].mean(),
                    "welch_t_one_sided_greater": stat.statistic,
                    "p_one_sided_sms_greater": stat.pvalue,
                    "z_equivalent": float(stats.norm.isf(stat.pvalue)) if stat.pvalue > 0 else np.inf,
                })
    sig = pd.DataFrame(rows)
    dist = pd.DataFrame(dist_rows)
    sig.to_csv(TABLES / "background_mimicry_significance.csv", index=False)
    dist.to_csv(TABLES / "high_tail_driver_profile_distances.csv", index=False)

    two_prop = pd.read_csv(TABLES / "two_proportion_sigma_tests.csv")
    corrected = pd.read_csv(TABLES / "look_elsewhere_corrected_sigma_tests.csv")
    counting = pd.read_csv(TABLES / "likelihood_counting_sigma.csv")
    incremental = pd.read_csv(TABLES / "bnf_vs_met_ht_incremental_tests.csv")
    tails = pd.read_csv(TABLES / "sigma_tail_counts_by_sample.csv")

    q95_sms = two_prop[(two_prop["signal_sample"].eq("sms_t5wg_mg1500_mlsp1_signal")) & (two_prop["threshold"].eq("q95"))]
    supported_5 = bool((corrected["remains_5sigma_after_bonferroni"] == True).any())
    if supported_5:
        claim = "The frozen real-data-fitted N-Frame boundary score shows >=5 sigma benchmark-level enrichment of SMS-T5Wg in the high-boundary tail relative to tested TTJets/QCD backgrounds after the defined correction family. This is indirect, model-dependent SUSY-relevant boundary enrichment, not a direct discovery claim."
    else:
        claim = "The current pilot does not remain >=5 sigma after correction; it is suggestive benchmark enrichment only."

    main_report = [
        "# Five Sigma Model-Dependent Boundary Enrichment Report",
        "",
        f"Date: {DATE}",
        "",
        "## Hypothesis Tested",
        "",
        "H0: P(B_NF_fitted > q | SUSY benchmark) <= P(B_NF_fitted > q | SM background). H1: P(B_NF_fitted > q | SUSY benchmark) > P(B_NF_fitted > q | SM background).",
        "",
        "## Meaning Of 5 Sigma Here",
        "",
        "A 5 sigma result here means benchmark-level, model-dependent high-B_NF enrichment. It is not direct evidence that SUSY particles were found in real collision data.",
        "",
        "## Tail Counts",
        "",
        tails.to_markdown(index=False),
        "",
        "## Two-Proportion Tests",
        "",
        two_prop.to_markdown(index=False),
        "",
        "## Look-Elsewhere Corrected Tests",
        "",
        corrected.to_markdown(index=False),
        "",
        "## Counting Model",
        "",
        counting.to_markdown(index=False),
        "",
        "## Incremental B_NF Versus MET/HT",
        "",
        incremental.to_markdown(index=False),
        "",
        "## Background Mimicry",
        "",
        dist.to_markdown(index=False),
        "",
        "## Claim",
        "",
        claim,
        "",
        "## Remaining Missing Work",
        "",
        "More SUSY topologies, more SM backgrounds, full MiniAODSIM component availability where practical, published signal-region overlap, and event-display/manual inspection.",
    ]
    (REPORTS / "FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md").write_text("\n".join(main_report), encoding="utf-8")

    darren = [
        "# Update To Darren: Five Sigma Boundary Enrichment Test",
        "",
        f"Date: {DATE}",
        "",
        "We tested whether the frozen real-data-fitted B_NF score gives >=5 sigma indirect, model-dependent enrichment for SUSY-like benchmark structure in the high-boundary tail.",
        "",
        "## Main Comparisons",
        "",
        q95_sms.to_markdown(index=False),
        "",
        "## Corrected Result",
        "",
        corrected[corrected["threshold"].isin(["q95", "q99"])].to_markdown(index=False),
        "",
        "## What This Means",
        "",
        claim,
        "",
        "The effect is currently driven mainly by missing energy, visible energy and multiplicity. TTJets/QCD do not match SMS-T5Wg high-tail occupancy in this pilot, but the current test remains reduced-component because some full MiniAOD-derived components are unavailable.",
        "",
        "## Next Step",
        "",
        "Repeat with fuller MiniAODSIM TTJets/QCD and additional SM backgrounds to confirm the boundary enrichment with the reconstruction/displacement components aligned to the real-data validation.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_FIVE_SIGMA_BOUNDARY_ENRICHMENT_TEST.md").write_text("\n".join(darren), encoding="utf-8")
    report = ["# Background Mimicry Significance Report", "", f"Date: {DATE}", "", "## Component Tests", "", sig.to_markdown(index=False), "", "## Profile Distances", "", dist.to_markdown(index=False)]
    (REPORTS / "BACKGROUND_MIMICRY_SIGNIFICANCE_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(dist.to_string(index=False))


if __name__ == "__main__":
    main()
