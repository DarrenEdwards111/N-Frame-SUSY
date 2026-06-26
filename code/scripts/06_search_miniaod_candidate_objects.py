from __future__ import annotations

import re

import pandas as pd

from real_collision_common import REPORTS, TABLES, ensure_dirs


INVENTORY = TABLES / "deep_miniaod_combined_branch_inventory.csv"

GROUPS = {
    "event_identifiers": ["run", "lumi", "luminosity", "event", "eventAuxiliary", "EventAuxiliary"],
    "met": ["met", "MET", "slimmedMETs", "patMET", "recoPFMET", "pfMET", "missing"],
    "jets_btags": ["jet", "slimmedJets", "patJets", "AK4", "btag", "bDiscriminator", "hadronFlavour", "partonFlavour", "csv", "deepcsv", "deepFlavour"],
    "muons": ["muon", "slimmedMuons", "patMuons"],
    "electrons": ["electron", "slimmedElectrons", "patElectrons", "gsfElectron"],
    "photons": ["photon", "slimmedPhotons"],
    "taus": ["tau", "slimmedTaus"],
    "tracks_vertices_displacement": [
        "packedPFCandidates",
        "lostTracks",
        "offlineSlimmedPrimaryVertices",
        "secondaryVertices",
        "vertex",
        "track",
        "dxy",
        "dz",
        "displaced",
        "lifetime",
    ],
    "triggers": ["TriggerResults", "HLT", "trigger", "patTrigger", "triggerObjects", "slimmedPatTrigger"],
    "filters_quality": ["Flag", "filter", "noise", "HBHE", "beamHalo", "badMuon", "ecal", "METFilters"],
}


def classify(text: str) -> list[tuple[str, str]]:
    found = []
    for group, tokens in GROUPS.items():
        for token in tokens:
            if re.search(re.escape(token), text, flags=re.IGNORECASE):
                found.append((group, token))
    return found


def yes_no(df: pd.DataFrame, group: str) -> str:
    return "yes" if (df["candidate_group"] == group).any() else "no"


def examples(df: pd.DataFrame, group: str, n: int = 12) -> str:
    vals = df.loc[df["candidate_group"] == group, "full_name"].drop_duplicates().head(n).tolist()
    return "\n".join(f"- `{v}`" for v in vals) if vals else "- none found"


def main() -> None:
    ensure_dirs()
    inv = pd.read_csv(INVENTORY)
    rows = []
    for _, row in inv.iterrows():
        text = " ".join(str(row.get(col, "")) for col in ["branch_name", "leaf_name", "full_name", "typename", "interpretation"])
        for group, token in classify(text):
            out = row.to_dict()
            out["candidate_group"] = group
            out["matched_token"] = token
            rows.append(out)
    candidates = pd.DataFrame(rows).drop_duplicates()
    candidates.to_csv(TABLES / "candidate_miniaod_objects_found.csv", index=False)

    summary = (
        candidates.groupby("candidate_group", as_index=False)
        .agg(
            rows=("full_name", "count"),
            unique_full_names=("full_name", "nunique"),
            files=("source_file", "nunique"),
            samples=("sample_id", "nunique"),
        )
        .sort_values("candidate_group")
        if not candidates.empty
        else pd.DataFrame(columns=["candidate_group", "rows", "unique_full_names", "files", "samples"])
    )
    summary_md = summary.to_markdown(index=False)

    report = f"""# Deep MiniAOD Object Search Report

## Summary

Candidate branches/leaves were searched in the combined deep MiniAOD inventory.

{summary_md}

## MET Candidates

MET candidate branches/leaves exist: {yes_no(candidates, 'met')}.

Examples:

{examples(candidates, 'met')}

## Muon/Electron Candidates

Muon candidate branches/leaves exist: {yes_no(candidates, 'muons')}.

{examples(candidates, 'muons')}

Electron candidate branches/leaves exist: {yes_no(candidates, 'electrons')}.

{examples(candidates, 'electrons')}

## Jet And B-Tag Candidates

Jet/b-tag candidate branches/leaves exist: {yes_no(candidates, 'jets_btags')}.

{examples(candidates, 'jets_btags', 20)}

The inventory includes jet kinematic leaves and hadron/parton flavour leaves. It also includes `pairDiscriVector`, but generic uproot readability must be tested before treating it as an experimental b-tag discriminator.

## Event IDs

Event identifier candidates exist: {yes_no(candidates, 'event_identifiers')}.

{examples(candidates, 'event_identifiers')}

The key candidate is `EventAuxiliary`, but previous quick testing showed it is not trivially readable with uproot due to CMS EDM serialisation.

## Triggers And Filters

Trigger/filter candidates exist: {yes_no(candidates, 'triggers')} / {yes_no(candidates, 'filters_quality')}.

Trigger examples:

{examples(candidates, 'triggers')}

Filter/quality examples:

{examples(candidates, 'filters_quality')}

## Displacement/Lifetime-Related Candidates

Displacement/track/vertex candidates exist: {yes_no(candidates, 'tracks_vertices_displacement')}.

{examples(candidates, 'tracks_vertices_displacement', 20)}

Packed candidate `dxy`/`dz` and vertex leaves are visible by name. These are candidate displacement-related inputs, but they need readability and interpretation checks before being used as an N-Frame lifetime/displacement component.

## Most Promising Extraction Route

The most promising non-Docker route is uproot branch/leaf decomposition for simple numeric leaves:

- jet kinematic leaves
- jet hadron/parton flavour leaves
- packed candidate pt/eta/phi/dxy/dz leaves
- primary vertex position/quality leaves

MET, muons, electrons, triggers, and event IDs appear present as CMS EDM object branches, but may require CMS-aware deserialisation. Phase 3 readability tests decide this.
"""
    (REPORTS / "DEEP_MINIAOD_OBJECT_SEARCH_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {TABLES / 'candidate_miniaod_objects_found.csv'}")
    print(f"Wrote {REPORTS / 'DEEP_MINIAOD_OBJECT_SEARCH_REPORT.md'}")


if __name__ == "__main__":
    main()
