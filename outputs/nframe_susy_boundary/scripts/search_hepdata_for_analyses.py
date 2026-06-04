import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT / "results" / "tables" / "analysis_source_manifest.csv"


def clean_arxiv(value):
    if pd.isna(value):
        return ""
    match = re.search(r"(\d{4}\.\d{4,5})", str(value))
    return match.group(1) if match else str(value).strip()


def search_hepdata(query):
    if not query:
        return []
    url = f"https://www.hepdata.net/search/?q={quote(query)}&format=json&size=5"
    response = requests.get(url, timeout=30, headers={"User-Agent": "nframe-hepdata-search/0.1"})
    response.raise_for_status()
    data = response.json()
    results = data.get("results", []) if isinstance(data, dict) else []
    out = []
    for item in results:
        rec = item.get("record", item)
        out.append(
            {
                "recid": rec.get("recid") or rec.get("id"),
                "title": rec.get("title", ""),
                "hepdata_doi": rec.get("hepdata_doi", ""),
                "arxiv_id": rec.get("arxiv_id", ""),
                "doi": rec.get("doi", ""),
                "url": f"https://www.hepdata.net/record/{rec.get('recid') or rec.get('id')}",
            }
        )
    return out


def main():
    parser = argparse.ArgumentParser(description="Search HEPData JSON endpoint for each analysis manifest row.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_MANIFEST))
    args = parser.parse_args()

    df = pd.read_csv(args.manifest)
    matches = []
    for _, row in df.iterrows():
        arxiv = clean_arxiv(row.get("arxiv", ""))
        doi = row.get("publicationDOI", "")
        queries = [arxiv]
        if isinstance(doi, str) and doi:
            queries.append(doi.replace("https://doi.org/", ""))
        found = []
        for query in queries:
            try:
                found = search_hepdata(query)
                if found:
                    break
            except Exception as exc:
                found = [{"error": str(exc), "query": query}]
                break
        matches.append(found)

    df["hepdata_matches_json"] = [json.dumps(m, ensure_ascii=True) for m in matches]
    df["hepdata_match_count"] = [len(m) if isinstance(m, list) and not (m and "error" in m[0]) else 0 for m in matches]
    df["hepdata_first_record_url"] = [
        m[0].get("url", "") if isinstance(m, list) and m and "error" not in m[0] else "" for m in matches
    ]
    df.to_csv(args.output, index=False)
    print(f"Wrote HEPData-enriched manifest: {args.output}")
    print(df[["analysis", "arxiv", "hepdata_match_count", "hepdata_first_record_url"]].to_string(index=False))


if __name__ == "__main__":
    main()
