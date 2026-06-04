from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FILELIST_DIR = DATA_DIR / "filelists"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
LOGS_DIR = RESULTS_DIR / "logs"
DEFAULT_INPUT_DIR = Path("D:/cern_open_data/cms_met_run2016g_miniaod_10gb")


def ensure_dirs() -> None:
    for path in [FILELIST_DIR, PROCESSED_DIR, TABLES_DIR, FIGURES_DIR, LOGS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_features(path: Path):
    import pandas as pd

    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def write_features(df, path: Path) -> None:
    if path.suffix.lower() == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
