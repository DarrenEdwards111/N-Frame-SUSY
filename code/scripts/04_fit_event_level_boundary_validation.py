from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from stage2_common import FIGURES, PROCESSED, REPORTS, SAMPLES, TABLES, ensure_dirs


def cohen_d(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / pooled) if pooled else np.nan


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(PROCESSED / "stage2_event_features_scored.csv")
    df["sample_type"] = df["sample_id"].map(lambda s: SAMPLES.get(s, {}).get("sample_type", "unknown"))
    score = "B_boundary_equal_weight_z"
    cutoff10 = df[score].quantile(0.90)
    cutoff5 = df[score].quantile(0.95)
    cutoff1 = df[score].quantile(0.99)

    summary_rows = []
    for sample_id, sub in df.groupby("sample_id", sort=False):
        vals = sub[score].dropna()
        q25, q75 = vals.quantile([0.25, 0.75]) if len(vals) else (np.nan, np.nan)
        summary_rows.append(
            {
                "sample_id": sample_id,
                "sample_type": sub["sample_type"].iloc[0],
                "n_events": len(sub),
                "mean_B_boundary_equal_weight_z": vals.mean(),
                "sd": vals.std(ddof=1),
                "median": vals.median(),
                "iqr": q75 - q25,
                "pct_global_top_10": 100 * (sub[score] >= cutoff10).mean(),
                "pct_global_top_5": 100 * (sub[score] >= cutoff5).mean(),
                "pct_global_top_1": 100 * (sub[score] >= cutoff1).mean(),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(TABLES / "stage2_event_boundary_summary_by_sample.csv", index=False)

    pair_rows = []
    real_samples = [sid for sid, meta in SAMPLES.items() if meta["sample_type"] == "real_collision"]
    signal_samples = [sid for sid, meta in SAMPLES.items() if meta["sample_type"] == "simulated_signal"]
    for sig in signal_samples:
        sig_vals = df[df["sample_id"] == sig][score].dropna()
        for real in real_samples:
            real_vals = df[df["sample_id"] == real][score].dropna()
            if len(sig_vals) < 2 or len(real_vals) < 2:
                pair_rows.append({"signal_sample": sig, "real_sample": real, "status": "insufficient_events"})
                continue
            t = stats.ttest_ind(sig_vals, real_vals, equal_var=False)
            mw = stats.mannwhitneyu(sig_vals, real_vals, alternative="two-sided")
            ks = stats.ks_2samp(sig_vals, real_vals)
            pair_rows.append(
                {
                    "signal_sample": sig,
                    "real_sample": real,
                    "signal_n": len(sig_vals),
                    "real_n": len(real_vals),
                    "signal_mean": sig_vals.mean(),
                    "real_mean": real_vals.mean(),
                    "mean_difference": sig_vals.mean() - real_vals.mean(),
                    "welch_t": t.statistic,
                    "welch_p": t.pvalue,
                    "mann_whitney_u": mw.statistic,
                    "mann_whitney_p": mw.pvalue,
                    "ks_stat": ks.statistic,
                    "ks_p": ks.pvalue,
                    "cohens_d": cohen_d(sig_vals, real_vals),
                    "status": "ok",
                }
            )
    pairwise = pd.DataFrame(pair_rows)
    pairwise.to_csv(TABLES / "stage2_signal_vs_real_pairwise_tests.csv", index=False)

    model_df = df[df["sample_type"].isin(["real_collision", "simulated_signal"])].copy()
    model_df["signal_vs_real"] = (model_df["sample_type"] == "simulated_signal").astype(int)
    term_rows = []
    metric_rows = []
    model_specs = {
        "score_only": [score],
        "components_only": ["R_missing", "R_multiplicity", "R_reconstruction", "R_compression_proxy"],
    }
    fitted_predictor_notes = []
    for model_name, requested in model_specs.items():
        predictors = [
            col
            for col in requested
            if col in model_df and model_df[col].notna().sum() > 10 and model_df[col].nunique(dropna=True) > 1
        ]
        fitted_predictor_notes.append(f"{model_name}: {';'.join(predictors) if predictors else 'none'}")
        model_complete = model_df[["signal_vs_real"] + predictors].dropna() if predictors else pd.DataFrame()
        if not len(model_complete) or model_complete["signal_vs_real"].nunique() != 2:
            continue
        x = sm.add_constant(model_complete[predictors], has_constant="add")
        fit = sm.Logit(model_complete["signal_vs_real"], x).fit(disp=False, maxiter=200)
        pred = fit.predict(x)
        auc = roc_auc_score(model_complete["signal_vs_real"], pred)
        for term in x.columns:
            term_rows.append(
                {
                    "model": model_name,
                    "term": term,
                    "beta": fit.params[term],
                    "std_error": fit.bse[term],
                    "p_value": fit.pvalues[term],
                    "odds_ratio": np.exp(fit.params[term]),
                }
            )
        cv_auc = np.nan
        if model_complete["signal_vs_real"].value_counts().min() >= 5:
            clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=20260605)
            cv_auc = cross_val_score(clf, model_complete[predictors], model_complete["signal_vs_real"], cv=cv, scoring="roc_auc").mean()
        metric_rows.append(
            {
                "model": model_name,
                "n": len(model_complete),
                "predictors": ";".join(predictors),
                "auc": auc,
                "cv_auc_5fold": cv_auc,
                "notes": "Score and components are not fitted together because the score is constructed from the components.",
            }
        )
    pd.DataFrame(term_rows).to_csv(TABLES / "stage2_event_level_model_terms.csv", index=False)
    pd.DataFrame(metric_rows).to_csv(TABLES / "stage2_event_level_model_metrics.csv", index=False)

    make_figures(df, summary, score)
    write_report(summary, pairwise, pd.DataFrame(term_rows), pd.DataFrame(metric_rows), fitted_predictor_notes)
    print(f"Wrote validation outputs to {TABLES}")


def make_figures(df: pd.DataFrame, summary: pd.DataFrame, score: str) -> None:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))
    for sample_id, sub in df.groupby("sample_id", sort=False):
        plt.hist(sub[score].dropna(), bins=80, density=True, alpha=0.45, label=sample_id)
    plt.xlabel("N-Frame event boundary score z")
    plt.ylabel("Density")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES / "stage2_boundary_score_by_sample.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 6))
    for sample_type, sub in df.groupby("sample_type", sort=False):
        plt.hist(sub[score].dropna(), bins=80, density=True, alpha=0.45, label=sample_type)
    plt.xlabel("N-Frame event boundary score z")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES / "stage2_boundary_score_hist_signal_vs_real.png", dpi=160)
    plt.close()

    plot_df = summary.set_index("sample_id")[["pct_global_top_10", "pct_global_top_5", "pct_global_top_1"]]
    ax = plot_df.plot(kind="bar", figsize=(11, 6))
    ax.set_ylabel("Percent of sample")
    ax.set_xlabel("")
    plt.tight_layout()
    plt.savefig(FIGURES / "stage2_top_quantile_enrichment.png", dpi=160)
    plt.close()


