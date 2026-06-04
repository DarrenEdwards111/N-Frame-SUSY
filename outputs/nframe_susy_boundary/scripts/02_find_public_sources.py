import argparse
import pandas as pd

from verified_metadata_common import INTERMEDIATE, TABLES, ensure_dirs, load_regions, find_public_sources


def main():
    parser = argparse.ArgumentParser(description="Find public source candidates for each analysis.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--manifest", default=TABLES / "analysis_source_manifest.csv")
    parser.add_argument("--output", default=INTERMEDIATE / "analysis_public_sources.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = load_regions(args.input)
    manifest = pd.read_csv(args.manifest) if args.manifest and pd.io.common.file_exists(args.manifest) else None
    sources = find_public_sources(df, manifest)
    sources.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(sources)} source candidates)")


if __name__ == "__main__":
    main()
