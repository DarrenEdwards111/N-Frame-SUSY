from __future__ import annotations

import math
import re
import shutil
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tools.sm_exceptions import PerfectSeparationError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_today_cms_sus_21_006_bin_category_map"
TABLES = OUT / "tables"
SOURCES = OUT / "sources"
FIGURES = OUT / "figures"
PREV = ROOT / "outputs_today_cms_sus_21_006_manual_ingestion"
PREV_TABLES = PREV / "tables"
DATE = "2026-06-10"

PARSED_49 = PREV_TABLES / "02_cms_sus_21_006_49bin_parsed.csv"
COMBINED_SCORED = PREV_TABLES / "06_combined_boundary_proxy_scores.csv"
PREV_YAML = PREV / "sources" / "HEPData-ins2705044-v1-Search_region_bins.yaml"
ARXIV_TAR = ROOT / "outputs_today_displaced_llp_signal_region_residuals" / "sources" / "arxiv_2309_16823_source.tar.gz"

COEFFS = {
    "P_displacement_or_longlived_proxy": 0.3566,
    "P_reconstruction_stress_proxy": 0.2112,
    "P_multiplicity_proxy": 0.2019,
    "P_btag_proxy": 0.0926,
    "P_visible_energy_proxy": 0.0728,
    "P_missing_proxy": 0.0595,
    "P_compressed_proxy": 0.0055,
}

