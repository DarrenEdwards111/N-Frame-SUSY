from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent
DOWNLOAD_ROOT = Path("D:/cern_open_data/nframe_stage2")
DATA = PROJECT / "data"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
RESULTS = PROJECT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
LOGS = RESULTS / "logs"
REPORTS = PROJECT / "reports"

SAMPLES = {
    "cms_met_run2016g_collision": {"sample_type": "real_collision", "record_id": 30509},
    "cms_jetht_run2016g_collision": {"sample_type": "real_collision", "record_id": 30508},
    "cms_singlemuon_run2016g_collision": {"sample_type": "real_collision", "record_id": 30513},
    "sms_t5wg_mg1500_mlsp1_signal": {"sample_type": "simulated_signal", "record_id": 63465},
    "susy_htoaa4b_m12_signal": {"sample_type": "simulated_signal", "record_id": 64906},
}


def ensure_dirs() -> None:
    for path in [INTERIM, PROCESSED, TABLES, FIGURES, LOGS, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def infer_sample_id(path: Path) -> str:
    parts = set(path.parts)
    for sample_id in SAMPLES:
        if sample_id in parts:
            return sample_id
    for parent in path.parents:
        if parent.name in SAMPLES:
            return parent.name
    return "unknown"


def find_root_files() -> list[Path]:
    if not DOWNLOAD_ROOT.exists():
        return []
    return sorted(DOWNLOAD_ROOT.rglob("*.root"))


def manifest_path() -> Path:
    return TABLES / "downloaded_root_manifest.csv"

