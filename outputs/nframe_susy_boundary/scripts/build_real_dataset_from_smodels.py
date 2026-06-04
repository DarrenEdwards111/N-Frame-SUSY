import argparse
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import pandas as pd
import requests

from common import RAW_DIR, ensure_dirs


RAW_BASE = "https://raw.githubusercontent.com/SModelS/smodels-database-release/main"
SKIP_REGION_PREFIXES = ("CR", "VR")


def parse_value(text: str, key: str):
    match = re.search(rf"^{re.escape(key)}\s*:\s*([^\n#]+)", text, flags=re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    number = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", value)
    return float(number.group(0)) if number else value


SESSION = requests.Session()


def fetch_text(path: str) -> str:
    url = f"{RAW_BASE}/{path}"
    response = SESSION.get(url, timeout=30, headers={"User-Agent": "nframe-boundary-reanalysis/0.1"})
    response.raise_for_status()
    return response.text


def infer_category(analysis: str, region: str, comment: str = "") -> str:
    text = f"{analysis} {region} {comment}".lower()
    tags = []
    if any(term in text for term in ["compressed", "soft", "isr", "lowmet", "low_mct", "lm_"]):
        tags.append("compressed")
    if any(term in text for term in ["disappearing", "tracklet", "dt"]):
        tags.append("disappearing_track")
    if any(term in text for term in ["long", "llp", "hs cp", "hscp", "rhad", "chargino_long"]):
        tags.append("long_lived")
    if any(term in text for term in ["displaced", "vertex", "dv"]):
        tags.append("displaced")
    if any(term in text for term in ["highmet", "high_met", "mht750", "met750", "ptmiss350", "mht600"]):
        tags.append("high_MET")
    if re.search(r"(?:nj|njet|sr)[_\-]?(?:8|9|10|11|12)|(?:8|9|10|11|12)j", text):
        tags.append("high_multiplicity")
    return " ".join(tags)


def num_from_patterns(text: str, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            vals = [float(v) for v in match.groups() if v is not None]
            if vals:
                return max(vals)
    return None


def infer_features(region: str, comment: str = "") -> dict:
    text = f"{region}_{comment}".replace("-", "_").replace("[", "_").replace("]", "_")
    return {
        "MET": num_from_patterns(
            text,
            [
                r"(?:MHT|MET|pTmiss|ETmiss|METsig)_?(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)MHT",
                r"(\d+(?:\.\d+)?)MET",
                r"MT2_?(\d+(?:\.\d+)?)",
            ],
        ),
        "HT_or_meff": num_from_patterns(
            text,
            [
                r"(?:HT|Meff|m_eff|MCT)_?(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)HT",
                r"SR(?:2|4|5|6)j_?(\d+(?:\.\d+)?)",
            ],
        ),
        "N_jets": num_from_patterns(text, [r"NJet_?(\d+)", r"Njet_?(\d+)", r"SR(\d+)j", r"(\d+)j"]),
        "N_btags": num_from_patterns(text, [r"Nb_?(\d+)", r"(\d+)b"]),
        "N_leptons": 2 if re.search(r"2l|sf|df|ee|mm|em", text, flags=re.IGNORECASE) else None,
    }


def parse_global(global_text: str) -> dict:
    return {
        "sqrt_s": parse_value(global_text, "sqrts") or 13,
        "luminosity": parse_value(global_text, "lumi"),
        "url": parse_value(global_text, "url"),
        "publication": parse_value(global_text, "publication"),
        "arxiv": parse_value(global_text, "arxiv"),
    }


def parse_one(path: str, global_cache: dict) -> Optional[dict]:
    parts = path.split("/")
    experiment = parts[1]
    analysis = parts[2]
    region = parts[-2]
    text = fetch_text(path)
    n_obs = parse_value(text, "observedN")
    n_exp = parse_value(text, "expectedBG")
    sigma = parse_value(text, "bgError")
    if n_obs is None or n_exp is None or sigma is None or float(sigma) <= 0:
        return None

    comment_match = re.search(r"^comment\s*:\s*(.*)$", text, flags=re.MULTILINE)
    comment = comment_match.group(1).strip() if comment_match else ""
    label_text = f"{region} {comment}".upper()
    if label_text.startswith(SKIP_REGION_PREFIXES) or any(token in label_text for token in ["CR_", "VR_", "CONTROL", "VALIDATION"]):
        return None

    global_path = "/".join(parts[:3] + ["globalInfo.txt"])
    if global_path not in global_cache:
        try:
            global_cache[global_path] = parse_global(fetch_text(global_path))
        except Exception:
            global_cache[global_path] = {}
    meta = global_cache[global_path]
    features = infer_features(region, comment)
    signal_region = comment if comment.lower().startswith("sr") else region
    return {
        "analysis": analysis,
        "experiment": experiment,
        "sqrt_s": 13,
        "luminosity": meta.get("luminosity"),
        "signal_region": signal_region,
        "N_obs": n_obs,
        "N_exp": n_exp,
        "sigma_exp": sigma,
        "MET": features["MET"],
        "HT_or_meff": features["HT_or_meff"],
        "N_jets": features["N_jets"],
        "N_leptons": features["N_leptons"],
        "N_btags": features["N_btags"],
        "category": infer_category(analysis, region, comment),
        "source_path": path,
        "source_url": f"{RAW_BASE}/{path}",
        "source_comment": comment,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build real signal-region CSV from SModelS public dataInfo files.")
    parser.add_argument("--tree", default=RAW_DIR / "smodels_tree.json")
    parser.add_argument("--output", default=RAW_DIR / "real_smodels_signal_regions.csv")
    parser.add_argument("--max-files", type=int, default=0, help="0 means all matching files.")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    ensure_dirs()
    tree = json.loads(Path(args.tree).read_text(encoding="utf-8"))["tree"]
    paths = [
        item["path"]
        for item in tree
        if item["type"] == "blob"
        and item["path"].startswith("13TeV/")
        and "/dataInfo.txt" in item["path"]
        and ("SUSY-" in item["path"] or "CMS-SUS" in item["path"] or "CMS-PAS-SUS" in item["path"])
    ]

    # Prefer signal-region-like directories and avoid obvious control/validation regions.
    selected = []
    for path in paths:
        region = Path(path).parent.name
        if region.upper().startswith(SKIP_REGION_PREFIXES):
            continue
        if any(token in region.upper() for token in ["CR_", "VR_", "CONTROL", "VALIDATION"]):
            continue
        selected.append(path)
    if args.max_files and args.max_files > 0:
        selected = selected[: args.max_files]

    global_cache = {}
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(parse_one, path, global_cache): path for path in selected}
        for i, future in enumerate(as_completed(futures), start=1):
            path = futures[future]
            try:
                row = future.result()
                if row:
                    rows.append(row)
            except Exception as exc:
                print(f"Skipping {path}: {exc}")
            if i % 100 == 0:
                print(f"Checked {i}/{len(selected)} files; kept {len(rows)} rows")

    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["experiment", "analysis", "signal_region", "source_path"]).reset_index(drop=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} real signal-region rows to {args.output}")
    if len(df):
        print(df.groupby(["experiment", "analysis"]).size().sort_values(ascending=False).head(20))


if __name__ == "__main__":
    main()
