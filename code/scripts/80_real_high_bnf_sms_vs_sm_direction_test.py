from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "trace_direction"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
FILES = {
    "Run2016G": OUT / "run2016g_real_with_trace_direction.csv",
    "Run2016H": OUT / "run2016h_real_with_trace_direction.csv",
    "combined": OUT / "combined_real_with_trace_direction.csv",
}
COMPONENTS = ["P_missing", "P_visible_energy", "P_multiplicity", "P_btag_structure", "P_compression"]


def centroids() -> pd.DataFrame:
    means = pd.read_csv(TABLES / "benchmark_trace_direction_component_means.csv")
    return means.set_index("sample_id")


def dist_matrix(df: pd.DataFrame, cent: pd.DataFrame, target: str) -> pd.Series:
    c = cent.loc[target, COMPONENTS].to_numpy(float)
    x = df[COMPONENTS].fillna(0).to_numpy(float)
    return pd.Series(np.linalg.norm(x - c, axis=1), index=df.index)


def main() -> None:
    cent = centroids()
    rows = []
    for dataset, path in FILES.items():
        df = pd.read_csv(path)
        df["distance_to_SMS"] = dist_matrix(df, cent, "sms_t5wg_mg1500_mlsp1_signal")
        df["distance_to_TTJets"] = dist_matrix(df, cent, "ttjets_nanoaodsim_pilot")
        df["distance_to_QCD"] = dist_matrix(df, cent, "qcd_ht700to1000_nanoaodsim_pilot")
        df["distance_to_pooledSM"] = dist_matrix(df, cent, "pooled_sm_benchmark")
        df["closer_to_SMS_than_pooledSM"] = df["distance_to_SMS"] < df["distance_to_pooledSM"]
        for label, q in [("top10", .90), ("top05", .95), ("top01", .99), ("top001", .999)]:
            high = df[df["B_NF_trace_base"] >= df["B_NF_trace_base"].quantile(q)]
            rest = df[df["B_NF_trace_base"] < df["B_NF_trace_base"].quantile(q)]
            frac_h = high["closer_to_SMS_than_pooledSM"].mean()
            frac_r = rest["closer_to_SMS_than_pooledSM"].mean()
            table = [[int(high["closer_to_SMS_than_pooledSM"].sum()), int((~high["closer_to_SMS_than_pooledSM"]).sum())],
                     [int(rest["closer_to_SMS_than_pooledSM"].sum()), int((~rest["closer_to_SMS_than_pooledSM"]).sum())]]
            fisher = stats.fisher_exact(table, alternative="greater")
            rows.append({
                "dataset": dataset, "bnf_tail": label, "events": len(high),
                "mean_distance_to_SMS": high["distance_to_SMS"].mean(),
                "mean_distance_to_TTJets": high["distance_to_TTJets"].mean(),
                "mean_distance_to_QCD": high["distance_to_QCD"].mean(),
                "mean_distance_to_pooledSM": high["distance_to_pooledSM"].mean(),
                "fraction_closer_to_SMS_than_pooledSM_high": frac_h,
                "fraction_closer_to_SMS_than_pooledSM_rest": frac_r,
                "enrichment_ratio": frac_h/frac_r if frac_r else np.inf,
                "fisher_p_one_sided": fisher.pvalue,
                "gaussian_z": float(stats.norm.isf(fisher.pvalue)) if fisher.pvalue > 0 else np.inf,
            })
        df.to_csv(OUT / f"{dataset.lower()}_real_with_trace_distances.csv", index=False)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "real_high_bnf_benchmark_distance_summary.csv", index=False)
    out.to_csv(TABLES / "real_high_bnf_sms_vs_sm_direction_tests.csv", index=False)
    report = ["# Real High-BNF SMS Versus SM Direction Test", "", f"Date: {DATE}", "", out.to_markdown(index=False)]
    (REPORTS / "REAL_HIGH_BNF_SMS_VS_SM_DIRECTION_TEST.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
