from __future__ import annotations

"""Audit current CERN Open Data availability for a fresh CMS-era validation.

This uses only the CERN Open Data metadata API. It intentionally does not
download event files: the purpose is to determine whether an equivalent remote
MiniAOD validation can be launched for Run2017 or Run2018.
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_current_cms_new_era_remote_availability_audit"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
API = "https://opendata.cern.ch/api/records/"

ERAS = ["Run2017", "Run2018"]
DATASETS = ["MET", "HTMHT", "JetHT", "SingleMuon"]


def query_records(query: str) -> list[dict]:
    response = requests.get(API, params={"q": query, "size": 100}, timeout=60)
    response.raise_for_status()
    return response.json().get("hits", {}).get("hits", [])


def title(hit: dict) -> str:
    return str(hit.get("metadata", {}).get("title", ""))


def is_usable_real_miniaod(hit: dict, era: str, dataset: str) -> bool:
    text = title(hit).lower()
    return (
        era.lower() in text
        and dataset.lower() in text
        and "miniaod" in text
        and "miniaodsim" not in text
        and "simulation" not in text
    )


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []
    candidates: list[dict] = []

    for era in ERAS:
        for dataset in DATASETS:
            # The exact stream query is the relevant route for an equivalent
            # MHT-aware validation. The broad query catches portal metadata
            # changes that might use a different title order.
            exact_query = f"CMS {dataset} {era} MINIAOD"
            broad_query = f"CMS {era} MINIAOD"
            exact = query_records(exact_query)
            broad = query_records(broad_query)
            all_hits = {str(hit.get("id")): hit for hit in [*exact, *broad]}.values()
            usable = [hit for hit in all_hits if is_usable_real_miniaod(hit, era, dataset)]
            rows.append(
                {
                    "audit_utc": timestamp,
                    "run_era": era,
                    "primary_dataset": dataset,
                    "exact_query": exact_query,
                    "exact_hit_count": len(exact),
                    "broad_query": broad_query,
                    "broad_hit_count": len(broad),
                    "usable_real_miniaod_record_count": len(usable),
                    "remote_feature_equivalent_validation_available": bool(usable),
                }
            )
            for hit in usable:
                candidates.append(
                    {
                        "run_era": era,
                        "primary_dataset": dataset,
                        "record_id": hit.get("id"),
                        "title": title(hit),
                        "record_url": f"https://opendata.cern.ch/record/{hit.get('id')}",
                    }
                )

    summary = pd.DataFrame(rows)
    candidate_df = pd.DataFrame(candidates)
    summary.to_csv(TABLES / "01_new_era_stream_availability.csv", index=False)
    candidate_df.to_csv(TABLES / "02_usable_real_miniaod_candidates.csv", index=False)

    available = summary["remote_feature_equivalent_validation_available"].sum()
    conclusion = (
        "At least one matching stream is available; inspect the candidate table before extraction."
        if available
        else "No matching real Run2017/Run2018 CMS MiniAOD stream was exposed by the CERN Open Data API in this audit."
    )
    report = f"""# Current CMS New-Era Remote Availability Audit

## Scope

This audit checked the CERN Open Data metadata API at `{timestamp}` for real CMS
Run2017 and Run2018 MiniAOD records matching the four streams required by the
feature-equivalent N-Frame validation: MET, HTMHT, JetHT, and SingleMuon.

No event file was downloaded. A non-empty usable-record result would be the
only condition required to proceed to a remote XRootD/CMSSW extraction.

## Result

{conclusion}

{summary.to_markdown(index=False)}

## Interpretation

This is an availability result, not a physics result. It means the next truly
new-era CMS validation cannot currently be executed from this portal route.
The completed Run2015D and Run2016H remote validations remain useful independent
real-data checks, but they are not a replacement for a Run2017/2018 validation.
"""
    (REPORTS / "01_CURRENT_CMS_NEW_ERA_REMOTE_AVAILABILITY_AUDIT.md").write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(REPORTS / "01_CURRENT_CMS_NEW_ERA_REMOTE_AVAILABILITY_AUDIT.md")


if __name__ == "__main__":
    main()
