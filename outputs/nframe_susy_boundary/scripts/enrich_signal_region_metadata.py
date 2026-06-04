import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests


RAW_BASE = "https://raw.githubusercontent.com/SModelS/smodels-database-release/main"
PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT / "data" / "raw" / "real_smodels_signal_regions_full.csv"
DEFAULT_OUTPUT = PROJECT / "data" / "processed" / "signal_regions_metadata_enriched.csv"
DEFAULT_MISSINGNESS = PROJECT / "results" / "tables" / "signal_region_metadata_missingness.csv"
DEFAULT_ANALYSES = PROJECT / "results" / "tables" / "analysis_source_manifest.csv"


def first_number(text):
    match = re.search(r"-?\d+(?:\.\d+)?", str(text))
    return float(match.group(0)) if match else np.nan


def max_group(pattern, text):
    vals = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        for group in match.groups():
            if group is not None:
                vals.append(float(group))
    return max(vals) if vals else np.nan


def infer_range(pattern, text):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return (np.nan, np.nan)
    vals = [float(g) for g in match.groups() if g is not None]
    if len(vals) >= 2:
        return vals[0], vals[1]
    if len(vals) == 1:
        return vals[0], np.nan
    return (np.nan, np.nan)


def clean_text(row):
    fields = [
        row.get("analysis", ""),
        row.get("signal_region", ""),
        row.get("source_comment", ""),
        row.get("category", ""),
        row.get("source_path", ""),
    ]
    return " ".join("" if pd.isna(v) else str(v) for v in fields)


def parse_metadata(row):
    text = clean_text(row)
    normalized = text.replace("-", "_").replace("[", "_").replace("]", "_").replace("(", "_").replace(")", "_")
    out = {}

    met = max_group(r"(?:MET|MHT|ETMISS|ETmiss|pTmiss|ptmiss)[_>=:]*\s*(\d+(?:\.\d+)?)", normalized)
    if np.isnan(met):
        met = max_group(r"(\d+(?:\.\d+)?)\s*(?:MET|MHT)", normalized)
    out["MET_extracted"] = met

    ht = max_group(r"(?:HT|Meff|meff|m_eff|MCT|mCT|MT2|mt2)[_>=:]*\s*(\d+(?:\.\d+)?)", normalized)
    if np.isnan(ht):
        ht = max_group(r"(\d+(?:\.\d+)?)\s*(?:HT|Meff|meff|m_eff|MCT|mCT|MT2|mt2)", normalized)
    if np.isnan(ht):
        ht = max_group(r"SR(?:2|3|4|5|6|7|8|9|10)j[_-]?(\d+(?:\.\d+)?)", normalized)
    out["HT_or_meff_extracted"] = ht

    nj = max_group(r"(?:NJet|Njet|Nj|nJ|Njets|jets)[_>=:]*(\d+)", normalized)
    if np.isnan(nj):
        nj = max_group(r"SR(\d+)j", normalized)
    if np.isnan(nj):
        nj = max_group(r"\b(\d+)j\b", normalized)
    out["N_jets_extracted"] = nj

    nb = max_group(r"(?:Nb|NB|nb|btag|btags|bjets|bjet)[_>=:]*(\d+)", normalized)
    if np.isnan(nb):
        nb = max_group(r"\b(\d+)b\b", normalized)
    out["N_btags_extracted"] = nb

    if re.search(r"\b0L\b|0lep|zero[_ ]?lepton|hadronic", normalized, flags=re.IGNORECASE):
        nlep = 0.0
    elif re.search(r"\b1L\b|1lep|single[_ ]?lepton", normalized, flags=re.IGNORECASE):
        nlep = 1.0
    elif re.search(r"\b2L\b|2lep|two[_ ]?lepton|SF|DF|ee|mm|em|OS", normalized, flags=re.IGNORECASE):
        nlep = 2.0
    elif re.search(r"\b3L\b|3lep|three[_ ]?lepton", normalized, flags=re.IGNORECASE):
        nlep = 3.0
    else:
        nlep = np.nan
    out["N_leptons_extracted"] = nlep

    mt2_low, mt2_high = infer_range(r"(?:MT2|mt2)[_=]*([0-9.]+)[_,to-]+([0-9.]+)", normalized)
    out["MT2_low"] = mt2_low
    out["MT2_high"] = mt2_high
    out["MET_threshold"] = met
    out["HT_meff_threshold"] = ht
    out["Njets_threshold"] = nj
    out["Nb_threshold"] = nb

    low = normalized.lower()
    out["is_compressed"] = int(any(x in low for x in ["compressed", "soft", "isr", "lowmet", "low_mct", "lm_"]))
    out["is_disappearing_track"] = int(any(x in low for x in ["disappearing", "tracklet"]))
    out["is_long_lived"] = int(any(x in low for x in ["long_lived", "long-lived", "llp", "hscp", "rhad", "_long"]))
    out["is_displaced"] = int(any(x in low for x in ["displaced", "vertex", "dv"]))
    out["is_high_MET_label"] = int(any(x in low for x in ["highmet", "high_met", "mht750", "met750", "ptmiss350"]))
    out["is_high_multiplicity_label"] = int(bool(re.search(r"(?:nj|njet|sr)[_\-]?(?:8|9|10|11|12)|(?:8|9|10|11|12)j", low)))

    categories = []
    for col, label in [
        ("is_compressed", "compressed"),
        ("is_disappearing_track", "disappearing_track"),
        ("is_long_lived", "long_lived"),
        ("is_displaced", "displaced"),
        ("is_high_MET_label", "high_MET"),
        ("is_high_multiplicity_label", "high_multiplicity"),
    ]:
        if out[col]:
            categories.append(label)
    out["category_enriched"] = " ".join(categories)
    return out