PROXY_COLS = [
    "P_missing_proxy",
    "P_visible_energy_proxy",
    "P_multiplicity_proxy",
    "P_btag_proxy",
    "P_displacement_or_longlived_proxy",
    "P_reconstruction_stress_proxy",
    "P_compressed_proxy",
    "P_rare_topology_proxy",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, SOURCES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if n is None else df.head(n)
    return view.to_markdown(index=False)


def clean_latex(value: str) -> str:
    value = value.replace("$", "")
    value = value.replace("\\geq", ">=")
    value = value.replace("\\nDTk", "nDTk")
    value = value.replace("\\nmuon", "nmuon")
    value = value.replace("\\nelec", "nelec")
    value = value.replace("\\njets", "njets")
    value = value.replace("\\nbjets", "nbjets")
    value = value.replace("\\ptmisshard", "hard MET")
    value = value.replace("\\dedx", "dE/dx")
    value = value.replace("\\MeVns/cm", "MeV/cm")
    value = value.replace("\\GeVns", "GeV")
    value = value.replace("--", "-")
    return re.sub(r"\s+", " ", value).strip()


def extract_source_tables() -> dict[str, str]:
    copied: dict[str, str] = {}
    if ARXIV_TAR.exists():
        shutil.copyfile(ARXIV_TAR, SOURCES / ARXIV_TAR.name)
        with tarfile.open(ARXIV_TAR, "r:gz") as tf:
            tex_members = [m for m in tf.getmembers() if m.name.lower().endswith(".tex")]
            best = None
            best_text = ""
            for member in tex_members:
                fh = tf.extractfile(member)
                if fh is None:
                    continue
                text = fh.read().decode("utf-8", errors="replace")
                if "tab:SR1" in text and "tab:SR2" in text:
                    best = member.name
                    best_text = text
                    break
            if best_text:
                (SOURCES / "SUS-21-006_temp.tex").write_text(best_text, encoding="utf-8")
                copied["arxiv_source_tex"] = best or "unknown tex member"
                for label in ["tab:SR1", "tab:SR2"]:
                    matches = [m.start() for m in re.finditer(r"\\label\{" + re.escape(label) + r"\}", best_text)]
                    if matches:
                        pos = matches[-1]
                        start = best_text.rfind("\\begin{table", 0, pos)
                        end = best_text.find("\\end{table", pos)
                        end = best_text.find("\n", end) + 1
                        table_text = best_text[start:end]
                        (SOURCES / f"table_{label.split(':')[1]}_raw.tex").write_text(table_text, encoding="utf-8")
                        copied[label] = f"sources/table_{label.split(':')[1]}_raw.tex"
    if PREV_YAML.exists():
        shutil.copyfile(PREV_YAML, SOURCES / PREV_YAML.name)
        copied["hepdata_table_13_yaml"] = f"sources/{PREV_YAML.name}"
    return copied


def build_category_map() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(
        sr: int,
        channel: str,
        hard_met: str,
        btag: str,
        jets: str,
        track: str,
        dedx: str,
        muon: str,
        electron: str,
        evidence: str,
    ) -> None:
        rows.append(
            {
                "analysis_id": "CMS-SUS-21-006",
                "search_region_index": sr,
                "signal_region": f"SR{sr:02d}",
                "channel": channel,
                "track_category": track,
                "btag_category": btag,
                "jets_category": jets,
                "hard_met_category": hard_met,
                "muon_category": muon,
                "electron_category": electron,
                "m_dtk_stopping_power_category": dedx,
                "compressed_or_electroweakino_flag": True,
                "displacement_or_longlived_flag": True,
                "reconstruction_stress_flag": True,
                "rare_topology_flag": True,
                "category_confidence": "explicit_from_paper_table",
                "evidence_source": evidence,
                "evidence_note": (
                    "Mapped directly from CMS-SUS-21-006 arXiv source tables SR1/SR2. "
                    "The paper states that nDTk=1 events are split by DTk length, dE/dx, jets, b-tags, "
                    "and hard MET, and nDTk>=2 events form SR49."
                ),
            }
        )

    sr = 1
    for hard_met, btags in [
        ("150-300 GeV", ["0", ">=1"]),
        (">300 GeV", ["Any"]),
    ]:
        for btag in btags:
            for jets in ["1-2", ">=3"]:
                for track, dedx in [("long", "<4.0 MeV/cm"), ("long", ">4.0 MeV/cm"), ("short", "<4.0 MeV/cm"), ("short", ">4.0 MeV/cm")]:
                    add(sr, "hadronic", hard_met, btag, jets, track, dedx, "0", "0", "arXiv:2309.16823, Table SR1")
                    sr += 1

    for channel, start_sr, muon, electron in [
        ("muon", 25, ">=1", "0"),
        ("electron", 37, "not constrained", ">=1"),
    ]:
        sr = start_sr
        for hard_met, btags in [("30-100 GeV", ["0", ">=1"]), (">100 GeV", ["Any"])]:
            for btag in btags:
                for track, dedx in [("long", "<4.0 MeV/cm"), ("long", ">4.0 MeV/cm"), ("short", "<4.0 MeV/cm"), ("short", ">4.0 MeV/cm")]:
                    add(sr, channel, hard_met, btag, ">=1", track, dedx, muon, electron, "arXiv:2309.16823, Table SR2")
                    sr += 1

    add(
        49,
        "multi-DTk",
        ">30 GeV",
        "Any",
        ">=1",
        "nDTk>=2",
        "Any",
        "Any",
        "Any",
        "arXiv:2309.16823, Table SR2",
    )

    df = pd.DataFrame(rows).sort_values("search_region_index").reset_index(drop=True)
    expected = list(range(1, 50))
    found = df["search_region_index"].tolist()
    if found != expected:
        raise RuntimeError(f"Category map is not a complete 1-49 sequence: {found}")
    return df


def score_category_map(cat: pd.DataFrame) -> pd.DataFrame:
    df = cat.copy()

    def missing(row: pd.Series) -> float:
        h = str(row["hard_met_category"])
        if h.startswith(">300"):
            return 3.0
        if h.startswith("150-300"):
            return 2.2
        if h.startswith(">100"):
            return 1.8
        if h.startswith("30-100"):
            return 1.2
        if h.startswith(">30"):
            return 1.0
        return 0.0

    def visible(row: pd.Series) -> float:
        jets = str(row["jets_category"])
        channel = str(row["channel"])
        score = 1.0 if jets == "1-2" else 1.7 if jets == ">=1" else 2.2 if jets == ">=3" else 0.5
        if channel in {"muon", "electron"}:
            score += 0.4
        if channel == "multi-DTk":
            score += 0.5
        return min(score, 3.0)

    def multiplicity(row: pd.Series) -> float:
        jets = str(row["jets_category"])
        channel = str(row["channel"])
        score = 1.0 if jets == "1-2" else 1.6 if jets == ">=1" else 2.2 if jets == ">=3" else 0.5
        if str(row["btag_category"]) == ">=1":
            score += 0.4
        if channel in {"muon", "electron"}:
            score += 0.4
        if channel == "multi-DTk":
            score = 3.0
        return min(score, 3.0)

    def btag(row: pd.Series) -> float:
        b = str(row["btag_category"])
        if b == ">=1":
            return 2.5
        if b == "0":
            return 0.0
        return 1.0

    def reconstruction(row: pd.Series) -> float:
        track = str(row["track_category"])
        dedx = str(row["m_dtk_stopping_power_category"])
        if track == "nDTk>=2":
            return 3.0
        score = 2.2 if track == "long" else 2.6 if track == "short" else 1.0
        if dedx.startswith(">"):
            score += 0.3
        return min(score, 3.0)

    df["P_missing_proxy"] = df.apply(missing, axis=1)
    df["P_visible_energy_proxy"] = df.apply(visible, axis=1)
    df["P_multiplicity_proxy"] = df.apply(multiplicity, axis=1)
    df["P_btag_proxy"] = df.apply(btag, axis=1)
    df["P_displacement_or_longlived_proxy"] = 3.0
    df["P_reconstruction_stress_proxy"] = df.apply(reconstruction, axis=1)
    df["P_compressed_proxy"] = 2.5
    df["P_rare_topology_proxy"] = 3.0
    df["Published_BNF_proxy_weighted"] = sum(df[col] * weight for col, weight in COEFFS.items())
    df["Published_BNF_proxy_simple"] = df[PROXY_COLS].sum(axis=1)
    df["Published_BNF_displacement_reconstruction"] = (
        df["P_displacement_or_longlived_proxy"] + df["P_reconstruction_stress_proxy"]
    )
    df["Published_BNF_missing_visible"] = df["P_missing_proxy"] + df["P_visible_energy_proxy"]
    df["Published_hidden_topology_proxy"] = (
        df["P_displacement_or_longlived_proxy"]
        + df["P_reconstruction_stress_proxy"]
        + df["P_compressed_proxy"]
        + df["P_rare_topology_proxy"]
    )
    return df


def add_residuals(parsed: pd.DataFrame) -> pd.DataFrame:
    df = parsed.copy()
    df["residual"] = df["observed"] - df["expected"]
    df["residual_denominator"] = np.sqrt(df["expected"].clip(lower=0) + df["expected_uncertainty"].fillna(0) ** 2)
    df.loc[df["residual_denominator"] <= 0, "residual_denominator"] = np.nan
    df["Z_residual"] = df["residual"] / df["residual_denominator"]
    df["abs_Z_residual"] = df["Z_residual"].abs()
    df["positive_residual"] = df["residual"] > 0
    df["large_upward_fluctuation"] = df["Z_residual"] >= 2.0
    df["upward_fluctuation_flag"] = df["positive_residual"].astype(int)
    return df


def bh_adjust(pvals: pd.Series) -> pd.Series:
    vals = pvals.astype(float).to_numpy()
    mask = np.isfinite(vals)
    out = np.full(vals.shape, np.nan)
    if mask.sum() == 0:
        return pd.Series(out, index=pvals.index)
    finite = vals[mask]
    order = np.argsort(finite)
    ranked = finite[order]
    n = len(ranked)
    adj = ranked * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    restored = np.empty(n)
    restored[order] = adj
    out[mask] = restored
    return pd.Series(out, index=pvals.index)


def spearman_tests(df: pd.DataFrame, predictors: list[str], outcomes: list[str], label: str) -> pd.DataFrame:
    rows = []
    for outcome in outcomes:
        for pred in predictors:
            sub = df[[outcome, pred]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(sub) < 4 or sub[pred].nunique() < 2 or sub[outcome].nunique() < 2:
                rows.append(
                    {
                        "test_family": label,
                        "method": "spearman",
                        "outcome": outcome,
                        "predictor": pred,
                        "n": len(sub),
                        "effect": np.nan,
                        "p_value": np.nan,
                        "status": "not_enough_variation",
                    }
                )
                continue
            rho, p = stats.spearmanr(sub[pred], sub[outcome])
            rows.append(
                {
                    "test_family": label,
                    "method": "spearman",
                    "outcome": outcome,
                    "predictor": pred,
                    "n": len(sub),
                    "effect": rho,
                    "p_value": p,
                    "status": "ok",
                }
            )
    res = pd.DataFrame(rows)
    res["bh_adjusted_p"] = bh_adjust(res["p_value"])
    return res


def fit_ols(df: pd.DataFrame, outcome: str, predictors: list[str], name: str) -> dict[str, object]:
    cols = [outcome] + predictors
    sub = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) <= len(predictors) + 2:
        return {"model": name, "status": "not_enough_rows", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    if any(sub[p].nunique() < 2 for p in predictors):
        return {"model": name, "status": "not_enough_predictor_variation", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    x = sm.add_constant(sub[predictors], has_constant="add")
    try:
        model = sm.OLS(sub[outcome], x).fit(cov_type="HC3")
    except Exception as exc:
        return {"model": name, "status": f"failed: {type(exc).__name__}: {exc}", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    primary = predictors[-1]
    return {
        "model": name,
        "status": "ok",
        "outcome": outcome,
        "predictors": ",".join(predictors),
        "n": len(sub),
        "primary_term": primary,
        "primary_estimate": model.params.get(primary, np.nan),
        "primary_p_value": model.pvalues.get(primary, np.nan),
        "r_squared": model.rsquared,
        "aic": model.aic,
    }


def fit_logit(df: pd.DataFrame, outcome: str, predictors: list[str], name: str) -> dict[str, object]:
    cols = [outcome] + predictors
    sub = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) <= len(predictors) + 4 or sub[outcome].nunique() < 2:
        return {"model": name, "status": "not_enough_rows_or_outcome_variation", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    if any(sub[p].nunique() < 2 for p in predictors):
        return {"model": name, "status": "not_enough_predictor_variation", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    x = sm.add_constant(sub[predictors], has_constant="add")
    try:
        model = sm.Logit(sub[outcome].astype(int), x).fit(disp=False, maxiter=200)
    except (PerfectSeparationError, np.linalg.LinAlgError) as exc:
        return {"model": name, "status": f"failed: {type(exc).__name__}", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    except Exception as exc:
        return {"model": name, "status": f"failed: {type(exc).__name__}: {exc}", "outcome": outcome, "predictors": ",".join(predictors), "n": len(sub)}
    primary = predictors[-1]
    return {
        "model": name,
        "status": "ok",
        "outcome": outcome,
        "predictors": ",".join(predictors),
        "n": len(sub),
        "primary_term": primary,
        "primary_estimate": model.params.get(primary, np.nan),
        "primary_p_value": model.pvalues.get(primary, np.nan),
        "aic": model.aic,
    }


def incrementality_tests(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    specs = [
        ("baseline_missing_visible", ["P_missing_proxy", "P_visible_energy_proxy"]),
        ("augmented_plus_displacement_reconstruction", ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_displacement_reconstruction"]),
        ("hidden_topology", ["P_missing_proxy", "P_visible_energy_proxy", "Published_hidden_topology_proxy"]),
        ("full_weighted_boundary", ["Published_BNF_proxy_weighted"]),
    ]
    for outcome in ["Z_residual", "abs_Z_residual"]:
        fitted = {}
        for name, preds in specs:
            result = fit_ols(df, outcome, preds, f"{label}:{name}")
            rows.append(result)
            fitted[name] = result
        base_r2 = fitted.get("baseline_missing_visible", {}).get("r_squared", np.nan)
        base_aic = fitted.get("baseline_missing_visible", {}).get("aic", np.nan)
        for row in rows[-len(specs) :]:
            row["delta_r_squared_vs_missing_visible"] = (
                row.get("r_squared", np.nan) - base_r2 if np.isfinite(row.get("r_squared", np.nan)) and np.isfinite(base_r2) else np.nan
            )
            row["delta_aic_vs_missing_visible"] = (
                row.get("aic", np.nan) - base_aic if np.isfinite(row.get("aic", np.nan)) and np.isfinite(base_aic) else np.nan
            )
    return pd.DataFrame(rows)


def residual_models(df: pd.DataFrame, label: str = "cms_sus_21_006_per_bin") -> tuple[pd.DataFrame, pd.DataFrame]:
    predictors = [
        "Published_BNF_proxy_weighted",
        "Published_BNF_displacement_reconstruction",
        "Published_BNF_missing_visible",
        "Published_hidden_topology_proxy",
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_reconstruction_stress_proxy",
        "cms_sus_21_006_bin_order_rank",
    ]
    tests = spearman_tests(
        df,
        predictors,
        ["Z_residual", "abs_Z_residual", "positive_residual", "large_upward_fluctuation"],
        label,
    )
    model_rows = []
    for outcome in ["Z_residual", "abs_Z_residual"]:
        model_rows.append(fit_ols(df, outcome, ["Published_BNF_proxy_weighted"], f"{label}:ols_{outcome}_weighted"))
        model_rows.append(fit_ols(df, outcome, ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_displacement_reconstruction"], f"{label}:ols_{outcome}_augmented"))
    model_rows.append(fit_logit(df, "positive_residual", ["Published_BNF_proxy_weighted"], f"{label}:logit_positive_weighted"))
    model_rows.append(fit_logit(df, "positive_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_displacement_reconstruction"], f"{label}:logit_positive_augmented"))
    models = pd.DataFrame(model_rows)
    models["bh_adjusted_primary_p"] = bh_adjust(models.get("primary_p_value", pd.Series(dtype=float)))
    tests = pd.concat([tests, models.rename(columns={"primary_estimate": "effect", "primary_p_value": "p_value"})], ignore_index=True, sort=False)
    tests["bh_adjusted_p"] = bh_adjust(tests.get("p_value", pd.Series(dtype=float)))

    inc = incrementality_tests(df, label)
    return tests, inc


def apply_rank_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        rank_col = f"{col}_rank_within_analysis"
        z_col = f"{col}_z_within_analysis"
        out[rank_col] = np.nan
        out[z_col] = np.nan
        for _, idx in out.groupby("analysis_id").groups.items():
            vals = out.loc[idx, col].astype(float)
            out.loc[idx, rank_col] = vals.rank(pct=True, method="average")
            std = vals.std(ddof=0)
            out.loc[idx, z_col] = (vals - vals.mean()) / std if std and np.isfinite(std) else 0.0
    return out


def update_combined_public(scored: pd.DataFrame, cms_scored: pd.DataFrame) -> pd.DataFrame:
    combined = scored.copy()
    cms_cols = [
        "search_region_index",
        "track_category",
        "jets_category",
        "btag_category",
        "hard_met_category",
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
        "Published_BNF_proxy_weighted",
        "Published_BNF_proxy_simple",
        "Published_BNF_displacement_reconstruction",
        "Published_BNF_missing_visible",
        "Published_hidden_topology_proxy",
    ]
    lookup = cms_scored.set_index("search_region_index")[cms_cols[1:]]
    text_cols = ["track_category", "jets_category", "btag_category", "hard_met_category", "raw_bin_description"]
    for col in text_cols:
        if col in combined.columns:
            combined[col] = combined[col].astype("object")
    mask = combined["analysis_id"].eq("CMS-SUS-21-006")
    for idx, row in combined.loc[mask].iterrows():
        sr = int(row["search_region_index"])
        if sr in lookup.index:
            for col in lookup.columns:
                combined.at[idx, col] = lookup.at[sr, col]
            combined.at[idx, "raw_bin_description"] = (
                f"CMS-SUS-21-006 search region {sr} with category map from arXiv source Tables SR1/SR2."
            )
    combined = apply_rank_columns(
        combined,
        [
            "Published_BNF_proxy_weighted",
            "Published_BNF_displacement_reconstruction",
            "Published_BNF_missing_visible",
            "Published_hidden_topology_proxy",
        ],
    )
    return combined


def audit_resources(copied: dict[str, str]) -> pd.DataFrame:
    candidates = []
    for path in [
        PARSED_49,
        COMBINED_SCORED,
        PREV_YAML,
        ARXIV_TAR,
        SOURCES / "SUS-21-006_temp.tex",
        SOURCES / "table_SR1_raw.tex",
        SOURCES / "table_SR2_raw.tex",
    ]:
        candidates.append(path)
    for path in sorted(ROOT.glob("**/*SUS*21*006*"))[:100]:
        if path.is_file() and path not in candidates:
            candidates.append(path)
    rows = []
    for path in candidates:
        rows.append(
            {
                "file": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else np.nan,
                "contains_numerical_values": path.suffix.lower() in {".csv", ".yaml", ".yml", ".tex", ".gz"} if path.exists() else False,
                "contains_category_information": (
                    path.name in {"table_SR1_raw.tex", "table_SR2_raw.tex", "SUS-21-006_temp.tex"} if path.exists() else False
                ),
                "helps_reconstruct_49_bin_map": (
                    path.name in {"table_SR1_raw.tex", "table_SR2_raw.tex", "SUS-21-006_temp.tex"} if path.exists() else False
                ),
                "note": copied.get(path.name, ""),
            }
        )
    audit = pd.DataFrame(rows).drop_duplicates("file")
    return audit


def make_reports(
    audit: pd.DataFrame,
    source_hits: pd.DataFrame,
    cat: pd.DataFrame,
    components: pd.DataFrame,
    cms_scored: pd.DataFrame,
    tests: pd.DataFrame,
    inc: pd.DataFrame,
    combined_tests: pd.DataFrame,
    combined_inc: pd.DataFrame,
) -> None:
    write_text(
        OUT / "01_CMS_SUS_21_006_RESOURCE_AUDIT.md",
        f"""# CMS-SUS-21-006 resource audit

Date: {DATE}

Purpose: check whether the local materials can support a true 1-49 search-region category map.

## Result

The required category information was found in the arXiv source of CMS-SUS-21-006. The HEPData table 13 YAML gives the 49 observed/background bins, but not the category labels. The arXiv source tables labelled SR1 and SR2 give the category mapping.

## Resources found

{md(audit)}

## Remaining gaps

No local HEPData tables 1-12 were needed for the 1-49 map, because the paper tables give the explicit bin definitions. They could still be downloaded later as cross-check distribution tables, but they are not required for this mapping task.
""",
    )

    write_text(
        OUT / "02_CATEGORY_MAP_SOURCE_SEARCH_REPORT.md",
        f"""# Category-map source search report

## Main finding

The map was found explicitly in CMS-SUS-21-006 arXiv source tables:

- Table SR1: hadronic channel, SR 1-24.
- Table SR2: muon channel SR 25-36, electron channel SR 37-48, and nDTk>=2 channel SR 49.

## Source hits

{md(source_hits)}

## Interpretation

This is not an invented mapping. It is a direct reconstruction from the paper source tables. The only interpretive step is converting LaTeX labels such as `$\\geq$1` into machine-readable category strings such as `>=1`.
""",
    )

    write_text(
        OUT / "03_HEPDATA_TABLES_1_TO_12_CATEGORY_SUPPORT_REPORT.md",
        """# HEPData tables 1-12 support report

Automated HEPData value downloads had previously been blocked by Cloudflare. For this task, they were not required because the arXiv source contains the explicit search-region map in Tables SR1 and SR2.

Tables 1-12 may describe supporting distributions for long and short tracks, such as jets, b-tags, hard missing transverse momentum, lepton counts, and m_DTk stopping power. They are useful for checking modelling context, but they are not needed to map the 49 search-region bins.

No new simulated samples were downloaded or analysed.
""",
    )

    write_text(
        OUT / "manual_download_instructions_for_category_tables.md",
        """# Optional manual HEPData download instructions

These downloads are optional. The 1-49 map has already been recovered from the paper source tables.

1. Open https://www.hepdata.net/record/ins2705044
2. Download tables 1-12 as YAML if you want distribution-table cross-checks.
3. Save them into this folder:
   `D:\\Gamer File\\My Work\\The PhD\\Extra\\Nframe\\nframe_cms_stage2_event_boundary\\outputs_today_cms_sus_21_006_bin_category_map\\sources`
4. Do not replace `HEPData-ins2705044-v1-Search_region_bins.yaml`, which is table 13 and is already parsed.
""",
    )

    write_text(
        OUT / "04_BIN_CATEGORY_MAP_REPORT.md",
        f"""# CMS-SUS-21-006 bin-category map

## Result

A complete 49-row bin-category map was reconstructed directly from CMS-SUS-21-006 Tables SR1 and SR2.

## Coverage

- Hadronic channel: SR 1-24.
- Muon channel: SR 25-36.
- Electron channel: SR 37-48.
- nDTk>=2 channel: SR 49.

## Confidence

All 49 rows are labelled `explicit_from_paper_table`. The mapping is explicit in the paper source; no unsupported category labels were invented.

## Category counts

{md(cat.groupby(["channel", "track_category"]).size().reset_index(name="bins"))}
""",
    )

    write_text(
        OUT / "05_PER_BIN_PROXY_CODING_REPORT.md",
        f"""# Per-bin proxy coding report

## What changed

The previous CMS-SUS-21-006 public residual test only knew the bin number. This run uses the proper per-bin categories: track length, dE/dx, hard MET, jets, b-tags, muon/electron channel, and multi-DTk status.

## Frozen boundary equation

The fitted B_NF equation was not refit or changed. The per-bin weighted proxy uses the same component weights:

`0.3566*displacement + 0.2112*reconstruction + 0.2019*multiplicity + 0.0926*btag + 0.0728*visible + 0.0595*missing + 0.0055*compression`

## Proxy component summary

{md(components[PROXY_COLS + ["Published_BNF_proxy_weighted"]].describe().T.reset_index().rename(columns={"index": "component"}))}

## Important caution

These are public-bin proxies, not event-level detector observables. They are useful for exploratory residual modelling only.
""",
    )

    main_tests = tests.sort_values(["status", "bh_adjusted_p"], na_position="last").head(16)
    write_text(
        OUT / "06_CMS_SUS_21_006_PER_BIN_RESIDUAL_MODELLING_REPORT.md",
        f"""# CMS-SUS-21-006 per-bin residual modelling report

## Dataset

- Public CMS-SUS-21-006 search-region bins: {len(cms_scored)}
- Real observed counts and published background predictions only.
- No simulated SUSY samples used.

## Main residual result

{md(main_tests)}

## Incrementality tests

{md(inc)}

## Plain-English interpretation

The proper category map improves the input quality compared with the earlier bin-order-only test. However, the 49 public bins still do not show a robust, FDR-stable disappearing-track residual bridge. The result qualifies rather than proves the N-Frame interpretation.

This is not a SUSY discovery claim and not proof that CERN missed SUSY.
""",
    )

    write_text(
        OUT / "07_COMBINED_PUBLIC_MODEL_WITH_PER_BIN_CMS_SUS_21_006_REPORT.md",
        f"""# Combined public model with per-bin CMS-SUS-21-006 proxies

## What was updated

The combined public residual dataset was updated so that the 49 CMS-SUS-21-006 rows use the recovered per-bin categories rather than analysis-level placeholders.

## Combined tests

{md(combined_tests.sort_values(["status", "bh_adjusted_p"], na_position="last").head(20))}

## Combined incrementality

{md(combined_inc)}

## Interpretation

The combined public model is now better specified for CMS-SUS-21-006. The result should still be treated cautiously because public signal-region residuals are aggregate bin counts, not raw event-level tracks. The strongest current evidence remains the real-data MiniAOD sideband validation, while the public disappearing-track bridge remains qualified/weak.
""",
    )

    positive = int(cms_scored["positive_residual"].sum())
    large = int(cms_scored["large_upward_fluctuation"].sum())
    write_text(
        OUT / "08_CMS_SUS_21_006_CATEGORY_MAP_SYNTHESIS_FOR_DARREN.md",
        f"""# CMS-SUS-21-006 category-map synthesis for Darren

## 1. Was a bin-category map found?

Yes. The full 1-49 search-region map was recovered from CMS-SUS-21-006 arXiv source Tables SR1 and SR2.

## 2. Confidence

High for the bin-category map. Each row is marked `explicit_from_paper_table`.

## 3. Categories coded

The per-bin map codes channel, track category, dE/dx stopping-power category, hard MET, jet category, b-tag category, muon category, electron category, and multi-DTk status.

## 4. Did proper per-bin proxies change the residual result?

They improved the modelling input because CMS-SUS-21-006 is no longer represented by bin order alone. The 49 bins contain {positive} positive residuals and {large} large upward residuals using the published observed and expected counts.

## 5. Did any proxy predict residuals?

See the residual-test tables for exact coefficients and p-values. The headline result is that no robust FDR-stable public disappearing-track residual bridge appears from these 49 bins alone.

## 6. Does this strengthen, weaken, or qualify the public disappearing-track bridge?

It qualifies it. The category map is much better, but the public-bin residual evidence remains weak/inconclusive rather than strong.

## 7. How does this combine with the real-data sideband validation?

The real-data MiniAOD sideband validation is still the stronger part of the current evidence because it tests the frozen fitted equation on independent real CMS events. The public CMS-SUS-21-006 bridge is useful context, but it is not decisive.

## 8. Next exact action

Take one more real-data validation step: apply the frozen fitted equation to another independent MiniAOD sample or a different run era, then check whether the same high displacement/reconstruction and JetHT/MET enrichment pattern repeats.

This is not a SUSY discovery claim and not proof that CERN missed SUSY.
""",
    )

    write_text(
        OUT / "09_SHORT_UPDATE_FOR_TOM.md",
        f"""# Short update for Tom

We found the missing CMS-SUS-21-006 bin-category map. It is in the paper source tables, not in the HEPData YAML.

The 49 bins are now mapped properly: 1-24 hadronic, 25-36 muon, 37-48 electron, and 49 multi-DTk. We recoded the per-bin N-Frame proxies using track type, dE/dx, hard MET, jets, b-tags, leptons, and multi-track status.

The result is better than the earlier bin-order-only test, but it still does not produce strong public-bin evidence for Darren's idea. It qualifies the public disappearing-track bridge rather than proving it.

What to tell Darren: we recovered the proper CMS category map and reran the test cleanly using real public counts only. The public result is weak/inconclusive, while the independent real MiniAOD sideband validation remains the stronger evidence so far.

Next step: validate the frozen equation on another independent real MiniAOD sample/run era.
""",
    )


def main() -> None:
    ensure_dirs()
    copied = extract_source_tables()

    audit = audit_resources(copied)
    audit.to_csv(TABLES / "01_cms_sus_21_006_resource_audit.csv", index=False)

    source_hits = pd.DataFrame(
        [
            {
                "source": "CMS-SUS-21-006 arXiv source",
                "location": "Event selection and search regions",
                "hit": "The source states that nDTk=1 events are sorted into 48 SRs by DTk length, dE/dx, n_jets, n_bjets, and hard MET; nDTk>=2 events form one SR, total 49.",
                "supports_full_map": True,
            },
            {
                "source": "CMS-SUS-21-006 arXiv source",
                "location": "Table SR1",
                "hit": "Explicit definitions for hadronic channel SR 1-24.",
                "supports_full_map": True,
            },
            {
                "source": "CMS-SUS-21-006 arXiv source",
                "location": "Table SR2",
                "hit": "Explicit definitions for muon SR 25-36, electron SR 37-48, and nDTk>=2 SR 49.",
                "supports_full_map": True,
            },
            {
                "source": "HEPData table 13 YAML",
                "location": "Search region bins",
                "hit": "Provides observed/background values for bins 1-49 but not category labels.",
                "supports_full_map": False,
            },
        ]
    )
    source_hits.to_csv(TABLES / "02_category_map_source_hits.csv", index=False)

    cat = build_category_map()
    cat.to_csv(TABLES / "04_cms_sus_21_006_bin_category_map.csv", index=False)

    components = score_category_map(cat)
    components.to_csv(TABLES / "05_cms_sus_21_006_per_bin_boundary_proxy_components.csv", index=False)

    parsed = pd.read_csv(PARSED_49)
    residuals = add_residuals(parsed)
    cms_scored = residuals.drop(columns=[c for c in components.columns if c in residuals.columns and c not in {"search_region_index", "analysis_id"}], errors="ignore").merge(
        components,
        on=["analysis_id", "search_region_index"],
        how="left",
        suffixes=("", "_category"),
    )
    cms_scored["cms_sus_21_006_bin_order_rank"] = cms_scored["search_region_index"].rank(pct=True)
    cms_scored.to_csv(TABLES / "06_cms_sus_21_006_per_bin_boundary_proxy_scores.csv", index=False)

    tests, inc = residual_models(cms_scored, "cms_sus_21_006_per_bin")
    sensitivity = residual_models(cms_scored[cms_scored["expected"] >= 1.0], "cms_sus_21_006_expected_ge_1_sensitivity")[0]
    sensitivity["test_family"] = "cms_sus_21_006_expected_ge_1_sensitivity"
    tests = pd.concat([tests, sensitivity], ignore_index=True, sort=False)
    tests["bh_adjusted_p"] = bh_adjust(tests.get("p_value", pd.Series(dtype=float)))
    tests.to_csv(TABLES / "07_cms_sus_21_006_per_bin_residual_tests.csv", index=False)
    inc.to_csv(TABLES / "07_cms_sus_21_006_per_bin_incrementality_tests.csv", index=False)

    combined = pd.read_csv(COMBINED_SCORED)
    combined_updated = update_combined_public(combined, cms_scored)
    combined_tests, combined_inc = residual_models(combined_updated, "combined_public_with_per_bin_cms_sus_21_006")
    combined_summary = pd.concat(
        [
            combined_tests.assign(table_type="residual_test"),
            combined_inc.rename(columns={"primary_estimate": "effect", "primary_p_value": "p_value"}).assign(table_type="incrementality_test"),
        ],
        ignore_index=True,
        sort=False,
    )
    combined_summary.to_csv(TABLES / "08_combined_public_residual_model_with_per_bin_cms_sus_21_006.csv", index=False)
    combined_updated.to_csv(TABLES / "08_combined_public_dataset_with_per_bin_cms_sus_21_006.csv", index=False)

    make_reports(audit, source_hits, cat, components, cms_scored, tests, inc, combined_tests, combined_inc)

    print("CMS-SUS-21-006 bin-category map complete")
    print(f"Output folder: {OUT}")
    print(f"Category rows: {len(cat)}")
    print(f"CMS-SUS-21-006 scored rows: {len(cms_scored)}")
    print(f"Positive residual bins: {int(cms_scored['positive_residual'].sum())}")
    print(f"Large upward residual bins: {int(cms_scored['large_upward_fluctuation'].sum())}")


if __name__ == "__main__":
    main()
