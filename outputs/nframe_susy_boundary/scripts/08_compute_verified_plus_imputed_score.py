import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, ensure_dirs, load_regions, score_verified_plus_imputed


def main():
    parser = argparse.ArgumentParser(description="Compute verified+imputed N-Frame boundary score with imputation flags.")
    parser.add_argument("--verified", default=PROCESSED / "signal_regions_verified_metadata.csv")
    parser.add_argument("--base", default=None)
    parser.add_argument("--output", default=PROCESSED / "signal_regions_verified_plus_imputed_scored.csv")
    args = parser.parse_args()
    ensure_dirs()
    verified = pd.read_csv(args.verified)
    base = load_regions(args.base)
    scored = score_verified_plus_imputed(verified, base)
    scored.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(scored)} rows)")


if __name__ == "__main__":
    main()
