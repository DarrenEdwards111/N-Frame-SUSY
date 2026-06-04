from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def main():
    event_path = ROOT / "data" / "processed" / "event_features_nframe_scored.csv"
    sr_candidates = [
        WORKSPACE / "nframe_susy_boundary" / "data" / "processed" / "signal_regions_verified_plus_imputed_scored.csv",
        WORKSPACE / "nframe_susy_boundary" / "data" / "processed" / "signal_regions_metadata_enriched_scored_outcomes.csv",
    ]
    if not event_path.exists():
        raise SystemExit("No event score file")
    event = pd.read_csv(event_path)
    sr_path = next((p for p in sr_candidates if p.exists()), None)
    rows = [{"dataset": "MiniAOD_event", "score": "B_event_z", "n": len(event), "mean": event.B_event_z.mean(), "std": event.B_event_z.std()}]
    if sr_path:
        sr = pd.read_csv(sr_path)
        score_col = "B_access_verified_imputed_z" if "B_access_verified_imputed_z" in sr else "B_access_z"
        rows.append({"dataset": "signal_region", "score": score_col, "n": len(sr), "mean": sr[score_col].mean(), "std": sr[score_col].std()})
        plt.figure(figsize=(7, 5))
        plt.hist(event.B_event_z.dropna(), bins=60, alpha=0.6, density=True, label="MiniAOD events")
        plt.hist(sr[score_col].dropna(), bins=40, alpha=0.6, density=True, label="Signal regions")
        plt.legend()
        plt.xlabel("Boundary score z")
        plt.tight_layout()
        plt.savefig(ROOT / "results" / "figures" / "event_vs_signal_boundary_distribution.png", dpi=170)
        plt.close()
    pd.DataFrame(rows).to_csv(ROOT / "results" / "tables" / "event_vs_signal_boundary_comparison.csv", index=False)
    print(pd.DataFrame(rows))


if __name__ == "__main__":
    main()
