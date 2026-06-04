from pathlib import Path

from verified_metadata_common import RESULTS, ensure_dirs, paper_ready_text


def main():
    ensure_dirs()
    output = RESULTS / "paper_ready_verified_methods_results.md"
    Path(output).write_text(paper_ready_text(), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
