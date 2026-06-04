import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, ensure_dirs, fit_simple_models


def main():
    parser = argparse.ArgumentParser(description="Run verified-only N-Frame models.")
    parser.add_argument("--input", default=PROCESSED / "signal_regions_verified_only_scored.csv")
    parser.add_argument("--output", default=TABLES / "verified_only_model_results.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = pd.read_csv(args.input)
    results = fit_simple_models(df, "B_access_verified_z", "verified_only", include_controls=False)
    results.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(results)} rows)")


if __name__ == "__main__":
    main()
