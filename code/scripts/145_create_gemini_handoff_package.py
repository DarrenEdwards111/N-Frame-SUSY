from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "GEMINI_HANDOFF"
TABLES_DIR = HANDOFF / "tables"
REPORTS_COPY_DIR = HANDOFF / "key_reports_copied"
FIGURES_DIR = HANDOFF / "figures_if_any"
DATE = "2026-06-10"


FROZEN_EQUATION = """B_NF_fitted =
0.3566*P_displacement_proxy
+ 0.2112*P_reconstruction
+ 0.2019*P_multiplicity
+ 0.0926*P_btag_structure
+ 0.0728*P_visible_energy
+ 0.0595*P_missing
+ 0.0055*P_compression"""


KEY_REPORTS = [
    "UPDATE_TO_DARREN_POST_SIGNAL_PARITY_STRONGER_TESTS.md",
    "FULL_COMPONENT_SIGNAL_SIDE_PARITY_SYNTHESIS.md",
    "UPDATE_TO_DARREN_FULL_COMPONENT_SIGNAL_SIDE_PARITY.md",
    "INTEGRATED_POST_SIGNAL_PARITY_STRONGER_TESTS_SYNTHESIS.md",
    "INTEGRATED_SIGNAL_BACKGROUND_PARITY_AFTER_UPDATES_REPORT.md",
    "REAL_DATA_SIDEBAND_CONTROL_AFTER_SIGNAL_PARITY_REPORT.md",
    "STRICT_ARTIFACT_SYSTEMATICS_AFTER_SIGNAL_PARITY_REPORT.md",
    "FULLER_COMPONENT_BENCHMARK_SYNTHESIS.md",
    "EXPANDED_BENCHMARK_AND_TRACE_ROBUSTNESS_SYNTHESIS.md",
    "REAL_DATA_TRACE_ALIGNMENT_SYNTHESIS.md",
    "REAL_TRACE_CANDIDATE_SANITY_CHECK_SYNTHESIS.md",
    "FIVE_SIGMA_MODEL_DEPENDENT_BOUNDARY_ENRICHMENT_REPORT.md",
    "PUBLISHED_SIGNAL_REGION_OVERLAP_AFTER_SIGNAL_PARITY_REPORT.md",
    "UPDATED_MASTER_AUDIT_AFTER_SIGNAL_PARITY.md",
    "CURRENT_FULLER_COMPONENT_STATE_AUDIT.md",
    "FULL_COMPONENT_SIGNAL_VS_QCD_COMPARISON_REPORT.md",
    "FULL_COMPONENT_REAL_TRACE_ALIGNMENT_REPORT.md",
]

KEY_TABLES = [
    "bnf_thresholds_real_and_sm.csv",
    "updated_master_audit_after_signal_parity.csv",
    "current_fuller_component_state_audit.csv",
    "accessible_susy_signal_bnf_summary.csv",
    "full_component_signal_vs_background_tail_fractions.csv",
    "full_component_signal_vs_background_corrected_tests.csv",
    "full_component_signal_bnf_vs_met_ht_incremental.csv",
    "full_component_trace_alignment_real_data.csv",
    "full_component_real_signal_vs_qcd_distances.csv",
    "integrated_signal_background_tail_fractions_after_updates.csv",
    "integrated_signal_background_corrected_after_updates.csv",
    "integrated_bnf_incrementality_after_updates.csv",
    "real_data_sideband_control_after_signal_parity.csv",
    "strict_artifact_systematics_after_signal_parity.csv",
    "published_signal_region_inventory_after_signal_parity.csv",
    "published_signal_region_boundary_proxy_after_signal_parity.csv",
    "published_signal_region_residual_models_after_signal_parity.csv",
    "targeted_t5wg_t1_highmet_miniaodsim_candidates.csv",
    "expanded_sm_after_signal_parity_manifest.csv",
    "expanded_sm_after_signal_parity_extraction_summary.csv",
    "fuller_component_bnf_summary.csv",
    "fuller_component_tail_fractions.csv",
    "fuller_component_sigma_tests.csv",
    "fuller_component_bnf_vs_met_ht_incremental_tests.csv",
    "expanded_benchmark_corrected_sigma_tests.csv",
    "expanded_benchmark_tail_fractions.csv",
    "expanded_bnf_vs_met_ht_incremental_tests.csv",
    "expanded_real_trace_alignment_summary.csv",
    "benchmark_trace_direction_weights.csv",
]


EXPECTED_OUTPUTS = [
    *[("reports", name) for name in KEY_REPORTS],
    *[("results/tables", name) for name in KEY_TABLES],
]


