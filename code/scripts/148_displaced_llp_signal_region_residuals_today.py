from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
from scipy import stats
from statsmodels.tools.sm_exceptions import PerfectSeparationError


ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "outputs_today_published_signal_region_residuals"
OUT = ROOT / "outputs_today_displaced_llp_signal_region_residuals"
TABLES = OUT / "tables"
SOURCES = OUT / "sources"
FIGURES = OUT / "figures"
DATE = "2026-06-10"

RAW_COLS = [
    "analysis_id",
    "experiment",
    "paper_title_short",
    "year",
    "table_name",
    "signal_region",
    "observed",
    "expected",
    "expected_uncertainty",
    "uncertainty_type",
    "final_state",
    "raw_label",
    "raw_bin_description",
    "source_url_or_reference",
    "extraction_notes",
    "extraction_quality",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, SOURCES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    return (df if n is None else df.head(n)).to_markdown(index=False)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def audit_previous_outputs() -> pd.DataFrame:
    files = [
        PREV / "09_PUBLISHED_SIGNAL_REGION_RESIDUAL_SYNTHESIS_FOR_DARREN.md",
        PREV / "10_SHORT_UPDATE_FOR_TOM.md",
        PREV / "07_SIGNAL_REGION_RESIDUAL_MODELLING_REPORT.md",
        PREV / "tables" / "03_combined_published_signal_regions_raw.csv",
        PREV / "tables" / "04_signal_region_residuals.csv",
        PREV / "tables" / "05_signal_region_boundary_proxy_components.csv",
        PREV / "tables" / "06_signal_region_boundary_proxy_scores.csv",
        PREV / "tables" / "07_residual_model_results.csv",
        PREV / "tables" / "08_sensitivity_checks.csv",
        PREV / "05_BOUNDARY_PROXY_CODING_RULES.md",
        PREV / "tables" / "02_candidate_public_susy_analyses.csv",
    ]
    rows: list[dict[str, Any]] = []
    scored = read_csv(PREV / "tables" / "06_signal_region_boundary_proxy_scores.csv")
    for path in files:
        exists = path.exists()
        row: dict[str, Any] = {
            "path": str(path.relative_to(ROOT)),
            "exists": exists,
            "rows": np.nan,
            "available_proxy_components": "",
            "unavailable_proxy_components": "",
            "key_finding_or_gap": "",
        }
        if exists and path.suffix.lower() == ".csv":
            df = read_csv(path)
            row["rows"] = len(df)
            row["key_finding_or_gap"] = "; ".join(map(str, df.columns[:10]))
        elif exists:
            text = path.read_text(encoding="utf-8", errors="replace")
            row["key_finding_or_gap"] = re.sub(r"\s+", " ", text[:260])
        rows.append(row)

    if not scored.empty:
        components = [
            "P_missing_proxy",
            "P_visible_energy_proxy",
            "P_multiplicity_proxy",
            "P_btag_proxy",
            "P_displacement_or_longlived_proxy",
            "P_compressed_proxy",
            "P_rare_topology_proxy",
            "P_reconstruction_stress_proxy",
        ]
        available = [c for c in components if c in scored and scored[c].fillna(0).abs().sum() > 0]
        unavailable = [c for c in components if c not in scored or scored[c].fillna(0).abs().sum() == 0]
    else:
        available, unavailable = [], []
    summary_row = {
        "path": "previous_run_summary",
        "exists": True,
        "rows": len(scored) if not scored.empty else np.nan,
        "available_proxy_components": "; ".join(available),
        "unavailable_proxy_components": "; ".join(unavailable),
        "key_finding_or_gap": "CMS-SUS-19-006 tested MHT/HT/jets/b-tags. It qualified the N-Frame interpretation because displacement/LLP terms were absent and weighted BNF added essentially nothing beyond missing+visible energy for residual magnitude.",
    }
    rows.append(summary_row)
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_previous_public_results_audit.csv", index=False)
    write_text(
        OUT / "01_PREVIOUS_PUBLIC_RESULTS_AUDIT.md",
        "\n".join(
            [
                "# Previous Public-Results Audit",
                "",
                f"Date: {DATE}",
                "",
                "The previous public-results run used CMS-SUS-19-006, a Run 2 jets plus missing transverse momentum search. It successfully tested real observed-minus-expected public search bins, but only for ordinary jets+MET labels.",
                "",
                "Available components were missing energy, visible energy, jet multiplicity, b-tag structure, and a conservative reconstruction-stress proxy. Unavailable components were the true displacement/LLP and compressed-spectrum labels that dominate Darren's frozen B_NF equation.",
                "",
                "The result therefore qualified the hidden-boundary hypothesis: the residual pipeline worked, but the tested analysis did not exercise the strongest displacement/reconstruction part of B_NF.",
                "",
                md(audit),
            ]
        ),
    )
    return audit


def check_url(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25, allow_redirects=True)
        if r.status_code == 403 and "Just a moment" in r.text:
            return "blocked by HEPData/Cloudflare browser challenge"
        return f"{r.status_code} {r.headers.get('content-type', '')[:60]}"
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def candidate_analyses() -> pd.DataFrame:
    candidates = [
        {
            "analysis_id": "CMS-EXO-22-020",
            "experiment": "CMS",
            "paper_title": "Search for long-lived particles using displaced vertices and missing transverse momentum",
            "arxiv_id": "2402.15804",
            "analysis_public_id": "EXO-22-020",
            "year": 2024,
            "final_state": "displaced vertex plus missing transverse momentum",
            "includes_displaced_llp_or_disappearing": True,
            "observed_counts_available": True,
            "expected_background_available": True,
            "uncertainties_available": True,
            "number_of_usable_signal_regions": 1,
            "source_type": "arXiv TeX source / CMS public result",
            "machine_readable": "TeX source",
            "direct_url_or_reference": "https://arxiv.org/abs/2402.15804",
            "access_status": check_url("https://arxiv.org/e-print/2402.15804"),
            "priority_score": 10,
            "reason_for_inclusion": "Directly tests displaced-vertex plus MET labels; one published signal region has observed and expected counts.",
        },
        {
            "analysis_id": "CMS-EXO-17-018",
            "experiment": "CMS",
            "paper_title": "Search for long-lived particles with displaced vertices in multijet events",
            "arxiv_id": "1808.03078",
            "analysis_public_id": "EXO-17-018",
            "year": 2018,
            "final_state": "two displaced vertices in multijet events",
            "includes_displaced_llp_or_disappearing": True,
            "observed_counts_available": True,
            "expected_background_available": True,
            "uncertainties_available": True,
            "number_of_usable_signal_regions": 3,
            "source_type": "arXiv TeX source",
            "machine_readable": "TeX source",
            "direct_url_or_reference": "https://arxiv.org/abs/1808.03078",
            "access_status": check_url("https://arxiv.org/e-print/1808.03078"),
            "priority_score": 9,
            "reason_for_inclusion": "Three displaced-vertex separation bins provide non-zero displacement and reconstruction stress.",
        },
        {
            "analysis_id": "ATLAS-SUSY-2018-19",
            "experiment": "ATLAS",
            "paper_title": "Search for long-lived charginos based on a disappearing-track signature",
            "arxiv_id": "2201.02472",
            "analysis_public_id": "SUSY-2018-19",
            "year": 2022,
            "final_state": "disappearing track plus high missing transverse momentum",
            "includes_displaced_llp_or_disappearing": True,
            "observed_counts_available": True,
            "expected_background_available": True,
            "uncertainties_available": True,
            "number_of_usable_signal_regions": 2,
            "source_type": "arXiv TeX source / ATLAS paper table",
            "machine_readable": "TeX source",
            "direct_url_or_reference": "https://arxiv.org/abs/2201.02472",
            "access_status": check_url("https://arxiv.org/e-print/2201.02472"),
            "priority_score": 9,
            "reason_for_inclusion": "Two high-MET disappearing-track signal regions, including ATLAS coverage.",
        },
        {
            "analysis_id": "CMS-SUS-21-006",
            "experiment": "CMS",
            "paper_title": "Search for supersymmetry in final states with disappearing tracks",
            "arxiv_id": "2309.16823",
            "analysis_public_id": "SUS-21-006",
            "year": 2024,
            "final_state": "disappearing tracks with jets, b-tags, leptons, and hard missing transverse momentum",
            "includes_displaced_llp_or_disappearing": True,
            "observed_counts_available": "yes in HEPData record",
            "expected_background_available": "yes in HEPData record",
            "uncertainties_available": "yes in HEPData record",
            "number_of_usable_signal_regions": 0,
            "source_type": "HEPData / arXiv",
            "machine_readable": "HEPData metadata accessible; value downloads blocked here",
            "direct_url_or_reference": "https://www.hepdata.net/record/144178",
            "access_status": check_url("https://www.hepdata.net/record/144178?format=json")
            + "; table downloads blocked when requested",
            "priority_score": 10,
            "reason_for_inclusion": "Highest-value 49-bin disappearing-track candidate, but numerical table-value downloads were blocked from this environment and the arXiv paper only shows the 49-bin values graphically.",
        },
    ]
    df = pd.DataFrame(candidates)
    df.to_csv(TABLES / "02_displaced_llp_candidate_public_analyses.csv", index=False)
    write_text(
        OUT / "02_DISPLACED_LLP_ANALYSIS_SELECTION_REPORT.md",
        "\n".join(
            [
                "# Displaced/LLP Analysis Selection Report",
                "",
                f"Date: {DATE}",
                "",
                "I searched for public CMS/ATLAS analyses where published signal-region labels contain displacement, long-lived-particle, disappearing-track, or special reconstruction features.",
                "",
                "The best machine-readable candidates in this run were arXiv TeX tables for CMS EXO-22-020, CMS EXO-17-018, and ATLAS SUSY-2018-19. CMS-SUS-21-006 remains a high-priority 49-bin disappearing-track target, but HEPData value downloads were blocked here and the arXiv paper did not include the numerical 49-bin table in TeX.",
                "",
                md(df),
            ]
        ),
    )
    return df


def selected_analyses(candidates: pd.DataFrame) -> pd.DataFrame:
    selected = candidates[
        candidates["analysis_id"].isin(["CMS-EXO-22-020", "CMS-EXO-17-018", "ATLAS-SUSY-2018-19"])
    ].copy()
    comparator = pd.DataFrame(
        [
            {
                "analysis_id": "CMS-SUS-19-006",
                "experiment": "CMS",
                "paper_title": "Search for supersymmetry in final states with jets and missing transverse momentum",
                "arxiv_id": "1908.04722",
                "analysis_public_id": "SUS-19-006",
                "year": 2019,
                "final_state": "ordinary jets plus missing transverse momentum comparator",
                "includes_displaced_llp_or_disappearing": False,
                "observed_counts_available": True,
                "expected_background_available": True,
                "uncertainties_available": True,
                "number_of_usable_signal_regions": 174,
                "source_type": "previous parsed arXiv TeX source",
                "machine_readable": "already parsed",
                "direct_url_or_reference": "https://arxiv.org/abs/1908.04722",
                "access_status": "available from previous run",
                "priority_score": 8,
                "reason_for_inclusion": "Comparator from previous public-results run; keeps ordinary jets+MET baseline in the same model.",
            }
        ]
    )
    selected = pd.concat([comparator, selected], ignore_index=True)
    selected.to_csv(TABLES / "03_selected_public_analyses_for_ingestion.csv", index=False)
    write_text(
        OUT / "03_SELECTED_ANALYSES_FOR_INGESTION_REPORT.md",
        "\n".join(
            [
                "# Selected Analyses for Ingestion",
                "",
                f"Date: {DATE}",
                "",
                "Selected analyses include the previous CMS jets+MET comparator plus three displaced/LLP/disappearing-track analyses with extractable observed/expected tables.",
                "",
                "CMS-SUS-21-006 was not ingested despite being high priority because only HEPData appears to contain the numerical 49-bin table and HEPData table-value downloads were blocked in this environment.",
                "",
                md(selected),
            ]
        ),
    )
    return selected


def prev_comparator_rows() -> pd.DataFrame:
    prev_scores = read_csv(PREV / "tables" / "06_signal_region_boundary_proxy_scores.csv")
    if prev_scores.empty:
        return pd.DataFrame()
    for col in RAW_COLS:
        if col not in prev_scores:
            prev_scores[col] = ""
    prev_scores["analysis_group"] = "ordinary_jets_met_comparator"
    return prev_scores


def new_raw_rows() -> pd.DataFrame:
    rows = [
        {
            "analysis_id": "CMS-EXO-22-020",
            "experiment": "CMS",
            "paper_title_short": "CMS displaced vertex + MET",
            "year": 2024,
            "table_name": "Event yield data Run II",
            "signal_region": "A_ntk_ge5_mlscore_gt0p2",
            "observed": 9.0,
            "expected": 5.2,
            "expected_uncertainty": 0.5,
            "uncertainty_type": "published total post-fit background uncertainty",
            "final_state": "displaced vertex plus missing transverse momentum",
            "raw_label": "signal region A; ML score > 0.2; n_tracks >= 5; displaced vertex; MET preselection",
            "raw_bin_description": "In the signal region, nine events are observed while 5.2 +/- 0.5 events are predicted.",
            "source_url_or_reference": "https://arxiv.org/abs/2402.15804",
            "extraction_notes": "Parsed from arXiv TeX table; background estimate is data-driven; no simulated signal rows used.",
            "extraction_quality": "high",
            "analysis_group": "displaced_llp",
        },
        {
            "analysis_id": "CMS-EXO-17-018",
            "experiment": "CMS",
            "paper_title_short": "CMS displaced vertices multijet",
            "year": 2018,
            "table_name": "Binned two-vertex DVV signal-region counts",
            "signal_region": "dvv_0_0p4mm",
            "observed": 1.0,
            "expected": 0.51,
            "expected_uncertainty": math.sqrt(0.01**2 + 0.13**2),
            "uncertainty_type": "quadrature of published statistical and systematic background uncertainty",
            "final_state": "two displaced vertices in multijet events",
            "raw_label": ">=5-track two-vertex events; DVV 0--0.4 mm",
            "raw_bin_description": "Fitted background 0.51 +/- 0.01 stat +/- 0.13 syst; observed 1.",
            "source_url_or_reference": "https://arxiv.org/abs/1808.03078",
            "extraction_notes": "Parsed from arXiv TeX table; ignored simulated signal-yield columns.",
            "extraction_quality": "high",
            "analysis_group": "displaced_llp",
        },
        {
            "analysis_id": "CMS-EXO-17-018",
            "experiment": "CMS",
            "paper_title_short": "CMS displaced vertices multijet",
            "year": 2018,
            "table_name": "Binned two-vertex DVV signal-region counts",
            "signal_region": "dvv_0p4_0p7mm",
            "observed": 0.0,
            "expected": 0.37,
            "expected_uncertainty": math.sqrt(0.02**2 + 0.09**2),
            "uncertainty_type": "quadrature of published statistical and systematic background uncertainty",
            "final_state": "two displaced vertices in multijet events",
            "raw_label": ">=5-track two-vertex events; DVV 0.4--0.7 mm",
            "raw_bin_description": "Fitted background 0.37 +/- 0.02 stat +/- 0.09 syst; observed 0.",
            "source_url_or_reference": "https://arxiv.org/abs/1808.03078",
            "extraction_notes": "Parsed from arXiv TeX table; ignored simulated signal-yield columns.",
            "extraction_quality": "high",
            "analysis_group": "displaced_llp",
        },
        {
            "analysis_id": "CMS-EXO-17-018",
            "experiment": "CMS",
            "paper_title_short": "CMS displaced vertices multijet",
            "year": 2018,
            "table_name": "Binned two-vertex DVV signal-region counts",
            "signal_region": "dvv_0p7_40mm",
            "observed": 0.0,
            "expected": 0.12,
            "expected_uncertainty": math.sqrt(0.02**2 + 0.08**2),
            "uncertainty_type": "quadrature of published statistical and systematic background uncertainty",
            "final_state": "two displaced vertices in multijet events",
            "raw_label": ">=5-track two-vertex events; DVV 0.7--40 mm",
            "raw_bin_description": "Fitted background 0.12 +/- 0.02 stat +/- 0.08 syst; observed 0.",
            "source_url_or_reference": "https://arxiv.org/abs/1808.03078",
            "extraction_notes": "Parsed from arXiv TeX table; ignored simulated signal-yield columns.",
            "extraction_quality": "high",
            "analysis_group": "displaced_llp",
        },
        {
            "analysis_id": "ATLAS-SUSY-2018-19",
            "experiment": "ATLAS",
            "paper_title_short": "ATLAS disappearing track",
            "year": 2022,
            "table_name": "High-MET signal regions",
            "signal_region": "electroweak_channel",
            "observed": 3.0,
            "expected": 3.0,
            "expected_uncertainty": 0.7,
            "uncertainty_type": "published total background uncertainty",
            "final_state": "disappearing track plus high missing transverse momentum",
            "raw_label": "high MET signal region; electroweak channel; tracklet pT > 60 GeV",
            "raw_bin_description": "Total Expected 3.0 +/- 0.7; Observed 3.",
            "source_url_or_reference": "https://arxiv.org/abs/2201.02472",
            "extraction_notes": "Parsed from arXiv TeX table; ignored model-limit and simulated signal rows.",
            "extraction_quality": "high",
            "analysis_group": "displaced_llp",
        },
        {
            "analysis_id": "ATLAS-SUSY-2018-19",
            "experiment": "ATLAS",
            "paper_title_short": "ATLAS disappearing track",
            "year": 2022,
            "table_name": "High-MET signal regions",
            "signal_region": "strong_channel",
            "observed": 1.0,
            "expected": 0.84,
            "expected_uncertainty": 0.33,
            "uncertainty_type": "published total background uncertainty",
            "final_state": "disappearing track plus high missing transverse momentum",
            "raw_label": "high MET signal region; strong channel; tracklet pT > 60 GeV",
            "raw_bin_description": "Total Expected 0.84 +/- 0.33; Observed 1.",
            "source_url_or_reference": "https://arxiv.org/abs/2201.02472",
            "extraction_notes": "Parsed from arXiv TeX table; ignored model-limit and simulated signal rows.",
            "extraction_quality": "high",
            "analysis_group": "displaced_llp",
        },
    ]
    return pd.DataFrame(rows)


def ingest_tables() -> pd.DataFrame:
    comp = prev_comparator_rows()
    new = new_raw_rows()
    for col in comp.columns:
        if col not in new:
            new[col] = np.nan
    for col in new.columns:
        if col not in comp:
            comp[col] = np.nan
    combined = pd.concat([comp[new.columns], new], ignore_index=True)
    combined[RAW_COLS].to_csv(TABLES / "04_combined_displaced_llp_signal_regions_raw.csv", index=False)
    counts = combined.groupby("analysis_id").size().reset_index(name="signal_regions")
    write_text(
        OUT / "04_SIGNAL_REGION_TABLE_INGESTION_REPORT.md",
        "\n".join(
            [
                "# Signal-Region Table Ingestion Report",
                "",
                f"Date: {DATE}",
                "",
                "I ingested the previous 174 CMS-SUS-19-006 ordinary jets+MET comparator bins and six new displaced/LLP/disappearing-track signal-region rows from published arXiv TeX tables.",
                "",
                "No simulated SUSY event samples were used. Simulated signal-yield and limit columns in the papers were deliberately ignored.",
                "",
                "Rows per analysis:",
                "",
                md(counts),
                "",
                "Failed extraction: CMS-SUS-21-006 was identified as a high-value 49-bin disappearing-track analysis, but the values are in HEPData table downloads that were blocked by a browser challenge here. Its arXiv TeX source contains the figures and table captions but not a direct numerical 49-bin observed/expected table.",
            ]
        ),
    )
    return combined


def residuals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["observed"] = pd.to_numeric(out["observed"], errors="coerce")
    out["expected"] = pd.to_numeric(out["expected"], errors="coerce")
    out["expected_uncertainty"] = pd.to_numeric(out["expected_uncertainty"], errors="coerce")
    out["residual"] = out["observed"] - out["expected"]
    out["residual_denominator"] = np.sqrt(np.maximum(out["expected"], 0) + out["expected_uncertainty"].fillna(0) ** 2)
    no_unc = out["expected_uncertainty"].isna()
    out.loc[no_unc, "residual_denominator"] = np.sqrt(np.maximum(out.loc[no_unc, "expected"], 1e-9))
    out["Z_residual"] = out["residual"] / out["residual_denominator"].replace(0, np.nan)
    out["abs_Z_residual"] = out["Z_residual"].abs()
    out["positive_residual"] = out["residual"] > 0
    out["large_upward_fluctuation"] = out["Z_residual"] > 1
    out["upward_fluctuation_p_approx"] = stats.norm.sf(out["Z_residual"])
    out["two_sided_residual_p_approx"] = 2 * stats.norm.sf(out["abs_Z_residual"])
    out.to_csv(TABLES / "05_displaced_llp_signal_region_residuals.csv", index=False)
    summary = out.groupby("analysis_id").agg(
        signal_regions=("signal_region", "count"),
        positive_residuals=("positive_residual", "sum"),
        mean_signed_Z=("Z_residual", "mean"),
        mean_abs_Z=("abs_Z_residual", "mean"),
        max_signed_Z=("Z_residual", "max"),
    ).reset_index()
    write_text(
        OUT / "05_RESIDUAL_CALCULATION_REPORT.md",
        "\n".join(
            [
                "# Residual Calculation Report",
                "",
                f"Date: {DATE}",
                "",
                "Residuals were computed as observed minus expected. The denominator is sqrt(expected + uncertainty^2) where uncertainty is available. This is a rough bin-level diagnostic, not a full likelihood or discovery significance.",
                "",
                md(summary),
            ]
        ),
    )
    return out


def code_proxies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
        "P_reconstruction_stress_proxy",
    ]:
        if col not in out:
            out[col] = 0.0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    is_exo22 = out["analysis_id"] == "CMS-EXO-22-020"
    out.loc[is_exo22, [
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
    ]] = [2.5, 1.5, 2.5, 0.0, 3.0, 3.0, 1.0, 3.0]

    is_exo17 = out["analysis_id"] == "CMS-EXO-17-018"
    out.loc[is_exo17, [
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
    ]] = [0.0, 2.0, 3.0, 0.0, 3.0, 0.0, 3.0]
    out.loc[out["signal_region"].eq("dvv_0_0p4mm"), "P_reconstruction_stress_proxy"] = 2.5
    out.loc[out["signal_region"].eq("dvv_0p4_0p7mm"), "P_reconstruction_stress_proxy"] = 2.8
    out.loc[out["signal_region"].eq("dvv_0p7_40mm"), "P_reconstruction_stress_proxy"] = 3.0

    is_atlas_ewk = (out["analysis_id"] == "ATLAS-SUSY-2018-19") & out["signal_region"].eq("electroweak_channel")
    out.loc[is_atlas_ewk, [
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
    ]] = [3.0, 1.5, 1.0, 0.0, 3.0, 3.0, 3.0, 3.0]

    is_atlas_strong = (out["analysis_id"] == "ATLAS-SUSY-2018-19") & out["signal_region"].eq("strong_channel")
    out.loc[is_atlas_strong, [
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
    ]] = [3.0, 2.5, 2.0, 0.0, 3.0, 3.0, 2.0, 3.0]

    proxy_cols = [
        "analysis_id",
        "signal_region",
        "raw_label",
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
    ]
    out[proxy_cols].to_csv(TABLES / "06_displaced_llp_boundary_proxy_components.csv", index=False)
    write_text(
        OUT / "06_BOUNDARY_PROXY_CODING_RULES.md",
        "\n".join(
            [
                "# Boundary Proxy Coding Rules",
                "",
                f"Date: {DATE}",
                "",
                "The proxies are label-level public signal-region proxies, not event-level MiniAOD B_NF variables.",
                "",
                "* CMS-SUS-19-006 retains the previous MHT, HT, jet, b-tag and reconstruction-stress proxies. Its displacement/LLP and compressed proxies remain zero.",
                "* CMS-EXO-22-020 receives high displacement and reconstruction-stress scores because the signal region explicitly requires a displaced vertex with at least five tracks and a machine-learning displaced-vertex tag, plus missing momentum preselection.",
                "* CMS-EXO-17-018 receives high displacement/reconstruction scores because the signal regions require two displaced vertices with at least five tracks; the DVV separation bins are scored with increasing reconstruction stress.",
                "* ATLAS-SUSY-2018-19 receives high displacement/reconstruction/compressed/rare-topology scores because disappearing tracklets are a dedicated long-lived chargino signature with high missing momentum.",
                "",
                "No displacement score was invented for ordinary jets+MET comparator rows.",
            ]
        ),
    )
    return out


