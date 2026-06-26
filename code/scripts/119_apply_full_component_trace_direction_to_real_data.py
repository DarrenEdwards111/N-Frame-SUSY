from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from fuller_component_common import FAMILIES
from susy_signal_common import DATE, REPORTS, ROOT, TABLES


TRACE = ROOT / "data" / "processed" / "trace_direction"
FILES = {
    "Run2016G": TRACE / "run2016g_real_with_trace_direction.csv",
    "Run2016H": TRACE / "run2016h_real_with_trace_direction.csv",
    "combined": TRACE / "combined_real_with_trace_direction.csv",
}
COMPONENTS = list(FAMILIES.keys())


def choose_direction(weights: pd.DataFrame) -> str:
    tests = pd.read_csv(TABLES / "full_component_signal_vs_background_corrected_tests.csv")
    q95 = tests[(tests["threshold"].eq("q95")) & (tests["background_process"].eq("QCD HT1000to1500"))]
    if not q95.empty:
        best = q95.sort_values("risk_difference", ascending=False).iloc[0]["signal_sample"]
        direction = f"{best}_vs_qcd_ht1000to1500"
        if direction in set(weights["direction"]):
            return direction
    return weights["direction"].iloc[0]


def main() -> None:
    weights_all = pd.read_csv(TABLES / "full_component_trace_direction_weights.csv")
    means = pd.read_csv(TABLES / "full_component_trace_direction_component_means.csv").set_index("sample_id")
    direction = choose_direction(weights_all)
    weights = weights_all[weights_all["direction"].eq(direction)].set_index("component")["unit_weight"].to_dict()
    signal_sample = weights_all[weights_all["direction"].eq(direction)]["signal_sample"].iloc[0]
    qcd_sample = weights_all[weights_all["direction"].eq(direction)]["background_sample"].iloc[0]
    sig_centroid = means.loc[signal_sample, COMPONENTS].to_numpy(float)
    qcd_centroid = means.loc[qcd_sample, COMPONENTS].to_numpy(float)
    rows, dist_rows = [], []
    for dataset, path in FILES.items():
        df = pd.read_csv(path, low_memory=False)
        for c in COMPONENTS:
            if c not in df.columns and f"B_{c}" in df.columns:
                df[c] = df[f"B_{c}"]
        df["Trace_full_component_signal_vs_qcd"] = sum(float(weights[c]) * df[c].fillna(0) for c in COMPONENTS)
        base = "B_NF_trace_base" if "B_NF_trace_base" in df.columns else "B_NF_fitted_raw"
        for label, q in [("top05", 0.95), ("top01", 0.99), ("top001", 0.999)]:
            threshold = df[base].quantile(q)
            high = df[df[base] >= threshold]
            rest = df[df[base] < threshold]
            res = stats.ttest_ind(high["Trace_full_component_signal_vs_qcd"], rest["Trace_full_component_signal_vs_qcd"], equal_var=False, alternative="greater")
            trace_q90 = df["Trace_full_component_signal_vs_qcd"].quantile(0.90)
            kh = float((high["Trace_full_component_signal_vs_qcd"] >= trace_q90).mean())
            kr = float((rest["Trace_full_component_signal_vs_qcd"] >= trace_q90).mean())
            rows.append({
                "dataset": dataset,
                "direction": direction,
                "bnf_tail": label,
                "high_events": len(high),
                "mean_trace_high": high["Trace_full_component_signal_vs_qcd"].mean(),
                "mean_trace_rest": rest["Trace_full_component_signal_vs_qcd"].mean(),
                "mean_diff": high["Trace_full_component_signal_vs_qcd"].mean() - rest["Trace_full_component_signal_vs_qcd"].mean(),
                "welch_p": res.pvalue,
                "welch_z": float(stats.norm.isf(res.pvalue)) if res.pvalue > 0 else np.inf,
                "fraction_high_above_trace_q90": kh,
                "fraction_rest_above_trace_q90": kr,
                "enrichment_ratio": kh / kr if kr else np.inf,
            })
            x = high[COMPONENTS].fillna(0).to_numpy(float)
            d_sig = np.linalg.norm(x - sig_centroid, axis=1)
            d_qcd = np.linalg.norm(x - qcd_centroid, axis=1)
            dist_rows.append({
                "dataset": dataset,
                "direction": direction,
                "bnf_tail": label,
                "events": len(high),
                "mean_distance_to_signal": d_sig.mean(),
                "mean_distance_to_qcd_ht1000": d_qcd.mean(),
                "fraction_closer_to_signal_than_qcd": float((d_sig < d_qcd).mean()),
            })
        df.to_csv(TRACE / f"{dataset.lower()}_real_with_full_component_signal_qcd_trace_direction.csv", index=False)
    align = pd.DataFrame(rows)
    dist = pd.DataFrame(dist_rows)
    align.to_csv(TABLES / "full_component_trace_alignment_real_data.csv", index=False)
    dist.to_csv(TABLES / "full_component_real_signal_vs_qcd_distances.csv", index=False)
    report = [
        "# Full Component Real Trace Alignment Report",
        "",
        f"Date: {DATE}",
        "",
        f"Applied direction: `{direction}`",
        "",
        "## Alignment",
        "",
        align.to_markdown(index=False),
        "",
        "## Distances",
        "",
        dist.to_markdown(index=False),
    ]
    (REPORTS / "FULL_COMPONENT_REAL_TRACE_ALIGNMENT_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(align.to_string(index=False))


if __name__ == "__main__":
    main()
