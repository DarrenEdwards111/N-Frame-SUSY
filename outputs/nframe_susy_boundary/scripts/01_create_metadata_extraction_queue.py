import argparse

from verified_metadata_common import INTERMEDIATE, ensure_dirs, load_regions, create_queue


def main():
    parser = argparse.ArgumentParser(description="Create a prioritized verified-metadata extraction queue.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=INTERMEDIATE / "metadata_extraction_queue.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = load_regions(args.input)
    queue = create_queue(df)
    queue.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(queue)} analyses)")


if __name__ == "__main__":
    main()
