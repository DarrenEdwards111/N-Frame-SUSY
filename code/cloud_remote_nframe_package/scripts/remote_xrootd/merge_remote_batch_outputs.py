from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("NFRAME_REMOTE_OUT", ROOT / "outputs_breakthrough_full_push_nframe_susy"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--out", default=str(OUT / "features/remote_miniaod_features_merged.csv"))
    args = parser.parse_args()
    ledger = pd.read_csv(args.ledger)
    frames = []
    for _, row in ledger[ledger["status"].eq("completed")].iterrows():
        p = Path(row["output_path"])
        if not p.exists():
            continue
        df = pd.read_csv(p, low_memory=False)
        df.insert(0, "record_id", row["record_id"])
        df.insert(1, "process_family", row["process_family"])
        df.insert(2, "dataset_label", row["dataset_label"])
        df.insert(3, "xrootd_url", row["xrootd_url"])
        frames.append(df)
    out = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(args.out)


if __name__ == "__main__":
    main()
