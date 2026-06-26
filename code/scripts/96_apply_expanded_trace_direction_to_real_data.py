from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
FILES = {
    "Run2016G": TRACE / "run2016g_real_with_trace_direction.csv",
    "Run2016H": TRACE / "run2016h_real_with_trace_direction.csv",
    "combined": TRACE / "combined_real_with_trace_direction.csv",
}
COMPONENTS = ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression"]


def main():
    weights = pd.read_csv(TABLES / "expanded_trace_direction_weights.csv").set_index("component")["unit_weight"].to_dict()
    rows = []
    dist_rows = []
    means = pd.read_csv(TABLES / "expanded_trace_direction_component_means.csv").set_index("sample_id")
    sms = means.loc["sms_t5wg_mg1500_mlsp1_signal", COMPONENTS].to_numpy(float)
    sm = means.loc["expanded_pooled_sm", COMPONENTS].to_numpy(float)
    for dataset, path in FILES.items():
        df = pd.read_csv(path, low_memory=False)
        df["Trace_expanded_SMS_vs_SM"] = sum(float(weights[c]) * df[c].fillna(0) for c in COMPONENTS)
        for label, q in [("top05", .95), ("top01", .99), ("top001", .999)]:
            high = df[df["B_NF_trace_base"] >= df["B_NF_trace_base"].quantile(q)]
            rest = df[df["B_NF_trace_base"] < df["B_NF_trace_base"].quantile(q)]
            res = stats.ttest_ind(high["Trace_expanded_SMS_vs_SM"], rest["Trace_expanded_SMS_vs_SM"], equal_var=False, alternative="greater")
            trace_q90 = df["Trace_expanded_SMS_vs_SM"].quantile(.90)
            kh, kr = (high["Trace_expanded_SMS_vs_SM"] >= trace_q90).mean(), (rest["Trace_expanded_SMS_vs_SM"] >= trace_q90).mean()
            rows.append({"dataset": dataset, "bnf_tail": label, "high_events": len(high), "mean_expanded_trace_high": high["Trace_expanded_SMS_vs_SM"].mean(), "mean_expanded_trace_rest": rest["Trace_expanded_SMS_vs_SM"].mean(), "mean_diff": high["Trace_expanded_SMS_vs_SM"].mean() - rest["Trace_expanded_SMS_vs_SM"].mean(), "welch_p": res.pvalue, "welch_z": float(stats.norm.isf(res.pvalue)) if res.pvalue > 0 else np.inf, "fraction_high_above_trace_q90": kh, "fraction_rest_above_trace_q90": kr, "enrichment_ratio": kh/kr if kr else np.inf})
            x = high[COMPONENTS].fillna(0).to_numpy(float)
            d_sms = np.linalg.norm(x - sms, axis=1)
            d_sm = np.linalg.norm(x - sm, axis=1)
            dist_rows.append({"dataset": dataset, "bnf_tail": label, "events": len(high), "mean_distance_to_SMS": d_sms.mean(), "mean_distance_to_expanded_pooledSM": d_sm.mean(), "fraction_closer_to_SMS_than_expandedSM": float((d_sms < d_sm).mean())})
        df.to_csv(TRACE / f"{dataset.lower()}_real_with_expanded_trace_direction.csv", index=False)
    align = pd.DataFrame(rows)
    dist = pd.DataFrame(dist_rows)
    align.to_csv(TABLES / "expanded_real_trace_alignment_summary.csv", index=False)
    dist.to_csv(TABLES / "expanded_real_sms_vs_sm_distance_tests.csv", index=False)
    report = ["# Expanded Real Trace Alignment Report", "", f"Date: {DATE}", "", "## Alignment", "", align.to_markdown(index=False), "", "## Distance Tests", "", dist.to_markdown(index=False)]
    (REPORTS / "EXPANDED_REAL_TRACE_ALIGNMENT_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(align.to_string(index=False))
    print(dist.to_string(index=False))


if __name__ == "__main__":
    main()
