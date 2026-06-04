import argparse
from pathlib import Path

import pandas as pd

from verified_metadata_common import PROCESSED, TABLES, RESULTS, ensure_dirs, summary_text


def read_table(path):
    return pd.read_csv(path) if Path(path).exists() else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Write verified metadata reanalysis summary.")
    parser.add_argument("--verified", default=PROCESSED / "signal_regions_verified_metadata.csv")
    parser.add_argument("--verified-models", default=TABLES / "verified_only_model_results.csv")
    parser.add_argument("--imputed-models", default=TABLES / "verified_plus_imputed_model_results.csv")
    parser.add_argument("--cv", default=TABLES / "verified_cross_validation_results.csv")
    parser.add_argument("--boot", default=TABLES / "verified_key_terms_bootstrap_permutation.csv")
    parser.add_argument("--output", default=RESULTS / "nframe_verified_metadata_summary.md")
    args = parser.parse_args()
    ensure_dirs()
    text = summary_text(
        pd.read_csv(args.verified),
        read_table(args.verified_models),
        read_table(args.imputed_models),
        read_table(args.cv),
        read_table(args.boot),
    )
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
