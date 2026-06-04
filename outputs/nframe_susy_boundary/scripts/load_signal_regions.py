import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from common import PROCESSED_DIR, RAW_DIR, REQUIRED_COLUMNS, ensure_dirs


OBS_PATTERNS = ["n_obs", "nobs", "observed", "data"]
EXP_PATTERNS = ["n_exp", "nexp", "background", "bkg", "sm total", "total sm", "total background"]
ERR_PATTERNS = ["sigma_exp", "uncert", "error", "err", "std"]


def clean_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def parse_numeric(value):
    if pd.isna(value):
        return np.nan
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else np.nan


def midpoint_from_label(label: str, token: str) -> float:
    text = str(label)
    patterns = [
        rf"{token}\s*[_:=]?\s*(\d+(?:\.\d+)?)\s*[-_to]+\s*(\d+(?:\.\d+)?)",
        rf"{token}\s*[_:=]?\s*(?:gt|ge|above|>)\s*(\d+(?:\.\d+)?)",
        rf"{token}\s*[_:=]?\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            vals = [float(v) for v in match.groups() if v is not None]
            if len(vals) == 2:
                return float(np.mean(vals))
            if len(vals) == 1:
                return vals[0]
    return np.nan


def normalize_columns(df: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    original = df.copy()
    df.columns = [clean_name(c) for c in df.columns]

    aliases = {
        "analysis": ["analysis", "analysis_id", "publication", "search"],
        "experiment": ["experiment", "collaboration"],
        "sqrt_s": ["sqrt_s", "sqrts", "collision_energy", "energy"],
        "luminosity": ["luminosity", "lumi", "integrated_luminosity"],
        "signal_region": ["signal_region", "region", "sr", "bin", "name"],
        "N_obs": ["n_obs", "nobs", "observed", "data", "number_observed"],
        "N_exp": ["n_exp", "nexp", "expected", "expected_background", "total_background", "background"],
        "sigma_exp": ["sigma_exp", "background_uncertainty", "total_uncertainty", "uncertainty", "error"],
        "MET": ["met", "etmiss", "e_t_miss", "missing_et", "missing_transverse_energy"],
        "HT_or_meff": ["ht_or_meff", "ht", "meff", "m_eff", "lt", "st"],
        "N_jets": ["n_jets", "njets", "njet", "jet_multiplicity"],
        "N_leptons": ["n_leptons", "nleptons", "nlep", "lepton_multiplicity"],
        "N_btags": ["n_btags", "nbtags", "nb", "n_b", "btag_multiplicity"],
        "category": ["category", "label", "channel"],
    }
    out = pd.DataFrame()
    for target, choices in aliases.items():
        match = next((c for c in choices if c in df.columns), None)
        if match:
            out[target] = df[match]

    # HEPData CSV exports may have verbose headers. Try broad matching if aliases missed.
    if "N_obs" not in out:
        obs = next((c for c in df.columns if any(p in c for p in OBS_PATTERNS)), None)
        if obs:
            out["N_obs"] = df[obs]
    if "N_exp" not in out:
        exp = next((c for c in df.columns if any(p in c for p in EXP_PATTERNS)), None)
        if exp:
            out["N_exp"] = df[exp]
    if "sigma_exp" not in out:
        err = next((c for c in df.columns if any(p in c for p in ERR_PATTERNS)), None)
        if err:
            out["sigma_exp"] = df[err]

    if "signal_region" not in out:
        out["signal_region"] = original.iloc[:, 0].astype(str)

    for col in REQUIRED_COLUMNS:
        if col not in out:
            out[col] = np.nan

    stem = source_path.stem
    out["analysis"] = out["analysis"].fillna(source_path.parent.name if source_path.parent.name != "raw" else stem)
    out["experiment"] = out["experiment"].fillna("")
    out["sqrt_s"] = out["sqrt_s"].fillna(13)
    out["luminosity"] = out["luminosity"].fillna(np.nan)
    out["category"] = out["category"].fillna("").astype(str)

    for col in ["N_obs", "N_exp", "sigma_exp", "MET", "HT_or_meff", "N_jets", "N_leptons", "N_btags", "sqrt_s", "luminosity"]:
        out[col] = out[col].map(parse_numeric)

    labels = out["signal_region"].astype(str)
    out["MET"] = out["MET"].fillna(labels.map(lambda x: midpoint_from_label(x, "MET|ETMISS|ETmiss")))
    out["HT_or_meff"] = out["HT_or_meff"].fillna(labels.map(lambda x: midpoint_from_label(x, "HT|MEFF|meff|LT|ST|mT2")))
    out["N_jets"] = out["N_jets"].fillna(labels.map(lambda x: midpoint_from_label(x, "Nj|Njet|jets?")))
    out["N_btags"] = out["N_btags"].fillna(labels.map(lambda x: midpoint_from_label(x, "Nb|Nbtags?|btags?")))
    out["N_leptons"] = out["N_leptons"].fillna(labels.str.extract(r"(\d+)[_\-\s]?(?:L|lep|lepton)", flags=re.IGNORECASE)[0].map(parse_numeric))

    valid = out["N_obs"].notna() & out["N_exp"].notna() & out["sigma_exp"].notna() & (out["sigma_exp"] > 0)
    out = out.loc[valid, REQUIRED_COLUMNS].copy()
    return out


def load_json_table(path: Path) -> pd.DataFrame:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "values" in data:
        return pd.DataFrame(data["values"])
    if isinstance(data, list):
        return pd.DataFrame(data)
    raise ValueError(f"Unsupported JSON table shape in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize signal-region CSV/JSON files into one analysis table.")
    parser.add_argument("--input-glob", default="**/*.csv")
    parser.add_argument("--output", default=PROCESSED_DIR / "signal_regions.csv")
    args = parser.parse_args()

    ensure_dirs()
    frames = []
    paths = sorted(RAW_DIR.glob(args.input_glob))
    for path in paths:
        if path.name == "selected_hepdata_sources.yml":
            continue
        try:
            if path.suffix.lower() == ".json":
                df = load_json_table(path)
            else:
                df = pd.read_csv(path, comment="#")
            norm = normalize_columns(df, path)
            if len(norm):
                print(f"Loaded {len(norm):4d} regions from {path}")
                frames.append(norm)
        except Exception as exc:
            print(f"Skipping {path}: {exc}")

    if not frames:
        raise SystemExit("No valid signal-region rows found. Try the demo CSV or add normalized HEPData CSVs.")

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(args.output, index=False)
    print(f"Wrote {len(combined)} rows to {args.output}")


if __name__ == "__main__":
    main()
