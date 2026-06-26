from __future__ import annotations

import numpy as np
import pandas as pd

from fuller_component_common import FAMILIES
from susy_signal_common import DATE, REPORTS, ROOT, TABLES


REAL = ROOT / "data" / "processed" / "trace_direction" / "combined_real_with_full_component_signal_qcd_trace_direction.csv"
COMPONENTS = list(FAMILIES.keys())


def sidebands(df: pd.DataFrame) -> dict[str, pd.Series]:
    bnf = df["B_NF_trace_base"]
    trace = df["Trace_full_component_signal_vs_qcd"]
    ht, met = df["HT"], df["MET_pt"]
    disp_reco = df[["P_displacement_proxy", "P_reconstruction"]].mean(axis=1)
    return {
        "high_BNF_high_trace": (bnf >= bnf.quantile(.95)) & (trace >= trace.quantile(.90)),
        "high_HT_low_MET": (ht >= ht.quantile(.90)) & (met <= met.quantile(.50)),
        "high_MET_low_HT": (met >= met.quantile(.90)) & (ht <= ht.quantile(.50)),
        "high_HT_high_MET_low_BNF": (ht >= ht.quantile(.90)) & (met >= met.quantile(.90)) & (bnf <= bnf.quantile(.50)),
        "high_BNF_low_trace": (bnf >= bnf.quantile(.95)) & (trace <= trace.quantile(.50)),
        "QCD_like_high_HT_low_MET": (ht >= ht.quantile(.95)) & (met <= met.quantile(.40)),
        "signal_like_MET_visible_multiplicity": (met >= met.quantile(.90)) & (ht >= ht.quantile(.75)) & (df["N_jets_30"] >= df["N_jets_30"].quantile(.75)),
        "high_displacement_reconstruction_low_missing": (disp_reco >= disp_reco.quantile(.95)) & (df["P_missing"] <= df["P_missing"].quantile(.50)),
        "high_missing_low_displacement_reconstruction": (df["P_missing"] >= df["P_missing"].quantile(.95)) & (disp_reco <= disp_reco.quantile(.50)),
    }


def top_fraction(s: pd.Series) -> float:
    vc = s.value_counts(dropna=False)
    return float(vc.iloc[0] / vc.sum()) if len(vc) else np.nan


def main() -> None:
    df = pd.read_csv(REAL, low_memory=False)
    means = pd.read_csv(TABLES / "full_component_trace_direction_component_means.csv").set_index("sample_id")
    weights = pd.read_csv(TABLES / "full_component_trace_direction_weights.csv")
    direction = pd.read_csv(TABLES / "full_component_trace_alignment_real_data.csv")["direction"].iloc[0]
    signal_sample = weights[weights["direction"].eq(direction)]["signal_sample"].iloc[0]
    qcd_sample = weights[weights["direction"].eq(direction)]["background_sample"].iloc[0]
    sig_centroid = means.loc[signal_sample, COMPONENTS].to_numpy(float)
    qcd_centroid = means.loc[qcd_sample, COMPONENTS].to_numpy(float)
    rows = []
    for name, mask in sidebands(df).items():
        g = df[mask].copy()
        rest = df[~mask]
        if g.empty:
            continue
        x = g[COMPONENTS].fillna(0).to_numpy(float)
        rows.append({
            "sideband": name,
            "events": len(g),
            "fraction_of_real": len(g) / len(df),
            "top_primary_dataset": g["primary_dataset"].mode().iloc[0] if "primary_dataset" in g else "",
            "top_primary_dataset_fraction": top_fraction(g["primary_dataset"]) if "primary_dataset" in g else np.nan,
            "top_source_file_fraction": top_fraction(g["source_file"]) if "source_file" in g else np.nan,
            "top_run_fraction": top_fraction(g["run"]) if "run" in g else np.nan,
            "top_lumi_fraction": top_fraction(g["lumi"]) if "lumi" in g else np.nan,
            "standard_quality_pass_rate": g["standard_quality_clean"].mean() if "standard_quality_clean" in g else np.nan,
            "mean_BNF": g["B_NF_trace_base"].mean(),
            "rest_mean_BNF": rest["B_NF_trace_base"].mean(),
            "mean_trace": g["Trace_full_component_signal_vs_qcd"].mean(),
            "rest_mean_trace": rest["Trace_full_component_signal_vs_qcd"].mean(),
            "mean_HT": g["HT"].mean(),
            "mean_MET": g["MET_pt"].mean(),
            "mean_P_missing": g["P_missing"].mean(),
            "mean_P_visible_energy": g["P_visible_energy"].mean(),
            "mean_P_displacement_proxy": g["P_displacement_proxy"].mean(),
            "mean_P_reconstruction": g["P_reconstruction"].mean(),
            "mean_distance_to_signal": np.linalg.norm(x - sig_centroid, axis=1).mean(),
            "mean_distance_to_qcd": np.linalg.norm(x - qcd_centroid, axis=1).mean(),
            "fraction_closer_to_signal_than_qcd": float((np.linalg.norm(x - sig_centroid, axis=1) < np.linalg.norm(x - qcd_centroid, axis=1)).mean()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "real_data_sideband_control_after_signal_parity.csv", index=False)
    report = [
        "# Real Data Sideband Control After Signal Parity Report",
        "",
        f"Date: {DATE}",
        "",
        "Sidebands use existing scored Run2016G/Run2016H real collision data. The goal is to check whether high-boundary/trace events remain unusual against nearby control regions, not to claim particle detection.",
        "",
        out.to_markdown(index=False),
    ]
    (REPORTS / "REAL_DATA_SIDEBAND_CONTROL_AFTER_SIGNAL_PARITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