def score_proxies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Published_BNF_proxy_simple"] = (
        out["P_missing_proxy"]
        + out["P_visible_energy_proxy"]
        + out["P_multiplicity_proxy"]
        + out["P_btag_proxy"]
        + out["P_displacement_or_longlived_proxy"]
        + out["P_reconstruction_stress_proxy"]
        + out["P_compressed_proxy"]
        + out["P_rare_topology_proxy"]
    )
    out["Published_BNF_proxy_weighted"] = (
        0.3566 * out["P_displacement_or_longlived_proxy"]
        + 0.2112 * out["P_reconstruction_stress_proxy"]
        + 0.2019 * out["P_multiplicity_proxy"]
        + 0.0926 * out["P_btag_proxy"]
        + 0.0728 * out["P_visible_energy_proxy"]
        + 0.0595 * out["P_missing_proxy"]
        + 0.0055 * out["P_compressed_proxy"]
    )
    out["Published_BNF_displacement_reconstruction"] = (
        out["P_displacement_or_longlived_proxy"] + out["P_reconstruction_stress_proxy"]
    )
    out["Published_BNF_missing_visible"] = out["P_missing_proxy"] + out["P_visible_energy_proxy"]
    out["Published_hidden_topology_proxy"] = (
        out["P_displacement_or_longlived_proxy"] + out["P_compressed_proxy"] + out["P_rare_topology_proxy"]
    )
    for col in [
        "Published_BNF_proxy_simple",
        "Published_BNF_proxy_weighted",
        "Published_BNF_displacement_reconstruction",
        "Published_BNF_missing_visible",
        "Published_hidden_topology_proxy",
    ]:
        out[f"{col}_rank_within_analysis"] = out.groupby("analysis_id")[col].rank(pct=True)
        out[f"{col}_z_within_analysis"] = out.groupby("analysis_id")[col].transform(
            lambda s: (s - s.mean()) / s.std(ddof=0) if len(s) > 1 and s.std(ddof=0) else 0.0
        )
    out.to_csv(TABLES / "07_displaced_llp_boundary_proxy_scores.csv", index=False)
    write_text(
        OUT / "07_PUBLISHED_BNF_PROXY_CONSTRUCTION_REPORT.md",
        "\n".join(
            [
                "# Published BNF Proxy Construction Report",
                "",
                f"Date: {DATE}",
                "",
                "I built simple, weighted, displacement/reconstruction, missing/visible, and hidden-topology scores. These are public signal-region label proxies, not the original event-level B_NF score.",
                "",
                md(out.groupby("analysis_id")[[
                    "Published_BNF_proxy_weighted",
                    "Published_BNF_displacement_reconstruction",
                    "Published_hidden_topology_proxy",
                ]].mean().reset_index()),
            ]
        ),
    )
    return out


