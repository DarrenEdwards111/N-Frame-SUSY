from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
CONTRAST = ROOT / "data" / "processed" / "nframe_parameter_fit"
MC = ROOT / "data" / "processed" / "matched_control"
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


def z(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    return (s - s.mean()) / std if std and not pd.isna(std) else pd.Series(np.nan, index=s.index)


def family_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["event_uid", "primary_dataset", "source_file", "run", "quality_subset", "boundary_score_type", "tail_definition"]].copy()
    for fam, feats in FAMILIES.items():
        cols = [f"diff_{f}" for f in feats if f"diff_{f}" in df]
        zcols = [z(pd.to_numeric(df[c], errors="coerce")).rename(c) for c in cols]
        out[fam] = pd.concat(zcols, axis=1).mean(axis=1) if zcols else np.nan
    return out


def family_effects(df: pd.DataFrame) -> dict[str, float]:
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
    return effects


def bootstrap_effect_ci(df: pd.DataFrame, family: str) -> tuple[float, float]:
    rng = np.random.default_rng(42)
    ids = df["event_uid"].to_numpy()
    vals = []
    for _ in range(400):
        b = df.set_index("event_uid").loc[rng.choice(ids, len(ids), replace=True)].reset_index()
        vals.append(family_effects(b)[family])
    return tuple(np.nanquantile(vals, [0.025, 0.975]))


def bootstrap_ci(values: pd.Series) -> tuple[float, float]:
    x = values.dropna().to_numpy()
    if len(x) < 10:
        return np.nan, np.nan
    rng = np.random.default_rng(42)
    means = [rng.choice(x, len(x), replace=True).mean() for _ in range(400)]
    return tuple(np.quantile(means, [0.025, 0.975]))


def load_event_level(match_name: str) -> tuple[pd.DataFrame, pd.Series]:
    events = pd.read_csv(MC / "standard_quality_clean_events_rescored.csv")
    if "real_only_unsupervised_boundary_score" not in events and "trigger_filter_unsupervised_boundary_score" in events:
        events["real_only_unsupervised_boundary_score"] = events["trigger_filter_unsupervised_boundary_score"]
    events["event_uid"] = events["source_file_stem"].astype(str) + ":" + events["run"].astype(str) + ":" + events["lumi"].astype(str) + ":" + events["event"].astype(str)
    events = events.set_index("event_uid", drop=False)
    m = pd.read_csv(MC / match_name)
    use_controls = m.sort_values("control_rank").groupby("case_event_id").head(1)
    case = events.loc[use_controls.case_event_id].copy()
    ctrl = events.loc[use_controls.control_event_id].copy()
    case["label"] = 1
    ctrl["label"] = 0
    case["group"] = use_controls.case_event_id.values
    ctrl["group"] = use_controls.case_event_id.values
    data = pd.concat([case, ctrl], ignore_index=True)
    groups = data["group"].copy()
    for fam, feats in FAMILIES.items():
        cols = [f for f in feats if f in data]
        data[fam] = data[cols].apply(pd.to_numeric, errors="coerce").pipe(lambda x: (x - x.mean()) / x.std(ddof=0)).mean(axis=1)
    return data[["label"] + list(FAMILIES)].fillna(0), groups


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    importance_rows, coef_rows, perf_rows, rank_rows = [], [], [], []
    contrast_files = sorted(CONTRAST.glob("contrasts_*.csv"))
    for path in contrast_files:
        label = path.stem.replace("contrasts_", "")
        df = pd.read_csv(path)
        fam = family_rows(df)
        effects = family_effects(df)
        for family in FAMILIES:
            lo, hi = bootstrap_effect_ci(df, family)
            importance_rows.append(
                {
                    "tail": label,
                    "family": family,
                    "mean_standardised_contrast": effects[family],
                    "abs_mean_standardised_contrast": abs(effects[family]),
                    "bootstrap_ci_low": lo,
                    "bootstrap_ci_high": hi,
                    "sign": np.sign(effects[family]),
                    "cases": len(fam),
                }
            )
        weights = pd.Series(effects).fillna(0)
        if weights.abs().sum():
            weights = weights / weights.abs().sum()
        match_name = f"matched_controls_{label}.csv"
        if (MC / match_name).exists():
            data, groups = load_event_level(match_name)
            X = data[list(FAMILIES)].to_numpy()
            y = data["label"].to_numpy()
            cv = GroupKFold(n_splits=5)
            aucs, accs, coefs = [], [], []
            for train, test in cv.split(X, y, groups):
                scaler = StandardScaler()
                Xt = scaler.fit_transform(X[train])
                Xv = scaler.transform(X[test])
                model = LogisticRegression(penalty="l1", solver="liblinear", C=0.25, max_iter=1000, random_state=42)
                model.fit(Xt, y[train])
                pred = model.predict_proba(Xv)[:, 1]
                aucs.append(roc_auc_score(y[test], pred))
                accs.append(accuracy_score(y[test], pred >= 0.5))
                coefs.append(model.coef_[0])
            coef = np.vstack(coefs).mean(axis=0)
            for f, c in zip(FAMILIES, coef):
                coef_rows.append({"tail": label, "family": f, "mean_l1_logistic_coefficient": c})
            perf_rows.append({"tail": label, "model": "l1_logistic_grouped_by_case", "mean_auc": np.mean(aucs), "mean_accuracy": np.mean(accs), "folds": len(aucs)})
            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            full_model = LogisticRegression(penalty="l1", solver="liblinear", C=0.25, max_iter=1000, random_state=42)
            full_model.fit(Xs, y)
            scored = pd.DataFrame({"group": groups.to_numpy(), "label": y, "score": full_model.predict_proba(Xs)[:, 1]})
            pair = scored.pivot_table(index="group", columns="label", values="score", aggfunc="mean")
            rank_rows.append({"tail": label, "ranking_accuracy_case_above_controls": float((pair[1] > pair[0]).mean()), "cases": len(pair)})
        else:
            score = sum(weights[f] * fam[f].fillna(0) for f in FAMILIES)
            rank_rows.append({"tail": label, "ranking_accuracy_case_above_controls": float((score > 0).mean()), "cases": len(fam)})
    importance = pd.DataFrame(importance_rows)
    coef = pd.DataFrame(coef_rows)
    perf = pd.DataFrame(perf_rows)
    rank = pd.DataFrame(rank_rows)
    importance.to_csv(TABLES / "nframe_parameter_importance_by_tail.csv", index=False)
    coef.to_csv(TABLES / "nframe_parameter_model_coefficients.csv", index=False)
    perf.to_csv(TABLES / "nframe_parameter_model_performance.csv", index=False)
    rank.to_csv(TABLES / "nframe_parameter_ranking_accuracy.csv", index=False)
    report = [
        "# N-Frame Parameter Fit Report",
        "",
        "Date: 2026-06-08",
        "",
        "Parameters were fitted from matched real-data case-control contrasts. Labels mean high-boundary case versus matched ordinary control, not SUSY.",
        "",
        "## Parameter Importance",
        "",
        importance.sort_values(["tail", "abs_mean_standardised_contrast"], ascending=[True, False]).to_markdown(index=False),
        "",
        "## Logistic Performance",
        "",
        perf.to_markdown(index=False),
        "",
        "## Ranking Accuracy",
        "",
        rank.to_markdown(index=False),
    ]
    (REPORTS / "NFRAME_PARAMETER_FIT_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(importance.sort_values(["tail", "abs_mean_standardised_contrast"], ascending=[True, False]).to_string(index=False))
    print(perf.to_string(index=False))


if __name__ == "__main__":
    main()
