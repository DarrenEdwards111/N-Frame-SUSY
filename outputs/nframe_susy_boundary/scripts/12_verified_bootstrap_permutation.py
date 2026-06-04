import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, ensure_dirs, bootstrap_permutation


def main():
    parser = argparse.ArgumentParser(description="Bootstrap and permutation tests for key N-Frame scores.")
    parser.add_argument("--verified-only", default=PROCESSED / "signal_regions_verified_only_scored.csv")
    parser.add_argument("--verified-imputed", default=PROCESSED / "signal_regions_verified_plus_imputed_scored.csv")
    parser.add_argument("--output", default=TABLES / "verified_key_terms_bootstrap_permutation.csv")
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    ensure_dirs()
    vo = pd.read_csv(args.verified_only)
    vi = pd.read_csv(args.verified_imputed)
    out = pd.concat(
        [
            bootstrap_permutation(vo, "B_access_verified_z", "verified_only", n=args.resamples),
            bootstrap_permutation(vi, "B_access_verified_imputed_z", "verified_plus_imputed", n=args.resamples),
        ],
        ignore_index=True,
    )
    out.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(out)} rows)")


if __name__ == "__main__":
    main()
