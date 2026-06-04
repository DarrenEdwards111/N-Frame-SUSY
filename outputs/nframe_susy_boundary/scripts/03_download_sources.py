import argparse
import pandas as pd

from verified_metadata_common import INTERMEDIATE, SOURCE_AUDIT, ensure_dirs, download_sources


def main():
    parser = argparse.ArgumentParser(description="Download candidate public sources where direct URLs are available.")
    parser.add_argument("--sources", default=INTERMEDIATE / "analysis_public_sources.csv")
    parser.add_argument("--output", default=SOURCE_AUDIT / "source_download_manifest.csv")
    args = parser.parse_args()
    ensure_dirs()
    sources = pd.read_csv(args.sources)
    manifest = download_sources(sources)
    manifest.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(manifest)} rows)")


if __name__ == "__main__":
    main()