def write_report(summary: pd.DataFrame, pairwise: pd.DataFrame, terms: pd.DataFrame, metrics: pd.DataFrame, predictor_notes: list[str]) -> None:
    lines = [
        "# Stage 2 Event-Level Boundary Validation",
        "",
        "This is a validation test, not a SUSY discovery test. It asks whether an N-Frame boundary score separates official simulated SUSY-like events from real CMS collision control samples.",
        "",
        "## Summary By Sample",
        "",
        "| sample | type | events | mean score z | top 10% | top 5% | top 1% |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| `{row.sample_id}` | {row.sample_type} | {int(row.n_events)} | {row.mean_B_boundary_equal_weight_z:.4f} | "
            f"{row.pct_global_top_10:.2f} | {row.pct_global_top_5:.2f} | {row.pct_global_top_1:.2f} |"
        )
    lines += ["", "## Pairwise Signal Versus Real Tests", "", "| signal | real | mean diff | Welch p | MW p | KS p | Cohen d |", "|---|---|---:|---:|---:|---:|---:|"]
    for _, row in pairwise.iterrows():
        if row.get("status") != "ok":
            lines.append(f"| `{row.signal_sample}` | `{row.real_sample}` | NA | NA | NA | NA | NA |")
        else:
            lines.append(
                f"| `{row.signal_sample}` | `{row.real_sample}` | {row.mean_difference:.4f} | {row.welch_p:.3e} | "
                f"{row.mann_whitney_p:.3e} | {row.ks_p:.3e} | {row.cohens_d:.3f} |"
            )
    lines += [
        "",
        "## Logistic Model",
        "",
        "The score and its component variables are not fitted in the same model because that would be mathematically redundant. Two models are reported instead.",
        "",
        "Predictors used:",
        "",
    ]
    for note in predictor_notes:
        lines.append(f"- `{note}`")
    if len(metrics):
        lines += ["", "| model | AUC | 5-fold CV AUC | predictors |", "|---|---:|---:|---|"]
        for _, row in metrics.iterrows():
            lines.append(f"| `{row.model}` | {row.auc:.4f} | {row.cv_auc_5fold:.4f} | `{row.predictors}` |")
    if len(terms):
        lines += ["", "| model | term | beta | p | odds ratio |", "|---|---|---:|---:|---:|"]
        for _, row in terms.iterrows():
            lines.append(f"| `{row.model}` | `{row.term}` | {row.beta:.4f} | {row.p_value:.3e} | {row.odds_ratio:.4f} |")
    lines += [
        "",
        "## Caution",
        "",
        "The simulated signal data are not evidence of real observed SUSY. This test only checks whether the boundary score identifies known SUSY-like simulated structures. A stronger later test would apply the fitted boundary model to real collision data only and look for high-boundary anomalies.",
        "",
    ]
    (REPORTS / "STAGE2_EVENT_LEVEL_BOUNDARY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
