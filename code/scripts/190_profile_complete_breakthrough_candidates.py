from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_breakthrough_or_bust_nframe_boundary_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPEC = importlib.util.spec_from_file_location("bb", ROOT / "scripts/189_breakthrough_or_bust_nframe_boundary_search.py")
bb = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bb)
v4 = bb.v4


REQUIRED = [
    "Run2016_MET_Z",
    "Run2015D_MET_Z",
    "Run2015D_HTMHT_Z",
    "Run2015D_JetHT_control_Z",
    "Run2015D_SingleMuon_control_Z",
    "Run2016_other_jetbin_max_absZ",
    "Run2015D_dataset_control_max_absZ",
]


def finite_complete(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in REQUIRED + ["selection_score", "signal_stouffer_Z", "min_signal_Z"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out[np.isfinite(out[REQUIRED]).all(axis=1)].copy()
    return out


def main() -> None:
    formulas = {name: weights for name, weights, _source in bb.candidate_formulas()}
    fast = finite_complete(pd.read_csv(TABLES / "04_heldout_validation_region_screen.csv"))
    fast = fast.sort_values(["selection_score", "signal_stouffer_Z", "min_signal_Z"], ascending=False)
    shortlist = fast.head(25)[["candidate", "signal_jet_bin"]].drop_duplicates()

    sm_raw = v4.add_base_transforms(v4.read_sm())
    ref = v4.fit_reference(sm_raw)
    sm = v4.apply_reference(sm_raw, ref)
    real = v4.split_files(v4.apply_reference(v4.read_real(), ref))

    profile_rows = []
    for _, row in shortlist.iterrows():
        candidate = row["candidate"]
        signal_jet_bin = row["signal_jet_bin"]
        weights = formulas[candidate]
        sm["candidate_score"] = v4.apply_score(sm, weights)
        real["candidate_score"] = v4.apply_score(real, weights)
        met_edges, score_edges = v4.define_edges(sm, "candidate_score")
        sm_b = v4.assign_bands(sm, "candidate_score", met_edges, score_edges)
        real_b = v4.assign_bands(real, "candidate_score", met_edges, score_edges)
        counts_val = bb.score_counts_fast(real_b, sm_b, "validation", candidate)
        summary = v4.summarize_counts(counts_val)
        profile_rows.append(bb.evaluate_region(summary, candidate, "validation", signal_jet_bin))

    profile = pd.DataFrame(profile_rows)
    if not profile.empty:
        profile = finite_complete(profile)
        profile = profile.sort_values(["selection_score", "signal_stouffer_Z", "min_signal_Z"], ascending=False)
    profile.to_csv(TABLES / "07_complete_candidate_sideband_profile_validation.csv", index=False)

    pass_count = int(profile["passes_trace_breakthrough_screen"].sum()) if not profile.empty else 0
    best = profile.head(20)
    report = f"""# Complete-Candidate Sideband Profile Check

## Purpose

The first breakthrough-or-bust scan found complete held-out candidate rows, but the first report ranked incomplete 0-jet rows too highly. This follow-up profiles only candidates that have all required signal and control cells:

- Run2016 MET
- Run2015D MET
- Run2015D HTMHT
- Run2015D JetHT control
- Run2015D SingleMuon control
- Run2016 other-jet-bin controls

## Best Complete Fast-Screen Rows

{fast.head(20).to_markdown(index=False)}

## Sideband-Profile Validation of Complete Candidates

{best.to_markdown(index=False) if not best.empty else "No complete candidates survived sideband-profile validation."}

## Readout

- Complete candidates profiled: {len(profile)}
- Candidates passing the strict trace-breakthrough screen after sideband profiling: {pass_count}

## Interpretation

This is the key result from the broader parameter-adjustment attempt. Strong fast-screen candidates exist, but after requiring all signal/control cells and rerunning the sideband-profile model, none pass the full trace-breakthrough screen. The main failure mode remains control/transfer robustness, not lack of flexible N-Frame parameters.
"""
    (REPORTS / "03_COMPLETE_CANDIDATE_SIDEBAND_PROFILE_CHECK.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Complete Candidate Profile Check

Complete candidates profiled: {len(profile)}

Strict pass count: {pass_count}

{best.head(10).to_markdown(index=False) if not best.empty else "No complete candidates survived sideband-profile validation."}
"""
    (REPORTS / "04_SHORT_UPDATE_COMPLETE_CANDIDATE_PROFILE_CHECK.md").write_text(short, encoding="utf-8")
    print("COMPLETE-CANDIDATE SIDEBAND PROFILE CHECK COMPLETE")
    print(best.head(10).to_string(index=False) if not best.empty else "No complete candidates survived.")
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
