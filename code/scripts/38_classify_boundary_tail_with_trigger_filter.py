from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUMMARY = TABLES / "top_boundary_with_trigger_filter_summary.csv"

FILTER_COLS = [
    "pass_HBHENoiseFilter",
    "pass_HBHENoiseIsoFilter",
    "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter",
    "pass_BadPFMuonFilter",
    "pass_globalSuperTightHalo2016Filter",
]
TRIGGER_COLS = ["HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any"]


def classify(row: pd.Series) -> tuple[str, str]:
    filter_fails = []
    for col in FILTER_COLS:
        top_col = f"{col}_top_fraction"
        if top_col in row and pd.notna(row[top_col]) and row[top_col] < 0.98:
            filter_fails.append(col)
    trigger_deltas = []
    for col in TRIGGER_COLS:
        delta_col = f"{col}_top_minus_rest"
        if delta_col in row and pd.notna(row[delta_col]) and abs(row[delta_col]) > 0.25:
            trigger_deltas.append((col, row[delta_col]))
    concentrated = (
        row.get("top_run_fraction", 0) > 0.35
        or row.get("top_lumi_bin_fraction", 0) > 0.35
        or row.get("top_file_fraction", 0) > 0.35
    )
    if filter_fails:
        return "data-quality/technical concern", "One or more quality-filter pass fractions are below 98% in the top tail."
    if concentrated and trigger_deltas:
        return "trigger-selection-dominated with concentration", "The tail is strongly tied to trigger category and run/file/lumi concentration."
    if concentrated:
        return "unclear/follow-up needed", "The tail remains concentrated in acquisition provenance even after adding trigger/filter diagnostics."
    if trigger_deltas:
        return "trigger-selection-dominated", "The top tail differs sharply from the rest in broad trigger category."
    return "physics-like within current diagnostics", "No large quality-filter failure or severe provenance concentration is visible in the current summary."


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SUMMARY)
    rows = []
    for _, row in df.iterrows():
        category, reason = classify(row)
        rows.append(
            {
                "score": row["score"],
                "tail": row["tail"],
                "classification": category,
                "reason": reason,
                "top_file_fraction": row["top_file_fraction"],
                "top_run_fraction": row["top_run_fraction"],
                "top_lumi_bin_fraction": row["top_lumi_bin_fraction"],
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "boundary_tail_trigger_filter_classification.csv", index=False)

    n_quality = (out["classification"] == "data-quality/technical concern").sum()
    n_trigger = out["classification"].str.contains("trigger-selection", regex=False).sum()
    n_unclear = (out["classification"] == "unclear/follow-up needed").sum()
    n_physics_like = out["classification"].str.contains("physics-like", regex=False).sum()
    judgement = (
        "qualified rather than strengthened"
        if n_quality or n_trigger or n_unclear
        else "strengthened within the present diagnostics"
    )

    report = [
        "# Boundary Tail Trigger/Filter Classification Report",
        "",
        "Date: 2026-06-08",
        "",
        "This is a diagnostic classification of real CMS collision high-boundary tails. It is not a discovery claim and it does not use simulated SUSY samples.",
        "",
        "## Classification",
        "",
        out.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        f"Current N-Frame interpretation is **{judgement}** by the trigger/filter check.",
        "",
        f"- Data-quality/technical concern rows: {n_quality}",
        f"- Trigger-selection-dominated rows: {n_trigger}",
        f"- Unclear/follow-up-needed rows: {n_unclear}",
        f"- Physics-like rows under current diagnostics: {n_physics_like}",
    ]
    (REPORTS / "BOUNDARY_TAIL_TRIGGER_FILTER_CLASSIFICATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    synthesis = [
        "# Real-Only Boundary With Trigger/Filter Synthesis For N-Frame",
        "",
        "Date: 2026-06-08",
        "",
        "## What changed",
        "",
        "We re-ran the real CMS collision extraction with broad trigger and event-quality diagnostics available for every event. The boundary model itself was kept independent of these diagnostics, so the trigger/filter columns are used only to test whether the high-boundary tail looks like physics structure, trigger selection, or a data-quality effect.",
        "",
        "## Main result",
        "",
        f"The current trigger/filter pass classifies the N-Frame interpretation as **{judgement}**. The strongest acceptable statement is that the high-boundary tail is structured and reproducible across real samples, but it still needs trigger and provenance controls before it can be interpreted as evidence for a hidden higher-dimensional process.",
        "",
        "## Classification table",
        "",
        out.to_markdown(index=False),
        "",
        "## Next task",
        "",
        "Build a control-matched comparison: compare high-boundary events only against events from the same primary dataset, same trigger category, same run range, and similar pileup/vertex conditions. That is the next step needed to separate N-Frame-like structure from CMS trigger and data-taking structure.",
    ]
    (REPORTS / "REAL_ONLY_BOUNDARY_WITH_TRIGGER_FILTER_SYNTHESIS_FOR_NFRAME.md").write_text("\n".join(synthesis), encoding="utf-8")

    update = [
        "# Update To Darren: Trigger/Filter Boundary Check",
        "",
        "Date: 2026-06-08",
        "",
        "We have moved from a topology-only reproduction into a real-data event-level boundary check with trigger/filter diagnostics.",
        "",
        "## Done",
        "",
        "- Re-ran real CMS MiniAOD extraction with broad HLT category flags and standard event-quality filter flags.",
        "- Recomputed the N-Frame-style boundary score without using trigger/filter flags as inputs.",
        "- Inspected the top boundary events against trigger category, event-quality filters, file, run, and luminosity-bin concentration.",
        "",
        "## Current interpretation",
        "",
        f"The result is **{judgement}**. It remains interesting because the high-boundary tail is structured, but the honest next step is a trigger/run-matched control test before interpreting the tail as anything beyond detector/data-taking structure.",
        "",
        "## Next",
        "",
        "Construct matched controls within the same CMS dataset and trigger category, then test whether the boundary excess remains after that matching.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_TRIGGER_FILTER_BOUNDARY_CHECK.md").write_text("\n".join(update), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
