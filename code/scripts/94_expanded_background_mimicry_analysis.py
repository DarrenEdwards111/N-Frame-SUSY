from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
EVENTS = ROOT / "data" / "processed" / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv"
DATE = "2026-06-09"
PARAMS = ["B_P_missing", "B_P_visible_energy", "B_P_multiplicity", "B_P_btag_structure", "B_P_displacement_proxy", "B_P_reconstruction", "B_P_compression"]
SUMMARY_PARAMS = [p.replace("B_", "") for p in PARAMS]


def dist(a, b):
    common = [p for p in SUMMARY_PARAMS if p in a.index and p in b.index and pd.notna(a[p]) and pd.notna(b[p])]
    if not common:
        return np.nan, np.nan, ""
    av, bv = a[common].to_numpy(float), b[common].to_numpy(float)
    cos = float(np.dot(av, bv) / (np.linalg.norm(av) * np.linalg.norm(bv))) if np.linalg.norm(av) and np.linalg.norm(bv) else np.nan
    return float(np.linalg.norm(av - bv)), cos, ";".join(common)


def main():
    df = pd.read_csv(EVENTS)
    q95 = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv").query("threshold == 'q95'")["value"].iloc[0]
    rows = []
    for (sample, proc, cls), g in df[df["B_NF_fitted_frozen_raw"] > q95].groupby(["sample_id", "process_label", "classification"]):
        row = {"sample_id": sample, "process_label": proc, "classification": cls, "q95_tail_events": len(g)}
        for p in PARAMS:
            row[p.replace("B_", "")] = g[p].mean() if p in g else np.nan
        rows.append(row)
    summ = pd.DataFrame(rows)
    summ.to_csv(TABLES / "expanded_background_mimicry_summary.csv", index=False)
    sms = summ[summ["sample_id"].eq("sms_t5wg_mg1500_mlsp1_signal")].iloc[0]
    dist_rows = []
    for _, r in summ.iterrows():
        if r.sample_id == "sms_t5wg_mg1500_mlsp1_signal":
            continue
        d, c, comps = dist(sms, r)
        dist_rows.append({"comparison": f"SMS-T5Wg vs {r.sample_id}", "other_classification": r.classification, "euclidean_distance": d, "cosine_similarity": c, "components_compared": comps})
    distances = pd.DataFrame(dist_rows)
    distances.to_csv(TABLES / "expanded_driver_profile_distances.csv", index=False)
    report = ["# Expanded Background Mimicry Report", "", f"Date: {DATE}", "", "## q95 Driver Summary", "", summ.to_markdown(index=False), "", "## SMS Driver Distances", "", distances.to_markdown(index=False)]
    (REPORTS / "EXPANDED_BACKGROUND_MIMICRY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(distances.to_string(index=False))


if __name__ == "__main__":
    main()