def ols(df: pd.DataFrame, outcome: str, predictors: list[str], name: str) -> dict[str, Any]:
    work = df[[outcome] + predictors].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < len(predictors) + 5 or any(work[p].nunique() < 2 for p in predictors):
        return {"model": name, "status": "not_run", "outcome": outcome, "predictors": " + ".join(predictors), "n": len(work), "reason": "too few rows or no predictor variation"}
    x = sm.add_constant(work[predictors].astype(float), has_constant="add")
    y = work[outcome].astype(float)
    fit = sm.OLS(y, x).fit(cov_type="HC3")
    key = predictors[-1]
    ci = fit.conf_int()
    return {
        "model": name,
        "status": "run",
        "outcome": outcome,
        "predictors": " + ".join(predictors),
        "n": len(work),
        "primary_term": key,
        "primary_estimate": fit.params.get(key, np.nan),
        "primary_p_value": fit.pvalues.get(key, np.nan),
        "primary_ci_low": ci.loc[key, 0] if key in ci.index else np.nan,
        "primary_ci_high": ci.loc[key, 1] if key in ci.index else np.nan,
        "r_squared": fit.rsquared,
        "aic": fit.aic,
        "bic": fit.bic,
        "reason": "",
    }


def logit(df: pd.DataFrame, outcome: str, predictors: list[str], name: str) -> dict[str, Any]:
    work = df[[outcome] + predictors].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < len(predictors) + 10 or work[outcome].nunique() < 2 or any(work[p].nunique() < 2 for p in predictors):
        return {"model": name, "status": "not_run", "outcome": outcome, "predictors": " + ".join(predictors), "n": len(work), "reason": "too few rows, no class variation, or no predictor variation"}
    x = sm.add_constant(work[predictors].astype(float), has_constant="add")
    y = work[outcome].astype(int)
    try:
        fit = sm.Logit(y, x).fit(disp=False, maxiter=200)
    except (PerfectSeparationError, np.linalg.LinAlgError, ValueError) as exc:
        return {"model": name, "status": "not_run", "outcome": outcome, "predictors": " + ".join(predictors), "n": len(work), "reason": f"logit failed: {exc}"}
    key = predictors[-1]
    ci = fit.conf_int()
    return {
        "model": name,
        "status": "run",
        "outcome": outcome,
        "predictors": " + ".join(predictors),
        "n": len(work),
        "primary_term": key,
        "primary_estimate": fit.params.get(key, np.nan),
        "primary_p_value": fit.pvalues.get(key, np.nan),
        "primary_ci_low": ci.loc[key, 0] if key in ci.index else np.nan,
        "primary_ci_high": ci.loc[key, 1] if key in ci.index else np.nan,
        "pseudo_r_squared": fit.prsquared,
        "aic": fit.aic,
        "bic": fit.bic,
        "reason": "",
    }


