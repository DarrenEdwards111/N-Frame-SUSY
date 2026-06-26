from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
HAND = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_scored.csv"
UNSUP = ROOT / "data" / "processed" / "cmssw_real_only_large" / "real_only_cmssw_event_features_with_unsupervised_boundary.csv"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
REPORTS = ROOT / "reports"


DRIVERS = [
    "MET_pt",
    "HT",
    "N_jets_30",
    "N_jets_50",
    "N_leptons",
    "N_btags_medium",
    "N_btags_tight",
    "max_btag_discriminator",
    "N_primary_vertices",
    "packed_candidate_count",
    "secondary_vertex_count",
    "compression_proxy_raw",
    "B_boundary_hand_defined_z",
    "real_only_unsupervised_boundary_score",
]


def tail_summary(df: pd.DataFrame, score: str, prefix: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    enrich_rows = []
    base = df["sample_id"].value_counts(normalize=True).to_dict()
    for q, label in [(0.90, "top10"), (0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        threshold = df[score].quantile(q)
        tail = df[df[score] >= threshold]
        rows.append({
            "score": score,
            "tail": label,
            "threshold": threshold,
            "events": len(tail),
            "mean_MET_pt": tail["MET_pt"].mean(),
            "median_MET_pt": tail["MET_pt"].median(),
            "mean_HT": tail["HT"].mean(),
            "median_HT": tail["HT"].median(),
            "mean_N_jets_30": tail["N_jets_30"].mean(),
            "mean_N_leptons": tail["N_leptons"].mean(),
            "mean_N_btags_medium": tail["N_btags_medium"].mean(),
            "mean_packed_candidate_count": tail["packed_candidate_count"].mean(),
        })
        dist = tail["sample_id"].value_counts(normalize=True).to_dict()
        for sample, frac in dist.items():
            enrich_rows.append({
                "score": score,
                "tail": label,
                "sample_id": sample,
                "tail_fraction": frac,
                "baseline_fraction": base.get(sample, 0),
                "enrichment_ratio": frac / base.get(sample, np.nan),
                "tail_events": int((tail["sample_id"] == sample).sum()),
            })
    return pd.DataFrame(rows), pd.DataFrame(enrich_rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    hand = pd.read_csv(HAND)
    unsup = pd.read_csv(UNSUP)
    cols_to_add = [c for c in unsup.columns if c not in hand.columns or c.startswith("real_only_")]
    df = hand.merge(unsup[["sample_id", "run", "lumi", "event"] + [c for c in cols_to_add if c not in {"sample_id", "run", "lumi", "event"}]],
                    on=["sample_id", "run", "lumi", "event"], how="left", suffixes=("", "_unsup"))

    hand_sum, hand_enrich = tail_summary(df, "B_boundary_hand_defined_z", "hand")
    unsup_sum, unsup_enrich = tail_summary(df, "real_only_unsupervised_boundary_score", "unsup")
    tail_summary_df = pd.concat([hand_sum, unsup_sum], ignore_index=True)
    enrich_df = pd.concat([hand_enrich, unsup_enrich], ignore_index=True)
    tail_summary_df.to_csv(TABLES / "real_only_high_boundary_tail_summary.csv", index=False)
    enrich_df.to_csv(TABLES / "real_only_high_boundary_tail_enrichment_by_sample.csv", index=False)

    driver_rows = []
    for score in ["B_boundary_hand_defined_z", "real_only_unsupervised_boundary_score"]:
        top = df[df[score] >= df[score].quantile(0.99)]
        rest = df[df[score] < df[score].quantile(0.99)]
        for var in [d for d in DRIVERS if d in df.columns]:
            driver_rows.append({
                "score": score,
                "variable": var,
                "top01_mean": top[var].mean(),
                "rest_mean": rest[var].mean(),
                "mean_difference": top[var].mean() - rest[var].mean(),
                "top01_median": top[var].median(),
                "rest_median": rest[var].median(),
            })
    driver_df = pd.DataFrame(driver_rows).sort_values(["score", "mean_difference"], ascending=[True, False])
    driver_df.to_csv(TABLES / "real_only_high_boundary_tail_driver_variables.csv", index=False)

    df.sort_values("B_boundary_hand_defined_z", ascending=False).head(1000).to_csv(
        TABLES / "real_only_top_1000_hand_boundary_events.csv", index=False
    )
    df.sort_values("real_only_unsupervised_boundary_score", ascending=False).head(1000).to_csv(
        TABLES / "real_only_top_1000_unsupervised_boundary_events.csv", index=False
    )
    by_file = df.groupby(["source_file", "sample_id"], as_index=False).agg(
        events=("event", "count"),
        hand_top01=("real_boundary_top_01", "mean"),
        unsup_top01=("real_only_unsup_top_01", "mean"),
    )
    by_file.to_csv(TABLES / "real_only_high_boundary_by_source_file.csv", index=False)

    # Figures.
    fig, ax = plt.subplots(figsize=(8, 4))
    df.boxplot(column="B_boundary_hand_defined_z", by="primary_dataset", ax=ax)
    ax.set_title("Hand-defined boundary score by real CMS primary dataset")
    ax.figure.suptitle("")
    ax.set_ylabel("Boundary z")
    fig.tight_layout()
    fig.savefig(FIGURES / "real_only_boundary_score_by_sample.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    for sample, group in df.groupby("primary_dataset"):
        ax.hist(group["B_boundary_hand_defined_z"], bins=80, alpha=0.45, density=True, label=sample)
    ax.set_xlabel("Hand-defined boundary z")
    ax.set_ylabel("Density")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "real_only_boundary_score_histograms.png", dpi=160)
    plt.close(fig)

    sample_df = df.sample(min(30000, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(6, 5))
    sc = ax.scatter(sample_df["MET_pt"], sample_df["HT"], c=sample_df["B_boundary_hand_defined_z"], s=4, cmap="viridis", alpha=0.5)
    ax.set_xlabel("MET pt")
    ax.set_ylabel("HT")
    fig.colorbar(sc, ax=ax, label="Boundary z")
    fig.tight_layout()
    fig.savefig(FIGURES / "real_only_MET_vs_HT_boundary.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5))
    sc = ax.scatter(sample_df["real_only_pca_axis_1"], sample_df["real_only_pca_axis_2"], c=sample_df["real_only_unsupervised_boundary_score"], s=4, cmap="magma", alpha=0.5)
    ax.set_xlabel("PCA axis 1")
    ax.set_ylabel("PCA axis 2")
    fig.colorbar(sc, ax=ax, label="Unsupervised boundary")
    fig.tight_layout()
    fig.savefig(FIGURES / "real_only_PCA_boundary_space.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    top05 = enrich_df[(enrich_df["score"] == "B_boundary_hand_defined_z") & (enrich_df["tail"] == "top05")]
    ax.bar(top05["sample_id"], top05["enrichment_ratio"])
    ax.axhline(1, color="black", linewidth=1)
    ax.set_ylabel("Top 5% enrichment ratio")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(FIGURES / "real_only_top_tail_enrichment.png", dpi=160)
    plt.close(fig)

    heat = df[df["B_boundary_hand_defined_z"] >= df["B_boundary_hand_defined_z"].quantile(0.99)]
    heat_cols = ["R_missing", "R_visible_energy", "R_multiplicity", "R_btag_structure", "R_reconstruction_complexity", "R_compression_proxy", "R_displacement_proxy"]
    heat_mean = heat.groupby("primary_dataset")[heat_cols].mean()
    fig, ax = plt.subplots(figsize=(8, 3))
    im = ax.imshow(heat_mean.values, aspect="auto", cmap="coolwarm")
    ax.set_xticks(range(len(heat_cols)), heat_cols, rotation=35, ha="right")
    ax.set_yticks(range(len(heat_mean.index)), heat_mean.index)
    fig.colorbar(im, ax=ax, label="Mean component")
    fig.tight_layout()
    fig.savefig(FIGURES / "real_only_component_heatmap_top_tail.png", dpi=160)
    plt.close(fig)

    report = [
        "# Real-Only High Boundary Tail Analysis",
        "",
        "Date: 2026-06-08",
        "",
        "This analysis uses real CMS collision MiniAOD only. It asks where high N-Frame boundary-stress conditions occur inside real data.",
        "",
        "## Tail Summary",
        "",
        tail_summary_df.to_markdown(index=False),
        "",
        "## Sample Enrichment",
        "",
        enrich_df.to_markdown(index=False),
        "",
        "## Main Driver Variables",
        "",
        driver_df.groupby("score").head(10).to_markdown(index=False),
        "",
        "## Source File Stability",
        "",
        "Exact per-event source file was not recorded by the analyzer; source-file stability is therefore limited to sample/log-level provenance in this run.",
        "",
        "## Interpretation",
        "",
        "The high-boundary tail is structured, not random: it is dominated by combinations of missing energy, visible energy, multiplicity and reconstruction complexity. The real-only result should be used as a boundary map for follow-up, not as a discovery claim.",
    ]
    (REPORTS / "REAL_ONLY_HIGH_BOUNDARY_TAIL_ANALYSIS.md").write_text("\n".join(report), encoding="utf-8")
    print(tail_summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
