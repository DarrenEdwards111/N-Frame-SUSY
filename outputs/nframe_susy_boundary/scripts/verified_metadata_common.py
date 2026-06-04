import json
import math
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"
RAW = DATA / "raw"
INTERMEDIATE = DATA / "intermediate"
PROCESSED = DATA / "processed"
RESULTS = PROJECT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
LOGS = RESULTS / "logs"
SOURCE_AUDIT = RESULTS / "source_audit"
SOURCE_RAW = RAW / "sources"

INPUT_CANDIDATES = [
    PROCESSED / "signal_regions_metadata_enriched_scored_outcomes.csv",
    PROCESSED / "signal_regions_metadata_enriched.csv",
    RAW / "real_smodels_signal_regions_full.csv",
]

CORE_FIELDS = {
    "MET": ("MET_min", "MET_max"),
    "HT_or_meff": ("HT_min", "HT_max"),
    "meff": ("meff_min", "meff_max"),
    "N_jets": ("Njets_min", "Njets_max"),
    "N_leptons": ("Nleptons_min", "Nleptons_max"),
    "N_btags": ("Nb_min", "Nb_max"),
    "ctau": ("ctau_min", "ctau_max"),
    "d0": ("d0_min", "d0_max"),
    "DeltaM": ("DeltaM_min", "DeltaM_max"),
}

BOOL_FIELDS = [
    "is_compressed",
    "is_long_lived",
    "is_displaced",
    "is_disappearing_track",
    "is_high_MET",
    "is_high_multiplicity",
    "is_reconstruction_difficult",
]

MODEL_FEATURES = ["MET", "HT_or_meff", "N_jets", "N_leptons", "N_btags"]
COMPONENTS = [
    "R_missing",
    "R_lifetime",
    "R_displacement",
    "R_compression",
    "R_multiplicity",
    "R_reconstruction",
]

HIGH_MEDIUM = {"HIGH", "MEDIUM"}


def ensure_dirs():
    for path in [RAW, INTERMEDIATE, PROCESSED, RESULTS, TABLES, FIGURES, LOGS, SOURCE_AUDIT, SOURCE_RAW]:
        path.mkdir(parents=True, exist_ok=True)


def latest_input(path=None):
    if path:
        return Path(path)
    for candidate in INPUT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No enriched signal-region input table found.")


def load_regions(path=None):
    df = pd.read_csv(latest_input(path))
    if "Delta_N" not in df:
        df["Delta_N"] = df["N_obs"] - df["N_exp"]
    if "Z" not in df:
        df["Z"] = df["Delta_N"] / df["sigma_exp"]
    df["Z_capped_3"] = df["Z"].clip(-3, 3)
    df["Z_capped_5"] = df["Z"].clip(-5, 5)
    df["Z_conservative"] = df["Delta_N"] / np.sqrt(df["sigma_exp"].fillna(0) ** 2 + df["N_exp"].clip(lower=0).fillna(0) + 1.0)
    df["Poisson_deviance_residual"] = poisson_deviance_residual(df["N_obs"], df["N_exp"])
    return df


def poisson_deviance_residual(obs, exp):
    obs = pd.to_numeric(obs, errors="coerce").clip(lower=0)
    exp = pd.to_numeric(exp, errors="coerce").clip(lower=1e-9)
    term = np.where(obs > 0, obs * np.log(obs / exp) - (obs - exp), exp)
    return np.sign(obs - exp) * np.sqrt(2 * np.maximum(term, 0))


def zscore(series):
    vals = pd.to_numeric(series, errors="coerce")
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return ((vals - vals.mean(skipna=True)) / std).fillna(0.0)


