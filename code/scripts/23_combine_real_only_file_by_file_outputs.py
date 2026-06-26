import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["file_by_file_test", "full_file_by_file", "trigger_filter_5k_by_file", "trigger_filter_full"], required=True)
    args = parser.parse_args()
    out_dir_map = {
        "file_by_file_test": "cmssw_real_only_file_by_file_test",
        "full_file_by_file": "cmssw_real_only_full_file_by_file",
        "trigger_filter_5k_by_file": "cmssw_real_only_trigger_filter_5k_by_file",
        "trigger_filter_full": "cmssw_real_only_trigger_filter_full",
    }
    out_dir_name = out_dir_map[args.mode]
    out_dir = ROOT / "data" / "processed" / out_dir_name
    files = sorted(out_dir.glob("*_event_features.csv"))
    frames = [pd.read_csv(path) for path in files]
    if not frames:
        raise RuntimeError(f"No per-file outputs found in {out_dir}")
    combined = pd.concat(frames, ignore_index=True)
    name_map = {
        "file_by_file_test": "real_only_file_by_file_test_combined.csv",
        "full_file_by_file": "real_only_full_cmssw_event_features_with_source_file.csv",
        "trigger_filter_5k_by_file": "real_only_trigger_filter_5k_combined.csv",
        "trigger_filter_full": "real_only_full_event_features_with_trigger_filter.csv",
    }
    name = name_map[args.mode]
    combined_path = out_dir / name
    combined.to_csv(combined_path, index=False)
    summary = combined.groupby(["sample_id", "primary_dataset", "source_file"], as_index=False).agg(
        events=("event", "count"),
        first_global_index=("event_index_global_within_sample", "min"),
        last_global_index=("event_index_global_within_sample", "max"),
    )
    summary.to_csv(TABLES / f"real_only_{args.mode}_combined_summary.csv", index=False)
    print(combined_path)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