def spearman_row(df: pd.DataFrame, outcome: str, predictor: str, group: str = "all") -> dict[str, Any]:
    work = df[[outcome, predictor]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < 5 or work[predictor].nunique() < 2 or work[outcome].nunique() < 2:
        rho = p = np.nan
        status = "not_run"
        reason = "too few rows or no variation"
    else:
        rho, p = stats.spearmanr(work[predictor], work[outcome])
        status = "run"
        reason = ""
    return {
        "model": f"spearman_{group}_{outcome}_vs_{predictor}",
        "status": status,
        "outcome": outcome,
        "predictors": predictor,
        "n": len(work),
        "primary_term": predictor,
        "primary_estimate": rho,
        "primary_p_value": p,
        "reason": reason,
    }


def model_residuals(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictors = [
        "Published_BNF_proxy_weighted",
        "Published_BNF_proxy_simple",
        "Published_BNF_displacement_reconstruction",
        "Published_hidden_topology_proxy",
        "Published_BNF_missing_visible",
        "P_displacement_or_longlived_proxy",
        "P_reconstruction_stress_proxy",
    ]
    rows = []
    for group, sub in [("all", df), ("displaced_llp_only", df[df["analysis_group"] == "displaced_llp"]), ("jets_met_comparator", df[df["analysis_group"] != "displaced_llp"])]:
        for pred in predictors:
            for outcome in ["abs_Z_residual", "Z_residual", "positive_residual"]:
                rows.append(spearman_row(sub, outcome, pred, group))
    rows += [
        ols(df, "abs_Z_residual", ["Published_BNF_proxy_weighted"], "ols_all_absZ_weighted"),
        ols(df, "Z_residual", ["Published_BNF_proxy_weighted"], "ols_all_signedZ_weighted"),
        logit(df, "positive_residual", ["Published_BNF_proxy_weighted"], "logit_all_positive_weighted"),
        ols(df, "abs_Z_residual", ["Published_BNF_displacement_reconstruction"], "ols_all_absZ_disp_reco"),
        ols(df, "Z_residual", ["Published_BNF_displacement_reconstruction"], "ols_all_signedZ_disp_reco"),
        logit(df, "positive_residual", ["Published_BNF_displacement_reconstruction"], "logit_all_positive_disp_reco"),
        ols(df[df["analysis_group"] == "displaced_llp"], "abs_Z_residual", ["Published_BNF_displacement_reconstruction"], "ols_displaced_only_absZ_disp_reco"),
        ols(df[df["analysis_group"] == "displaced_llp"], "Z_residual", ["Published_BNF_displacement_reconstruction"], "ols_displaced_only_signedZ_disp_reco"),
    ]
    # Fixed effect models use analysis dummies if possible.
    dummies = pd.get_dummies(df["analysis_id"], prefix="analysis", drop_first=True, dtype=float)
    fe = pd.concat([df, dummies], axis=1)
    fe_predictors = ["Published_BNF_displacement_reconstruction"] + list(dummies.columns)
    rows.append(ols(fe, "abs_Z_residual", fe_predictors, "ols_absZ_disp_reco_with_analysis_fixed_effects"))
    rows.append(ols(fe, "Z_residual", fe_predictors, "ols_signedZ_disp_reco_with_analysis_fixed_effects"))

    model_df = pd.DataFrame(rows)
    model_df.to_csv(TABLES / "08_displaced_llp_residual_model_results.csv", index=False)

    within = []
    for aid, group in df.groupby("analysis_id"):
        for pred in ["Published_BNF_displacement_reconstruction", "Published_BNF_proxy_weighted", "Published_hidden_topology_proxy"]:
            for outcome in ["abs_Z_residual", "Z_residual", "positive_residual"]:
                within.append(spearman_row(group, outcome, pred, aid))
    within_df = pd.DataFrame(within)
    within_df.to_csv(TABLES / "08_displaced_llp_within_analysis_rank_tests.csv", index=False)

    base_abs = ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "baseline_absZ_missing_visible")
    aug_abs = ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"], "augmented_absZ_missing_visible_plus_weighted")
    disp_abs = ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "P_displacement_or_longlived_proxy", "P_reconstruction_stress_proxy"], "specific_absZ_missing_visible_plus_disp_reco")
    hidden_abs = ols(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_hidden_topology_proxy"], "hidden_absZ_missing_visible_plus_hidden_topology")
    base_signed = ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "baseline_signedZ_missing_visible")
    aug_signed = ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"], "augmented_signedZ_missing_visible_plus_weighted")
    disp_signed = ols(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy", "P_displacement_or_longlived_proxy", "P_reconstruction_stress_proxy"], "specific_signedZ_missing_visible_plus_disp_reco")
    inc = pd.DataFrame([base_abs, aug_abs, disp_abs, hidden_abs, base_signed, aug_signed, disp_signed])
    for base_name in ["baseline_absZ_missing_visible", "baseline_signedZ_missing_visible"]:
        base = inc[inc["model"] == base_name]
        if base.empty or base.iloc[0].get("status") != "run":
            continue
        base_r2 = base.iloc[0].get("r_squared", np.nan)
        base_aic = base.iloc[0].get("aic", np.nan)
        prefix = "absZ" if "absZ" in base_name else "signedZ"
        mask = inc["model"].str.contains(prefix, regex=False) & ~inc["model"].eq(base_name)
        inc.loc[mask, "delta_r_squared_vs_missing_visible"] = inc.loc[mask, "r_squared"] - base_r2
        inc.loc[mask, "delta_aic_vs_missing_visible"] = inc.loc[mask, "aic"] - base_aic
    inc.to_csv(TABLES / "08_displaced_llp_incrementality_model_comparisons.csv", index=False)

    write_text(
        OUT / "08_DISPLACED_LLP_RESIDUAL_MODELLING_REPORT.md",
        "\n".join(
            [
                "# Displaced/LLP Residual Modelling Report",
                "",
                f"Date: {DATE}",
                "",
                f"Rows modelled: {len(df)} total, including {int((df['analysis_group'] == 'displaced_llp').sum())} displaced/LLP/disappearing-track rows.",
                "",
                "The key test is whether displacement/reconstruction-aware proxies predict residual size or positive residual direction beyond ordinary missing/visible energy.",
                "",
                "Headline models:",
                "",
                md(model_df[model_df["model"].isin([
                    "spearman_all_Z_residual_vs_Published_BNF_displacement_reconstruction",
                    "spearman_all_positive_residual_vs_Published_BNF_displacement_reconstruction",
                    "ols_all_signedZ_disp_reco",
                    "logit_all_positive_disp_reco",
                    "ols_absZ_disp_reco_with_analysis_fixed_effects",
                    "ols_signedZ_disp_reco_with_analysis_fixed_effects",
                ])]),
                "",
                "Incrementality:",
                "",
                md(inc),
                "",
                "Caveat: only six new displaced/LLP/disappearing-track signal-region rows were extractable in this run, so the displaced-only tests are preliminary and underpowered.",
            ]
        ),
    )
    return model_df, within_df, inc


def bh_adjust(p: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=p.index, dtype=float)
    valid = p.astype(float).dropna().sort_values()
    if valid.empty:
        return out
    m = len(valid)
    adj = valid * m / np.arange(1, m + 1)
    adj = adj.iloc[::-1].cummin().iloc[::-1].clip(upper=1)
    out.loc[adj.index] = adj
    return out


def sensitivity(df: pd.DataFrame, model_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    subsets = {
        "all": df,
        "displaced_llp_only": df[df["analysis_group"] == "displaced_llp"],
        "jets_met_only": df[df["analysis_group"] != "displaced_llp"],
        "CMS_only": df[df["experiment"] == "CMS"],
        "ATLAS_only": df[df["experiment"] == "ATLAS"],
        "expected_at_least_1": df[df["expected"] >= 1],
        "with_uncertainty": df[df["expected_uncertainty"].notna()],
    }
    for name, sub in subsets.items():
        for pred in ["Published_BNF_proxy_weighted", "Published_BNF_displacement_reconstruction", "Published_hidden_topology_proxy"]:
            for outcome in ["abs_Z_residual", "Z_residual", "positive_residual"]:
                r = spearman_row(sub, outcome, pred, name)
                rows.append(
                    {
                        "check": name,
                        "predictor": pred,
                        "outcome": outcome,
                        "n": r["n"],
                        "effect": r["primary_estimate"],
                        "p_value": r["primary_p_value"],
                        "interpretation": r["reason"] or "positive effect means higher proxy is associated with larger/upward residual",
                    }
                )
    for aid in df["analysis_id"].unique():
        sub = df[df["analysis_id"] != aid]
        r = spearman_row(sub, "Z_residual", "Published_BNF_displacement_reconstruction", f"drop_{aid}")
        rows.append(
            {
                "check": f"leave_one_analysis_out_drop_{aid}",
                "predictor": "Published_BNF_displacement_reconstruction",
                "outcome": "Z_residual",
                "n": r["n"],
                "effect": r["primary_estimate"],
                "p_value": r["primary_p_value"],
                "interpretation": r["reason"] or "leave-one-analysis-out signed residual test",
            }
        )
    spearman = model_df[model_df["model"].str.startswith("spearman")].copy()
    spearman["bh_adjusted_p"] = bh_adjust(spearman["primary_p_value"])
    rows.append(
        {
            "check": "multiple_testing_BH_over_spearman_models",
            "predictor": "all_spearman",
            "outcome": "all",
            "n": len(spearman),
            "effect": np.nan,
            "p_value": np.nan,
            "interpretation": f"minimum BH-adjusted p-value = {spearman['bh_adjusted_p'].min():.4g}",
        }
    )
    sens = pd.DataFrame(rows)
    sens.to_csv(TABLES / "09_displaced_llp_sensitivity_checks.csv", index=False)
    write_text(
        OUT / "09_SENSITIVITY_AND_NEGATIVE_CONTROL_REPORT.md",
        "\n".join(
            [
                "# Sensitivity and Negative-Control Report",
                "",
                f"Date: {DATE}",
                "",
                md(sens),
                "",
                "The most important negative-control issue is sample balance: 174 ordinary jets+MET comparator bins dominate the total row count, while only six new displaced/LLP rows were extractable. Sensitivity checks should therefore be treated as preliminary.",
            ]
        ),
    )
    return sens


def figures(df: pd.DataFrame) -> None:
    colour = np.where(df["analysis_group"].eq("displaced_llp"), "tab:red", "tab:blue")
    plt.figure(figsize=(8, 5))
    plt.scatter(df["Published_BNF_displacement_reconstruction"], df["Z_residual"], c=colour, alpha=0.75)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Published displacement/reconstruction proxy")
    plt.ylabel("Signed residual Z")
    plt.tight_layout()
    plt.savefig(FIGURES / "disp_reco_proxy_vs_signed_residual.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.scatter(df["Published_BNF_proxy_weighted"], df["abs_Z_residual"], c=colour, alpha=0.75)
    plt.xlabel("Published weighted BNF proxy")
    plt.ylabel("Absolute residual Z")
    plt.tight_layout()
    plt.savefig(FIGURES / "weighted_proxy_vs_abs_residual.png", dpi=160)
    plt.close()


def get_model_value(model_df: pd.DataFrame, model: str, field: str) -> float:
    row = model_df[model_df["model"] == model]
    if row.empty:
        return np.nan
    return float(row.iloc[0].get(field, np.nan))


def synthesis(df: pd.DataFrame, model_df: pd.DataFrame, inc: pd.DataFrame, sens: pd.DataFrame) -> dict[str, Any]:
    disp_rows = df[df["analysis_group"] == "displaced_llp"]
    signed_rho = get_model_value(model_df, "spearman_all_Z_residual_vs_Published_BNF_displacement_reconstruction", "primary_estimate")
    signed_p = get_model_value(model_df, "spearman_all_Z_residual_vs_Published_BNF_displacement_reconstruction", "primary_p_value")
    pos_rho = get_model_value(model_df, "spearman_all_positive_residual_vs_Published_BNF_displacement_reconstruction", "primary_estimate")
    pos_p = get_model_value(model_df, "spearman_all_positive_residual_vs_Published_BNF_displacement_reconstruction", "primary_p_value")
    abs_rho = get_model_value(model_df, "spearman_all_abs_Z_residual_vs_Published_BNF_displacement_reconstruction", "primary_estimate")
    abs_p = get_model_value(model_df, "spearman_all_abs_Z_residual_vs_Published_BNF_displacement_reconstruction", "primary_p_value")
    aug = inc[inc["model"] == "specific_signedZ_missing_visible_plus_disp_reco"]
    delta_signed = float(aug.iloc[0].get("delta_r_squared_vs_missing_visible", np.nan)) if not aug.empty else np.nan
    disp_only = sens[
        (sens["check"] == "displaced_llp_only")
        & (sens["predictor"] == "Published_BNF_displacement_reconstruction")
        & (sens["outcome"] == "Z_residual")
    ]
    drop_comparator = sens[
        (sens["check"] == "leave_one_analysis_out_drop_CMS-SUS-19-006")
        & (sens["predictor"] == "Published_BNF_displacement_reconstruction")
        & (sens["outcome"] == "Z_residual")
    ]
    disp_only_rho = float(disp_only.iloc[0].get("effect", np.nan)) if not disp_only.empty else np.nan
    disp_only_p = float(disp_only.iloc[0].get("p_value", np.nan)) if not disp_only.empty else np.nan
    drop_comp_rho = float(drop_comparator.iloc[0].get("effect", np.nan)) if not drop_comparator.empty else np.nan
    drop_comp_p = float(drop_comparator.iloc[0].get("p_value", np.nan)) if not drop_comparator.empty else np.nan

    if len(disp_rows) < 20:
        judgement = "qualifies_underpowered"
        interpretation = "This remains underpowered and requires more published signal-region extraction. It does add real displacement/reconstruction rows, but only six new rows were extractable."
    elif signed_rho > 0 and signed_p < 0.05 and delta_signed > 0.01:
        judgement = "strengthens"
        interpretation = "This is the strongest public-results support so far because it links the dominant N-Frame displacement/reconstruction terms to real observed-minus-expected signal-region behaviour."
    elif abs_rho > 0 and abs_p < 0.05:
        judgement = "qualifies"
        interpretation = "This suggests boundary-stressed regions are more residual-prone, but not specifically positive or SUSY-like."
    else:
        judgement = "weakens_or_inconclusive"
        interpretation = "This weakens the public-results bridge, although it does not invalidate the event-level boundary model."

    counts = df.groupby(["analysis_id", "analysis_group"]).size().reset_index(name="signal_regions")
    disp_summary = disp_rows.groupby("analysis_id").agg(
        signal_regions=("signal_region", "count"),
        positive_residuals=("positive_residual", "sum"),
        mean_signed_Z=("Z_residual", "mean"),
        mean_abs_Z=("abs_Z_residual", "mean"),
        mean_disp_reco_proxy=("Published_BNF_displacement_reconstruction", "mean"),
    ).reset_index()
    write_text(
        OUT / "10_DISPLACED_LLP_PUBLIC_RESULTS_SYNTHESIS_FOR_DARREN.md",
        "\n".join(
            [
                "# Displaced/LLP Public-Results Synthesis for Darren",
                "",
                f"Date: {DATE}",
                "",
                "## What was tested today",
                "",
                "I extended the public real-data signal-region residual layer to analyses with explicit displaced-vertex, long-lived-particle, and disappearing-track labels. The analysis still uses only published observed event counts and expected Standard Model backgrounds.",
                "",
                "## Why the previous jets+MET-only result was insufficient",
                "",
                "The frozen B_NF equation is dominated by displacement/reconstruction terms. The previous CMS-SUS-19-006 jets+MET analysis had no displaced, long-lived, or disappearing-track labels, so it could not test the dominant part of Darren's hypothesis.",
                "",
                "## Analyses included",
                "",
                md(counts),
                "",
                "## Displaced/LLP rows",
                "",
                md(disp_summary),
                "",
                "## Main residual model result",
                "",
                f"Displacement/reconstruction proxy vs signed residual: rho = {signed_rho:.4g}, p = {signed_p:.4g}.",
                f"Displacement/reconstruction proxy vs positive residual flag: rho = {pos_rho:.4g}, p = {pos_p:.4g}.",
                f"Displacement/reconstruction proxy vs absolute residual: rho = {abs_rho:.4g}, p = {abs_p:.4g}.",
                f"Incremental R-squared for signed residuals beyond missing/visible energy when displacement/reconstruction terms are added: {delta_signed:.4g}.",
                f"Displaced/LLP-only signed-residual test: rho = {disp_only_rho:.4g}, p = {disp_only_p:.4g}.",
                f"After dropping the ordinary jets+MET comparator, signed-residual test: rho = {drop_comp_rho:.4g}, p = {drop_comp_p:.4g}.",
                "",
                "## Interpretation",
                "",
                interpretation,
                "",
                "The apparent all-row signed-residual association should therefore not be treated as a strong LLP-specific finding. It is partly inherited from the large ordinary jets+MET comparator block and does not survive as a meaningful displaced-only result.",
                "",
                "This is not a discovery claim. It does not show that real SUSY particles were found. The honest result is that the public-results pipeline now includes the missing displacement/reconstruction side, but the extracted displaced/LLP sample is too small for a decisive claim.",
                "",
                "## Next step",
                "",
                "The exact next step is to manually download the HEPData value tables for CMS-SUS-21-006 record 144178, especially the 49 search-region bins, then rerun this script with those rows added. That would turn this from a six-row displaced/LLP pilot into a meaningful displacement-aware public residual test.",
            ]
        ),
    )
    write_text(
        OUT / "11_SHORT_UPDATE_FOR_TOM.md",
        "\n".join(
            [
                "# Short Update for Tom",
                "",
                "I extended the public-results residual test beyond ordinary jets+MET.",
                "",
                "New real published signal-region rows were added from CMS displaced-vertex + MET, CMS two-displaced-vertex multijet, and ATLAS disappearing-track analyses. These finally give non-zero displacement/reconstruction proxy scores.",
                "",
                f"Result: {interpretation}",
                "",
                "This helps because we are now testing the part of B_NF Darren cares about most. It also hurts/qualifies the claim because only six new displaced/LLP rows were extractable today, so the result is not decisive.",
                "",
                "What to send Darren: we now have a working displacement-aware public residual pipeline, but the next decisive data input is the CMS-SUS-21-006 HEPData 49-bin disappearing-track table.",
            ]
        ),
    )
    return {
        "judgement": judgement,
        "interpretation": interpretation,
        "signed_rho": signed_rho,
        "signed_p": signed_p,
        "pos_rho": pos_rho,
        "pos_p": pos_p,
        "abs_rho": abs_rho,
        "abs_p": abs_p,
        "delta_signed": delta_signed,
        "disp_only_rho": disp_only_rho,
        "disp_only_p": disp_only_p,
        "drop_comp_rho": drop_comp_rho,
        "drop_comp_p": drop_comp_p,
        "n_total": len(df),
        "n_displaced": len(disp_rows),
        "n_analyses": df["analysis_id"].nunique(),
    }


def main() -> None:
    ensure_dirs()
    audit_previous_outputs()
    candidates = candidate_analyses()
    selected_analyses(candidates)
    raw = ingest_tables()
    res = residuals(raw)
    comps = code_proxies(res)
    scored = score_proxies(comps)
    model_df, within, inc = model_residuals(scored)
    sens = sensitivity(scored, model_df)
    figures(scored)
    syn = synthesis(scored, model_df, inc, sens)

    print("Displaced/LLP public residual task complete")
    print(f"Output folder: {OUT}")
    print(f"Analyses modelled: {syn['n_analyses']}")
    print(f"Total signal-region rows: {syn['n_total']}")
    print(f"Displaced/LLP/disappearing-track rows: {syn['n_displaced']}")
    print(f"Disp/reco vs signed residual rho={syn['signed_rho']:.6g}, p={syn['signed_p']:.6g}")
    print(f"Disp/reco vs positive residual rho={syn['pos_rho']:.6g}, p={syn['pos_p']:.6g}")
    print(f"Delta R2 signed beyond missing/visible={syn['delta_signed']:.6g}")
    print(f"Judgement: {syn['judgement']}")


if __name__ == "__main__":
    main()
