from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path("D:/cern_open_data/cms_met_run2016g_miniaod_10gb")


def yes_no(path):
    return "yes" if Path(path).exists() else "no"


def main():
    roots = sorted(DATA_PATH.rglob("*.root"))
    total_gb = sum(p.stat().st_size for p in roots) / 1e9
    scored = ROOT / "data" / "processed" / "event_features_nframe_scored.csv"
    n_events = 0
    status = "CMSSW extraction was not completed in this environment."
    met_status = jets_status = lepton_status = btag_status = "not tested"
    if scored.exists():
        df = pd.read_csv(scored)
        n_events = len(df)
        status = "CMSSW event table and N-Frame score were produced."
        met_status = "yes" if (df.MET_pt > 0).any() else "all zero"
        jets_status = "yes" if (df.N_jets_30 >= 0).all() else "invalid"
        lepton_status = "yes" if "N_leptons" in df else "missing"
        btag_status = "yes" if (df.N_btags_medium > 0).any() else "zero_or_unresolved"
    pseudo = ROOT / "results" / "tables" / "pseudo_signal_regions_from_cmssw.csv"
    pseudo_text = pd.read_csv(pseudo).to_string(index=False) if pseudo.exists() else "Pseudo signal regions not produced."
    text = f"""# N-Frame CMSSW Event-Level Summary

## Dataset

- Local data path: `{DATA_PATH}`
- ROOT files: {len(roots)}
- Total size: {total_gb:.3f} GB
- Events processed: {n_events}

## Extraction Status

{status}

- event_features.csv: {yes_no(ROOT / 'data' / 'processed' / 'event_features.csv')}
- event_features_nframe_scored.csv: {yes_no(scored)}
- MET extracted: {met_status}
- jets extracted: {jets_status}
- muons/electrons extracted: {lepton_status}
- b-tags extracted: {btag_status}

## Boundary Score

`B_event = z(MET_pt) + z(HT) + z(N_jets_30) + z(N_leptons) + z(N_btags_medium) + z(MET_fraction) + z(S_event_proxy)`

Component scores:

- `R_missing = z_MET + z_MET_fraction + high_MET`
- `R_multiplicity = z_Njets + z_Nleptons + z_Nbtags + high_multiplicity`
- `R_reconstruction = z_MET_fraction + z_S_event + z(N_objects)`

## Pseudo Signal Regions

```text
{pseudo_text}
```

## Limitations

- No Standard Model background comparison.
- No SUSY claim.
- No hidden-symmetry claim.
- 10 GB MiniAOD subset only.
- MET dataset trigger bias is expected.
- No luminosity or background weighting.

Correct conclusion:

The CMS MiniAOD subset was used to construct event-level N-Frame boundary-access variables from reconstructed event objects only if the CMSSW event files exist above. This demonstrates event-level feasibility but does not constitute a search for supersymmetry or hidden symmetry.
"""
    (ROOT / "results" / "nframe_cmssw_event_level_summary.md").write_text(text, encoding="utf-8")
    print(f"Wrote {ROOT / 'results' / 'nframe_cmssw_event_level_summary.md'}")


if __name__ == "__main__":
    main()