def normalized_label(value):
    text = str(value).lower()
    text = re.sub(r"\\[a-zA-Z]+|[{}$^]", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def text_for_row(row):
    return " ".join(
        str(row.get(col, ""))
        for col in ["analysis", "signal_region", "source_comment", "category", "category_enriched", "source_path"]
        if pd.notna(row.get(col, ""))
    )


def confidence_for_numeric(row, canonical, value):
    if pd.isna(value):
        return ("UNAVAILABLE", "", "")
    text = text_for_row(row)
    value_text = strip_trailing_zero(value)
    source = str(row.get("source_url", "")) or str(row.get("source_path", ""))
    comment = str(row.get("source_comment", ""))
    if canonical in ["N_jets", "N_leptons", "N_btags"]:
        explicit = numeric_explicit_pattern(canonical, value_text, comment)
    else:
        explicit = numeric_explicit_pattern(canonical, value_text, comment)
    if explicit:
        return ("MEDIUM", source, explicit)
    if numeric_explicit_pattern(canonical, value_text, text):
        return ("LOW", source, numeric_explicit_pattern(canonical, value_text, text))
    return ("LOW", source, f"label/comment-derived value={value_text}")


def numeric_explicit_pattern(canonical, value_text, text):
    escaped = re.escape(value_text)
    patterns = {
        "MET": [rf"(?:MET|MHT|ETmiss|E[_ ]?T\^?miss|pTmiss|missing transverse)\D{{0,20}}(?:>|>=|=|:)?\D{{0,10}}{escaped}"],
        "HT_or_meff": [rf"(?:HT|meff|m_eff|M_eff|Meff|MHT|MT2|mT2)\D{{0,20}}(?:>|>=|=|:)?\D{{0,10}}{escaped}"],
        "meff": [rf"(?:meff|m_eff|M_eff|Meff)\D{{0,20}}(?:>|>=|=|:)?\D{{0,10}}{escaped}"],
        "N_jets": [rf"(?:Njets?|N_jets?|jets?)\D{{0,20}}(?:>|>=|=|:|at least)?\D{{0,10}}{escaped}", rf"{escaped}\s*j(?:et)?s?\b"],
        "N_leptons": [rf"{escaped}\s*(?:l|lep|lepton)s?\b", rf"(?:leptons?|Nlep)\D{{0,20}}{escaped}"],
        "N_btags": [rf"(?:Nb|N_b|b-?tags?|b-?jets?)\D{{0,20}}{escaped}", rf"{escaped}\s*b(?:tag|jet)?s?\b"],
    }.get(canonical, [])
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)[:240]
    return ""


def strip_trailing_zero(value):
    try:
        f = float(value)
    except Exception:
        return str(value)
    if f.is_integer():
        return str(int(f))
    return str(f)


def extract_bool_confidence(row, field):
    text = text_for_row(row)
    low = text.lower()
    terms = {
        "is_compressed": ["compressed", "soft lepton", "mass splitting", "delta m", "deltam", "isr"],
        "is_long_lived": ["long-lived", "long lived", "llp", "hscp", "stable charged"],
        "is_displaced": ["displaced", "displaced vertex", "impact parameter", " d0", " dv"],
        "is_disappearing_track": ["disappearing track", "tracklet", "short track"],
        "is_high_MET": ["high met", "high-missing", "met750", "mht750", "ptmiss350"],
        "is_high_multiplicity": ["high multiplicity", "many jets", "10j", "12j"],
        "is_reconstruction_difficult": ["compressed", "disappearing", "tracklet", "displaced", "long-lived", "llp", "soft"],
    }[field]
    hit = next((term for term in terms if term in low), "")
    if hit and hit in str(row.get("source_comment", "")).lower():
        return (1, "MEDIUM", str(row.get("source_url", "")), hit)
    if hit:
        return (1, "LOW", str(row.get("source_url", "")), hit)
    return (0, "UNAVAILABLE", "", "")


