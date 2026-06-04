import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, ensure_dirs, load_regions, create_verified_table, missingness_table


def main():
    parser = argparse.ArgumentParser(description="Create verified metadata table with confidence and provenance columns.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--matched", default="data/intermediate/sr_metadata_matched.csv")
    parser.add_argument("--output", default=PROCESSED / "signal_regions_verified_metadata.csv")
    parser.add_argument("--missingness-output", default=TABLES / "verified_metadata_missingness.csv")
    parser.add_argument("--conflict-output", default=TABLES / "metadata_conflict_report.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = load_regions(args.input)
    matched = pd.read_csv(args.matched)
    verified, conflicts = create_verified_table(df, matched)
    verified.to_csv(args.output, index=False)
    missingness_table(verified).to_csv(args.missingness_output, index=False)
    conflicts.to_csv(args.conflict_output, index=False)
    print(f"Wrote {args.output} ({len(verified)} rows)")
    print(f"Wrote {args.missingness_output}")


if __name__ == "__main__":
    main()
