from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
THRESHOLDS = TABLES / "bnf_thresholds_real_and_sm.csv"
DATE = "2026-06-09"
PARAMS = ["B_P_displacement_proxy", "B_P_reconstruction", "B_P_multiplicity", "B_P_btag_structure", "B_P_visible_energy", "B_P_missing", "B_P_compression"]


def load_events() -> pd.DataFrame:
    frames = []
    for path in [SUSY, SM]:
        if path.exists():
            frames.append(pd.read_csv(path))
    if not frames:
        raise FileNotFoundError("No event-level benchmark files found.")
    return pd.concat(frames, ignore_index=True)


def load_thresholds() -> pd.DataFrame:
    th = pd.read_csv(THRESHOLDS)
    return th.rename(columns={"quantile": "real_quantile"})


def component_status(group: pd.DataFrame) -> str:
    available = [p for p in PARAMS if p in group and group[p].notna().any()]
    missing = [p for p in PARAMS if p not in group or not group[p].notna().any()]
    reduced_notes = []
    if "packed_candidate_count" not in group:
        reduced_notes.append("P_reconstruction lacks packed_candidate_count")
    if not missing:
        return "full component score available" if not reduced_notes else "reduced component score; " + "; ".join(reduced_notes)
    return "reduced component score; missing " + "; ".join(x.replace("B_", "") for x in missing + reduced_notes)


def main() -> None:
    events = load_events()
    thresholds = load_thresholds()
    rows = []
    inventory = []
    for (sample_id, process_label, classification), group in events.groupby(["sample_id", "process_label", "classification"]):
        score_cols = [c for c in group.columns if "B_NF" in c]
        components = [c for c in PARAMS if c in group and group[c].notna().any()]
        inventory.append({
            "sample_id": sample_id,
            "process_label": process_label,
            "classification": classification,
            "event_level_rows": len(group),
            "score_columns": ";".join(score_cols),
            "component_columns_available": ";".join(components),
            "component_mode": component_status(group),
        })
        score = group["B_NF_fitted_frozen_raw"]
        for t in thresholds.itertuples(index=False):
            n_total = len(group)
            n_above = int((score > t.value).sum())
            rows.append({
                "sample_id": sample_id,
                "process_label": process_label,
                "classification": classification,
                "threshold": t.threshold,
                "threshold_value": float(t.value),
                "n_total": n_total,
                "n_above_threshold": n_above,
                "n_below_threshold": n_total - n_above,
                "tail_fraction": n_above / n_total if n_total else float("nan"),
                "mean_BNF": score.mean(),
                "median_BNF": score.median(),
                "component_mode": component_status(group),
            })
    counts = pd.DataFrame(rows)
    inv = pd.DataFrame(inventory)
    counts.to_csv(TABLES / "sigma_tail_counts_by_sample.csv", index=False)
    inv.to_csv(TABLES / "sigma_test_input_inventory.csv", index=False)

    report = [
        "# Sigma Test Input Audit",
        "",
        f"Date: {DATE}",
        "",
        "## Event-Level Files",
        "",
        f"- SUSY benchmark events: `{SUSY}` exists={SUSY.exists()}",
        f"- SM background events: `{SM}` exists={SM.exists()}",
        f"- Real-data threshold table: `{THRESHOLDS}` exists={THRESHOLDS.exists()}",
        "",
        "## Input Inventory",
        "",
        inv.to_markdown(index=False),
        "",
        "## Thresholds",
        "",
        thresholds.to_markdown(index=False),
        "",
        "## Missing Data Issues",
        "",
        "The tests use the frozen real-data-fitted B_NF score. They are reduced-component benchmark tests when a sample lacks one or more fitted components; missing components are not silently set to zero.",
    ]
    (REPORTS / "SIGMA_TEST_INPUT_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    report2 = [
        "# Sigma Tail Count Reconstruction Report",
        "",
        f"Date: {DATE}",
        "",
        "Counts were reconstructed from event-level scored files by applying the real-data q90/q95/q99/q999 thresholds to `B_NF_fitted_frozen_raw`.",
        "",
        counts.to_markdown(index=False),
    ]
    (REPORTS / "SIGMA_TAIL_COUNT_RECONSTRUCTION_REPORT.md").write_text("\n".join(report2), encoding="utf-8")
    print(counts.to_string(index=False))


if __name__ == "__main__":
    main()
