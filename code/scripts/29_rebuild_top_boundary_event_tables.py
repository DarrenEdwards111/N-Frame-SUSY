from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
OUTDIR = ROOT / "results" / "tables" / "top_boundary_events"
REPORTS = ROOT / "reports"

BASE_COLS = [
    "sample_id", "primary_dataset", "source_file", "source_file_stem", "source_file_index",
    "run", "lumi", "event", "event_index_within_file", "event_index_global_within_sample",
    "B_boundary_hand_defined_z", "real_only_full_unsupervised_boundary_score",
    "R_missing", "R_visible_energy", "R_multiplicity", "R_btag_structure",
    "R_reconstruction_complexity", "R_compression_proxy", "R_displacement_proxy",
    "MET_pt", "HT", "N_jets_30", "N_jets_50", "leading_jet_pt", "subleading_jet_pt",
    "N_muons", "N_electrons", "N_leptons", "N_btags_loose", "N_btags_medium",
    "N_btags_tight", "max_btag_discriminator", "N_primary_vertices",
    "packed_candidate_count", "secondary_vertex_count", "compression_proxy_raw",
    "displacement_proxy_raw", "scoring_limitations",
]


def write_top(df: pd.DataFrame, score: str, label: str, ascending: bool = False) -> list[dict]:
    rows = []
    prefix = "hand" if label == "hand" else "unsupervised"
    specs = [
        ("top100", 100),
        ("top500", 500),
        ("top1000", 1000),
        ("top5000", 5000),
        ("top1pct", max(1, int(round(len(df) * 0.01)))),
        ("top0p1pct", max(1, int(round(len(df) * 0.001)))),
    ]
    ordered = df.sort_values(score, ascending=ascending)
    cols = [c for c in BASE_COLS if c in df.columns]
    trigger_cols = [c for c in df.columns if any(token in c.lower() for token in ["trigger", "hlt", "filter", "hbhe", "halo"])]
    cols += [c for c in trigger_cols if c not in cols]
    for name, n in specs:
        out = OUTDIR / f"{name}_{prefix}_boundary_events.csv"
        table = ordered.head(n)[cols].copy()
        table.to_csv(out, index=False)
        rows.append({"score": score, "table": out.name, "rows": len(table), "path": str(out)})
    return rows


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    rows = []
    rows += write_top(df, "B_boundary_hand_defined_z", "hand")
    rows += write_top(df, "real_only_full_unsupervised_boundary_score", "unsupervised")
    summary = pd.DataFrame(rows)
    summary.to_csv(OUTDIR / "top_boundary_tables_manifest.csv", index=False)
    report = [
        "# Top Boundary Tables Rebuilt",
        "",
        "Date: 2026-06-08",
        "",
        f"Input: `{INPUT}`",
        "",
        "All tables were rebuilt from the most complete full real-only scored dataset. No simulated samples were used.",
        "",
        summary.to_markdown(index=False),
    ]
    (REPORTS / "TOP_BOUNDARY_TABLES_REBUILT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