def mkdirs() -> None:
    for path in [HANDOFF, TABLES_DIR, REPORTS_COPY_DIR, FIGURES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def size_label(size: int) -> str:
    if size >= 1024**3:
        return f"{size / 1024**3:.2f} GiB"
    if size >= 1024**2:
        return f"{size / 1024**2:.2f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} B"


def purpose_for(path: Path) -> str:
    s = rel(path).lower()
    if "trace_direction" in s and s.endswith(".csv"):
        return "Large real-data trace/scored event table; use only if an analysis needs event-level real data."
    if "real" in s and "report" in s:
        return "Real-data validation, trace alignment or candidate sanity report."
    if "signal" in s and "background" in s:
        return "Signal-vs-background benchmark comparison output."
    if "increment" in s or "met_ht" in s:
        return "B_NF versus standard collider-variable incrementality output."
    if "sideband" in s or "artifact" in s or "systematics" in s:
        return "Real-data control or artefact/systematics stress-test output."
    if "susy" in s or "signal" in s:
        return "SUSY-like benchmark simulation feature, score or summary output."
    if "sm" in s or "background" in s or "qcd" in s:
        return "Standard Model simulation/background feature, score or summary output."
    if "threshold" in s:
        return "Frozen real-data threshold table used for q90/q95/q99/q999 comparisons."
    if s.startswith("scripts/"):
        return "Analysis script. Read before modifying or rerunning."
    if s.startswith("reports/"):
        return "Readable project report."
    return "Project output or support file."


def should_read(path: Path) -> str:
    s = rel(path).lower()
    size = path.stat().st_size if path.exists() and path.is_file() else 0
    if size > 50 * 1024**2:
        return "no, unless event-level analysis is required"
    if s.startswith("reports/") or s.startswith("results/tables/") or s.startswith("scripts/"):
        return "yes"
    return "maybe"


def should_modify(path: Path) -> str:
    s = rel(path).lower()
    if s.startswith("data/processed/") or s.startswith("reports/") or s.startswith("results/tables/"):
        return "no; create new versioned outputs instead"
    if s.startswith("scripts/"):
        return "only by adding new scripts or carefully patching with audit trail"
    return "no"


def file_type(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "file"


def raw_or_huge(path: Path) -> str:
    s = str(path).lower()
    size = path.stat().st_size if path.exists() and path.is_file() else 0
    if ".root" in s or "cern_open_data" in s or size > 100 * 1024**2:
        return "yes"
    return "no"


def one_line(path: Path) -> str:
    s = rel(path)
    if not path.exists():
        return "Expected file is missing."
    if path.is_dir():
        return "Directory path reference; contents may be large."
    if path.name in KEY_REPORTS:
        return "Key copied report for Gemini context."
    if path.name in KEY_TABLES:
        return "Key copied table for Gemini context."
    if s.startswith("data/processed"):
        return "Processed analysis dataset; do not overwrite."
    if s.startswith("scripts"):
        return "Script used to produce or package analysis outputs."
    return "Project file."


def inventory_rows() -> list[dict[str, str]]:
    paths: list[Path] = []
    for sub in ["reports", "results/tables", "data/processed", "scripts"]:
        root = ROOT / sub
        if root.exists():
            paths.extend([p for p in root.rglob("*") if p.is_file()])
    for external in [
        Path(r"D:\cern_open_data"),
        ROOT.parents[0] / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction",
    ]:
        if external.exists():
            paths.append(external)
    seen = set()
    rows = []
    for path in sorted(paths, key=lambda p: str(p).lower()):
        if str(path) in seen:
            continue
        seen.add(str(path))
        size = path.stat().st_size if path.exists() and path.is_file() else 0
        rows.append(
            {
                "relative_path": rel(path),
                "absolute_path": str(path),
                "file_type": file_type(path),
                "approx_size": size_label(size),
                "size_bytes": str(size),
                "purpose": purpose_for(path),
                "gemini_should_read": should_read(path),
                "gemini_should_modify": should_modify(path),
                "huge_or_raw_do_not_copy": raw_or_huge(path),
                "description": one_line(path),
            }
        )
    for folder, name in EXPECTED_OUTPUTS:
        path = ROOT / folder / name
        if not path.exists():
            rows.append(
                {
                    "relative_path": f"{folder}/{name}",
                    "absolute_path": str(path),
                    "file_type": "missing",
                    "approx_size": "missing",
                    "size_bytes": "0",
                    "purpose": "Expected handoff file",
                    "gemini_should_read": "missing",
                    "gemini_should_modify": "no",
                    "huge_or_raw_do_not_copy": "no",
                    "description": "Expected file was not found; continue without failing.",
                }
            )
    return rows


def write_inventory(rows: list[dict[str, str]]) -> None:
    csv_path = TABLES_DIR / "gemini_handoff_file_inventory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    missing = [r for r in rows if r["file_type"] == "missing"]
    huge = [r for r in rows if r["huge_or_raw_do_not_copy"] == "yes"]
    read_first = [r for r in rows if r["gemini_should_read"] == "yes"][:80]
    md = [
        "# Data and Output Inventory",
        "",
        f"Generated: {DATE}",
        "",
        "This inventory references important project outputs without copying huge ROOT files or large event-level CSVs. Gemini should use it to find the current state quickly.",
        "",
        f"Full CSV inventory: `tables/gemini_handoff_file_inventory.csv`",
        "",
        "## Read First",
        "",
        "| Relative path | Size | Purpose | Modify? |",
        "|---|---:|---|---|",
    ]
    for r in read_first:
        md.append(f"| `{r['relative_path']}` | {r['approx_size']} | {r['purpose']} | {r['gemini_should_modify']} |")
    md += [
        "",
        "## Missing Expected Files",
        "",
    ]
    if missing:
        md += ["| Relative path | Note |", "|---|---|"]
        for r in missing:
            md.append(f"| `{r['relative_path']}` | {r['description']} |")
    else:
        md.append("No expected key files were missing.")
    md += [
        "",
        "## Huge Or Raw Paths Not Copied",
        "",
    ]
    if huge:
        md += ["| Path | Size | Note |", "|---|---:|---|"]
        for r in huge[:80]:
            md.append(f"| `{r['absolute_path']}` | {r['approx_size']} | Reference only; do not copy into handoff. |")
    else:
        md.append("No huge/raw files were copied.")
    (HANDOFF / "DATA_AND_OUTPUT_INVENTORY.md").write_text("\n".join(md), encoding="utf-8")


def copy_key_files(rows: list[dict[str, str]]) -> list[str]:
    copied: list[str] = []
    for report in KEY_REPORTS:
        src = ROOT / "reports" / report
        if src.exists() and src.stat().st_size < 20 * 1024**2:
            shutil.copy2(src, REPORTS_COPY_DIR / report)
            copied.append(rel(src))
    for table in KEY_TABLES:
        src = ROOT / "results" / "tables" / table
        if src.exists() and src.stat().st_size < 20 * 1024**2:
            shutil.copy2(src, TABLES_DIR / table)
            copied.append(rel(src))
    return copied


def write(path: str, text: str) -> None:
    (HANDOFF / path).write_text(text.strip() + "\n", encoding="utf-8")


def project_state_full_handoff() -> str:
    return f"""
# Project State Full Handoff For Gemini

Generated: {DATE}

## 1. Project Aim

This project uses CMS Open Data to test whether a frozen real-data-fitted N-Frame boundary score gives indirect, model-dependent evidence that SUSY-like benchmark structures preferentially occupy a high-boundary tail compared with Standard Model backgrounds.

This is not a direct SUSY discovery claim. It is not a claim that CERN missed SUSY particles. It is an exploratory, computational, topology-specific search-prior programme. The current aim is to build discovery-level robustness step by step: frozen real-data boundary modelling, independent real validation, SUSY-like benchmark enrichment, Standard Model mimicry controls, real-data trace controls, published signal-region residual overlap, and eventually external replication.

## 2. N-Frame Interpretation

In this project, `B_NF` is treated as an observer/reconstruction boundary-stress score. High `B_NF` events are not automatically new particles. They are events whose visible detector-level structure, missing-information structure, reconstruction complexity, displaced/secondary-vertex proxy structure, multiplicity and energy flow jointly sit in a high-boundary region learned from real CMS data.

Darren's hypothesis frames this as possible trace dynamics at a lower thermodynamic/observational boundary: we may not directly see hidden-sector or SUSY-like degrees of freedom, but we may see boundary traces in directions where visible information appears stressed, incomplete, displaced, compressed, or reconstruction-heavy. The analysis therefore asks whether known SUSY-like benchmark simulations occupy this boundary region more than Standard Model controls, and whether real CMS high-boundary events align with similar directions.

This must be interpreted as a search-prior or boundary-stress model, not direct detection.

## 3. Frozen B_NF Equation

The fitted equation is frozen:

```text
{FROZEN_EQUATION}
```

Variable meanings:

| Component | Meaning in this project |
|---|---|
| `P_displacement_proxy` | Secondary-vertex/displacement proxy, mainly from `secondary_vertex_count` or derived displacement proxy features. |
| `P_reconstruction` | Reconstruction complexity, including packed candidate count, primary vertices and secondary vertices. |
| `P_multiplicity` | Jet/lepton object multiplicity structure. |
| `P_btag_structure` | b-tag count and discriminator structure. |
| `P_visible_energy` | HT and leading/subleading jet visible recoil/energy structure. |
| `P_missing` | MET/missing-information stress. |
| `P_compression` | Compression proxy from MET relative to visible energy. |

The variables came from real MiniAOD/CMSSW event extraction wherever full MiniAOD was available. Some older NanoAODSIM/reduced samples lacked packed-candidate and secondary-vertex richness, and those must be labelled as reduced-component comparisons.

Do not refit this equation. It was fitted from real CMS Run2016G MiniAOD matched real-event contrasts, with no simulated data used for fitting. Changing it would invalidate the frozen-validation chain.

## 4. Real-Data Fitting

The original model used real CMS Run2016G MiniAOD collision data. The main real-only subset included MET, JetHT and SingleMuon, totalling 665,902 real CMS collision events. No simulated data were used to fit `B_NF`.

Docker/CMSSW was made operational and used to extract MiniAOD-style event-level variables: MET, HT, jets, leptons, b-tags, primary vertices, secondary vertices, packed candidates, event IDs, trigger/filter diagnostics and provenance.

The boundary tails persisted after quality cleaning and matched-control checks. The strongest fitted parameters were secondary-vertex/displacement proxy structure, reconstruction complexity, multiplicity, b-tag structure, visible energy and missing energy. Compression remained weak/secondary.

Interpretation: real CMS collision data contain a structured high-boundary region reflecting topology/reconstruction boundary stress. This was not evidence for SUSY by itself.

## 5. Independent Real Validation

The frozen equation was applied to independent Run2016H MiniAOD real data. The expanded Run2016H validation included 156,975 real CMS events:

| Dataset | Events |
|---|---:|
| JetHT | 64,120 |
| MET | 40,283 |
| SingleMuon | 52,572 |

JetHT enrichment replicated strongly. SingleMuon depletion replicated strongly. MET enrichment did not replicate cleanly across broader tails. `P_displacement_proxy` remained strongest; `P_multiplicity`, `P_visible_energy`, `P_reconstruction` and `P_btag_structure` remained strong; `P_compression` remained weak/secondary.

Classification: partial validation of topology/reconstruction boundary interpretation, not a pure missing-energy finder.

## 6. Reduced Benchmark Tests

The frozen score was applied to reduced-component benchmark samples:

| Sample | Events | q95 tail fraction |
|---|---:|---:|
| SMS-T5Wg mGluino1500 mLSP1 | 5,000 | 19.78% |
| SUSY HToAA4B mA12 | 2,394 | 0% |
| TTJets inclusive | 50,000 | 4.91% |
| QCD HT700-1000 | 50,000 | 2.45% |

Two-proportion q95 tests gave approximately:

| Comparison | Z |
|---|---:|
| SMS-T5Wg vs TTJets | 41.39 |
| SMS-T5Wg vs QCD HT700-1000 | 59.48 |
| SMS-T5Wg vs pooled SM | 53.92-53.93 |

After look-elsewhere correction, q95 comparisons remained well above 5 sigma. q99 remained above 5 sigma against QCD but not all backgrounds.

This was important because it moved the work from real-data boundary stress to SUSY-relevant benchmark enrichment. However, the samples were reduced-component and not direct particle evidence.

## 7. Expanded Reduced-Component Robustness

Additional reduced-component NanoAODSIM samples included WJetsToLNu, QCD HT500-700, QCD HT1000-1500 and SMS-T2tt compressed stop.

SMS-T5Wg remained at or above 5 sigma enriched at q95 against all expanded SM backgrounds after correction. q95 corrected Z examples:

| Background | Corrected q95 Z |
|---|---:|
| WJetsToLNu | about 100.25 |
| QCD HT500-700 | about 79.83 |
| QCD HT700-1000 | about 59.41 |
| TTJets | about 41.29 |
| QCD HT1000-1500 | about 27.24 |

QCD HT1000-1500 was the strongest reduced-component SM mimic. SMS-T2tt compressed stop was not robustly enriched. Interpretation: topology-specific, not "all SUSY goes high".

## 8. Trace-Direction Analysis

A SUSY-vs-SM benchmark contrast defined an SMS-like trace direction. Reduced shared trace-direction weights were approximately:

| Component | Weight |
|---|---:|
| `P_missing` | 0.899 |
| `P_visible_energy` | 0.379 |
| `P_multiplicity` | 0.203 |
| `P_btag_structure` | -0.023 |
| `P_compression` | 0.082 |

`P_displacement_proxy` and `P_reconstruction` were kept as separate real-data axes because they were unavailable/reduced in some benchmark features.

Real high-B_NF events in Run2016G and Run2016H strongly aligned with the SMS-like trace direction:

| Dataset | Top 1% high events | Enrichment | Z |
|---|---:|---:|---:|
| Run2016G | 6,049 | about 5.27x | about 105.6 |
| Run2016H | 1,570 | about 3.92x | about 37.3 |
| Combined | 7,619 | about 5.07x | about 113.3 |

Expanded trace direction also survived. Caveat: real high-B_NF events moved along the SMS-like trace direction as B_NF increased, but in absolute centroid space they remained closer to QCD/SM profiles than to the SUSY signal centroid.

Interpretation: boundary-stress trace dynamics in real data, not direct SUSY-like event identity.

## 9. Candidate Sanity And Artefact Screening

Automated screening classified top trace candidates because Tom cannot manually inspect physics event displays.

| Candidate set | Trace-compatible follow-up | Trace-aligned but SM-like/provenance-caveated | SM top/heavy-flavour-like | Unclear |
|---|---:|---:|---:|---:|
| Combined top 100 | 6 | 82 | 10 | 2 |
| Run2016G top 100 | 6 | 79 | 14 | 1 |
| Run2016H top 100 | 2 | 34 | 25 | 39 |

All available quality-filter checks passed. Strong source/run/lumi concentration remained a caveat.

Matched-control comparisons showed top candidates were unusual relative to nearby ordinary real controls:

| Feature | Median candidate-minus-control |
|---|---:|
| B_NF | +3.02 |
| SMS-like trace score | +5.75 |
| MET | +311 GeV |
| HT | +989 GeV |
| secondary vertices | +4.5 |
| distance to SMS | -4.73 |
| distance to pooled SM | +4.95 |

Interpretation: small follow-up subset, but most candidates remain SM-like/provenance-caveated.

## 10. Fuller MiniAODSIM Background Test

The analysis moved from reduced NanoAODSIM to fuller MiniAODSIM backgrounds so that `P_displacement_proxy` and `P_reconstruction` could be populated properly.

Successful full-component MiniAODSIM background extraction:

| Background | Events | q95 | q99 |
|---|---:|---:|---:|
| QCD HT1000to1500 | 794 | 24.94% | 4.41% |
| QCD HT700to1000 | 196 | 7.14% | 1.02% |
| WJetsToLNu | 457 | 0.22% | 0% |

Key result: high-HT QCD became a strong SM mimic. QCD HT1000to1500 full-component q95 was 24.94%, higher than the prior reduced SMS-T5Wg q95 of 19.78%.

Interpretation: N-Frame boundary detects high-energy/high-complexity/reconstruction-stressed structure, but the SUSY-specific interpretation was qualified because high-HT QCD can mimic or exceed reduced SMS-T5Wg when QCD has fuller components.

## 11. Full-Component Signal-Side Parity

Accessible MiniAODSIM SUSY-like signal samples were found and processed:

| Signal | Events | q95 | q99 |
|---|---:|---:|---:|
| neutralino/gluino-to-neutralino | 2,000 | 62.20% | 26.05% |
| SMS-T2tt | 1,453 | 9.15% | 1.38% |
| gluino/splitSUSY | 948 | 4.32% | 1.05% |

Main positive result:

| Comparison | q95 signal | q95 background | Bonferroni-corrected Z |
|---|---:|---:|---:|
| neutralino/gluino-to-neutralino vs QCD HT1000to1500 | 62.20% | 24.94% | about 17.57 |

SMS-T2tt and splitSUSY did not beat QCD HT1000to1500. Interpretation: full-component signal-side parity restored a positive SUSY-relevant benchmark result for one topology, but not generally across all SUSY-like signals.

Important caveat: topology-specific; high-HT QCD remains a serious mimic. Incrementality caveat remained: `P_missing + P_visible_energy` produced the strongest median AUC around 0.919 in one parity layer, while full B_NF was weaker in that layer.

## 12. Post-Signal-Parity Stronger Tests

Darren requested stronger tests toward discovery-level robustness.

Targeted SMS-T5Wg/T1 high-MET MiniAODSIM search:

- no accessible T5Wg/T1 MiniAODSIM was found;
- accessible older long-lived squark-like MiniAODSIM candidates were found, but not the missing T5/T1 high-MET family.

Expanded SM MiniAODSIM controls:

| Control | Events | Notes |
|---|---:|---|
| ZJetsToNuNu | 66 | full-component MiniAODSIM |
| ZZ query control | 187 | provenance caveat from broad query matching |
| WW query control | 323 | provenance caveat from broad query matching |
| WZ | 1,000 | full-component MiniAODSIM |

Integrated q95 neutralino/gluino-to-neutralino results:

| Background | Signal q95 | Background q95 | Corrected Z |
|---|---:|---:|---:|
| QCD HT1000to1500 | 62.2% | 24.94% | about 17.53 |
| QCD HT700to1000 | 62.2% | 7.14% | about 14.57 |
| ZJetsToNuNu | 62.2% | 4.55% | about 8.94 |
| WJets/WZ/WW/ZZ controls | 62.2% | low | all >5 sigma after correction |

SMS-T2tt and splitSUSY remained weaker and did not beat QCD HT1000to1500.

Incrementality after SM controls:

| Score | Median AUC |
|---|---:|
| `P_missing + P_visible_energy` | about 0.879 |
| full `B_NF` | about 0.720 |

B_NF improved compared with the prior parity layer but still did not beat ordinary missing/visible-energy structure.

Real-data sideband and artefact tests:

- trace alignment survived source/run/lumi exclusions and reconstruction-outlier exclusions;
- real high-trace/high-boundary events remained mostly closer to QCD than to the signal centroid.

Published signal-region overlap:

- not yet run as a residual model;
- local structured observed/expected HEPData-style tables were not available;
- an inventory/template was created.

Overall classification: qualified support.

## 13. Darren's Latest Interpretation

Darren's latest framing is that the result is better than the previous version because it moved from “real CMS boundary stress exists” to “some SUSY-like benchmarks preferentially occupy the high-boundary tail.”

The strongest part is the full-component neutralino/gluino-to-neutralino benchmark:

- 62.20% above q95 compared with 24.94% for QCD HT1000-1500;
- Bonferroni-corrected Z about 17.5;
- full-component signal-side parity was achieved.

Major limitations:

1. topology-specific, not general to SUSY;
2. high-HT QCD remains a serious mimic;
3. full B_NF does not clearly outperform simple collider variables, especially `P_missing + P_visible_energy`.

Strongest paper-safe claim:

> The frozen real-data-fitted N-Frame boundary score identifies a high-boundary region preferentially occupied by at least one full-component neutralino/gluino-to-neutralino SUSY-like benchmark relative to expanded Standard Model controls, including high-HT QCD. However, the effect is topology-specific, not general across all SUSY-like benchmarks, and much of the separation remains driven by missing/visible-energy structure rather than uniquely by the full N-Frame composite.

Darren's next decisive test is published CMS/ATLAS signal-region residual modelling.

## 14. Current Weaknesses

- Topology-specific: neutralino/gluino-to-neutralino works; SMS-T2tt and splitSUSY are weak against QCD HT1000to1500.
- High-HT QCD mimicry remains serious.
- B_NF does not yet clearly beat `P_missing + P_visible_energy`.
- Real high-boundary events remain closer to QCD than to signal centroid.
- No accessible T5Wg/T1 MiniAODSIM was found.
- Published residual modelling is not done.
- Manual event displays are not done.
- Independent external replication/open frozen pipeline is not done.

## 15. What Gemini Should Do Next

First read these handoff files and the inventory. Do not rerun expensive extraction until the state is audited.

Recommended order:

1. Run or extend incrementality tests beyond standard collider variables.
2. Run strict high-HT QCD matched mimicry controls against the neutralino/gluino-to-neutralino benchmark.
3. Build the published CMS/ATLAS/HEPData signal-region residual model.
4. Prepare a frozen validation plan on independent real CMS data if feasible.
5. Extend the SUSY topology map.
6. Plan manual event-display inspection and an open frozen replication pipeline.
"""


def current_results_numerical_summary() -> str:
    return f"""
# Current Results Numerical Summary

Generated: {DATE}

## A. Frozen B_NF Coefficients

| Component | Coefficient |
|---|---:|
| `P_displacement_proxy` | 0.3566 |
| `P_reconstruction` | 0.2112 |
| `P_multiplicity` | 0.2019 |
| `P_btag_structure` | 0.0926 |
| `P_visible_energy` | 0.0728 |
| `P_missing` | 0.0595 |
| `P_compression` | 0.0055 |

## B. Real Data

| Stage | Dataset | Events | Status |
|---|---|---:|---|
| Fit | Run2016G MET/JetHT/SingleMuon | 665,902 | real MiniAOD, used to fit frozen B_NF |
| Validation | Run2016H JetHT | 64,120 | independent real MiniAOD validation |
| Validation | Run2016H MET | 40,283 | independent real MiniAOD validation |
| Validation | Run2016H SingleMuon | 52,572 | independent real MiniAOD validation |
| Validation total | Run2016H | 156,975 | partial validation |

## C. Reduced Benchmark q95/q99

| Sample | Events | q95 | q99 | Notes |
|---|---:|---:|---:|---|
| SMS-T5Wg mGluino1500 mLSP1 | 5,000 | 19.78% | about 0.52% | reduced-component signal |
| HToAA4B mA12 | 2,394 | 0% | 0% | weak/negative |
| TTJets inclusive | 50,000 | 4.91% | about 0.31% | reduced SM |
| QCD HT700-1000 | 50,000 | 2.45% | about 0.12% | reduced SM |
| QCD HT500-700 | 50,000 | about 0.89% | about 0.01% | reduced SM |
| QCD HT1000-1500 | 33,536 | about 7.73% | about 0.50% | strongest reduced SM mimic |
| WJetsToLNu | 50,000 | about 0.002% | 0% | reduced SM |
| SMS-T2tt compressed | 50,000 | about 1.37% | about 0.13% | not robustly enriched |

## D. Reduced Sigma Tests

| Comparison | Tail | Z / corrected Z |
|---|---|---:|
| SMS-T5Wg vs TTJets | q95 | about 41.39 |
| SMS-T5Wg vs QCD HT700-1000 | q95 | about 59.48 |
| SMS-T5Wg vs pooled SM | q95 | about 53.92-53.93 |
| SMS-T5Wg vs QCD HT1000-1500 expanded | q95 corrected | about 27.24 |

## E. Full-Component Background q95/q99

| Background | Events | q95 | q99 |
|---|---:|---:|---:|
| QCD HT1000to1500 | 794 | 24.94% | 4.41% |
| QCD HT700to1000 | 196 | 7.14% | 1.02% |
| WJetsToLNu | 457 | 0.22% | 0% |

## F. Full-Component Signals q95/q99

| Signal | Events | q95 | q99 |
|---|---:|---:|---:|
| neutralino/gluino-to-neutralino | 2,000 | 62.20% | 26.05% |
| SMS-T2tt | 1,453 | 9.15% | 1.38% |
| gluino/splitSUSY | 948 | 4.32% | 1.05% |

## G. Integrated Expanded SM Controls

| Control | Events | q95 | Notes |
|---|---:|---:|---|
| ZJetsToNuNu | 66 | 4.55% | small full-component control |
| WZ | 1,000 | 0.20% | full-component control |
| WW query control | 323 | 0.62% | provenance caveat from broad query matching |
| ZZ query control | 187 | 0.53% | provenance caveat from broad query matching |

## H. Integrated Signal-vs-Background q95 Results

| Signal | Background | Signal q95 | Background q95 | Bonferroni Z | Result |
|---|---|---:|---:|---:|---|
| neutralino/gluino-to-neutralino | QCD HT1000to1500 | 62.2% | 24.94% | about 17.53 | >5 sigma after correction |
| neutralino/gluino-to-neutralino | QCD HT700to1000 | 62.2% | 7.14% | about 14.57 | >5 sigma after correction |
| neutralino/gluino-to-neutralino | ZJetsToNuNu | 62.2% | 4.55% | about 8.94 | >5 sigma after correction |
| neutralino/gluino-to-neutralino | WJets/WZ/WW/ZZ | 62.2% | low | all >5 sigma | controls, some provenance caveats |

## I. Incrementality

| Layer | Score | Median AUC |
|---|---|---:|
| Full-component signal-side parity | `P_missing + P_visible_energy` | about 0.919 |
| Full-component signal-side parity | full `B_NF` | much weaker, about 0.444 in latest table |
| Integrated after SM controls | `P_missing + P_visible_energy` | about 0.879 |
| Integrated after SM controls | full `B_NF` | about 0.720 |

Interpret cautiously: B_NF improves after adding controls, but still does not beat ordinary missing/visible-energy structure.

## J. Real-Data Trace And Artefact

Trace alignment survived exclusions:

| Stress test | Outcome |
|---|---|
| exclude top source file | trace alignment survives |
| exclude top run | trace alignment survives |
| exclude top lumi | trace alignment survives |
| standard quality only | trace alignment survives |
| exclude extreme primary vertices | trace alignment survives |
| exclude extreme packed candidates | trace alignment survives |
| exclude extreme secondary vertices | trace alignment survives |
| JetHT only / MET only / SingleMuon only | trace alignment survives |

However, real high-boundary events mostly remain closer to QCD than to the signal centroid.
"""


def claim_hierarchy() -> str:
    return """
# Current Claim Hierarchy

## What We Can Currently Claim

1. A real-data N-Frame boundary-stress model exists in CMS Open Data.
2. The boundary model survives quality cleaning and matched-control checks.
3. Independent Run2016H real MiniAOD gives partial validation of the topology/reconstruction boundary interpretation.
4. Reduced-component SMS-T5Wg benchmark enrichment reaches >=5 sigma against tested SM backgrounds.
5. Full-component signal-side parity shows one neutralino/gluino-to-neutralino SUSY-like benchmark beats high-HT QCD and expanded SM controls.
6. Real high-boundary events align strongly with SUSY-like/full-component trace directions.
7. The strongest current claim is promising, indirect, model-dependent, topology-specific SUSY-relevant boundary enrichment.

## What We Cannot Claim

1. We cannot claim discovery of SUSY.
2. We cannot claim CERN missed SUSY.
3. We cannot claim all SUSY-like topologies enrich the boundary tail.
4. We cannot claim B_NF uniquely outperforms standard collider variables.
5. We cannot claim real high-boundary events are SUSY events.
6. We cannot claim published CMS/ATLAS signal-region residual alignment yet.
7. We cannot claim independent external replication yet.

## What Is Needed For Stronger Claims

| Stronger claim | Required evidence |
|---|---|
| Matched background-controlled benchmark enrichment | Strict matching/stratification against QCD on HT, MET, jets, b-tags, vertices, packed candidates, displacement/reconstruction proxies. |
| N-Frame-specific value beyond standard variables | Incremental models showing B_NF improves AUC, likelihood, calibration and q95 enrichment beyond MET/visible energy/multiplicity. |
| Published signal-region residual alignment | Observed-minus-expected residual tables from CMS/ATLAS/HEPData showing residuals increase with a transparent boundary proxy. |
| Frozen independent validation | New independent real CMS data processed with fixed weights, thresholds and candidate-selection rules. |
| Discovery-level physics | Manual/event-display review, external replication, systematic uncertainties, collaboration-grade statistical treatment and open frozen pipeline. |

Therefore current claim is promising exploratory computational evidence, not discovery-level evidence.
"""


def next_tests_from_darren() -> str:
    return """
# Next Tests From Darren

## 1. Incrementality Beyond MET/Visible Energy

Why it matters: the main caveat is that `P_missing + P_visible_energy` often beats full B_NF. If B_NF does not add predictive value beyond ordinary collider variables, the N-Frame interpretation is weaker.

Data needed: all available signal/background scored samples with B_NF components.

Can do now: yes.

Likely blocking issues: small full-component samples and topology imbalance.

Suggested Gemini task: compare logistic/rank/AUC models with and without B_NF, bootstrap confidence intervals, and q95 enrichment.

## 2. Strict High-HT QCD Mimicry Control

Why it matters: QCD HT1000to1500 is the strongest SM mimic.

Data needed: neutralino/gluino-to-neutralino and QCD HT1000to1500 event-level full-component data.

Can do now: yes, with existing files.

Likely blocking issues: limited QCD event count, 794 events.

Suggested Gemini task: match/stratify on HT, MET, jets, b-tags, vertices, packed candidates and secondary vertices; test residual B_NF enrichment after matching.

## 3. Published CMS/ATLAS Signal-Region Residual Modelling

Why it matters: this connects event-level boundary behaviour to public search-region outcomes.

Data needed: observed events, expected background, uncertainty, MET/HT/jet/b-tag/displacement labels for published signal regions.

Can do now: partially. Inventory/template exists; numerical yield extraction still required.

Likely blocking issues: HEPData/CMS tables may need manual mapping or API ingestion.

Suggested Gemini task: ingest HEPData/CMS public tables, build `Published_BNF_proxy`, test residual magnitude/positive residuals versus proxy with analysis-level fixed effects if possible.

## 4. Frozen Independent Real Validation

Why it matters: discovery-level robustness needs new real data with unchanged weights, thresholds and candidate rules.

Data needed: independent real CMS sample, preferably MiniAOD with MET/JetHT/SingleMuon-like coverage.

Can do now: planning only, unless small verified files are available.

Likely blocking issues: disk/download size and CMSSW runtime.

Suggested Gemini task: create staged validation plan and do not download huge files without asking.

## 5. Broader SUSY Topology Mapping

Why it matters: current support is topology-specific.

Data needed: additional accessible MiniAODSIM SUSY-like samples across T5/T1/electroweakino/compressed/long-lived/displaced.

Can do now: metadata search and small verified downloads.

Likely blocking issues: inaccessible or stale CERN EOS paths.

Suggested Gemini task: map which SUSY-like topologies enrich and which do not; avoid saying “SUSY as a whole”.

## 6. Manual Event-Display Inspection

Why it matters: automated candidates need detector-level sanity checking.

Data needed: event display tooling or exported event identifiers for expert review.

Can do now: prepare candidate list; Tom should not manually inspect unless tooling is ready.

Likely blocking issues: event display setup complexity.

Suggested Gemini task: produce an event-display preparation manifest, not a physics conclusion.

## 7. Independent Replication/Open Frozen Pipeline

Why it matters: external credibility requires reproducibility.

Data needed: locked scripts, checksums, frozen parameters, environment documentation and reproducible run commands.

Can do now: yes, as packaging.

Likely blocking issues: Docker/CMSSW environment and raw data availability.

Suggested Gemini task: produce a frozen replication README and run manifest.
"""


def readme_for_gemini(copied: list[str]) -> str:
    return f"""
# README For Gemini

This folder is a handoff package for the local N-Frame/CERN project.

Project root:

`{ROOT}`

Handoff generated:

`{HANDOFF}`

Generated date: {DATE}

## What Gemini Should Do First

1. Read `PROJECT_STATE_FULL_HANDOFF.md`.
2. Read `CURRENT_RESULTS_NUMERICAL_SUMMARY.md`.
3. Read `CURRENT_CLAIM_HIERARCHY.md`.
4. Read `NEXT_TESTS_FROM_DARREN.md`.
5. Check `DATA_AND_OUTPUT_INVENTORY.md` and `tables/gemini_handoff_file_inventory.csv`.
6. Do not rerun expensive extraction or download data until the state is audited.

## Frozen Rule

Do not refit B_NF.

```text
{FROZEN_EQUATION}
```

## Copied Files

Small key reports are in `key_reports_copied/`.

Small key tables are in `tables/`.

Large raw ROOT files and huge event CSVs were not copied. They are referenced by path in the inventory.

Copied file count: {len(copied)}.
"""


def gemini_starter_prompt() -> str:
    return f"""
You are working in my local N-Frame/CERN project.

Project root:
`{ROOT}`

Stage 2 project:
`{ROOT}`

First read the handoff folder:
`{HANDOFF}`

Start by reading:
1. `GEMINI_HANDOFF/README_FOR_GEMINI.md`
2. `GEMINI_HANDOFF/PROJECT_STATE_FULL_HANDOFF.md`
3. `GEMINI_HANDOFF/CURRENT_RESULTS_NUMERICAL_SUMMARY.md`
4. `GEMINI_HANDOFF/CURRENT_CLAIM_HIERARCHY.md`
5. `GEMINI_HANDOFF/NEXT_TESTS_FROM_DARREN.md`
6. `GEMINI_HANDOFF/DATA_AND_OUTPUT_INVENTORY.md`

Do not rerun expensive CMSSW extraction. Do not download new data. Do not refit B_NF. Do not delete or overwrite previous outputs.

Use UK English. Do not claim SUSY discovery. Do not claim CERN missed SUSY. Treat the current result as indirect, model-dependent, topology-specific SUSY-relevant boundary enrichment.

After reading, summarise your understanding of:
- the frozen B_NF equation;
- what has already been done;
- the strongest current positive result;
- the major caveats;
- what files/tables/reports are available;
- what is missing;
- the next best action.

Then wait for my next instruction.
"""


def gemini_next_analysis_prompt() -> str:
    return f"""
Continue the N-Frame/CERN project from the handoff state. Do not refit B_NF and do not rerun expensive extraction unless explicitly needed.

Priority 1: Incrementality beyond standard collider variables.

Use all available signal/background samples. Test whether B_NF adds value beyond `P_missing`, `P_visible_energy`, `P_multiplicity`, HT/MET-like variables.

Compare:

- baseline: `y ~ P_missing + P_visible_energy`
- add boundary: `y ~ P_missing + P_visible_energy + B_NF`
- expanded: `y ~ P_missing + P_visible_energy + P_multiplicity + P_displacement_proxy + P_reconstruction + B_NF`

Use logistic/rank/AUC models. Compare AUC, likelihood or log loss, calibration, q95 enrichment, and bootstrap confidence intervals. Report whether B_NF improvement is meaningful or negligible.

Priority 2: Strict high-HT QCD matched mimicry.

Compare neutralino/gluino-to-neutralino vs QCD HT1000to1500. Match or stratify on HT, MET, jet multiplicity, b-tags, primary vertices, secondary vertices, packed candidate count, displacement/reconstruction proxies. Test whether signal remains enriched in B_NF after matching. If not, state clearly that QCD mimicry explains much of the signal.

Priority 3: Published signal-region residual modelling.

Search local files first, then public CMS/ATLAS/HEPData sources if internet access is available. Prioritise SUSY searches with observed and expected yields. Code signal regions by MET, HT, jet multiplicity, b-tags, lepton count, displaced/long-lived, compressed-spectrum, disappearing-track, multi-b and same-sign dilepton labels. Build a transparent `Published_BNF_proxy`. Model standardised observed-minus-expected residuals. Test whether residual magnitude and/or positive residuals increase with the boundary proxy. Include analysis-level fixed effects where possible. Avoid overclaiming.

Priority 4: Frozen validation plan.

Identify independent real CMS data for a frozen validation. Do not download huge data without asking. Prepare a staged plan.

Priority 5: Broader SUSY topology map.

Map which SUSY-like samples enrich and which do not. Avoid saying "SUSY as a whole".

Produce readable reports, tables, effect sizes, p/Z values where appropriate, exact caveats, and a next action.
"""


def do_not_do_list() -> str:
    return """
# Do Not Do List

- Do not refit B_NF unless Tom explicitly asks.
- Do not change frozen thresholds unless explicitly asked.
- Do not claim SUSY discovery.
- Do not claim CERN missed SUSY.
- Do not treat all SUSY topologies as equivalent.
- Do not ignore QCD HT1000to1500 mimicry.
- Do not rely only on p-values without checking incrementality.
- Do not confuse NanoAODSIM reduced-component with MiniAODSIM full-component.
- Do not silently set missing components to zero.
- Do not download massive files without asking.
- Do not delete, move or overwrite previous outputs.
- Do not overinterpret broad-query WW/ZZ controls with provenance caveats.
- Do not copy huge ROOT files into the handoff.
- Do not describe simulated benchmark enrichment as real-particle detection.
"""


def quick_context_for_tom() -> str:
    return """
# Quick Context For Tom

## What We Have Achieved

We built a frozen N-Frame boundary score from real CMS Run2016G MiniAOD data and validated parts of it on independent Run2016H real data. We then tested whether SUSY-like benchmark simulations occupy the high-boundary tail more than Standard Model backgrounds.

The strongest current result is that one full-component neutralino/gluino-to-neutralino SUSY-like benchmark has 62.2% of events above the real-data q95 boundary threshold, compared with 24.94% for QCD HT1000to1500. This remains above 5 sigma after correction in the benchmark comparison.

## What Is Weakest

The result is topology-specific. SMS-T2tt and splitSUSY do not beat QCD HT1000to1500. High-HT QCD remains a serious mimic. The full B_NF score still does not clearly beat the simpler `P_missing + P_visible_energy` combination.

## What To Ask Gemini First

Ask Gemini to read `GEMINI_HANDOFF/GEMINI_STARTER_PROMPT.md` and summarise the project state. Then use `GEMINI_NEXT_ANALYSIS_PROMPT.md` for the next analysis.

## What To Send Darren If He Asks

The safe summary is:

> The frozen real-data-fitted N-Frame boundary score identifies a high-boundary region preferentially occupied by at least one full-component neutralino/gluino-to-neutralino SUSY-like benchmark relative to expanded Standard Model controls, including high-HT QCD. However, the effect is topology-specific, not general across all SUSY-like benchmarks, and much of the separation remains driven by missing/visible-energy structure rather than uniquely by the full N-Frame composite.

## What Not To Say

Do not say we found SUSY. Do not say CERN missed SUSY. Do not say all SUSY-like samples work. Do not hide the QCD mimicry or incrementality caveat.
"""


def main() -> None:
    mkdirs()
    rows = inventory_rows()
    write_inventory(rows)
    copied = copy_key_files(rows)
    write("README_FOR_GEMINI.md", readme_for_gemini(copied))
    write("PROJECT_STATE_FULL_HANDOFF.md", project_state_full_handoff())
    write("CURRENT_RESULTS_NUMERICAL_SUMMARY.md", current_results_numerical_summary())
    write("CURRENT_CLAIM_HIERARCHY.md", claim_hierarchy())
    write("NEXT_TESTS_FROM_DARREN.md", next_tests_from_darren())
    write("GEMINI_STARTER_PROMPT.md", gemini_starter_prompt())
    write("GEMINI_NEXT_ANALYSIS_PROMPT.md", gemini_next_analysis_prompt())
    write("DO_NOT_DO_LIST.md", do_not_do_list())
    write("QUICK_CONTEXT_FOR_TOM.md", quick_context_for_tom())

    summary = [
        "# Gemini Handoff Creation Summary",
        "",
        f"Generated: {DATE}",
        "",
        f"Handoff folder: `{HANDOFF}`",
        "",
        f"Inventory rows: {len(rows)}",
        f"Copied small reports/tables: {len(copied)}",
        "",
        "Huge raw files were not copied. Existing outputs were not moved or deleted. B_NF was not refitted.",
    ]
    write("HANDOFF_CREATION_SUMMARY.md", "\n".join(summary))
    print(HANDOFF)
    print(f"inventory_rows={len(rows)} copied={len(copied)}")


if __name__ == "__main__":
    main()
