import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, ensure_dirs, cross_validation


def main():
    parser = argparse.ArgumentParser(description="Cross-validate verified-only and verified+imputed scores.")
    parser.add_argument("--verified-only", default=PROCESSED / "signal_regions_verified_only_scored.csv")
    parser.add_argument("--verified-imputed", default=PROCESSED / "signal_regions_verified_plus_imputed_scored.csv")
    parser.add_argument("--output", default=TABLES / "verified_cross_validation_results.csv")
    args = parser.parse_args()
    ensure_dirs()
    rows = []
    vo = pd.read_csv(args.verified_only)
    vi = pd.read_csv(args.verified_imputed)
    a = cross_validation(vo, "B_access_verified_z")
    a["dataset"] = "verified_only"
    b = cross_validation(vi, "B_access_verified_imputed_z")
    b["dataset"] = "verified_plus_imputed"
    rows.extend([a, b])
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(out)} rows)")


if __name__ == "__main__":
    main()
