from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from real_collision_common import REPORTS, LOGS, TABLES, ensure_dirs


ROUTE_REPORTS = REPORTS / "non_docker_cms_aware_route"
MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"


def run_command(command: list[str], shell: bool = False) -> dict:
    text = command if shell else " ".join(command)
    try:
        proc = subprocess.run(command if not shell else text, shell=shell, capture_output=True, text=True, timeout=60)
        return {
            "command": text,
            "available": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"command": text, "available": False, "returncode": "", "stdout": "", "stderr": repr(exc)}


def main() -> None:
    ensure_dirs()
    ROUTE_REPORTS.mkdir(parents=True, exist_ok=True)
    rows = []
    log_lines = []

    rows.append({"check": "python_executable", "status": "ok", "detail": sys.executable})
    rows.append({"check": "python_version", "status": "ok", "detail": sys.version.replace("\n", " ")})
    rows.append({"check": "platform", "status": "ok", "detail": platform.platform()})
    rows.append({"check": "conda_default_env", "status": "ok" if os.environ.get("CONDA_DEFAULT_ENV") else "missing", "detail": os.environ.get("CONDA_DEFAULT_ENV", "")})
    rows.append({"check": "conda_prefix", "status": "ok" if os.environ.get("CONDA_PREFIX") else "missing", "detail": os.environ.get("CONDA_PREFIX", "")})

    pyroot_detail = ""
    pyroot_ok = False
    try:
        import ROOT  # type: ignore

        pyroot_ok = True
        pyroot_detail = f"ROOT import succeeded; version={ROOT.gROOT.GetVersion()}"
        manifest = pd.read_csv(MANIFEST)
        first_file = Path(manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)].iloc[0]["local_path"])
        tfile = ROOT.TFile.Open(str(first_file))
        events = tfile.Get("Events") if tfile else None
        pyroot_detail += f"; TFile opens={bool(tfile and not tfile.IsZombie())}; Events visible={bool(events)}"
        if tfile:
            tfile.Close()
    except Exception as exc:
        pyroot_detail = f"ROOT import/check failed: {repr(exc)}"
    rows.append({"check": "import_ROOT", "status": "ok" if pyroot_ok else "missing_or_failed", "detail": pyroot_detail})

    commands = [
        ("where_root", ["where", "root"], True),
        ("root_b_q", ["root", "-b", "-q"], False),
        ("where_cmsRun", ["where", "cmsRun"], True),
        ("where_scram", ["where", "scram"], True),
        ("docker_version", ["docker", "--version"], False),
        ("docker_info", ["docker", "info"], False),
        ("wsl_status", ["wsl", "--status"], False),
        ("wsl_list_verbose", ["wsl", "-l", "-v"], False),
        ("where_conda", ["where", "conda"], True),
        ("where_mamba", ["where", "mamba"], True),
    ]
    for check, command, shell in commands:
        result = run_command(command, shell=shell)
        detail = "\n".join(part for part in [result["stdout"], result["stderr"]] if part)
        rows.append({"check": check, "status": "ok" if result["available"] else "missing_or_failed", "detail": detail[:4000]})
        log_lines.append(f"## {check}\nCOMMAND: {result['command']}\nRETURNCODE: {result['returncode']}\nSTDOUT:\n{result['stdout']}\nSTDERR:\n{result['stderr']}\n")

    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "root_pyroot_environment_check.csv", index=False)
    (LOGS / "root_pyroot_environment_check.log").write_text("\n\n".join(log_lines), encoding="utf-8")

    def detail(check: str) -> str:
        val = df.loc[df["check"] == check, "detail"]
        return val.iloc[0] if len(val) else ""

    report = f"""# ROOT/PyROOT Environment Check

## Python

- Executable: `{sys.executable}`
- Version: `{sys.version.split()[0]}`
- Conda environment: `{os.environ.get('CONDA_DEFAULT_ENV', 'not detected')}`
- Conda prefix: `{os.environ.get('CONDA_PREFIX', 'not detected')}`

## PyROOT

Status: **{'available' if pyroot_ok else 'not available'}**

```text
{pyroot_detail}
```

## Command-Line Tools

| check | status |
|---|---|
{chr(10).join(f"| {r.check} | {r.status} |" for r in df.itertuples() if r.check not in {'python_executable','python_version','platform','conda_default_env','conda_prefix','import_ROOT'})}

## Docker

```text
docker --version:
{detail('docker_version')}

docker info:
{detail('docker_info')}
```

## WSL

```text
wsl --status:
{detail('wsl_status')}

wsl -l -v:
{detail('wsl_list_verbose')}
```

## Logs

- `results/logs/root_pyroot_environment_check.log`
- `results/tables/root_pyroot_environment_check.csv`
"""
    (ROUTE_REPORTS / "ROOT_PYROOT_ENVIRONMENT_CHECK.md").write_text(report, encoding="utf-8")
    print(f"Wrote {ROUTE_REPORTS / 'ROOT_PYROOT_ENVIRONMENT_CHECK.md'}")
    print(f"Wrote {LOGS / 'root_pyroot_environment_check.log'}")


if __name__ == "__main__":
    main()
