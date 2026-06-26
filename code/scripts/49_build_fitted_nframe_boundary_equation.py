from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    imp = pd.read_csv(TABLES / "nframe_parameter_importance_by_tail.csv")
    stab = pd.read_csv(TABLES / "nframe_parameter_bootstrap_stability.csv")
    primary = imp[imp["tail"].isin(["hand_top05", "hand_top01", "hand_top001"])]
    stability = stab[stab["tail"].isin(["hand_top05", "hand_top01", "hand_top001"])]
    base = primary.groupby("family", as_index=False).agg(
        mean_abs_importance=("abs_mean_standardised_contrast", "mean"),
        mean_signed_contrast=("mean_standardised_contrast", "mean"),
    )
    st = stability.groupby("family", as_index=False).agg(
        sign_stability=("sign_stability", "mean"),
        top3_rank_fraction=("top3_rank_fraction", "mean"),
        median_rank=("median_abs_rank", "median"),
    )
    weights = base.merge(st, on="family", how="left")
    weights["stable_importance"] = weights["mean_abs_importance"] * weights["sign_stability"].fillna(0) * (0.5 + 0.5 * weights["top3_rank_fraction"].fillna(0))
    weights["signed_weight_raw"] = weights["stable_importance"] * weights["mean_signed_contrast"].apply(lambda x: 1 if x >= 0 else -1)
    weights["weight"] = weights["signed_weight_raw"] / weights["signed_weight_raw"].abs().sum()
    weights["role"] = weights["family"].map({"P_compression": "secondary"}).fillna("primary")
    weights = weights.sort_values("weight", key=lambda s: s.abs(), ascending=False)
    weights.to_csv(TABLES / "nframe_fitted_boundary_equation_weights.csv", index=False)
    eq = "B_NF_fitted = " + " + ".join([f"{r.weight:.4f}*{r.family}" for r in weights.itertuples()])
    report = [
        "# Fitted N-Frame Boundary Equation",
        "",
        "Date: 2026-06-08",
        "",
        "The fitted equation is derived from stable matched-control parameter importance in real CMS collision data. It is a boundary equation, not a SUSY classifier.",
        "",
        "## Equation",
        "",
        f"`{eq}`",
        "",
        "## Weights",
        "",
        weights.to_markdown(index=False),
        "",
        "## Meaning",
        "",
        "- P_reconstruction: reconstruction complexity and event-building load.",
        "- P_displacement_proxy: secondary-vertex/displacement-like proxy, not direct evidence of displaced particles.",
        "- P_multiplicity: jet/lepton/object multiplicity.",
        "- P_btag_structure: b-tag and heavy-flavour-like reconstruction structure.",
        "- P_visible_energy: HT and visible-energy scale.",
        "- P_missing: MET and missing-energy scale.",
        "- P_compression: compression-like imbalance; treated as secondary because it is weak after matching.",
        "",
        "## Next Test",
        "",
        "Apply the equation to quality-clean real events and compare it with the previous hand-defined and unsupervised boundary scores.",
    ]
    (REPORTS / "FITTED_NFRAME_BOUNDARY_EQUATION.md").write_text("\n".join(report), encoding="utf-8")
    print(weights.to_string(index=False))
    print(eq)


if __name__ == "__main__":
    main()
