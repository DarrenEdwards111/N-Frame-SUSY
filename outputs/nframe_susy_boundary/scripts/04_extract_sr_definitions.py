import argparse

from verified_metadata_common import INTERMEDIATE, ensure_dirs, load_regions, extract_metadata_long, long_to_wide


def main():
    parser = argparse.ArgumentParser(description="Extract signal-region metadata with provenance/confidence labels.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--long-output", default=INTERMEDIATE / "extracted_sr_metadata_long.csv")
    parser.add_argument("--wide-output", default=INTERMEDIATE / "extracted_sr_metadata_wide.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = load_regions(args.input)
    long_df = extract_metadata_long(df)
    wide_df = long_to_wide(long_df)
    long_df.to_csv(args.long_output, index=False)
    wide_df.to_csv(args.wide_output, index=False)
    print(f"Wrote {args.long_output} ({len(long_df)} field rows)")
    print(f"Wrote {args.wide_output} ({len(wide_df)} signal-region rows)")


if __name__ == "__main__":
    main()
