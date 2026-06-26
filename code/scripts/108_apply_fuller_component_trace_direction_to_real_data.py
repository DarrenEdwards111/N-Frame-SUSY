from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError
from scipy import stats

from fuller_component_common import DATE, FAMILIES, REPORTS, ROOT, TABLES


TRACE = ROOT / "data" / "processed" / "trace_direction"
FILES = {
    "Run2016G": TRACE / "run2016g_real_with_trace_direction.csv",
    "Run2016H": TRACE / "run2016h_real_with_trace_direction.csv",
    "combined": TRACE / "combined_real_with_trace_direction.csv",
}
COMPONENTS = list(FAMILIES.keys())


def main() -> None:
    weights_path = TABLES / "fuller_component_trace_direction_weights.csv"
    try:
        weights_existing = pd.read_csv(weights_path) if weights_path.exists() else pd.DataFrame()
    except EmptyDataError:
        weights_existing = pd.DataFrame()
    if weights_existing.empty:
        summary = pd.DataFrame([{
            "status": "not_run",
            "reason": "No accessible MiniAODSIM signal sample survived download/smoke extraction, so no full-component signal-vs-SM direction could be defined.",
            "fallback_available": (TABLES / "expanded_real_trace_alignment_summary.csv").exists(),
            "fallback_table": str(TABLES / "expanded_real_trace_alignment_summary.csv"),
        }])
        summary.to_csv(TABLES / "fuller_component_real_trace_alignment_summary.csv", index=False)
        pd.DataFrame().to_csv(TABLES / "fuller_component_real_signal_vs_sm_distance_tests.csv", index=False)
        (REPORTS / "FULLER_COMPONENT_REAL_TRACE_ALIGNMENT_REPORT.md").write_text(
            "# Fuller Component Real Trace Alignment Report\n\n"
            f"Date: {DATE}\n\n"
            "No fuller-component signal direction was applied to real data because the selected MiniAODSIM signal file was inaccessible at the advertised CERN EOS path. "
            "The earlier expanded reduced-component SMS-T5Wg trace alignment remains the available fallback, but it is not a full-component MiniAODSIM validation.\n\n"
            + summary.to_markdown(index=False),
            encoding="utf-8",
        )
        print(summary.to_string(index=False))
        return
    weights_all = weights_existing
    direction = weights_all["direction"].iloc[0]
    weights = weights_all[weights_all["direction"].eq(direction)].set_index("component")["unit_weight"].to_dict()
    means = pd.read_csv(TABLES / "fuller_component_trace_direction_component_means.csv").set_index("sample_id")
    sig_sample = direction.split("_vs_fuller_pooled_sm")[0]
    sig = means.loc[sig_sample, COMPONENTS].to_numpy(float)
    sm = means.loc["fuller_pooled_sm", COMPONENTS].to_numpy(float)
    rows, dist_rows = [], []
    for dataset, path in FILES.items():
        df = pd.read_csv(path, low_memory=False)
        for c in COMPONENTS:
            if c not in df.columns and f"B_{c}" in df.columns:
                df[c] = df[f"B_{c}"]
        df["Trace_fuller_component_T2tt_vs_SM"] = sum(float(weights[c]) * df[c].fillna(0) for c in COMPONENTS)
        base = "B_NF_trace_base" if "B_NF_trace_base" in df.columns else "B_NF_fitted_frozen_raw"
        for label, q in [("top05", 0.95), ("top01", 0.99), ("top001", 0.999)]:
            threshold = df[base].quantile(q)
            high = df[df[base] >= threshold]
            rest = df[df[base] < threshold]
            res = stats.ttest_ind(high["Trace_fuller_component_T2tt_vs_SM"], rest["Trace_fuller_component_T2tt_vs_SM"], equal_var=False, alternative="greater")
            trace_q90 = df["Trace_fuller_component_T2tt_vs_SM"].quantile(0.90)
            kh = (high["Trace_fuller_component_T2tt_vs_SM"] >= trace_q90).mean()
            kr = (rest["Trace_fuller_component_T2tt_vs_SM"] >= trace_q90).mean()
            rows.append({
                "dataset": dataset,
                "direction": direction,
                "bnf_tail": label,
                "high_events": len(high),
                "mean_trace_high": high["Trace_fuller_component_T2tt_vs_SM"].mean(),
                "mean_trace_rest": rest["Trace_fuller_component_T2tt_vs_SM"].mean(),
                "mean_diff": high["Trace_fuller_component_T2tt_vs_SM"].mean() - rest["Trace_fuller_component_T2tt_vs_SM"].mean(),
                "welch_p": res.pvalue,
                "welch_z": float(stats.norm.isf(res.pvalue)) if res.pvalue > 0 else np.inf,
                "fraction_high_above_trace_q90": kh,
                "fraction_rest_above_trace_q90": kr,
                "enrichment_ratio": kh / kr if kr else np.inf,
            })
            x = high[COMPONENTS].fillna(0).to_numpy(float)
            d_sig = np.linalg.norm(x - sig, axis=1)
            d_sm = np.linalg.norm(x - sm, axis=1)
            dist_rows.append({
                "dataset": dataset,
                "direction": direction,
                "bnf_tail": label,
                "events": len(high),
                "mean_distance_to_fuller_signal": d_sig.mean(),
                "mean_distance_to_fuller_pooledSM": d_sm.mean(),
                "fraction_closer_to_fuller_signal_than_SM": float((d_sig < d_sm).mean()),
            })
        df.to_csv(TRACE / f"{dataset.lower()}_real_with_fuller_component_trace_direction.csv", index=False)
    align = pd.DataFrame(rows)
    dist = pd.DataFrame(dist_rows)
    align.to_csv(TABLES / "fuller_component_real_trace_alignment_summary.csv", index=False)
    dist.to_csv(TABLES / "fuller_component_real_signal_vs_sm_distance_tests.csv", index=False)
    report = [
        "# Fuller Component Real Trace Alignment Report",
        "",
        f"Date: {DATE}",
        "",
        "The fuller-component direction is based on the available compressed T2tt MiniAODSIM benchmark against selected MiniAODSIM SM backgrounds. It is a trace-direction stress test, not direct evidence for SUSY.",
        "",
        "## Alignment",
        "",
        align.to_markdown(index=False),
        "",
        "## Distance Tests",
        "",
        dist.to_markdown(index=False),
    ]
    (REPORTS / "FULLER_COMPONENT_REAL_TRACE_ALIGNMENT_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(align.to_string(index=False))


if __name__ == "__main__":
    main()
