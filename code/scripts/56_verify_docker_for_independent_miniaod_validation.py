import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
DATA_ROOT = Path(r"D:\cern_open_data\nframe_validation_real_independent")
REPORTS = ROOT / "reports"
LOGS = ROOT / "results" / "logs"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700"


def run(cmd, timeout=120):
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    checks = []
    log_lines = []
    commands = [
        ("docker_info", ["docker", "info"]),
        ("image_available", ["docker", "image", "inspect", IMAGE]),
        (
            "cmsrun_scram_mount_check",
            [
                "docker", "run", "--rm",
                "-v", f"{CMSSW_WORK}:/work",
                "-v", f"{DATA_ROOT}:/data",
                IMAGE,
                "bash", "-lc",
                "which cmsRun && which scram && test -f /work/run_one_sample.sh && find /data -name '*.root' | head -3",
            ],
        ),
    ]
    for name, cmd in commands:
        code, out, err = run(cmd, timeout=180)
        checks.append({"check": name, "status": "pass" if code == 0 else "fail", "returncode": code})
        log_lines.extend([f"$ {' '.join(cmd)}", out, err, ""])
        if code != 0:
            break
    (LOGS / "independent_miniaod_docker_status.log").write_text("\n".join(log_lines), encoding="utf-8", errors="replace")
    report = [
        "# Independent MiniAOD Docker Status",
        "",
        "Date: 2026-06-09",
        "",
        "## Checks",
        "",
        "| check | status | returncode |",
        "|---|---:|---:|",
    ]
    report.extend([f"| {c['check']} | {c['status']} | {c['returncode']} |" for c in checks])
    report.extend(["", f"Log: `{LOGS / 'independent_miniaod_docker_status.log'}`"])
    (REPORTS / "INDEPENDENT_MINIAOD_DOCKER_STATUS.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    if any(c["status"] != "pass" for c in checks):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
