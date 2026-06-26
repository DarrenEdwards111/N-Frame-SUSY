from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parents[0]
OUT = Path(os.environ.get("NFRAME_REMOTE_OUT", ROOT / "outputs_breakthrough_full_push_nframe_susy"))
CMSSW_WORK = Path(os.environ.get("NFRAME_CMSSW_WORK", MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"))
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--process-family", required=True)
    parser.add_argument("--max-events", type=int, default=100)
    args = parser.parse_args()

    run_id = f"xrootd_smoke_{args.record_id}_{args.process_family}".replace("/", "_").replace(" ", "_")
    out_dir = CMSSW_WORK / "outputs" / run_id
    log_path = OUT / "remote_xrootd" / f"{run_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES='{args.url}'; "
        "export NFRAME_INPUT_DIR=/data; "
        "export NFRAME_OUTPUT_DIR=/work/outputs/${SAMPLE_ID}; "
        f"export NFRAME_TEST_MAXEVENTS={args.max_events}; "
        f"export NFRAME_MAXEVENTS_FULL={args.max_events}; "
        "bash /work/run_one_sample.sh"
    )
    cmd = ["docker", "run", "--rm", "-v", f"{CMSSW_WORK}:/work", IMAGE, "bash", "-lc", cmd_inside]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=7200)
    raw = out_dir / "event_features.csv"
    print(f"status={'success' if proc.returncode == 0 and raw.exists() else 'failed'}")
    print(f"returncode={proc.returncode}")
    print(f"output={raw}")
    print(f"log={log_path}")


if __name__ == "__main__":
    main()
