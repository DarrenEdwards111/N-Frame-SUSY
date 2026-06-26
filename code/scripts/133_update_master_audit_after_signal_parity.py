from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TABLES = ROOT / "results" / "tables"
DATE = "2026-06-09"

REPORT_NAMES = [
    "FULL_COMPONENT_SIGNAL_SIDE_PARITY_SYNTHESIS.md",
    "UPDATE_TO_DARREN_FULL_COMPONENT_SIGNAL_SIDE_PARITY.md",
    "FULL_COMPONENT_SIGNAL_VS_QCD_COMPARISON_REPORT.md",
    "FULL_COMPONENT_REAL_TRACE_ALIGNMENT_REPORT.md",
    "FULLER_COMPONENT_BENCHMARK_SYNTHESIS.md",
    "EXPANDED_BENCHMARK_AND_TRACE_ROBUSTNESS_SYNTHESIS.md",
    "REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md",
    "REAL_TRACE_CANDIDATE_SANITY_CHECK_SYNTHESIS.md",
    "FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md",
]


def exists(name: str) -> str:
    path = REPORTS / name
    return "present" if path.exists() else "missing"


def main() -> None:
    signal = pd.read_csv(TABLES / "accessible_susy_signal_bnf_summary.csv")
    backgrounds = pd.read_csv(TABLES / "current_fuller_component_state_audit.csv")
    tests = pd.read_csv(TABLES / "full_component_signal_vs_background_corrected_tests.csv")
    inc = pd.read_csv(TABLES / "full_component_signal_bnf_vs_met_ht_incremental.csv")
    q95_qcd = tests[(tests["threshold"].eq("q95")) & (tests["background_process"].eq("QCD HT1000to1500"))].copy()
    beat_qcd = q95_qcd[q95_qcd["risk_difference"] > 0]
    lose_qcd = q95_qcd[q95_qcd["risk_difference"] <= 0]
    inc_med = inc.groupby("score", as_index=False)["auc"].median().sort_values("auc", ascending=False)
    rows = [
        {
            "category": "resolved",
            "finding": "Full-component signal-side parity was achieved for three accessible MiniAODSIM SUSY-like benchmark files.",
            "evidence": f"{int(signal['events'].sum())} extracted signal events; full components available.",
            "status": "resolved",
        },
        {
            "category": "resolved",
            "finding": "One full-component SUSY-like benchmark beats the strongest existing QCD mimic.",
            "evidence": beat_qcd[["signal_process", "signal_tail_fraction", "background_tail_fraction", "bonferroni_z"]].to_dict("records").__str__(),
            "status": "positive_model_dependent",
        },
        {
            "category": "unresolved",
            "finding": "Not all SUSY-like signals beat QCD HT1000to1500.",
            "evidence": lose_qcd[["signal_process", "signal_tail_fraction", "background_tail_fraction"]].to_dict("records").__str__(),
            "status": "qualified",
        },
        {
            "category": "unresolved",
            "finding": "SMS-T5Wg/T1 high-MET MiniAODSIM remains the most important missing signal-side test.",
            "evidence": "The restored positive result is for an accessible gluino-to-neutralino benchmark, not the original SMS-T5Wg/T1 family.",
            "status": "missing_target",
        },
        {
            "category": "unresolved",
            "finding": "Broader SM coverage remains needed.",
            "evidence": "Existing full-component backgrounds are QCD HT1000to1500, QCD HT700to1000 and WJets only.",
            "status": "needs_more_SM_mimics",
        },
        {
            "category": "caveat",
            "finding": "B_NF does not currently add strongly beyond simpler energy/recoil structure.",
            "evidence": f"Best median AUC: {inc_med.iloc[0]['score']}={inc_med.iloc[0]['auc']:.3f}; full B_NF median AUC={float(inc_med[inc_med['score'].eq('B_NF_fitted')]['auc'].iloc[0]):.3f}.",
            "status": "qualified",
        },
        {
            "category": "baseline",
            "finding": "Strongest current full-component SM mimic remains QCD HT1000to1500.",
            "evidence": backgrounds.sort_values("q95_tail_fraction", ascending=False).head(1)[["process_label", "q95_tail_fraction", "q99_tail_fraction"]].to_dict("records").__str__(),
            "status": "baseline",
        },
    ]
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "updated_master_audit_after_signal_parity.csv", index=False)
    report_inventory = pd.DataFrame({"report": REPORT_NAMES, "status": [exists(n) for n in REPORT_NAMES]})
    report = [
        "# Updated Master Audit After Signal-Side Parity",
        "",
        f"Date: {DATE}",
        "",
        "The frozen B_NF equation remains unchanged. This audit consolidates the latest full-component signal-side parity result with the prior real-data and benchmark evidence.",
        "",
        "## Audit Findings",
        "",
        audit.to_markdown(index=False),
        "",
        "## Report Inventory",
        "",
        report_inventory.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "The signal-side parity run strengthens the N-Frame/SUSY interpretation in a qualified, model-dependent way: one accessible full-component gluino-to-neutralino benchmark beats QCD HT1000to1500 strongly, but other SUSY-like samples do not, and B_NF remains largely energy/recoil-driven in incrementality tests.",
    ]
    (REPORTS / "UPDATED_MASTER_AUDIT_AFTER_SIGNAL_PARITY.md").write_text("\n".join(report), encoding="utf-8")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
