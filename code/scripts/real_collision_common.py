from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent
DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_stage2_real_collision_20gb")
PACKAGE = REPO / "nframe_next_stage_package"
SOURCE_MANIFEST = PACKAGE / "real_collision_20gb_manifest.csv"
SOURCE_REPORT = PACKAGE / "REAL_COLLISION_DOWNLOAD_REPORT.md"

DATA = PROJECT / "data"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
FILELISTS = DATA / "filelists_real_collision_20gb"
RESULTS = PROJECT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
LOGS = RESULTS / "logs"
REPORTS = PROJECT / "reports"
SCRIPTS = PROJECT / "scripts"

SAMPLES = {
    "cms_met_run2016g_collision": {
        "primary_dataset": "MET",
        "record_id": 30509,
        "sample_type": "real_collision_MET",
        "expected_files": 3,
    },
    "cms_jetht_run2016g_collision": {
        "primary_dataset": "JetHT",
        "record_id": 30508,
        "sample_type": "real_collision_JetHT",
        "expected_files": 4,
    },
    "cms_singlemuon_run2016g_collision": {
        "primary_dataset": "SingleMuon",
        "record_id": 30513,
        "sample_type": "real_collision_SingleMuon",
        "expected_files": 2,
    },
}


def ensure_dirs() -> None:
    for path in [DATA, INTERIM, PROCESSED, FILELISTS, RESULTS, TABLES, FIGURES, LOGS, REPORTS, SCRIPTS]:
        path.mkdir(parents=True, exist_ok=True)


def infer_sample_id(path: Path) -> str:
    parts = set(path.parts)
    for sample_id in SAMPLES:
        if sample_id in parts:
            return sample_id
    return "unknown"


def find_real_root_files() -> list[Path]:
    if not DOWNLOAD_ROOT.exists():
        return []
    return sorted(DOWNLOAD_ROOT.rglob("*.root"))


def safe_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}

