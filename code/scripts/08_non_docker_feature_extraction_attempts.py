from __future__ import annotations

import shutil
import subprocess
import sys
import traceback

import pandas as pd

from real_collision_common import LOGS, REPORTS, TABLES, ensure_dirs


READ_TESTS = TABLES / "candidate_branch_read_tests.csv"


def command_result(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except Exception as exc:
        return False, repr(exc)


def main() -> None:
    ensure_dirs()
    tests = pd.read_csv(READ_TESTS)
    group_summary = (
        tests.groupby("candidate_group", as_index=False)
        .agg(tested=("candidate_name", "count"), readable=("success", "sum"), extractable=("could_support_real_extraction", "sum"))
        .sort_values("candidate_group")
    )

    pyroot_ok = False
    pyroot_msg = ""
    try:
        import ROOT  # type: ignore

        pyroot_ok = True
        pyroot_msg = f"import ROOT succeeded: {ROOT.gROOT.GetVersion()}"
    except Exception as exc:
        pyroot_msg = f"import ROOT failed: {repr(exc)}"

    root_cmd = shutil.which("root") or shutil.which("root.exe")
    root_ok = bool(root_cmd)
    root_msg = f"ROOT command found: {root_cmd}" if root_cmd else "ROOT command not found on PATH"
    if root_cmd:
        ok, out = command_result([root_cmd, "-b", "-q"])
        root_msg += f"\nMinimal command success={ok}\n{out[:1000]}"

    route_notes = []
    def readable(group: str) -> int:
        return int(group_summary.loc[group_summary["candidate_group"] == group, "readable"].sum())

    route_notes.append(f"Route A - uproot direct arrays: readable groups include jets={readable('jets')}, packed_candidates={readable('packed_candidates')}, vertices={readable('vertices')}.")
    route_notes.append("Route B - uproot branch/leaf decomposition: promising for jet leaves, packed-candidate dxy/dz leaves, and primary-vertex leaves.")
    route_notes.append(f"Route C - PyROOT availability: {pyroot_msg}")
    route_notes.append("Route D - conda ROOT suggestion: PyROOT is not installed in the current Python environment. Conda ROOT could be tried later as a non-Docker route, but it was not installed automatically.")
    route_notes.append(f"Route E - ROOT command line: {root_msg}")
    (LOGS / "non_docker_extraction_strategy_checks.log").write_text("\n\n".join(route_notes), encoding="utf-8")

    can_met = bool(tests[(tests["candidate_group"] == "met") & (tests["success"] == True) & ~tests["candidate_name"].str.endswith(".present", na=False)].shape[0])
    can_mu = bool(tests[(tests["candidate_group"] == "muons") & (tests["success"] == True) & ~tests["candidate_name"].str.endswith(".present", na=False)].shape[0])
    can_el = bool(tests[(tests["candidate_group"] == "electrons") & (tests["success"] == True) & ~tests["candidate_name"].str.endswith(".present", na=False)].shape[0])
    can_event = bool(tests[(tests["candidate_group"] == "event_ids") & (tests["success"] == True)].shape[0])
    can_trig = bool(tests[(tests["candidate_group"] == "triggers") & (tests["success"] == True) & ~tests["candidate_name"].str.endswith(".present", na=False)].shape[0])
    can_jets = readable("jets") > 0
    can_tracks = readable("packed_candidates") > 0
    can_vertices = readable("vertices") > 0

    report = f"""# Non-Docker Extraction Strategy Report

## Route Results

{chr(10).join('- ' + note for note in route_notes)}

## Candidate Readability Summary

{group_summary.to_markdown(index=False)}

## Answers

1. Can we extract MET without Docker?

   Current evidence: {'yes' if can_met else 'no'}. `slimmedMETs` exists, but generic uproot only read the product-present flag, not MET pt/phi.

2. Can we extract muons/electrons without Docker?

   Current evidence: {'yes' if (can_mu and can_el) else 'no'}. `slimmedMuons` and `slimmedElectrons` exist, but generic uproot only read product-present flags, not pt/eta/counts.

3. Can we extract b-tags without Docker?

   Current evidence: partially. Jet hadron/parton flavour leaves and some user-float structures are readable, but an experimental b-tag discriminator was not identified as a clean scalar branch. Hadron flavour can be labelled as a proxy only, not as a measured b-tag.

4. Can we extract run/lumi/event without Docker?

   Current evidence: {'yes' if can_event else 'no'}. `EventAuxiliary` exists but failed generic uproot deserialisation in the tested environment.

5. Can we extract triggers/filters without Docker?

   Current evidence: partially. Trigger/filter products are visible and present flags are readable, but trigger decisions were not extracted as named decisions. Some filter/noise object branches are visible but not yet physics-ready.

6. Can we construct the full N-Frame boundary score without Docker?

   Current evidence: no. We can improve the visible/reconstruction side using jets, packed-candidate displacement-like leaves, and vertex complexity, but the full score needs MET and event IDs.

7. If not, exactly what remains inaccessible?

   MET pt/phi, muon/electron kinematics or counts, experimental b-tag discriminators, run/lumi/event IDs, named trigger decisions, and CMS-interpreted filter decisions remain inaccessible with the tested non-Docker tools.
"""
    (REPORTS / "NON_DOCKER_EXTRACTION_STRATEGY_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {REPORTS / 'NON_DOCKER_EXTRACTION_STRATEGY_REPORT.md'}")


if __name__ == "__main__":
    main()
