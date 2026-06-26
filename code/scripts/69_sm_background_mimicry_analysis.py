from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
DATE = "2026-06-09"
PARAMS = ["B_P_displacement_proxy", "B_P_reconstruction", "B_P_multiplicity", "B_P_btag_structure", "B_P_visible_energy", "B_P_missing", "B_P_compression"]


def load_all() -> pd.DataFrame:
    return pd.concat([pd.read_csv(SUSY), pd.read_csv(SM)], ignore_index=True)


def parameter_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sample, process, classification), group in df.groupby(["sample_id", "process_label", "classification"]):
        for param in PARAMS:
            if param in group:
                rows.append({
                    "sample_id": sample,
                    "process_label": process,
                    "classification": classification,
                    "parameter_family": param.replace("B_", ""),
                    "mean_parameter": group[param].mean(),
                    "median_parameter": group[param].median(),
                    "p95_parameter": group[param].quantile(.95) if group[param].notna().any() else np.nan,
                })
    return pd.DataFrame(rows)


def contrast(summary: pd.DataFrame) -> pd.DataFrame:
    sms = summary[summary["sample_id"].eq("sms_t5wg_mg1500_mlsp1_signal")]
    sm = summary[summary["classification"].eq("SM_background")]
    rows = []
    for bg in sm["sample_id"].unique():
        bg_rows = sm[sm["sample_id"].eq(bg)]
        for param in PARAMS:
            fam = param.replace("B_", "")
            s = sms[sms["parameter_family"].eq(fam)]
            b = bg_rows[bg_rows["parameter_family"].eq(fam)]
            if s.empty or b.empty:
                continue
            rows.append({
                "parameter_family": fam,
                "signal_sample": "sms_t5wg_mg1500_mlsp1_signal",
                "sm_background_sample": bg,
                "signal_mean": s["mean_parameter"].iloc[0],
                "sm_mean": b["mean_parameter"].iloc[0],
                "signal_minus_sm": s["mean_parameter"].iloc[0] - b["mean_parameter"].iloc[0],
            })
    return pd.DataFrame(rows)


def write_report(path: Path, title: str, sections: list[tuple[str, object]]) -> None:
    lines = [f"# {title}", "", f"Date: {DATE}"]
    for header, body in sections:
        lines += ["", f"## {header}", ""]
        lines.append(body.to_markdown(index=False) if isinstance(body, pd.DataFrame) else str(body))
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = load_all()
    summary = parameter_summary(df)
    comp = contrast(summary)
    summary.to_csv(TABLES / "sm_background_mimicry_parameter_summary.csv", index=False)
    comp.to_csv(TABLES / "susy_vs_sm_driver_contrast.csv", index=False)

    tails = pd.read_csv(TABLES / "susy_vs_sm_bnf_tail_fractions.csv")
    ratios = pd.read_csv(TABLES / "susy_vs_sm_bnf_tail_ratios.csv")
    sep = pd.read_csv(TABLES / "susy_vs_sm_simple_separability.csv")
    q95 = tails[tails["threshold"].eq("q95")].sort_values("tail_fraction", ascending=False)
    q95_ratios = ratios[ratios["threshold"].eq("q95")].sort_values("tail_ratio_signal_over_sm", ascending=False)

    sms_q95 = q95[q95["sample_id"].eq("sms_t5wg_mg1500_mlsp1_signal")]["tail_fraction"].iloc[0]
    sm_max = q95[q95["classification"].eq("SM_background")]["tail_fraction"].max()
    if sms_q95 > sm_max:
        verdict = "SMS-T5Wg remains higher than the tested SM backgrounds in q95 high-boundary occupancy. This strengthens the SUSY-relevance interpretation at benchmark level, while still not making a discovery claim."
    else:
        verdict = "At least one tested SM background matches or exceeds SMS-T5Wg in q95 high-boundary occupancy. This qualifies the interpretation: the boundary score may be responding to generic SM topology/reconstruction stress."

    write_report(
        REPORTS / "SM_BACKGROUND_MIMICRY_ANALYSIS_REPORT.md",
        "SM Background Mimicry Analysis Report",
        [("Parameter Summary", summary), ("SMS-T5Wg Versus SM Driver Contrast", comp), ("Interpretation", verdict)],
    )
    write_report(
        REPORTS / "BOUNDARY_STRESS_TO_SUSY_RELEVANCE_WITH_SM_BACKGROUNDS.md",
        "Boundary Stress To SUSY Relevance With SM Backgrounds",
        [
            ("Frozen Equation", "The real-data-fitted B_NF equation was frozen. It was not refitted on SUSY or SM simulation."),
            ("SUSY Benchmarks And SM Backgrounds", q95),
            ("q95 Ratios", q95_ratios),
            ("Simple Separability", sep),
            ("Interpretation", verdict + " HToAA4B remains low in this pilot. The NanoAODSIM route is partial because packed_candidate_count is unavailable; MiniAODSIM would be needed for the fullest reconstruction component."),
            ("Remaining Missing Work", "Add more SUSY topologies, more SM backgrounds, full MiniAOD variables where practical, published SUSY signal-region overlap, and manual/event-display inspection."),
        ],
    )
    write_report(
        REPORTS / "UPDATE_TO_DARREN_SUSY_VS_SM_BACKGROUND_TEST.md",
        "Update To Darren: SUSY Versus SM Background Test",
        [
            ("Plain English Summary", "We froze the real-data-fitted N-Frame boundary equation and added two Standard Model simulated benchmark backgrounds: inclusive TTJets and high-HT QCD. This is a benchmark/specificity test, not a discovery test."),
            ("q95 Tail Fractions", q95),
            ("Interpretation", verdict + " Positive enrichment here should be described as benchmark-level SUSY-relevant support only, not evidence that SUSY was found in real collision data."),
            ("Next Step", "Repeat with more SM backgrounds and, where manageable, MiniAODSIM extraction so the secondary-vertex and reconstruction components match the real-data validation more completely."),
        ],
    )
    print(q95.to_string(index=False))


if __name__ == "__main__":
    main()