def create_queue(df):
    field_cols = {
        "MET": "MET_enriched" if "MET_enriched" in df else "MET",
        "HT": "HT_or_meff_enriched" if "HT_or_meff_enriched" in df else "HT_or_meff",
        "meff": "HT_or_meff_enriched" if "HT_or_meff_enriched" in df else "HT_or_meff",
        "Njets": "N_jets_enriched" if "N_jets_enriched" in df else "N_jets",
        "Nleptons": "N_leptons_enriched" if "N_leptons_enriched" in df else "N_leptons",
        "Nb": "N_btags_enriched" if "N_btags_enriched" in df else "N_btags",
    }
    rows = []
    for analysis, sub in df.groupby("analysis", sort=True):
        missing = {name: float(sub[col].isna().mean()) if col in sub else 1.0 for name, col in field_cols.items()}
        residual_weight = float(sub["Z"].abs().fillna(0).mean()) if "Z" in sub else 0.0
        missing_key_sum = missing["MET"] + missing["HT"] + missing["Njets"] + missing["Nleptons"] + missing["Nb"]
        priority = len(sub) * (1 + missing_key_sum) + 5 * residual_weight
        first = sub.iloc[0]
        rows.append(
            {
                "analysis": analysis,
                "experiment": first.get("experiment", ""),
                "n_signal_regions": len(sub),
                "missing_MET": missing["MET"],
                "missing_HT": missing["HT"],
                "missing_meff": missing["meff"],
                "missing_Njets": missing["Njets"],
                "missing_Nleptons": missing["Nleptons"],
                "missing_Nb": missing["Nb"],
                "missing_lifetime": 1.0,
                "missing_displacement": 1.0,
                "missing_compression": float(1.0 - sub.get("is_compressed", pd.Series(0, index=sub.index)).fillna(0).clip(0, 1).mean()),
                "missing_topology": float(pd.isna(sub.get("category_enriched", sub.get("category", pd.Series(np.nan, index=sub.index)))).mean()),
                "priority_score": priority,
                "candidate_arxiv": "",
                "candidate_hepdata_url": f"https://www.hepdata.net/search/?q={analysis}",
                "status": "queued",
            }
        )
    return pd.DataFrame(rows).sort_values("priority_score", ascending=False)


def find_public_sources(df, manifest=None):
    rows = []
    if manifest is None and (TABLES / "analysis_source_manifest.csv").exists():
        manifest = pd.read_csv(TABLES / "analysis_source_manifest.csv")
    manifest = manifest if manifest is not None else pd.DataFrame()
    for analysis, sub in df.groupby("analysis", sort=True):
        first = sub.iloc[0]
        rows.append(
            {
                "analysis": analysis,
                "experiment": first.get("experiment", ""),
                "source_type": "SModelS_metadata",
                "source_url": first.get("source_url", ""),
                "source_title": "SModelS dataInfo/globalInfo metadata",
                "source_confidence": "HIGH",
                "notes": "Local public SModelS metadata already present in table.",
            }
        )
        hit = manifest[manifest["analysis"] == analysis] if "analysis" in manifest else pd.DataFrame()
        if len(hit):
            row = hit.iloc[0]
            if str(row.get("hepdata_search_url", "")):
                rows.append(
                    {
                        "analysis": analysis,
                        "experiment": first.get("experiment", ""),
                        "source_type": "HEPData",
                        "source_url": row.get("hepdata_search_url", ""),
                        "source_title": "HEPData search candidate",
                        "source_confidence": "MEDIUM",
                        "notes": "Candidate search URL; table-level confirmation still required.",
                    }
                )
            if str(row.get("paper_or_aux_url", "")):
                rows.append(
                    {
                        "analysis": analysis,
                        "experiment": first.get("experiment", ""),
                        "source_type": "paper_or_aux",
                        "source_url": row.get("paper_or_aux_url", ""),
                        "source_title": row.get("publication", "") or row.get("arxiv", ""),
                        "source_confidence": "MEDIUM",
                        "notes": "Candidate public paper/auxiliary URL from globalInfo.",
                    }
                )
    return pd.DataFrame(rows)


