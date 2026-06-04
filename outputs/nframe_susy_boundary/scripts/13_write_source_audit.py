import argparse
from pathlib import Path

import pandas as pd

from verified_metadata_common import PROCESSED, INTERMEDIATE, TABLES, SOURCE_AUDIT, ensure_dirs, source_audit_text, missingness_table


def main():
    parser = argparse.ArgumentParser(description="Write verified metadata source audit.")
    parser.add_argument("--verified", default=PROCESSED / "signal_regions_verified_metadata.csv")
    parser.add_argument("--sources", default=INTERMEDIATE / "analysis_public_sources.csv")
    parser.add_argument("--conflicts", default=TABLES / "metadata_conflict_report.csv")
    parser.add_argument("--output", default=SOURCE_AUDIT / "metadata_source_audit.md")
    args = parser.parse_args()
    ensure_dirs()
    verified = pd.read_csv(args.verified)
    sources = pd.read_csv(args.sources) if Path(args.sources).exists() else pd.DataFrame()
    try:
        conflicts = pd.read_csv(args.conflicts) if Path(args.conflicts).exists() and Path(args.conflicts).stat().st_size else pd.DataFrame()
    except pd.errors.EmptyDataError:
        conflicts = pd.DataFrame()
    missingness = missingness_table(verified)
    text = source_audit_text(verified, sources, missingness, conflicts)
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
