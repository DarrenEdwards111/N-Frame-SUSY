import argparse
import pandas as pd

from verified_metadata_common import INTERMEDIATE, ensure_dirs, match_metadata


def main():
    parser = argparse.ArgumentParser(description="Match extracted metadata back to signal regions.")
    parser.add_argument("--extracted", default=INTERMEDIATE / "extracted_sr_metadata_long.csv")
    parser.add_argument("--output", default=INTERMEDIATE / "sr_metadata_matched.csv")
    args = parser.parse_args()
    ensure_dirs()
    extracted = pd.read_csv(args.extracted)
    matched = match_metadata(None, extracted)
    matched.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(matched)} field matches)")


if __name__ == "__main__":
    main()
