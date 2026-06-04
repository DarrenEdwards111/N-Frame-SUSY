import argparse
from pathlib import Path

import pandas as pd

from common import FILELIST_DIR, PROCESSED_DIR, RESULTS_DIR, TABLES_DIR, LOGS_DIR, ensure_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the MiniAOD event-level N-Frame summary.")
    parser.add_argument("--features", default=str(PROCESSED_DIR / "event_features_nframe_scored.parquet"))
    parser.add_argument("--output", default=str(RESULTS_DIR / "nframe_miniaod_event_level_summary.md"))
    args = parser.parse_args()

    ensure_dirs()
    filelist = FILELIST_DIR / "miniaod_files.txt"
    files = [Path(line.strip()) for line in filelist.read_text(encoding="utf-8").splitlines() if line.strip()] if filelist.exists() else []
    total_gb = sum(path.stat().st_size for path in files if path.exists()) / 1e9
    inspect_text = (LOGS_DIR / "root_file_structure.txt").read_text(encoding="utf-8") if (LOGS_DIR / "root_file_structure.txt").exists() else ""
    features_path = Path(args.features)
    processed = False
    n_events = 0
    columns = []
    if features_path.exists():
        if features_path.suffix.lower() == ".parquet":
            df = pd.read_parquet(features_path)
        else:
            df = pd.read_csv(features_path)
        processed = True
        n_events = len(df)
        columns = list(df.columns)
        extraction_modes = ", ".join(sorted(df["extraction_mode"].dropna().astype(str).unique())) if "extraction_mode" in df else "unknown"
        score_status = ", ".join(sorted(df["B_event_status"].dropna().astype(str).unique())) if "B_event_status" in df else "unknown"
        full_available = int(df["full_boundary_features_available"].max()) if "full_boundary_features_available" in df else 0
        missing_met = float(df["MET_pt"].isna().mean()) if "MET_pt" in df else 1.0
        missing_leptons = float(df["N_leptons"].isna().mean()) if "N_leptons" in df else 1.0
        missing_btags = float(df["N_btags_medium"].isna().mean()) if "N_btags_medium" in df else 1.0
    else:
        extraction_modes = "none"
        score_status = "none"
        full_available = 0
        missing_met = 1.0
        missing_leptons = 1.0
        missing_btags = 1.0
    pseudo = TABLES_DIR / "pseudo_signal_region_summary.csv"
    if pseudo.exists():
        pseudo_text = "```text\n" + pd.read_csv(pseudo).to_string(index=False) + "\n```"
    else:
        pseudo_text = "Pseudo-SR table not produced."

    if processed and full_available:
        claim = "Full event-level N-Frame boundary variables were extracted from readable event branches."
    elif processed:
        claim = (
            "A real, testable jet-level event feature table was extracted from CMS MiniAOD with uproot. "
            "MET, lepton counts, and true b-tag discriminators remain unavailable in this Python-only EDM readout, "
            "so the full event-level N-Frame score still requires the included CMSSW analyzer."
        )
    elif "MiniAOD requires CMSSW/FWLite analyzer" in inspect_text:
        claim = "MiniAOD requires CMSSW and an analyzer was prepared but not fully executed."
    else:
        claim = "The available 10GB subset is useful for constructing B_event, but extraction status is incomplete."

    markdown = f"""# N-Frame Event-Level Boundary-Access Analysis using CMS 2016G MiniAOD

## Data

- Input path: `D:/cern_open_data/cms_met_run2016g_miniaod_10gb`
- ROOT files found: {len(files)}
- Total ROOT size: {total_gb:.3f} GB
- Events processed: {n_events}

## Extraction Status

{claim}

The inspection log is at `results/logs/root_file_structure.txt`.

- Extraction modes: `{extraction_modes}`
- Score status: `{score_status}`
- Full boundary feature flag: `{full_available}`
- Missing MET fraction: {missing_met:.3f}
- Missing lepton-count fraction: {missing_leptons:.3f}
- Missing b-tag fraction: {missing_btags:.3f}

## Variables

Extracted/scored columns:

`{', '.join(columns) if columns else 'No flat event feature table was produced in this environment.'}`

## Boundary Score

`MET_fraction = MET_pt / (HT + MET_pt + 1)`

`S_event_proxy = log(1 + N_jets_30 + N_leptons + N_btags_medium)`

`B_event_jetonly = z(HT) + z(N_jets_30) + z(N_jets_50) + z(S_event_proxy)`

`B_event` includes only available extracted components. In the current uproot EDM extraction this is a partial jet-level score because MET, leptons, and true b-tags are not readable from the MiniAOD objects without CMSSW/FWLite.

Missing MET, lepton, and b-tag information is recorded in the feature/status columns rather than silently filled as observed physics.

## Pseudo Signal Regions

{pseudo_text}

## Interpretation

This MiniAOD subset is used to construct event-level N-Frame boundary-access variables directly from reconstructed CMS event objects where possible. The analysis does not test for supersymmetry directly and does not constitute a full CMS search reinterpretation. It demonstrates the feasibility status of computing `B_event` from real event-level data and using it to classify events by missing information, visible activity, multiplicity, and reconstruction complexity.

Do not interpret high-boundary events as SUSY candidates.
"""
    Path(args.output).write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
