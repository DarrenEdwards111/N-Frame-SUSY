from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path("D:/cern_open_data/cms_met_run2016g_miniaod_10gb")
OUT = ROOT / "data" / "filelists" / "miniaod_files_windows.txt"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_PATH.rglob("*.root"))
    OUT.write_text("\n".join(str(path) for path in files) + ("\n" if files else ""), encoding="utf-8")
    total_gb = sum(path.stat().st_size for path in files) / 1e9
    print(f"ROOT files: {len(files)}")
    print(f"Total size GB: {total_gb:.3f}")
    print("First files:")
    for path in files[:10]:
        print(path)


if __name__ == "__main__":
    main()
