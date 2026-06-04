import argparse
import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, ensure_dirs, fit_simple_models


def main():
    parser = argparse.ArgumentParser(description="Run verified+imputed N-Frame models with imputation controls.")
    parser.add_argument("--input", default=PROCESSED / "signal_regions_verified_plus_imputed_scored.csv")
    parser.add_argument("--output", default=TABLES / "verified_plus_imputed_model_results.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = pd.read_csv(args.input)
    results = fit_simple_models(df, "B_access_verified_imputed_z", "verified_plus_imputed", include_controls=True)
    results.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(results)} rows)")


if __name__ == "__main__":
    main()
