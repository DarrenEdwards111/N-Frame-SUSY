import argparse
from pathlib import Path

from common import DEFAULT_INPUT_DIR, FILELIST_DIR, ensure_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a ROOT file list for the CMS MiniAOD subset.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output", default=str(FILELIST_DIR / "miniaod_files.txt"))
    args = parser.parse_args()

    ensure_dirs()
    input_dir = Path(args.input_dir)
    files = sorted(input_dir.rglob("*.root"))
    total_size = sum(path.stat().st_size for path in files)
    output = Path(args.output)
    output.write_text("\n".join(str(path) for path in files) + ("\n" if files else ""), encoding="utf-8")

    print(f"Input directory: {input_dir}")
    print(f"Number of ROOT files: {len(files)}")
    print(f"Total size: {total_size / 1e9:.3f} GB")
    print("First 5 files:")
    for path in files[:5]:
        print(f"  {path}")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
