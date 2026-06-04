import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "nframe_cmssw_outputs"


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for rel in ["data/processed", "results/tables", "results/figures", "results/logs", "cmssw", "scripts", "README.md", "requirements.txt"]:
        src = ROOT / rel
        dst = OUT / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    summary = ROOT / "results" / "nframe_cmssw_event_level_summary.md"
    if summary.exists():
        (OUT / "results").mkdir(parents=True, exist_ok=True)
        shutil.copy2(summary, OUT / "results" / summary.name)
    zip_base = ROOT / "nframe_cmssw_outputs"
    shutil.make_archive(str(zip_base), "zip", OUT)
    print(f"Wrote {zip_base}.zip")


if __name__ == "__main__":
    main()
