from __future__ import annotations

import traceback
from pathlib import Path

import pandas as pd

from real_collision_common import LOGS, REPORTS, TABLES, ensure_dirs


MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"
INVENTORY = TABLES / "deep_miniaod_combined_branch_inventory.csv"

KEY_PATTERNS = {
    "event_ids": ["EventAuxiliary"],
    "met": ["patMETs_slimmedMETs__PAT"],
    "jets": [
        "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt",
        "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fEta",
        "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi",
        "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fM",
        "patJets_slimmedJets__PAT.obj.jetFlavourInfo_.m_hadronFlavour",
        "patJets_slimmedJets__PAT.obj.jetFlavourInfo_.m_partonFlavour",
        "patJets_slimmedJets__PAT.obj.pairDiscriVector",
        "patJets_slimmedJets__PAT.obj.userFloats_",
    ],
    "muons": ["patMuons_slimmedMuons__PAT"],
    "electrons": ["patElectrons_slimmedElectrons__PAT"],
    "photons": ["patPhotons_slimmedPhotons__PAT"],
    "taus": ["patTaus_slimmedTaus__PAT"],
    "packed_candidates": [
        "patPackedCandidates_packedPFCandidates__PAT.obj.packedPt_",
        "patPackedCandidates_packedPFCandidates__PAT.obj.packedEta_",
        "patPackedCandidates_packedPFCandidates__PAT.obj.packedPhi_",
        "patPackedCandidates_packedPFCandidates__PAT.obj.packedDxy_",
        "patPackedCandidates_packedPFCandidates__PAT.obj.packedDz_",
        "patPackedCandidates_packedPFCandidates__PAT.obj.pdgId_",
        "patPackedCandidates_packedPFCandidates__PAT.obj.qualityFlags_",
    ],
    "vertices": [
        "recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj.position_.fCoordinates.fX",
        "recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj.position_.fCoordinates.fY",
        "recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj.position_.fCoordinates.fZ",
        "recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj.chi2_",
        "recoVertexs_offlineSlimmedPrimaryVertices__PAT.obj.ndof_",
    ],
    "secondary_vertices": ["recoVertexCompositePtrCandidates_slimmedSecondaryVertices__PAT"],
    "triggers": ["edmTriggerResults_TriggerResults__HLT", "edmTriggerResults_TriggerResults__PAT"],
    "filters_quality": ["HcalNoiseSummary_hcalnoise__RECO", "recoBeamHaloSummary_BeamHaloSummary__RECO"],
}


def find_candidates(inv: pd.DataFrame) -> list[tuple[str, str]]:
    pairs = []
    names = inv["full_name"].dropna().drop_duplicates().tolist()
    for group, patterns in KEY_PATTERNS.items():
        group_hits = []
        for pattern in patterns:
            hits = [name for name in names if pattern.lower() in name.lower()]
            group_hits.extend(hits[:8])
        for hit in sorted(set(group_hits)):
            pairs.append((group, hit))
    return pairs


def summarise_array(arr) -> tuple[str, str]:
    try:
        type_text = str(arr.type)
    except Exception:
        type_text = str(type(arr))
    try:
        preview = str(arr[:3])
    except Exception:
        preview = ""
    return type_text, preview[:700]


def test_branch(tree, name: str, group: str) -> dict:
    row = {
        "candidate_group": group,
        "candidate_name": name,
        "read_mode": "exact",
        "success": False,
        "returned_type": "",
        "example_values": "",
        "could_support_real_extraction": False,
        "error": "",
    }
    try:
        arr = tree.arrays([name], entry_start=0, entry_stop=100, library="ak")[name]
        typ, preview = summarise_array(arr)
        row.update(
            {
                "success": True,
                "returned_type": typ,
                "example_values": preview,
                "could_support_real_extraction": True,
            }
        )
    except Exception as exc:
        row["error"] = repr(exc)
    return row


def main() -> None:
    ensure_dirs()
    import uproot

    inv = pd.read_csv(INVENTORY)
    manifest = pd.read_csv(MANIFEST)
    first = Path(manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)].iloc[0]["local_path"])
    pairs = find_candidates(inv[inv["source_file"] == first.name])
    rows = []
    logs = [f"Testing first file: {first}"]
    with uproot.open(first) as root_file:
        tree = root_file["Events"]
        for group, name in pairs:
            result = test_branch(tree, name, group)
            rows.append(result)
            logs.append(f"{group} :: {name} :: success={result['success']} :: {result['returned_type'] or result['error']}")

        # Also try wildcard group reads for object roots.
        for group, pattern in [
            ("met", "patMETs_slimmedMETs__PAT*"),
            ("muons", "patMuons_slimmedMuons__PAT*"),
            ("electrons", "patElectrons_slimmedElectrons__PAT*"),
            ("triggers", "edmTriggerResults_TriggerResults__HLT*"),
        ]:
            row = {
                "candidate_group": group,
                "candidate_name": pattern,
                "read_mode": "filter_name",
                "success": False,
                "returned_type": "",
                "example_values": "",
                "could_support_real_extraction": False,
                "error": "",
            }
            try:
                arrs = tree.arrays(filter_name=pattern, entry_start=0, entry_stop=100, library="ak")
                row["success"] = len(arrs.fields) > 0
                row["returned_type"] = "; ".join(f"{field}: {arrs[field].type}" for field in arrs.fields[:10])
                row["example_values"] = str({field: str(arrs[field][:2])[:200] for field in arrs.fields[:5]})[:700]
                row["could_support_real_extraction"] = row["success"]
            except Exception as exc:
                row["error"] = repr(exc)
                logs.append(traceback.format_exc())
            rows.append(row)
            logs.append(f"{group} :: {pattern} :: success={row['success']} :: {row['returned_type'] or row['error']}")

    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "candidate_branch_read_tests.csv", index=False)
    (LOGS / "candidate_branch_read_tests.log").write_text("\n".join(logs), encoding="utf-8")

    summary = (
        out.groupby("candidate_group", as_index=False)
        .agg(tested=("candidate_name", "count"), readable=("success", "sum"), potentially_extractable=("could_support_real_extraction", "sum"))
        .sort_values("candidate_group")
    )
    report = f"""# Candidate Branch Readability Report

## Test Scope

Tested candidate branches on one representative real CMS MiniAOD file:

`{first}`

Each candidate was read for the first 100 events using uproot exact branch reads or wildcard/filter reads.

## Summary

{summary.to_markdown(index=False)}

## Interpretation

Readable groups with simple numeric jagged leaves can support non-Docker extraction. Object-only CMS EDM branches may be present by name but still not useful if generic uproot cannot deserialize them into physics quantities.

Detailed results are in:

`{TABLES / 'candidate_branch_read_tests.csv'}`
"""
    (REPORTS / "CANDIDATE_BRANCH_READABILITY_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {TABLES / 'candidate_branch_read_tests.csv'}")
    print(f"Wrote {REPORTS / 'CANDIDATE_BRANCH_READABILITY_REPORT.md'}")


if __name__ == "__main__":
    main()
