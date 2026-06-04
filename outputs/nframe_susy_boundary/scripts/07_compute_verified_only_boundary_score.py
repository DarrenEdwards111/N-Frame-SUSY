import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, ensure_dirs, score_verified_only


def main():
    parser = argparse.ArgumentParser(description="Compute verified-only N-Frame boundary score.")
    parser.add_argument("--input", default=PROCESSED / "signal_regions_verified_metadata.csv")
    parser.add_argument("--output", default=PROCESSED / "signal_regions_verified_only_scored.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = pd.read_csv(args.input)
    scored = score_verified_only(df)
    scored.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(scored)} rows)")


if __name__ == "__main__":
    main()
