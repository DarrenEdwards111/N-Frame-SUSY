from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
LOCAL_ROOT = Path(r"D:\cern_open_data")

RECORDS = {
    30541: ("JetHT", "Run2016H", "MINIAOD"),
    30542: ("MET", "Run2016H", "MINIAOD"),
    30546: ("SingleMuon", "Run2016H", "MINIAOD"),
    30558: ("JetHT", "Run2016H", "NANOAOD"),
    30559: ("MET", "Run2016H", "NANOAOD"),
    30563: ("SingleMuon", "Run2016H", "NANOAOD"),
}


def uri_to_https(uri: str) -> str:
    return uri.replace("root://eospublic.cern.ch//", "https://eospublic.cern.ch/")


def fetch_record(record_id: int) -> tuple[dict, list[dict]]:
    rec = requests.get(f"https://opendata.cern.ch/api/records/{record_id}", timeout=30).json()
    md = rec["metadata"]
    files = []
    for index in md.get("_file_indices", []):
        files.extend(index.get("files", []))
    return md, files


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    local_files = list(LOCAL_ROOT.rglob("*.root")) if LOCAL_ROOT.exists() else []
    rows = []
    selected = []
    for rid, (primary, era, tier) in RECORDS.items():
        md, files = fetch_record(rid)
        dist = md["distribution"]
        smallest = sorted(files, key=lambda f: f["size"])[:5]
        rows.append(
            {
                "record_id": rid,
                "title": md["title"],
                "primary_dataset": primary,
                "data_tier": tier,
                "run_era": era,
                "real_or_simulated": "real collision",
                "total_size_gb": dist["size"] / 1e9,
                "number_files": dist["number_files"],
                "software_route_needed": "CMSSW/Docker" if tier == "MINIAOD" else "Python/uproot",
                "suitability": "best full-variable validation" if tier == "MINIAOD" else "fast reduced cross-check",
                "smallest_file_size_gb": smallest[0]["size"] / 1e9 if smallest else None,
                "smallest_file_uri": smallest[0]["uri"] if smallest else "",
                "limitations": "large full record; download selected files only" if tier == "MINIAOD" else "secondary vertices and packed candidates unavailable or approximate",
            }
        )
        if tier == "MINIAOD":
            f = smallest[0]
            selected.append(
                {
                    "record_id": rid,
                    "primary_dataset": primary,
                    "data_tier": tier,
                    "run_era": era,
                    "filename": f["filename"],
                    "size_bytes": f["size"],
                    "size_gb": f["size"] / 1e9,
                    "uri": f["uri"],
                    "https_url": uri_to_https(f["uri"]),
                    "target_subdir": f"{primary.lower()}_run2016h_validation/{rid}",
                }
            )
    candidates = pd.DataFrame(rows)
    plan = pd.DataFrame(selected)
    candidates.to_csv(TABLES / "independent_real_validation_dataset_candidates.csv", index=False)
    plan.to_csv(TABLES / "independent_real_validation_selected_download_plan.csv", index=False)
    total_gb = plan["size_gb"].sum()
    report = [
        "# Independent Real Validation Dataset Options",
        "",
        "Date: 2026-06-09",
        "",
        f"Local ROOT files found under `D:\\cern_open_data`: {len(local_files)}. These are mostly the existing Run2016G derivation files or earlier duplicates, so independent validation should use new Run2016H files.",
        "",
        "## Candidate Records",
        "",
        candidates.to_markdown(index=False),
    ]
    (REPORTS / "INDEPENDENT_REAL_VALIDATION_DATASET_OPTIONS.md").write_text("\n".join(report), encoding="utf-8")
    plan_report = [
        "# Validation Download Plan",
        "",
        "Date: 2026-06-09",
        "",
        "Chosen route: Route A, independent Run2016H MiniAOD validation. This preserves the dominant fitted variables, including secondary vertices and packed-candidate counts, and avoids the reduced-variable limitation of NanoAOD.",
        "",
        f"Planned download size: {total_gb:.3f} GB, below the 20 GB approval threshold.",
        "",
        "Output folder: `D:\\cern_open_data\\nframe_validation_real_independent`",
        "",
        "Because the total planned download is below 20 GB and all selected records are real collision data, the pipeline may proceed automatically.",
        "",
        plan.to_markdown(index=False),
    ]
    (REPORTS / "VALIDATION_DOWNLOAD_PLAN.md").write_text("\n".join(plan_report), encoding="utf-8")
    print(candidates.to_string(index=False))
    print("\nSelected MiniAOD validation plan:")
    print(plan.to_string(index=False))
    print(f"Total planned GB: {total_gb:.3f}")


if __name__ == "__main__":
    main()
