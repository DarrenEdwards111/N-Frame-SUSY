from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"


REQUIRED_COLUMNS = [
    "analysis",
    "experiment",
    "sqrt_s",
    "luminosity",
    "signal_region",
    "N_obs",
    "N_exp",
    "sigma_exp",
    "MET",
    "HT_or_meff",
    "N_jets",
    "N_leptons",
    "N_btags",
    "category",
]


def ensure_dirs() -> None:
    for path in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR, TABLES_DIR]:
        path.mkdir(parents=True, exist_ok=True)