def fetch_global_info(analysis, source_path):
    try:
        parts = str(source_path).split("/")
        global_path = "/".join(parts[:3] + ["globalInfo.txt"])
        response = requests.get(f"{RAW_BASE}/{global_path}", timeout=20, headers={"User-Agent": "nframe-metadata-enrichment/0.1"})
        response.raise_for_status()
        text = response.text
    except Exception:
        text = ""
    fields = {"analysis": analysis}
    for key in ["id", "url", "arxiv", "publication", "publicationDOI", "lumi", "sqrts"]:
        match = re.search(rf"^{re.escape(key)}\s*:\s*(.+)$", text, flags=re.MULTILINE)
        fields[key] = match.group(1).strip() if match else ""
    fields["globalInfo_available"] = bool(text)
    fields["hepdata_search_url"] = (
        f"https://www.hepdata.net/search/?q={fields.get('arxiv') or analysis}"
    )
    fields["paper_or_aux_url"] = fields.get("url", "")
    return fields


def missingness(df, cols, label):
    return pd.DataFrame(
        {
            "stage": label,
            "column": cols,
            "missing_count": [int(df[col].isna().sum()) if col in df else len(df) for col in cols],
            "missing_fraction": [float(df[col].isna().mean()) if col in df else 1.0 for col in cols],
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Enrich SModelS-derived signal-region metadata from labels/comments/globalInfo.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--missingness-output", default=str(DEFAULT_MISSINGNESS))
    parser.add_argument("--analysis-manifest-output", default=str(DEFAULT_ANALYSES))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    original_cols = ["MET", "HT_or_meff", "N_jets", "N_leptons", "N_btags", "category"]
    before = missingness(df, original_cols, "before")

    parsed = pd.DataFrame([parse_metadata(row) for _, row in df.iterrows()])
    enriched = pd.concat([df, parsed], axis=1)

    enriched["MET_enriched"] = enriched["MET"].combine_first(enriched["MET_extracted"])
    enriched["HT_or_meff_enriched"] = enriched["HT_or_meff"].combine_first(enriched["HT_or_meff_extracted"])
    enriched["N_jets_enriched"] = enriched["N_jets"].combine_first(enriched["N_jets_extracted"])
    enriched["N_leptons_enriched"] = enriched["N_leptons"].combine_first(enriched["N_leptons_extracted"])
    enriched["N_btags_enriched"] = enriched["N_btags"].combine_first(enriched["N_btags_extracted"])
    enriched["category_enriched"] = (
        enriched["category"].fillna("").astype(str).str.strip()
        + " "
        + enriched["category_enriched"].fillna("").astype(str)
    ).str.strip()
    enriched.loc[enriched["category_enriched"] == "", "category_enriched"] = np.nan

    enriched_cols = [
        "MET_enriched",
        "HT_or_meff_enriched",
        "N_jets_enriched",
        "N_leptons_enriched",
        "N_btags_enriched",
        "category_enriched",
    ]
    after = missingness(enriched, enriched_cols, "after")
    missing = pd.concat([before, after], ignore_index=True)

    analysis_rows = []
    for analysis, sub in enriched.groupby("analysis", sort=True):
        analysis_rows.append(fetch_global_info(analysis, sub["source_path"].dropna().iloc[0] if sub["source_path"].notna().any() else ""))
    manifest = pd.DataFrame(analysis_rows)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.missingness_output).parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(args.output, index=False)
    missing.to_csv(args.missingness_output, index=False)
    manifest.to_csv(args.analysis_manifest_output, index=False)

    print(f"Wrote enriched table: {args.output} ({len(enriched)} rows)")
    print(f"Wrote missingness: {args.missingness_output}")
    print(f"Wrote analysis manifest: {args.analysis_manifest_output}")
    print(missing.to_string(index=False))


if __name__ == "__main__":
    main()
