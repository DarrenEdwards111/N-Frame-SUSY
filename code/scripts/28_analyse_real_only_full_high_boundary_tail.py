from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "cmssw_real_only_full_file_by_file" / "real_only_full_cmssw_event_features_with_unsupervised_boundary.csv"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
REPORTS = ROOT / "reports"
DRIVERS = ["MET_pt", "HT", "N_jets_30", "N_jets_50", "N_leptons", "N_btags_medium", "N_btags_tight", "max_btag_discriminator", "N_primary_vertices", "packed_candidate_count", "secondary_vertex_count", "compression_proxy_raw", "B_boundary_hand_defined_z", "real_only_full_unsupervised_boundary_score"]


def summaries(df, score):
    rows, sample_rows, file_rows, driver_rows = [], [], [], []
    sample_base = df["sample_id"].value_counts(normalize=True).to_dict()
    file_base = df["source_file"].value_counts(normalize=True).to_dict()
    for q, label in [(0.9, "top10"), (0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        thr = df[score].quantile(q)
        tail = df[df[score] >= thr]
        rows.append({"score": score, "tail": label, "threshold": thr, "events": len(tail), "mean_MET": tail.MET_pt.mean(), "median_MET": tail.MET_pt.median(), "mean_HT": tail.HT.mean(), "median_HT": tail.HT.median(), "mean_N_jets_30": tail.N_jets_30.mean(), "mean_N_leptons": tail.N_leptons.mean(), "mean_secondary_vertices": tail.secondary_vertex_count.mean(), "mean_packed_candidates": tail.packed_candidate_count.mean()})
        for sample, frac in tail["sample_id"].value_counts(normalize=True).items():
            sample_rows.append({"score": score, "tail": label, "sample_id": sample, "tail_fraction": frac, "baseline_fraction": sample_base[sample], "enrichment_ratio": frac / sample_base[sample], "tail_events": int((tail.sample_id == sample).sum())})
        for src, frac in tail["source_file"].value_counts(normalize=True).items():
            file_rows.append({"score": score, "tail": label, "source_file": src, "tail_fraction": frac, "baseline_fraction": file_base[src], "enrichment_ratio": frac / file_base[src], "tail_events": int((tail.source_file == src).sum())})
        if label == "top01":
            rest = df[df[score] < thr]
            for var in [v for v in DRIVERS if v in df]:
                driver_rows.append({"score": score, "variable": var, "top01_mean": tail[var].mean(), "rest_mean": rest[var].mean(), "mean_difference": tail[var].mean() - rest[var].mean(), "top01_median": tail[var].median(), "rest_median": rest[var].median()})
    return pd.DataFrame(rows), pd.DataFrame(sample_rows), pd.DataFrame(file_rows), pd.DataFrame(driver_rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    h1, h2, h3, h4 = summaries(df, "B_boundary_hand_defined_z")
    u1, u2, u3, u4 = summaries(df, "real_only_full_unsupervised_boundary_score")
    tail = pd.concat([h1, u1], ignore_index=True)
    sample = pd.concat([h2, u2], ignore_index=True)
    file = pd.concat([h3, u3], ignore_index=True)
    drivers = pd.concat([h4, u4], ignore_index=True).sort_values(["score", "mean_difference"], ascending=[True, False])
    tail.to_csv(TABLES / "real_only_full_tail_summary.csv", index=False)
    sample.to_csv(TABLES / "real_only_full_tail_sample_enrichment.csv", index=False)
    file.to_csv(TABLES / "real_only_full_tail_file_enrichment.csv", index=False)
    drivers.to_csv(TABLES / "real_only_full_tail_driver_variables.csv", index=False)
    df.sort_values("B_boundary_hand_defined_z", ascending=False).head(1000).to_csv(TABLES / "real_only_full_top_1000_hand_boundary_events.csv", index=False)
    df.sort_values("real_only_full_unsupervised_boundary_score", ascending=False).head(1000).to_csv(TABLES / "real_only_full_top_1000_unsupervised_boundary_events.csv", index=False)

    # Figures on a sample for scatter plots.
    sample_df = df.sample(min(60000, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(8, 4))
    df.boxplot(column="B_boundary_hand_defined_z", by="primary_dataset", ax=ax)
    ax.figure.suptitle("")
    ax.set_title("Full real-only boundary score by sample")
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_boundary_score_by_sample.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4))
    order = df.groupby("source_file")["B_boundary_hand_defined_z"].median().sort_values().index
    data = [df[df.source_file == src]["B_boundary_hand_defined_z"].values for src in order]
    ax.boxplot(data, labels=[s[:8] for s in order], showfliers=False)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("Boundary z")
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_boundary_score_by_file.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 5))
    sc = ax.scatter(sample_df.MET_pt, sample_df.HT, c=sample_df.B_boundary_hand_defined_z, s=3, alpha=.45, cmap="viridis")
    ax.set_xlabel("MET pt"); ax.set_ylabel("HT"); fig.colorbar(sc, ax=ax, label="Boundary z")
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_MET_vs_HT_boundary.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 5))
    sc = ax.scatter(sample_df.real_only_full_pca_axis_1, sample_df.real_only_full_pca_axis_2, c=sample_df.real_only_full_unsupervised_boundary_score, s=3, alpha=.45, cmap="magma")
    ax.set_xlabel("PCA axis 1"); ax.set_ylabel("PCA axis 2"); fig.colorbar(sc, ax=ax, label="Unsupervised boundary")
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_PCA_boundary_space.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    s05 = sample[(sample.score == "B_boundary_hand_defined_z") & (sample.tail == "top05")]
    ax.bar(s05.sample_id, s05.enrichment_ratio); ax.axhline(1, color="black", linewidth=1); ax.tick_params(axis="x", rotation=20)
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_tail_enrichment_by_sample.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4))
    f05 = file[(file.score == "B_boundary_hand_defined_z") & (file.tail == "top05")].sort_values("enrichment_ratio", ascending=False)
    ax.bar([s[:8] for s in f05.source_file], f05.enrichment_ratio); ax.axhline(1, color="black", linewidth=1); ax.tick_params(axis="x", rotation=45)
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_tail_enrichment_by_file.png", dpi=160); plt.close(fig)
    top = df[df.B_boundary_hand_defined_z >= df.B_boundary_hand_defined_z.quantile(.99)]
    comps = ["R_missing", "R_visible_energy", "R_multiplicity", "R_btag_structure", "R_reconstruction_complexity", "R_compression_proxy", "R_displacement_proxy"]
    heat = top.groupby("primary_dataset")[comps].mean()
    fig, ax = plt.subplots(figsize=(8, 3)); im = ax.imshow(heat.values, aspect="auto", cmap="coolwarm")
    ax.set_xticks(range(len(comps)), comps, rotation=35, ha="right"); ax.set_yticks(range(len(heat.index)), heat.index); fig.colorbar(im, ax=ax)
    fig.tight_layout(); fig.savefig(FIGURES / "real_only_full_component_heatmap_top_tail.png", dpi=160); plt.close(fig)
    report = ["# Real-Only Full High Boundary Tail Report", "", "Date: 2026-06-08", "", "No simulated samples were used.", "", "## Tail Summary", "", tail.to_markdown(index=False), "", "## Sample Enrichment", "", sample.to_markdown(index=False), "", "## Strongest File Enrichment", "", file.sort_values("enrichment_ratio", ascending=False).head(25).to_markdown(index=False), "", "## Driver Variables", "", drivers.groupby("score").head(12).to_markdown(index=False)]
    (REPORTS / "REAL_ONLY_FULL_HIGH_BOUNDARY_TAIL_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(tail.to_string(index=False))


if __name__ == "__main__":
    main()
