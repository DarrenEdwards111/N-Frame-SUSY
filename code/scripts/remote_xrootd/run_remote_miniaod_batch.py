from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parents[0]
OUT = Path(os.environ.get("NFRAME_REMOTE_OUT", ROOT / "outputs_breakthrough_full_push_nframe_susy"))
CMSSW_WORK = Path(os.environ.get("NFRAME_CMSSW_WORK", MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"))
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def run_one(row: pd.Series) -> dict:
    run_id = f"remote_{int(row.record_id)}_{row.process_family}_{int(row.file_index)}".replace("/", "_").replace(" ", "_")
    out_dir = CMSSW_WORK / "outputs" / run_id
    log_path = OUT / "remote_xrootd" / f"{run_id}.log"
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES='{row.xrootd_url}'; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        "export NFRAME_TEST_MAXEVENTS=100; "
        f"export NFRAME_MAXEVENTS_FULL={int(row.planned_max_events)}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", IMAGE, "bash", "-lc", cmd_inside]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        try:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=7200)
            rc = proc.returncode
        except Exception as exc:
            log.write("\nEXCEPTION " + repr(exc) + "\n")
            rc = 999
    output = out_dir / "event_features.csv"
    return {
        **row.to_dict(),
        "status": "completed" if rc == 0 and output.exists() else "failed",
        "output_path": str(output) if output.exists() else "",
        "log_path": str(log_path),
        "returncode": rc,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    manifest = pd.read_csv(args.manifest)
    pending = manifest[manifest["status"].eq("pending")].head(args.limit)
    rows = [run_one(row) for _, row in pending.iterrows()]
    ledger_path = OUT / "remote_xrootd" / "remote_processing_ledger.csv"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(ledger_path) if ledger_path.exists() else pd.DataFrame()
    pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(ledger_path, index=False)
    print(ledger_path)


if __name__ == "__main__":
    main()
