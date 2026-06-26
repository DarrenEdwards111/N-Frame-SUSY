from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
FIGS = ROOT / "results" / "figures" / "trace_candidate_diagnostics"
DATE = "2026-06-09"


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(TABLES / "classified_top_trace_candidates_combined.csv").head(5)
    made = []
    for i, row in df.reset_index(drop=True).iterrows():
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = ["MET", "HT", "jets", "b-tags", "leptons", "sec vertices"]
        vals = [row.MET_pt, row.HT, row.N_jets_30 * 100, row.N_btags_medium * 100, row.N_leptons * 100, row.secondary_vertex_count * 50]
        ax.bar(labels, vals)
        ax.set_title(f"Diagnostic sketch candidate {i+1}: run {row.run} event {row.event}")
        ax.set_ylabel("Scaled value for quick comparison")
        fig.tight_layout()
        out = FIGS / f"candidate_{i+1:02d}_diagnostic_sketch.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        made.append(str(out))
    report = [
        "# Event Display Feasibility Check",
        "",
        f"Date: {DATE}",
        "",
        "A full CMS detector event display was not generated automatically. The candidate tables contain run/lumi/event/source-file identifiers needed for a physicist to inspect events with CMS Open Data tools.",
        "",
        "Simple diagnostic sketches were feasible from extracted variables. They are not detector event displays; they are quick non-expert summaries of MET, HT, jets, b-tags, leptons and secondary vertices.",
        "",
        "## Diagnostic Sketches",
        "",
        "\n".join(f"- `{p}`" for p in made),
    ]
    (REPORTS / "EVENT_DISPLAY_FEASIBILITY_CHECK.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(made))


if __name__ == "__main__":
    main()
