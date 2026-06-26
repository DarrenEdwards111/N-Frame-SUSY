from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONTRAST = ROOT / "data" / "processed" / "nframe_parameter_fit"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"

FAMILIES = {
    "P_reconstruction": ["R_reconstruction_complexity", "packed_candidate_count", "N_primary_vertices", "secondary_vertex_count"],
    "P_displacement_proxy": ["R_displacement_proxy", "secondary_vertex_count", "displacement_proxy_raw"],
    "P_multiplicity": ["R_multiplicity", "N_jets_30", "N_jets_50", "N_leptons"],
    "P_btag_structure": ["R_btag_structure", "N_btags_medium", "N_btags_tight", "max_btag_discriminator"],
    "P_visible_energy": ["R_visible_energy", "HT"],
    "P_missing": ["R_missing", "MET_pt"],
    "P_compression": ["R_compression_proxy", "compression_proxy_raw"],
}


def z(s):
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def family_effects(df):
    effects = {}
    for fam, feats in FAMILIES.items():
        vals = []
        for feat in feats:
            col = f"diff_{feat}"
            if col not in df:
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            std = s.std(ddof=0)
            if len(s) and std and not pd.isna(std):
                vals.append(s.mean() / std)
        effects[fam] = float(np.mean(vals)) if vals else np.nan
    return pd.Series(effects)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    rows, rank_rows = [], []
    for path in sorted(CONTRAST.glob("contrasts_*.csv")):
        tail = path.stem.replace("contrasts_", "")
        df = pd.read_csv(path)
        ids = df["event_uid"].to_numpy()
        boot_means = []
        for _ in range(500):
            sample_ids = rng.choice(ids, len(ids), replace=True)
            b = df.set_index("event_uid").loc[sample_ids].reset_index()
            boot_means.append(family_effects(b))
        boot = pd.DataFrame(boot_means)
        mean = family_effects(df)
        ranks = boot.abs().rank(axis=1, ascending=False, method="min")
        for fam in FAMILIES:
            vals = boot[fam].dropna()
            rows.append({
                "tail": tail,
                "family": fam,
                "mean_standardised_contrast": mean[fam],
                "ci_low": vals.quantile(.025),
                "ci_high": vals.quantile(.975),
                "sign_stability": float((np.sign(vals) == np.sign(mean[fam])).mean()),
                "median_abs_rank": float(ranks[fam].median()),
                "top3_rank_fraction": float((ranks[fam] <= 3).mean()),
            })
            rank_rows.append({"tail": tail, "family": fam, "mean_rank": float(ranks[fam].mean()), "median_rank": float(ranks[fam].median())})
    stability = pd.DataFrame(rows)
    rank = pd.DataFrame(rank_rows)
    stability.to_csv(TABLES / "nframe_parameter_bootstrap_stability.csv", index=False)
    rank.to_csv(TABLES / "nframe_parameter_rank_stability.csv", index=False)
    report = [
        "# N-Frame Parameter Stability Report",
        "",
        "Date: 2026-06-08",
        "",
        "Uncertainty was estimated by bootstrapping case IDs, not raw matched rows.",
        "",
        stability.sort_values(["tail", "median_abs_rank"]).to_markdown(index=False),
    ]
    (REPORTS / "NFRAME_PARAMETER_STABILITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(stability.sort_values(["tail", "median_abs_rank"]).to_string(index=False))


if __name__ == "__main__":
    main()