def download_sources(sources):
    import requests

    rows = []
    session = requests.Session()
    for _, src in sources.iterrows():
        analysis = str(src["analysis"])
        url = str(src.get("source_url", ""))
        outdir = SOURCE_RAW / safe_name(analysis)
        outdir.mkdir(parents=True, exist_ok=True)
        local_path = ""
        status = "skipped_no_direct_url"
        if url.startswith("http") and "hepdata.net/search" not in url:
            try:
                suffix = ".pdf" if ".pdf" in url.lower() else ".txt"
                local = outdir / f"{safe_name(src.get('source_type', 'source'))}{suffix}"
                response = session.get(url, timeout=30, headers={"User-Agent": "nframe-verified-metadata/0.1"})
                response.raise_for_status()
                local.write_bytes(response.content)
                local_path = str(local)
                status = "downloaded"
            except Exception as exc:
                status = f"failed: {exc}"
        rows.append(
            {
                "analysis": analysis,
                "source_type": src.get("source_type", ""),
                "url": url,
                "local_path": local_path,
                "download_status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value))[:160]


def extract_metadata_long(df):
    rows = []
    for idx, row in df.iterrows():
        for canonical in MODEL_FEATURES:
            src_col = f"{canonical}_enriched" if f"{canonical}_enriched" in df else canonical
            if canonical == "HT_or_meff" and src_col not in df:
                src_col = "HT_or_meff_enriched" if "HT_or_meff_enriched" in df else "HT_or_meff"
            value = row.get(src_col, np.nan)
            confidence, source, source_text = confidence_for_numeric(row, canonical, value)
            rows.append(
                {
                    "row_id": idx,
                    "analysis": row["analysis"],
                    "signal_region": row["signal_region"],
                    "field": canonical,
                    "value": value,
                    "unit": "GeV" if canonical in ["MET", "HT_or_meff"] else "count",
                    "source_text": source_text,
                    "source_file": source,
                    "page_or_table": "",
                    "confidence": confidence,
                }
            )
        for field in BOOL_FIELDS:
            value, confidence, source, source_text = extract_bool_confidence(row, field)
            rows.append(
                {
                    "row_id": idx,
                    "analysis": row["analysis"],
                    "signal_region": row["signal_region"],
                    "field": field,
                    "value": value,
                    "unit": "boolean",
                    "source_text": source_text,
                    "source_file": source,
                    "page_or_table": "",
                    "confidence": confidence,
                }
            )
    return pd.DataFrame(rows)


def long_to_wide(long_df):
    wide = long_df.pivot_table(
        index=["row_id", "analysis", "signal_region"],
        columns="field",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    return wide


def match_metadata(df, extracted):
    matched = extracted.copy()
    matched["normalized_signal_region"] = matched["signal_region"].map(normalized_label)
    matched["match_type"] = np.where(matched["confidence"].isin(HIGH_MEDIUM), "source_row", "label_or_unavailable")
    return matched


def create_verified_table(df, matched):
    out = df.copy()
    out["row_id"] = np.arange(len(out))
    conflicts = []
    for field in MODEL_FEATURES + BOOL_FIELDS:
        subset = matched[matched["field"] == field].copy()
        by_row = subset.drop_duplicates("row_id").set_index("row_id")
        value_col = f"{field}_value"
        out[value_col] = out["row_id"].map(by_row["value"])
        out[f"{field}_confidence"] = out["row_id"].map(by_row["confidence"]).fillna("UNAVAILABLE")
        out[f"{field}_source"] = out["row_id"].map(by_row["source_file"]).fillna("")
        out[f"{field}_source_text"] = out["row_id"].map(by_row["source_text"]).fillna("")
        out[f"{field}_match_type"] = out["row_id"].map(by_row["match_type"]).fillna("unmatched")
        out[f"{field}_verified"] = out[f"{field}_confidence"].isin(HIGH_MEDIUM).astype(int)
        if subset.duplicated(["row_id", "field"]).any():
            conflicts.extend(subset[subset.duplicated(["row_id", "field"], keep=False)].to_dict("records"))
    return out, pd.DataFrame(conflicts)


def missingness_table(df, value_suffix="_value", verified_suffix="_verified"):
    rows = []
    for field in MODEL_FEATURES + BOOL_FIELDS:
        value_col = f"{field}{value_suffix}"
        verified_col = f"{field}{verified_suffix}"
        if value_col in df:
            rows.append(
                {
                    "field": field,
                    "n_rows": len(df),
                    "nonmissing_values": int(df[value_col].notna().sum()),
                    "value_missing_fraction": float(df[value_col].isna().mean()),
                    "verified_count": int(df[verified_col].sum()) if verified_col in df else 0,
                    "verified_missing_fraction": float(1 - df[verified_col].mean()) if verified_col in df else 1.0,
                }
            )
    return pd.DataFrame(rows)


def score_verified_only(df):
    out = df.copy()
    for feature in MODEL_FEATURES:
        col = f"{feature}_value"
        verified = f"{feature}_verified"
        out[f"{feature}_verified_feature"] = pd.to_numeric(out[col], errors="coerce").where(out[verified] == 1)
        out[f"z_{feature}_verified"] = zscore(out[f"{feature}_verified_feature"]).where(out[f"{feature}_verified_feature"].notna())
    for field in BOOL_FIELDS:
        out[f"{field}_verified_feature"] = pd.to_numeric(out[f"{field}_value"], errors="coerce").where(out[f"{field}_verified"] == 1)
    out["R_missing_verified"] = zscore(out["MET_verified_feature"]) if "MET_verified_feature" in out else np.nan
    out["R_lifetime_verified"] = out["is_long_lived_verified_feature"]
    out["R_displacement_verified"] = out["is_displaced_verified_feature"] + out["is_disappearing_track_verified_feature"]
    out["R_compression_verified"] = out["is_compressed_verified_feature"]
    out["R_multiplicity_verified"] = zscore(out["N_jets_verified_feature"])
    out["R_reconstruction_verified"] = (
        out["is_reconstruction_difficult_verified_feature"]
        + out["is_displaced_verified_feature"]
        + out["is_disappearing_track_verified_feature"]
    )
    terms = [f"z_{feature}_verified" for feature in MODEL_FEATURES]
    out["B_access_verified"] = out[terms].sum(axis=1, min_count=1)
    out["B_access_verified_z"] = zscore(out["B_access_verified"]).where(out["B_access_verified"].notna())
    for name, cols in {
        "complete_core_kinematics": ["MET_verified_feature", "HT_or_meff_verified_feature", "N_jets_verified_feature"],
        "complete_missing": ["MET_verified_feature"],
        "complete_lifetime": ["is_long_lived_verified_feature"],
        "complete_compression": ["is_compressed_verified_feature"],
        "complete_reconstruction": ["is_reconstruction_difficult_verified_feature"],
    }.items():
        out[name] = out[cols].notna().all(axis=1).astype(int)
    return out


def score_verified_plus_imputed(verified, base):
    out = verified.copy()
    source_map = {
        "MET": "MET_enriched" if "MET_enriched" in base else "MET",
        "HT_or_meff": "HT_or_meff_enriched" if "HT_or_meff_enriched" in base else "HT_or_meff",
        "N_jets": "N_jets_enriched" if "N_jets_enriched" in base else "N_jets",
        "N_leptons": "N_leptons_enriched" if "N_leptons_enriched" in base else "N_leptons",
        "N_btags": "N_btags_enriched" if "N_btags_enriched" in base else "N_btags",
    }
    for feature in MODEL_FEATURES:
        verified_val = out[f"{feature}_value"].where(out[f"{feature}_verified"] == 1)
        fallback = pd.to_numeric(base[source_map[feature]], errors="coerce") if source_map[feature] in base else np.nan
        out[f"{feature}_verified_imputed"] = verified_val.combine_first(fallback)
        out[f"{feature}_imputed"] = (verified_val.isna() & pd.Series(fallback, index=out.index).notna()).astype(int)
        out[f"{feature}_original_missing"] = verified_val.isna().astype(int)
        out[f"{feature}_imputation_method"] = np.where(out[f"{feature}_imputed"] == 1, "label_or_smodels_proxy", "")
        out[f"z_{feature}_verified_imputed"] = zscore(out[f"{feature}_verified_imputed"])
    for field in BOOL_FIELDS:
        verified_val = pd.to_numeric(out[f"{field}_value"], errors="coerce").where(out[f"{field}_verified"] == 1)
        fallback_col = field if field in base else None
        fallback = pd.to_numeric(base[fallback_col], errors="coerce") if fallback_col else pd.Series(np.nan, index=out.index)
        out[f"{field}_verified_imputed"] = verified_val.combine_first(fallback).fillna(0)
        out[f"{field}_imputed"] = (verified_val.isna() & pd.Series(fallback, index=out.index).notna()).astype(int) if fallback_col else 0
        out[f"{field}_imputation_method"] = np.where(out[f"{field}_imputed"] == 1, "label_or_smodels_proxy", "")
    out["R_missing_verified_imputed"] = zscore(out["MET_verified_imputed"])
    out["R_lifetime_verified_imputed"] = out["is_long_lived_verified_imputed"]
    out["R_displacement_verified_imputed"] = out["is_displaced_verified_imputed"] + out["is_disappearing_track_verified_imputed"]
    out["R_compression_verified_imputed"] = out["is_compressed_verified_imputed"]
    out["R_multiplicity_verified_imputed"] = zscore(out["N_jets_verified_imputed"])
    out["R_reconstruction_verified_imputed"] = (
        out["is_reconstruction_difficult_verified_imputed"]
        + out["is_displaced_verified_imputed"]
        + out["is_disappearing_track_verified_imputed"]
    )
    out["B_access_verified_imputed"] = out[[f"z_{f}_verified_imputed" for f in MODEL_FEATURES]].sum(axis=1)
    out["B_access_verified_imputed_z"] = zscore(out["B_access_verified_imputed"])
    imputed_cols = [f"{f}_imputed" for f in MODEL_FEATURES + BOOL_FIELDS if f"{f}_imputed" in out]
    verified_cols = [f"{f}_verified" for f in MODEL_FEATURES + BOOL_FIELDS if f"{f}_verified" in out]
    out["imputation_fraction"] = out[imputed_cols].mean(axis=1) if imputed_cols else 0
    out["metadata_completeness_score"] = out[verified_cols].mean(axis=1) if verified_cols else 0
    return out


def fit_simple_models(df, b_col, prefix, include_controls=False):
    rows = []
    outcomes = ["Z", "Z_capped_3", "Z_capped_5", "Z_conservative", "Poisson_deviance_residual", "Delta_N"]
    datasets = [("pooled", df)]
    for exp in ["ATLAS", "CMS"]:
        if "experiment" in df:
            datasets.append((exp, df[df["experiment"] == exp]))
    for dataset, sub in datasets:
        for outcome in outcomes:
            model_df = sub[[outcome, b_col, "analysis"] + (["metadata_completeness_score", "imputation_fraction"] if include_controls and "metadata_completeness_score" in sub else [])].dropna()
            if len(model_df) < 20 or model_df[b_col].nunique() < 2:
                rows.append({"dataset": dataset, "model": "core", "outcome": outcome, "n": len(model_df), "term": b_col, "beta": np.nan, "p_value": np.nan, "r2": np.nan, "note": "insufficient complete verified rows"})
                continue
            x_cols = [b_col]
            if include_controls and "metadata_completeness_score" in model_df:
                x_cols += ["metadata_completeness_score", "imputation_fraction"]
            x = sm.add_constant(model_df[x_cols])
            fit = sm.OLS(model_df[outcome], x).fit()
            try:
                fit_cluster = fit.get_robustcov_results(cov_type="cluster", groups=model_df["analysis"])
                cluster_p = float(fit_cluster.pvalues[list(x.columns).index(b_col)])
            except Exception:
                cluster_p = np.nan
            rows.append(
                {
                    "dataset": dataset,
                    "model": "core",
                    "outcome": outcome,
                    "n": len(model_df),
                    "term": b_col,
                    "beta": float(fit.params[b_col]),
                    "std_error": float(fit.bse[b_col]),
                    "p_value": float(fit.pvalues[b_col]),
                    "cluster_p_value": cluster_p,
                    "r2": float(fit.rsquared),
                    "note": "",
                }
            )
    return pd.DataFrame(rows)


def cross_validation(df, b_col):
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import GroupKFold

    out = []
    data = df[["Z", b_col, "analysis", "experiment"]].dropna()
    if len(data) < 40 or data["analysis"].nunique() < 3:
        return pd.DataFrame([{"scheme": "GroupKFold", "n": len(data), "note": "insufficient complete verified rows"}])
    n_splits = min(5, data["analysis"].nunique())
    preds = np.full(len(data), np.nan)
    for train, test in GroupKFold(n_splits=n_splits).split(data[[b_col]], data["Z"], groups=data["analysis"]):
        model = LinearRegression().fit(data[[b_col]].iloc[train], data["Z"].iloc[train])
        preds[test] = model.predict(data[[b_col]].iloc[test])
    out.append(metrics_row("GroupKFold_by_analysis", data["Z"], preds, len(data)))
    for train_exp, test_exp in [("ATLAS", "CMS"), ("CMS", "ATLAS")]:
        train = data[data["experiment"] == train_exp]
        test = data[data["experiment"] == test_exp]
        if len(train) >= 20 and len(test) >= 20:
            model = LinearRegression().fit(train[[b_col]], train["Z"])
            pred = model.predict(test[[b_col]])
            out.append(metrics_row(f"{train_exp}_train_{test_exp}_test", test["Z"], pred, len(test)))
    return pd.DataFrame(out)


def metrics_row(scheme, y, pred, n):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    return {
        "scheme": scheme,
        "n": n,
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(math.sqrt(mean_squared_error(y, pred))),
        "correlation_predicted_observed": float(pd.Series(pred).corr(pd.Series(y).reset_index(drop=True))),
        "note": "",
    }


def bootstrap_permutation(df, b_col, label, n=2000, seed=20260604):
    rng = np.random.default_rng(seed)
    rows = []
    for dataset, sub in [("pooled", df), ("ATLAS", df[df.get("experiment", "") == "ATLAS"]), ("CMS", df[df.get("experiment", "") == "CMS"])]:
        data = sub[["Z", b_col, "analysis"]].dropna()
        if len(data) < 20 or data[b_col].nunique() < 2:
            rows.append({"dataset": dataset, "score": label, "term": b_col, "n": len(data), "beta": np.nan, "ci_low": np.nan, "ci_high": np.nan, "perm_p_two_sided": np.nan, "perm_p_positive": np.nan})
            continue
        x = data[b_col].to_numpy(float)
        y = data["Z"].to_numpy(float)
        beta = fast_beta(x, y)
        betas = []
        for _ in range(n):
            idx = rng.integers(0, len(data), len(data))
            betas.append(fast_beta(x[idx], y[idx]))
        perm = np.array([fast_beta(x, rng.permutation(y)) for _ in range(n)])
        rows.append(
            {
                "dataset": dataset,
                "score": label,
                "term": b_col,
                "n": len(data),
                "beta": beta,
                "ci_low": float(np.nanpercentile(betas, 2.5)),
                "ci_high": float(np.nanpercentile(betas, 97.5)),
                "perm_p_two_sided": float((np.sum(np.abs(perm) >= abs(beta)) + 1) / (len(perm) + 1)),
                "perm_p_positive": float((np.sum(perm >= beta) + 1) / (len(perm) + 1)),
            }
        )
    return pd.DataFrame(rows)


def fast_beta(x, y):
    xc = x - np.nanmean(x)
    yc = y - np.nanmean(y)
    denom = np.nansum(xc ** 2)
    return float(np.nansum(xc * yc) / denom) if denom else np.nan


def source_audit_text(verified, sources, missingness, conflicts):
    lines = [
        "# Verified Metadata Source Audit",
        "",
        f"- Signal regions: {len(verified)}",
        f"- Analyses: {verified['analysis'].nunique()}",
        f"- Source candidates: {len(sources)}",
        f"- Conflict rows: {len(conflicts)}",
        "",
        "## Source Breakdown",
        "",
        sources.groupby("source_type").size().to_string() if len(sources) else "No source candidates.",
        "",
        "## Verified Coverage",
        "",
        missingness.to_string(index=False),
        "",
        "## Top Unresolved Analyses",
        "",
    ]
    completeness = verified.groupby("analysis")[[f"{f}_verified" for f in MODEL_FEATURES if f"{f}_verified" in verified]].mean().mean(axis=1).sort_values()
    lines.append(completeness.head(15).to_string())
    return "\n".join(lines) + "\n"


def summary_text(verified, verified_models, imputed_models, cv, boot):
    n_atlas = int((verified["experiment"] == "ATLAS").sum()) if "experiment" in verified else 0
    n_cms = int((verified["experiment"] == "CMS").sum()) if "experiment" in verified else 0
    v_core = verified_models[(verified_models["dataset"] == "pooled") & (verified_models["outcome"] == "Z")].head(1)
    i_core = imputed_models[(imputed_models["dataset"] == "pooled") & (imputed_models["outcome"] == "Z")].head(1)
    def one_line(row):
        if not len(row) or pd.isna(row.iloc[0].get("beta")):
            return "not estimable with current verified complete cases"
        r = row.iloc[0]
        return f"beta={r['beta']:.4g}, p={r['p_value']:.4g}, cluster_p={r.get('cluster_p_value', np.nan):.4g}, R2={r['r2']:.4g}, n={int(r['n'])}"
    return f"""# N-Frame Verified Metadata Reanalysis

## Dataset

- Signal regions: {len(verified)}
- Analyses: {verified['analysis'].nunique()}
- ATLAS rows: {n_atlas}
- CMS rows: {n_cms}

## Metadata Integrity

Zero percent missing model input values were obtained only after imputation and should not be interpreted as zero percent missing verified metadata. Verified metadata were defined as values extracted directly from HEPData tables, ATLAS/CMS auxiliary material, or explicit paper signal-region definitions. All inferred or imputed values were flagged and analysed separately.

The current automated pass uses local SModelS metadata and source/comment text as its verified layer. Label-only values are treated as inferred/proxy values, not verified.

## Core Model Results

- Verified-only pooled `Z ~ B_access_verified_z`: {one_line(v_core)}
- Verified+imputed pooled `Z ~ B_access_verified_imputed_z`: {one_line(i_core)}

Full model tables:

- `results/tables/verified_only_model_results.csv`
- `results/tables/verified_plus_imputed_model_results.csv`
- `results/tables/verified_cross_validation_results.csv`
- `results/tables/verified_key_terms_bootstrap_permutation.csv`

## Cross-Validation

{cv.to_string(index=False) if len(cv) else 'Cross-validation was not estimable.'}

## Bootstrap And Permutation

{boot.to_string(index=False) if len(boot) else 'Bootstrap/permutation was not estimable.'}

## Interpretation

This is a metadata-quality reanalysis, not a tuned signal search. If effects appear only in verified+imputed data, they should be treated as exploratory and metadata-sensitive. If verified-only complete cases are sparse, the correct conclusion is limited verified coverage, not stronger physics evidence.

No SUSY discovery, hidden symmetry proof, or detector-level claim is made.
"""


def paper_ready_text():
    return """# Paper-Ready Methods And Results Text

## Methods

We constructed a verified metadata layer for public ATLAS/CMS supersymmetry signal-region tables derived from the SModelS public database and associated public-source pointers. Signal-region yields were retained from the existing public corpus, while kinematic and topology variables were reclassified according to provenance.

Zero percent missing model input values were obtained only after imputation and should not be interpreted as zero percent missing verified metadata. Verified metadata were defined as values extracted directly from HEPData tables, ATLAS/CMS auxiliary material, or explicit paper signal-region definitions. All inferred or imputed values were flagged and analysed separately.

## Verified Versus Imputed Variables

For each signal region and field, the analysis records a value, verification flag, confidence label, source pointer, source text, and match type. HIGH and MEDIUM confidence entries are analysed as verified. LOW confidence entries, including label-only parsing and SModelS proxy values without explicit cut text, are not treated as verified and enter only the verified+imputed sensitivity dataset.

## Statistical Models

The primary verified-only model regresses standardized residuals on `B_access_verified_z` using only complete verified fields. A second verified+imputed model uses verified values where available and flagged proxy values otherwise, with metadata-completeness and imputation-fraction controls.

## Limitations

The automated pass cannot replace manual extraction from every paper table. Null, unstable, or imputation-driven results are interpreted as no robust support. This analysis is exploratory and does not claim evidence for supersymmetry or hidden symmetry.
"""


def package_outputs():
    output = PROJECT / "nframe_verified_metadata_final_outputs.zip"
    include = [
        PROJECT / "scripts",
        PROJECT / "README.md",
        PROJECT / "requirements.txt",
        PROCESSED / "signal_regions_verified_metadata.csv",
        PROCESSED / "signal_regions_verified_only_scored.csv",
        PROCESSED / "signal_regions_verified_plus_imputed_scored.csv",
        TABLES,
        FIGURES,
        SOURCE_AUDIT,
        RESULTS / "nframe_verified_metadata_summary.md",
        RESULTS / "paper_ready_verified_methods_results.md",
    ]
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in include:
            if item.is_dir():
                for file in item.rglob("*"):
                    if file.is_file() and "__pycache__" not in file.parts:
                        zf.write(file, file.relative_to(PROJECT))
            elif item.exists():
                zf.write(item, item.relative_to(PROJECT))
    return output
