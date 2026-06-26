from __future__ import annotations

from pathlib import Path
import traceback

import pandas as pd

from real_collision_common import INTERIM, LOGS, REPORTS, TABLES, ensure_dirs


ROUTE_REPORTS = REPORTS / "non_docker_cms_aware_route"
MANIFEST = TABLES / "real_collision_20gb_manifest_validated.csv"


BTAG_NAME = "pfCombinedInclusiveSecondaryVertexV2BJetTags"


def representative_files() -> pd.DataFrame:
    manifest = pd.read_csv(MANIFEST)
    manifest = manifest[(manifest["validation_status"] == "valid") & (manifest["is_real_collision"] == True)]
    return manifest.sort_values(["sample_id", "file_name"]).groupby("sample_id", as_index=False).first()


def main() -> None:
    ensure_dirs()
    ROUTE_REPORTS.mkdir(parents=True, exist_ok=True)
    logs = []
    try:
        import ROOT  # type: ignore
        ROOT.gSystem.Load("libFWCoreFWLite")
        ROOT.gSystem.Load("libDataFormatsFWLite")
        ROOT.FWLiteEnabler.enable()
        from DataFormats.FWLite import Events, Handle  # type: ignore
    except Exception as exc:
        msg = "FWLite unavailable in current environment:\n" + repr(exc)
        (LOGS / "fwlite_test_unavailable.log").write_text(msg + "\n" + traceback.format_exc(), encoding="utf-8")
        (ROUTE_REPORTS / "FWLITE_TEST_EXTRACTION_REPORT.md").write_text(
            f"# FWLite Test Extraction Report\n\nFWLite is not available in the current environment.\n\n```text\n{msg}\n```\n",
            encoding="utf-8",
        )
        print(msg)
        return

    all_status = []
    for _, sample in representative_files().iterrows():
        sample_id = sample["sample_id"]
        path = sample["local_path"]
        out_rows = []
        log_path = LOGS / f"fwlite_test_{sample_id}.log"
        try:
            events = Events([path])
            handles = {
                "mets": (Handle("std::vector<pat::MET>"), "slimmedMETs"),
                "jets": (Handle("std::vector<pat::Jet>"), "slimmedJets"),
                "muons": (Handle("std::vector<pat::Muon>"), "slimmedMuons"),
                "electrons": (Handle("std::vector<pat::Electron>"), "slimmedElectrons"),
                "vertices": (Handle("std::vector<reco::Vertex>"), "offlineSlimmedPrimaryVertices"),
            }
            for idx, event in enumerate(events):
                if idx >= 1000:
                    break
                row = {
                    "sample_id": sample_id,
                    "primary_dataset": sample["primary_dataset"],
                    "source_file": Path(path).name,
                    "event_index": idx,
                    "run": event.eventAuxiliary().run(),
                    "lumi": event.eventAuxiliary().luminosityBlock(),
                    "event": event.eventAuxiliary().event(),
                    "MET_pt": None,
                    "MET_phi": None,
                    "N_jets": None,
                    "N_jets_30": None,
                    "N_jets_50": None,
                    "HT": None,
                    "leading_jet_pt": None,
                    "subleading_jet_pt": None,
                    "N_muons": None,
                    "N_electrons": None,
                    "N_btags_loose": None,
                    "N_btags_medium": None,
                    "max_btag_discriminator": None,
                    "N_primary_vertices": None,
                    "packed_candidate_count": None,
                    "lost_track_count": None,
                    "secondary_vertex_count": None,
                    "extraction_limitations": "FWLite 1000-event test",
                }
                for key, (handle, label) in handles.items():
                    try:
                        event.getByLabel(label, handle)
                    except Exception:
                        continue
                    product = handle.product()
                    if key == "mets" and len(product):
                        row["MET_pt"] = product[0].pt()
                        row["MET_phi"] = product[0].phi()
                    elif key == "jets":
                        pts = [j.pt() for j in product if abs(j.eta()) < 2.4]
                        row["N_jets"] = len(pts)
                        row["N_jets_30"] = sum(p > 30 for p in pts)
                        row["N_jets_50"] = sum(p > 50 for p in pts)
                        row["HT"] = sum(p for p in pts if p > 30)
                        pts_sorted = sorted(pts, reverse=True)
                        row["leading_jet_pt"] = pts_sorted[0] if pts_sorted else None
                        row["subleading_jet_pt"] = pts_sorted[1] if len(pts_sorted) > 1 else None
                        btags = []
                        for jet in product:
                            try:
                                btags.append(jet.bDiscriminator(BTAG_NAME))
                            except Exception:
                                pass
                        if btags:
                            row["N_btags_loose"] = sum(b > 0.5426 for b in btags)
                            row["N_btags_medium"] = sum(b > 0.8484 for b in btags)
                            row["max_btag_discriminator"] = max(btags)
                    elif key == "muons":
                        row["N_muons"] = sum(mu.pt() > 10 and abs(mu.eta()) < 2.4 for mu in product)
                    elif key == "electrons":
                        row["N_electrons"] = sum(el.pt() > 10 and abs(el.eta()) < 2.5 for el in product)
                    elif key == "vertices":
                        row["N_primary_vertices"] = len(product)
                out_rows.append(row)
            df = pd.DataFrame(out_rows)
            out_path = INTERIM / f"fwlite_test_real_collision_{sample_id}_fwlite_test_events.csv"
            df.to_csv(out_path, index=False)
            all_status.append({"sample_id": sample_id, "success": not df.empty, "rows": len(df), "output": str(out_path)})
            log_path.write_text(f"FWLite test wrote {len(df)} rows\n", encoding="utf-8")
        except Exception as exc:
            all_status.append({"sample_id": sample_id, "success": False, "rows": 0, "output": "", "error": repr(exc)})
            log_path.write_text(traceback.format_exc(), encoding="utf-8")

    status = pd.DataFrame(all_status)
    report = f"""# FWLite Test Extraction Report

FWLite imported successfully and a 1000-event extraction test was attempted on one file from each real sample.

{status.to_markdown(index=False)}
"""
    (ROUTE_REPORTS / "FWLITE_TEST_EXTRACTION_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {ROUTE_REPORTS / 'FWLITE_TEST_EXTRACTION_REPORT.md'}")


if __name__ == "__main__":
    main()
