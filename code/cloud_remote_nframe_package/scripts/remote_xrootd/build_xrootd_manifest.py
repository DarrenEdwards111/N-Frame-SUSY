from __future__ import annotations

import argparse
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-records", type=int, default=12)
    parser.add_argument("--planned-max-events", type=int, default=20000)
    args = parser.parse_args()
    candidates = pd.read_csv(args.candidates)
    rows = []
    selected = candidates.sort_values(["priority", "smallest_file_size_bytes"]).head(args.max_records)
    for idx, row in selected.iterrows():
        rows.append({
            "dataset_label": str(row.get("title", "")).split("/")[1] if "/" in str(row.get("title", "")) else row.get("search_label", ""),
            "record_id": int(row["record_id"]),
            "process_family": row.get("process_family", ""),
            "primary_dataset": "",
            "run_era": "RunIISummer20UL16MiniAODv2",
            "data_tier": row.get("data_tier", "MINIAODSIM"),
            "xrootd_url": row.get("smallest_file_url", ""),
            "file_index": 0,
            "planned_max_events": args.planned_max_events,
            "status": "pending",
            "output_path": "",
            "notes": row.get("reason_for_inclusion", ""),
        })
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(args.out)


if __name__ == "__main__":
    main()
