from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
SUSY = ROOT / "data" / "processed" / "susy_relevance_benchmark_features" / "susy_sm_benchmark_events_with_BNF.csv"
SM = ROOT / "data" / "processed" / "sm_background_pilot_features" / "sm_background_events_with_BNF.csv"
REAL = ROOT / "data" / "processed" / "nframe_parameter_fit" / "real_data_with_fitted_nframe_boundary_score.csv"
DATE = "2026-06-09"
PARAMS = ["B_P_displacement_proxy", "B_P_reconstruction", "B_P_multiplicity", "B_P_btag_structure", "B_P_visible_energy", "B_P_missing", "B_P_compression"]
FEATURES = ["B_NF_fitted_frozen_raw", "B_P_missing", "B_P_visible_energy", "B_P_multiplicity", "B_P_btag_structure", "B_P_reconstruction", "B_P_displacement_proxy"]


def ci_bootstrap(values: pd.Series, threshold: float, reps: int = 500, seed: int = 13) -> tuple[float, float]:
    arr = (pd.to_numeric(values, errors="coerce").dropna().to_numpy() > threshold).astype(float)
    if len(arr) == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    boot = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(reps)]
    return float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def thresholds() -> pd.DataFrame:
    real = pd.read_csv(REAL)
    rows = []
    for label, q in [("q90", .90), ("q95", .95), ("q99", .99), ("q999", .999)]:
        rows.append({"threshold": label, "quantile": q, "value": real["B_NF_fitted_z"].quantile(q)})
    return pd.DataFrame(rows)


def load_all() -> pd.DataFrame:
    frames = []
    for path in [SUSY, SM]:
        if path.exists():
            frames.append(pd.read_csv(path))
    if not frames:
        raise FileNotFoundError("No SUSY or SM benchmark B_NF files found.")
    return pd.concat(frames, ignore_index=True)


def tail_fractions(df: pd.DataFrame, th: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sample, label, classification), group in df.groupby(["sample_id", "process_label", "classification"]):
        for t in th.itertuples(index=False):
            score = group["B_NF_fitted_frozen_raw"]
            frac = (score > t.value).mean()
            lo, hi = ci_bootstrap(score, t.value)
            rows.append({
                "sample_id": sample,
                "process_label": label,
                "classification": classification,
                "threshold": t.threshold,
                "threshold_value": t.value,
                "events": len(group),
                "mean_BNF": score.mean(),
                "median_BNF": score.median(),
                "tail_fraction": frac,
                "ci_low": lo,
                "ci_high": hi,
            })
    return pd.DataFrame(rows)


def ratios(tails: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold, group in tails.groupby("threshold"):
        susy = group[group["classification"].eq("signal")]
        sm = group[group["classification"].eq("SM_background")]
        for s in susy.itertuples(index=False):
            for b in sm.itertuples(index=False):
                denom = b.tail_fraction
                rows.append({
                    "threshold": threshold,
                    "signal_sample": s.sample_id,
                    "sm_background_sample": b.sample_id,
                    "signal_tail_fraction": s.tail_fraction,
                    "sm_tail_fraction": b.tail_fraction,
                    "tail_ratio_signal_over_sm": np.inf if denom == 0 and s.tail_fraction > 0 else (s.tail_fraction / denom if denom > 0 else np.nan),
                    "signal_minus_sm": s.tail_fraction - b.tail_fraction,
                })
    return pd.DataFrame(rows)


def drivers(df: pd.DataFrame, q95: float) -> pd.DataFrame:
    rows = []
    for sample, group in df.groupby("sample_id"):
        tail = group[group["B_NF_fitted_frozen_raw"] > q95]
        rest = group[group["B_NF_fitted_frozen_raw"] <= q95]
        for param in PARAMS:
            if param not in group:
                continue
            rows.append({
                "sample_id": sample,
                "process_label": group["process_label"].iloc[0],
                "classification": group["classification"].iloc[0],
                "parameter_family": param.replace("B_", ""),
                "q95_tail_mean": tail[param].mean() if len(tail) else np.nan,
                "rest_mean": rest[param].mean() if len(rest) else np.nan,
                "top_minus_rest": (tail[param].mean() - rest[param].mean()) if len(tail) and len(rest) else np.nan,
                "tail_events": len(tail),
            })
    return pd.DataFrame(rows)


def separability(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    signals = df[df["classification"].eq("signal")]
    backgrounds = df[df["classification"].eq("SM_background")]
    for signal_id, s in signals.groupby("sample_id"):
        for bg_id, b in backgrounds.groupby("sample_id"):
            pair = pd.concat([s, b], ignore_index=True)
            y = pair["classification"].eq("signal").astype(int)
            for feature in FEATURES:
                if feature not in pair or pair[feature].notna().sum() < 10:
                    auc = np.nan
                else:
                    valid = pair[feature].notna()
                    try:
                        auc = roc_auc_score(y[valid], pair.loc[valid, feature])
                    except ValueError:
                        auc = np.nan
                rows.append({"signal_sample": signal_id, "sm_background_sample": bg_id, "feature": feature, "auc_signal_vs_sm": auc})
    return pd.DataFrame(rows)


def write_report(path: Path, title: str, sections: list[tuple[str, object]]) -> None:
    lines = [f"# {title}", "", f"Date: {DATE}"]
    for header, body in sections:
        lines += ["", f"## {header}", ""]
        lines.append(body.to_markdown(index=False) if isinstance(body, pd.DataFrame) else str(body))
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = load_all()
    th = thresholds()
    tails = tail_fractions(df, th)
    ratio = ratios(tails)
    driver = drivers(df, float(th[th["threshold"].eq("q95")]["value"].iloc[0]))
    sep = separability(df)
    tails.to_csv(TABLES / "susy_vs_sm_bnf_tail_fractions.csv", index=False)
    ratio.to_csv(TABLES / "susy_vs_sm_bnf_tail_ratios.csv", index=False)
    driver.to_csv(TABLES / "susy_vs_sm_parameter_driver_comparison.csv", index=False)
    sep.to_csv(TABLES / "susy_vs_sm_simple_separability.csv", index=False)

    q95_rows = ratio[ratio["threshold"].eq("q95")].copy()
    if not q95_rows.empty and q95_rows["signal_minus_sm"].max() > 0:
        interpretation = "At q95, at least one SUSY benchmark has higher high-B_NF occupancy than at least one SM background. This is benchmark-level SUSY-relevant enrichment only, not a discovery claim."
    else:
        interpretation = "At q95, the available SUSY benchmarks do not exceed the SM backgrounds. The boundary score is not showing specificity in this pilot."
    write_report(
        REPORTS / "SUSY_VS_SM_SPECIFICITY_TEST_REPORT.md",
        "SUSY Versus SM Specificity Test Report",
        [("Tail Fractions", tails), ("Tail Ratios", ratio), ("Parameter Drivers In q95 Tail", driver), ("Interpretation", interpretation)],
    )
    write_report(
        REPORTS / "SUSY_VS_SM_SIMPLE_SEPARABILITY_CHECK.md",
        "SUSY Versus SM Simple Separability Check",
        [("AUC Checks", sep), ("Caution", "This is a descriptive benchmark separability check using the frozen B_NF score and components. It is not a discovery classifier and no equation was refitted on simulation.")],
    )
    print(tails.to_string(index=False))


if __name__ == "__main__":
    main()
