from __future__ import annotations

from pathlib import Path
import traceback

import pandas as pd

from real_collision_common import INTERIM, LOGS, REPORTS, TABLES, ensure_dirs


ROUTE_REPORTS = REPORTS / "non_docker_cms_aware_route"
MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"


TARGETS = ["slimmedMETs", "slimmedJets", "slimmedMuons", "slimmedElectrons", "TriggerResults", "EventAuxiliary"]


def representative_files() -> pd.DataFrame:
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)]
    return manifest.sort_values(["sample_id", "file_name"]).groupby("sample_id", as_index=False).first()


def main() -> None:
    ensure_dirs()
    ROUTE_REPORTS.mkdir(parents=True, exist_ok=True)
    rows = []
    logs = []
    try:
        import ROOT  # type: ignore
    except Exception as exc:
        msg = f"PyROOT unavailable: {repr(exc)}"
        (LOGS / "pyroot_miniaod_reading.log").write_text(msg, encoding="utf-8")
        pd.DataFrame([{"sample_id": "", "source_file": "", "test": "import_ROOT", "success": False, "detail": msg}]).to_csv(
            TABLES / "pyroot_miniaod_branch_read_tests.csv", index=False
        )
        (ROUTE_REPORTS / "PYROOT_MINIAOD_READING_REPORT.md").write_text(
            f"# PyROOT MiniAOD Reading Report\n\nPyROOT is not available in the current Python environment.\n\n```text\n{msg}\n```\n",
            encoding="utf-8",
        )
        print(msg)
        return

    for _, row in representative_files().iterrows():
        path = Path(row["local_path"])
        sample_id = row["sample_id"]
        logs.append(f"=== {sample_id}: {path} ===")
        try:
            root_file = ROOT.TFile.Open(str(path))
            ok_file = bool(root_file and not root_file.IsZombie())
            tree = root_file.Get("Events") if ok_file else None
            rows.append({"sample_id": sample_id, "source_file": path.name, "test": "TFile.Open", "success": ok_file, "detail": ""})
            rows.append({"sample_id": sample_id, "source_file": path.name, "test": "Events tree", "success": bool(tree), "detail": f"entries={tree.GetEntries() if tree else ''}"})
            if tree:
                branch_names = [b.GetName() for b in tree.GetListOfBranches()]
                for target in TARGETS:
                    hits = [name for name in branch_names if target.lower() in name.lower()]
                    rows.append({"sample_id": sample_id, "source_file": path.name, "test": f"branch_search_{target}", "success": bool(hits), "detail": ";".join(hits[:20])})
                for i in range(min(10, tree.GetEntries())):
                    status = tree.GetEntry(i)
                    if i == 0:
                        rows.append({"sample_id": sample_id, "source_file": path.name, "test": "GetEntry_first", "success": status > 0, "detail": f"GetEntry returned {status}"})
            if root_file:
                root_file.Close()
        except Exception as exc:
            rows.append({"sample_id": sample_id, "source_file": path.name, "test": "pyroot_exception", "success": False, "detail": repr(exc)})
            logs.append(traceback.format_exc())

    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "pyroot_miniaod_branch_read_tests.csv", index=False)
    (LOGS / "pyroot_miniaod_reading.log").write_text("\n".join(logs), encoding="utf-8")
    report = f"""# PyROOT MiniAOD Reading Report

PyROOT imported successfully.

Branch-level tests were run on one file from each real sample. Generic PyROOT can inspect ROOT branch names if dictionaries are sufficient, but CMS EDM object access may still require FWLite/CMSSW dictionaries.

## Test Summary

{out.to_markdown(index=False)}
"""
    (ROUTE_REPORTS / "PYROOT_MINIAOD_READING_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {TABLES / 'pyroot_miniaod_branch_read_tests.csv'}")


if __name__ == "__main__":
    main()
