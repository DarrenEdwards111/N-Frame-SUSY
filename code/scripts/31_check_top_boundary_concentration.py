from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
TOPDIR = TABLES / "top_boundary_events"
SETS = [
    ("hand_top100", "top100_hand_boundary_events.csv"),
    ("hand_top1000", "top1000_hand_boundary_events.csv"),
    ("hand_top0p1pct", "top0p1pct_hand_boundary_events.csv"),
    ("unsup_top100", "top100_unsupervised_boundary_events.csv"),
    ("unsup_top1000", "top1000_unsupervised_boundary_events.csv"),
    ("unsup_top0p1pct", "top0p1pct_unsupervised_boundary_events.csv"),
]


def concentration(top: pd.DataFrame, col: str, ns: list[int]) -> dict:
    vc = top[col].value_counts(normalize=True)
    return {f"top_{n}_{col}_fraction": vc.head(n).sum() for n in ns}


def enrichment(top: pd.DataFrame, full: pd.DataFrame, col: str, set_name: str) -> pd.DataFrame:
    base = full[col].value_counts()
    obs = top[col].value_counts()
    rows = []
    total_top = len(top)
    total = len(full)
    for key, b in base.items():
        o = int(obs.get(key, 0))
        exp = b * total_top / total
        rows.append({"top_set": set_name, col: key, "observed": o, "expected": exp, "baseline_fraction": b / total, "tail_fraction": o / total_top, "enrichment_ratio": o / exp if exp else np.nan})
    return pd.DataFrame(rows)


def judge(row: pd.Series) -> str:
    if row["top_1_source_file_fraction"] > 0.5 or row["top_1_run_fraction"] > 0.3 or row["top_1_lumi_bin_fraction"] > 0.3:
        return "strongly file/run/lumi concentrated; requires data-quality/trigger follow-up"
    if row["top_1_source_file_fraction"] > 0.3 or row["top_2_source_file_fraction"] > 0.6:
        return "partly file-driven; requires trigger/data-quality follow-up"
    return "not obviously one-file driven"


def main() -> None:
    full = pd.read_csv(INPUT, usecols=["sample_id", "source_file", "run", "lumi", "event"])
    full = full.assign(lumi_bin=(full["lumi"] // 50) * 50)
    summary_rows, src_enrich, run_enrich, lumi_enrich = [], [], [], []
    for set_name, filename in SETS:
        top = pd.read_csv(TOPDIR / filename, usecols=["sample_id", "source_file", "run", "lumi", "event"])
        top = top.assign(lumi_bin=(top["lumi"] // 50) * 50)
        row = {"top_set": set_name, "events": len(top)}
        row.update(concentration(top, "source_file", [1, 2, 3]))
        row.update(concentration(top, "run", [1, 5, 10]))
        row.update(concentration(top, "lumi_bin", [1, 5]))
        row["judgement"] = judge(pd.Series(row))
        summary_rows.append(row)
        src_enrich.append(enrichment(top, full, "source_file", set_name))
        run_enrich.append(enrichment(top, full, "run", set_name))
        lumi_enrich.append(enrichment(top, full, "lumi_bin", set_name))
    summary = pd.DataFrame(summary_rows)
    src = pd.concat(src_enrich, ignore_index=True).sort_values(["top_set", "enrichment_ratio"], ascending=[True, False])
    run = pd.concat(run_enrich, ignore_index=True).sort_values(["top_set", "enrichment_ratio"], ascending=[True, False])
    lumi = pd.concat(lumi_enrich, ignore_index=True).sort_values(["top_set", "enrichment_ratio"], ascending=[True, False])
    summary.to_csv(TABLES / "top_boundary_concentration_summary.csv", index=False)
    src.to_csv(TABLES / "top_boundary_source_file_enrichment.csv", index=False)
    run.to_csv(TABLES / "top_boundary_run_enrichment.csv", index=False)
    lumi.to_csv(TABLES / "top_boundary_lumi_enrichment.csv", index=False)
    report = [
        "# Top Boundary Concentration Report",
        "",
        "Date: 2026-06-08",
        "",
        "This checks whether top boundary events are concentrated in individual files, runs or lumi bins.",
        "",
        "## Concentration Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Strongest Source File Enrichments",
        "",
        src.groupby("top_set").head(8).to_markdown(index=False),
        "",
        "## Strongest Run Enrichments",
        "",
        run.groupby("top_set").head(8).to_markdown(index=False),
    ]
    (REPORTS / "TOP_BOUNDARY_CONCENTRATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
