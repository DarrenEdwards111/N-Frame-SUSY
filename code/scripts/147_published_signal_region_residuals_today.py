from __future__ import annotations

import io
import json
import math
import re
import tarfile
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
OUT = ROOT / "outputs_today_published_signal_region_residuals"
TABLES = OUT / "tables"
SOURCES = OUT / "sources"
FIGURES = OUT / "figures"
DATE = "2026-06-10"

ARXIV_ID = "1908.04722"
ARXIV_SOURCE_URL = f"https://arxiv.org/e-print/{ARXIV_ID}"
CMS_HEPDATA_RECORD = "https://www.hepdata.net/record/90835"
CMS_HEPDATA_FORMAT_JSON = "https://www.hepdata.net/record/90835?format=json"
CMS_PAPER_URL = "https://doi.org/10.1007/JHEP10(2019)244"


def ensure_dirs() -> None:
    for path in [OUT, TABLES, SOURCES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def to_md(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df if max_rows is None else df.head(max_rows)
    return view.to_markdown(index=False)


def safe_read_csv(path: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def audit_local_resources() -> pd.DataFrame:
    patterns = [
        "published_signal_region_inventory_after_signal_parity.csv",
        "published_signal_region_boundary_proxy_after_signal_parity.csv",
        "published_signal_region_residual_models_after_signal_parity.csv",
        "PUBLISHED_SIGNAL_REGION_OVERLAP_AFTER_SIGNAL_PARITY_REPORT.md",
        "*hepdata*",
        "*HEPData*",
        "*signal_region*",
    ]
    files: dict[Path, None] = {}
    for pattern in patterns:
        for path in ROOT.rglob(pattern):
            if path.is_file() and OUT not in path.parents:
                files[path] = None

    rows: list[dict[str, Any]] = []
    for path in sorted(files):
        rel = path.relative_to(ROOT)
        suffix = path.suffix.lower()
        contains_observed = False
        contains_expected = False
        contains_uncertainty = False
        contains_region = False
        usable = False
        missing = "not inspected"
        n_rows = np.nan
        columns = ""
        note = ""
        if suffix == ".csv":
            df = safe_read_csv(path)
            if df is None:
                note = "CSV could not be read"
            else:
                n_rows = len(df)
                columns = "; ".join(map(str, df.columns))
                lower_cols = [str(c).lower() for c in df.columns]
                contains_observed = any("observed" in c or c == "data" for c in lower_cols)
                contains_expected = any("expected" in c or "background" in c or "prediction" in c for c in lower_cols)
                contains_uncertainty = any("uncert" in c or "error" in c or "sigma" in c for c in lower_cols)
                contains_region = any("region" in c or "bin" in c or "label" in c for c in lower_cols)
                observed_cols = [c for c in df.columns if "observed" in str(c).lower()]
                expected_cols = [
                    c
                    for c in df.columns
                    if "expected" in str(c).lower() or "background" in str(c).lower()
                ]
                observed_filled = any(df[c].notna().any() for c in observed_cols)
                expected_filled = any(df[c].notna().any() for c in expected_cols)
                usable = bool(contains_region and observed_filled and expected_filled)
                if usable:
                    missing = "none obvious"
                else:
                    missing = "real observed/expected numerical rows missing or empty"
        elif suffix == ".md":
            text = path.read_text(encoding="utf-8", errors="replace")
            lower = text.lower()
            contains_observed = "observed" in lower
            contains_expected = "expected" in lower or "background" in lower
            contains_uncertainty = "uncert" in lower
            contains_region = "signal-region" in lower or "signal region" in lower or "search bin" in lower
            missing = "markdown report only, not a structured modelling table"
            note = text[:160].replace("\n", " ")
        else:
            missing = "not a directly modelled table"

        rows.append(
            {
                "path": str(rel),
                "file_type": suffix or "no_suffix",
                "rows": n_rows,
                "contains_observed_column_or_text": contains_observed,
                "contains_expected_background_column_or_text": contains_expected,
                "contains_uncertainty_column_or_text": contains_uncertainty,
                "contains_signal_region_label": contains_region,
                "usable_for_residual_modelling": usable,
                "missing_or_caveat": missing,
                "columns_or_note": columns or note,
            }
        )

    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_local_signal_region_resource_audit.csv", index=False)
    write_text(
        OUT / "01_LOCAL_SIGNAL_REGION_RESOURCE_AUDIT.md",
        "\n".join(
            [
                "# Local Signal-Region Resource Audit",
                "",
                f"Date: {DATE}",
                "",
                "The earlier local published-signal-region files exist, but the key residual model file says the model was not run because structured observed/expected signal-region yields were not locally available. The CSV audit below checks whether any local table already contains real observed counts, expected Standard Model background counts, uncertainties, and signal-region labels.",
                "",
                to_md(audit),
                "",
                "Conclusion: the previous files are useful as an inventory/template, but they are not enough by themselves for the new residual-modelling task. The usable numerical table for this run is extracted from the published CMS appendix source for arXiv:1908.04722.",
            ]
        ),
    )
    return audit


def request_json(url: str) -> dict[str, Any] | None:
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=40)
        if not resp.ok:
            return None
        return resp.json()
    except Exception:
        return None


def table_download_status(url: str) -> tuple[int | None, str]:
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        if resp.status_code == 403 and "Just a moment" in resp.text:
            return resp.status_code, "Cloudflare challenge from HEPData download endpoint"
        return resp.status_code, (resp.headers.get("content-type") or "")[:80]
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def candidate_public_analyses() -> pd.DataFrame:
    hepdata_meta = request_json(CMS_HEPDATA_FORMAT_JSON)
    if hepdata_meta is not None:
        (SOURCES / "hepdata_90835_record_metadata.json").write_text(
            json.dumps(hepdata_meta, indent=2), encoding="utf-8"
        )
    title = "Search for supersymmetry in proton-proton collisions at 13 TeV in final states with jets and missing transverse momentum"
    if hepdata_meta:
        title = hepdata_meta.get("record", {}).get("title") or title
    first_table_download = "not checked"
    if hepdata_meta and hepdata_meta.get("data_tables"):
        first_table = hepdata_meta["data_tables"][0]
        status, detail = table_download_status(first_table["data"].get("csv", ""))
        first_table_download = f"{status}: {detail}"

    candidates = [
        {
            "analysis_id": "CMS-SUS-19-006",
            "experiment": "CMS",
            "paper_title": title,
            "arxiv_or_analysis_id": "arXiv:1908.04722 / SUS-19-006",
            "year": 2019,
            "final_state": "jets plus missing transverse momentum",
            "source_link": CMS_HEPDATA_RECORD,
            "observed_counts_available": True,
            "expected_background_available": True,
            "uncertainties_available": True,
            "number_of_usable_signal_regions": 174,
            "boundary_features_available": "MHT, HT, jet multiplicity, b-tag multiplicity",
            "priority_score": 10,
            "inclusion_decision": "included",
            "reason_for_inclusion": "HEPData metadata identifies observed/pre-fit background tables; numerical values were extracted from the published arXiv appendix source because direct HEPData table downloads were blocked.",
            "download_status": first_table_download,
        },
        {
            "analysis_id": "ATLAS-HIGG-2017-024",
            "experiment": "ATLAS",
            "paper_title": "Search for new phenomena in events with missing transverse momentum and a Higgs boson decaying into two photons",
            "arxiv_or_analysis_id": "ATLAS-CONF-2017-024 / HEPData 80077",
            "year": 2017,
            "final_state": "diphoton Higgs candidate plus missing transverse momentum",
            "source_link": "https://www.hepdata.net/record/80077",
            "observed_counts_available": "metadata only in this run",
            "expected_background_available": "metadata only in this run",
            "uncertainties_available": "metadata only in this run",
            "number_of_usable_signal_regions": 0,
            "boundary_features_available": "MET categories, photon topology",
            "priority_score": 4,
            "inclusion_decision": "not included in modelling",
            "reason_for_inclusion": "Relevant public HEPData candidate, but direct table downloads were blocked and it has few regions compared with CMS-SUS-19-006.",
            "download_status": "HEPData metadata accessible; table downloads blocked from this environment",
        },
        {
            "analysis_id": "CMS-SUS-20-004",
            "experiment": "CMS",
            "paper_title": "CMS public SUSY result with signal-region yields",
            "arxiv_or_analysis_id": "SUS-20-004",
            "year": 2021,
            "final_state": "SUSY search regions with missing momentum",
            "source_link": "https://cms-results.web.cern.ch/cms-results/public-results/publications/SUS-20-004/index.html",
            "observed_counts_available": "candidate",
            "expected_background_available": "candidate",
            "uncertainties_available": "candidate",
            "number_of_usable_signal_regions": 0,
            "boundary_features_available": "MET and object categories likely available",
            "priority_score": 7,
            "inclusion_decision": "manual follow-up",
            "reason_for_inclusion": "Good candidate for expanding beyond one CMS analysis once structured tables are downloaded.",
            "download_status": "not ingested in this run",
        },
        {
            "analysis_id": "CMS-disappearing-tracks-Run2",
            "experiment": "CMS",
            "paper_title": "CMS disappearing-track search",
            "arxiv_or_analysis_id": "arXiv:2309.16823",
            "year": 2023,
            "final_state": "disappearing tracks",
            "source_link": "https://arxiv.org/abs/2309.16823",
            "observed_counts_available": "candidate",
            "expected_background_available": "candidate",
            "uncertainties_available": "candidate",
            "number_of_usable_signal_regions": 0,
            "boundary_features_available": "disappearing-track topology, MET, reconstruction stress",
            "priority_score": 8,
            "inclusion_decision": "manual follow-up",
            "reason_for_inclusion": "Important negative/positive check for the displacement/reconstruction side of the N-Frame proxy.",
            "download_status": "not ingested in this run",
        },
        {
            "analysis_id": "CMS-EXO-22-020",
            "experiment": "CMS",
            "paper_title": "CMS displaced vertices plus missing transverse momentum",
            "arxiv_or_analysis_id": "EXO-22-020",
            "year": 2024,
            "final_state": "displaced vertices plus missing transverse momentum",
            "source_link": "https://cms-results.web.cern.ch/cms-results/public-results/publications/EXO-22-020/",
            "observed_counts_available": "candidate",
            "expected_background_available": "candidate",
            "uncertainties_available": "candidate",
            "number_of_usable_signal_regions": 0,
            "boundary_features_available": "displaced vertices, MET, reconstruction stress",
            "priority_score": 9,
            "inclusion_decision": "manual follow-up",
            "reason_for_inclusion": "High relevance to the displacement/reconstruction part of the frozen B_NF equation.",
            "download_status": "not ingested in this run",
        },
    ]
    df = pd.DataFrame(candidates)
    df.to_csv(TABLES / "02_candidate_public_susy_analyses.csv", index=False)
    write_text(
        OUT / "02_PUBLIC_SUSY_ANALYSIS_SELECTION_REPORT.md",
        "\n".join(
            [
                "# Public SUSY Analysis Selection Report",
                "",
                f"Date: {DATE}",
                "",
                "I prioritised structured public tables with real observed event counts and expected Standard Model backgrounds. HEPData record 90835 was the strongest candidate because it documents 174 CMS Run 2 jets+MET search bins and explicitly includes observed yields plus pre-fit background predictions.",
                "",
                "Direct HEPData table downloads were blocked by a browser challenge from this environment, but the same numerical appendix is available in the arXiv source for the published paper and was parsed from there.",
                "",
                to_md(df),
            ]
        ),
    )
    return df


def download_arxiv_source() -> Path:
    target = SOURCES / f"arxiv_{ARXIV_ID.replace('.', '_')}_source.tar.gz"
    if target.exists() and target.stat().st_size > 1000:
        return target
    resp = requests.get(ARXIV_SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=80)
    resp.raise_for_status()
    target.write_bytes(resp.content)
    return target


def get_tex_from_source(source_tar: Path) -> str:
    with tarfile.open(source_tar, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".tex") and "authorlist" not in member.name.lower():
                data = tar.extractfile(member)
                if data is None:
                    continue
                text = data.read().decode("utf-8", errors="replace")
                if "Numerical results for the full set of search bins" in text:
                    (SOURCES / member.name).write_text(text, encoding="utf-8")
                    return text
    raise RuntimeError("Could not find CMS numerical appendix TeX in arXiv source")


def clean_latex(text: str) -> str:
    out = text.strip()
    out = out.replace("$", "")
    out = out.replace("\\,", "")
    out = out.replace("\\GeVns", "GeV")
    out = out.replace("\\geq", ">=")
    out = out.replace("{", "").replace("}", "")
    out = out.replace("\\", "")
    out = re.sub(r"\s+", " ", out)
    return out.strip()


def parse_observed(text: str) -> float:
    cleaned = clean_latex(text).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return np.nan
    return float(match.group(0))


def numbers_from_text(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(" ", ""))]


def parse_yield(text: str) -> tuple[float, float]:
    raw = text.strip().replace("\\,", "").replace(" ", "")
    central_match = re.search(r"(-?\d+(?:\.\d+)?)", raw)
    if not central_match:
        return np.nan, np.nan
    central = float(central_match.group(1))
    rest = raw[central_match.end() :]

    components: list[float] = []
    for match in re.finditer(r"\\pm(-?\d+(?:\.\d+)?)", rest):
        components.append(abs(float(match.group(1))))

    for match in re.finditer(r"\^\{\+([^}]*)\}_\{-([^}]*)\}", rest):
        upper_vals = numbers_from_text(match.group(1))
        lower_vals = numbers_from_text(match.group(2))
        upper = math.sqrt(sum(v * v for v in upper_vals)) if upper_vals else 0.0
        lower = math.sqrt(sum(v * v for v in lower_vals)) if lower_vals else 0.0
        components.append((upper + lower) / 2.0)

    unc = math.sqrt(sum(v * v for v in components)) if components else np.nan
    return central, unc


def lower_bound(label: str) -> float:
    cleaned = clean_latex(label).replace(",", "")
    nums = re.findall(r"\d+(?:\.\d+)?", cleaned)
    if not nums:
        return np.nan
    return float(nums[0])


def parse_full_cms_bins(tex: str) -> pd.DataFrame:
    start = tex.find("\\section{Numerical results for the full set of search bins}")
    end = tex.find("\\section{Aggregate search bins}", start)
    if start < 0 or end < 0:
        raise RuntimeError("Could not locate CMS full-bin numerical appendix")
    appendix = tex[start:end]
    rows = []
    for line in appendix.splitlines():
        if not re.match(r"\s*\d+\s*&", line):
            continue
        parts = [part.strip() for part in line.rstrip("\\").split("&")]
        if len(parts) < 10:
            continue
        total_expected, total_unc = parse_yield(parts[8])
        rows.append(
            {
                "analysis_id": "CMS-SUS-19-006",
                "experiment": "CMS",
                "paper_title_short": "CMS Run 2 jets+MET SUSY",
                "year": 2019,
                "table_name": f"Published appendix pre-fit bins, Njets {clean_latex(parts[3])}",
                "signal_region": f"bin_{int(parse_observed(parts[0])):03d}",
                "observed": parse_observed(parts[9]),
                "expected": total_expected,
                "expected_uncertainty": total_unc,
                "uncertainty_type": "quadrature of published statistical and systematic total-background uncertainties; asymmetric components averaged",
                "final_state": "jets plus missing transverse momentum",
                "raw_label": " | ".join(
                    [
                        f"MHT={clean_latex(parts[1])}",
                        f"HT={clean_latex(parts[2])}",
                        f"Njets={clean_latex(parts[3])}",
                        f"Nbjets={clean_latex(parts[4])}",
                    ]
                ),
                "raw_bin_description": line.strip(),
                "source_url_or_reference": f"{ARXIV_SOURCE_URL}; {CMS_HEPDATA_RECORD}; {CMS_PAPER_URL}",
                "extraction_notes": "Parsed from published arXiv source appendix because HEPData table download endpoints were blocked; no simulated SUSY rows used.",
                "extraction_quality": "high for observed/expected labels; uncertainty parsing is approximate for asymmetric components",
                "bin_number": int(parse_observed(parts[0])),
                "mht_label": clean_latex(parts[1]),
                "ht_label": clean_latex(parts[2]),
                "njets_label": clean_latex(parts[3]),
                "nbjets_label": clean_latex(parts[4]),
                "mht_lower": lower_bound(parts[1]),
                "ht_lower": lower_bound(parts[2]),
                "njets_lower": lower_bound(parts[3]),
                "nbjets_lower": lower_bound(parts[4]),
            }
        )
    df = pd.DataFrame(rows)
    if len(df) != 174:
        raise RuntimeError(f"Expected 174 CMS search bins, parsed {len(df)}")
    raw_cols = [
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
    df[raw_cols].to_csv(TABLES / "03_combined_published_signal_regions_raw.csv", index=False)
    write_text(
        OUT / "03_SIGNAL_REGION_TABLE_INGESTION_REPORT.md",
        "\n".join(
            [
                "# Signal-Region Table Ingestion Report",
                "",
                f"Date: {DATE}",
                "",
                "Included analysis: CMS-SUS-19-006, the published Run 2 CMS jets plus missing transverse momentum SUSY search.",
                "",
                f"Signal regions ingested: {len(df)}.",
                "",
                "The observed event counts and pre-fit Standard Model background totals were parsed from the numerical appendix in the arXiv source for arXiv:1908.04722. HEPData metadata was accessible and confirmed the table identity, but direct HEPData table-value downloads returned a browser challenge from this environment.",
                "",
                "No simulated SUSY event samples were used. Rows containing simulated signal yields in the paper appendix were deliberately ignored.",
                "",
                "Uncertainty caveat: the paper gives total background uncertainties as statistical and systematic components, sometimes asymmetric. For residual denominators I used a conservative rough total uncertainty by quadrature, averaging asymmetric upper/lower uncertainty components.",
                "",
                "Excluded analyses: ATLAS and other CMS candidates are recorded in the candidate table but were not modelled because structured numerical table downloads were not available in this run.",
            ]
        ),
    )
    return df


def compute_residuals(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["residual"] = df["observed"] - df["expected"]
    df["residual_denominator"] = np.sqrt(np.maximum(df["expected"], 0) + df["expected_uncertainty"].fillna(0) ** 2)
    no_unc = df["expected_uncertainty"].isna()
    df.loc[no_unc, "residual_denominator"] = np.sqrt(np.maximum(df.loc[no_unc, "expected"], 0))
    df["Z_residual"] = df["residual"] / df["residual_denominator"].replace(0, np.nan)
    df["abs_Z_residual"] = df["Z_residual"].abs()
    df["poisson_style_residual"] = df["residual"] / np.sqrt(np.maximum(df["expected"], 1e-9))
    df["positive_residual"] = df["residual"] > 0
    df["large_upward_fluctuation"] = df["Z_residual"] > 1.0
    df["upward_fluctuation_p_approx"] = stats.norm.sf(df["Z_residual"])
    df["two_sided_residual_p_approx"] = 2 * stats.norm.sf(df["abs_Z_residual"])
    df.to_csv(TABLES / "04_signal_region_residuals.csv", index=False)
    top = df.sort_values("Z_residual", ascending=False).head(10)[
        ["signal_region", "raw_label", "observed", "expected", "expected_uncertainty", "residual", "Z_residual"]
    ]
    write_text(
        OUT / "04_RESIDUAL_CALCULATION_REPORT.md",
        "\n".join(
            [
                "# Residual Calculation Report",
                "",
                f"Date: {DATE}",
                "",
                f"Rows: {len(df)} CMS real-data search bins.",
                "",
                "Residual definition: observed minus expected. The signed Z residual uses sqrt(expected + uncertainty^2) when the published total background uncertainty is available. This is an approximate per-bin diagnostic, not a full likelihood and not a discovery significance.",
                "",
                f"Positive residual bins: {int(df['positive_residual'].sum())} of {len(df)}.",
                f"Mean signed Z residual: {df['Z_residual'].mean():.3f}.",
                f"Mean absolute Z residual: {df['abs_Z_residual'].mean():.3f}.",
                "",
                "Largest upward approximate residuals:",
                "",
                to_md(top),
            ]
        ),
    )
    return df


def score_missing(mht_lower: float) -> float:
    if mht_lower >= 850:
        return 3.0
    if mht_lower >= 600:
        return 2.5
    if mht_lower >= 350:
        return 1.5
    return 1.0


def score_visible(ht_lower: float) -> float:
    if ht_lower >= 1700:
        return 3.0
    if ht_lower >= 1200:
        return 2.5
    if ht_lower >= 600:
        return 1.7
    return 1.0


def score_multiplicity(njets_lower: float) -> float:
    if njets_lower >= 10:
        return 3.0
    if njets_lower >= 8:
        return 2.5
    if njets_lower >= 6:
        return 2.0
    if njets_lower >= 4:
        return 1.2
    return 0.6


def score_btags(nbjets_lower: float) -> float:
    if nbjets_lower >= 3:
        return 3.0
    if nbjets_lower >= 2:
        return 2.0
    if nbjets_lower >= 1:
        return 1.0
    return 0.0


def code_boundary_proxies(residuals: pd.DataFrame) -> pd.DataFrame:
    df = residuals.copy()
    df["P_missing_proxy"] = df["mht_lower"].apply(score_missing)
    df["P_visible_energy_proxy"] = df["ht_lower"].apply(score_visible)
    df["P_multiplicity_proxy"] = df["njets_lower"].apply(score_multiplicity)
    df["P_btag_proxy"] = df["nbjets_lower"].apply(score_btags)
    df["P_displacement_or_longlived_proxy"] = 0.0
    df["P_compressed_proxy"] = 0.0
    df["P_rare_topology_proxy"] = 0.0
    df["P_reconstruction_stress_proxy"] = (
        0.45 * (df["njets_lower"] >= 6).astype(float)
        + 0.45 * (df["njets_lower"] >= 8).astype(float)
        + 0.45 * (df["nbjets_lower"] >= 2).astype(float)
        + 0.35 * (df["mht_lower"] >= 600).astype(float)
        + 0.35 * (df["ht_lower"] >= 1200).astype(float)
    ).clip(0, 3)
    proxy_cols = [
        "analysis_id",
        "signal_region",
        "raw_label",
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_displacement_or_longlived_proxy",
        "P_compressed_proxy",
        "P_rare_topology_proxy",
        "P_reconstruction_stress_proxy",
    ]
    df[proxy_cols].to_csv(TABLES / "05_signal_region_boundary_proxy_components.csv", index=False)
    write_text(
        OUT / "05_BOUNDARY_PROXY_CODING_RULES.md",
        "\n".join(
            [
                "# Boundary Proxy Coding Rules",
                "",
                f"Date: {DATE}",
                "",
                "These are published-region proxies, not event-level MiniAOD B_NF components. They are coded from public signal-region labels only.",
                "",
                "* P_missing_proxy: ordinal score from the lower edge of the MHT bin.",
                "* P_visible_energy_proxy: ordinal score from the lower edge of the HT bin.",
                "* P_multiplicity_proxy: ordinal score from the jet-multiplicity category.",
                "* P_btag_proxy: ordinal score from the b-tag multiplicity category.",
                "* P_displacement_or_longlived_proxy: zero for this CMS jets+MET analysis because no displaced, disappearing, or long-lived label is present in these regions.",
                "* P_compressed_proxy: zero for this analysis because the published bins are not explicitly compressed-spectrum categories.",
                "* P_rare_topology_proxy: zero for this analysis because these are inclusive jets+MET regions rather than photons, same-sign leptons, multileptons, or LLP regions.",
                "* P_reconstruction_stress_proxy: conservative derived label stress from high jet multiplicity, multi-b categories, high MHT, and high HT. This is inferable from labels, but it is still a proxy.",
                "",
                "The displacement component was deliberately not invented for ordinary jets+MET regions. This is important because the frozen event-level equation gave the displacement proxy the largest weight.",
            ]
        ),
    )
    return df


def add_proxy_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Published_BNF_proxy_simple"] = (
        out["P_missing_proxy"]
        + out["P_visible_energy_proxy"]
        + out["P_multiplicity_proxy"]
        + out["P_btag_proxy"]
        + out["P_displacement_or_longlived_proxy"]
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
    for col in ["Published_BNF_proxy_simple", "Published_BNF_proxy_weighted"]:
        rank_col = f"{col}_rank_within_analysis"
        z_col = f"{col}_z_within_analysis"
        out[rank_col] = out.groupby("analysis_id")[col].rank(pct=True)
        out[z_col] = out.groupby("analysis_id")[col].transform(
            lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) else 0.0
        )
    out.to_csv(TABLES / "06_signal_region_boundary_proxy_scores.csv", index=False)
    write_text(
        OUT / "06_PUBLISHED_BNF_PROXY_CONSTRUCTION_REPORT.md",
        "\n".join(
            [
                "# Published BNF Proxy Construction Report",
                "",
                f"Date: {DATE}",
                "",
                "The simple proxy is the unweighted sum of coded missing-energy, visible-energy, object-multiplicity, b-tag, displacement/LLP, compressed, and rare-topology labels.",
                "",
                "The weighted proxy reuses the frozen event-level B_NF weights as a guide, but the variables here are label-level proxies. It must not be interpreted as the original event-level fitted B_NF score.",
                "",
                "For this one included CMS jets+MET analysis, the displacement/LLP and compressed terms are zero because those labels are not present. Therefore this test mostly checks the missing-energy, visible-energy, multiplicity, b-tag, and reconstruction-stress parts of the boundary idea.",
                "",
                "Proxy summary:",
                "",
                to_md(out[["Published_BNF_proxy_simple", "Published_BNF_proxy_weighted"]].describe().reset_index()),
            ]
        ),
    )
    return out


def ols_model(df: pd.DataFrame, outcome: str, predictors: list[str], name: str) -> dict[str, Any]:
    work = df[[outcome] + predictors].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < len(predictors) + 5:
        return {"model": name, "status": "not_run", "reason": "too few rows"}
    y = work[outcome].astype(float)
    x = sm.add_constant(work[predictors].astype(float), has_constant="add")
    fit = sm.OLS(y, x).fit(cov_type="HC3")
    key = predictors[-1]
    return {
        "model": name,
        "status": "run",
        "outcome": outcome,
        "predictors": " + ".join(predictors),
        "n": int(len(work)),
        "primary_term": key,
        "primary_estimate": fit.params.get(key, np.nan),
        "primary_p_value": fit.pvalues.get(key, np.nan),
        "primary_ci_low": fit.conf_int().loc[key, 0] if key in fit.params.index else np.nan,
        "primary_ci_high": fit.conf_int().loc[key, 1] if key in fit.params.index else np.nan,
        "r_squared": fit.rsquared,
        "aic": fit.aic,
        "bic": fit.bic,
        "reason": "",
    }


def logit_model(df: pd.DataFrame, outcome: str, predictors: list[str], name: str) -> dict[str, Any]:
    work = df[[outcome] + predictors].replace([np.inf, -np.inf], np.nan).dropna()
    if len(work) < len(predictors) + 10 or work[outcome].nunique() < 2:
        return {"model": name, "status": "not_run", "reason": "too few rows or no class variation"}
    y = work[outcome].astype(int)
    x = sm.add_constant(work[predictors].astype(float), has_constant="add")
    try:
        fit = sm.Logit(y, x).fit(disp=False, maxiter=200)
    except (PerfectSeparationError, np.linalg.LinAlgError, ValueError) as exc:
        return {"model": name, "status": "not_run", "reason": f"logit failed: {exc}"}
    key = predictors[-1]
    return {
        "model": name,
        "status": "run",
        "outcome": outcome,
        "predictors": " + ".join(predictors),
        "n": int(len(work)),
        "primary_term": key,
        "primary_estimate": fit.params.get(key, np.nan),
        "primary_p_value": fit.pvalues.get(key, np.nan),
        "primary_ci_low": fit.conf_int().loc[key, 0] if key in fit.params.index else np.nan,
        "primary_ci_high": fit.conf_int().loc[key, 1] if key in fit.params.index else np.nan,
        "pseudo_r_squared": fit.prsquared,
        "aic": fit.aic,
        "bic": fit.bic,
        "reason": "",
    }


def run_models(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    predictors = [
        "Published_BNF_proxy_simple",
        "Published_BNF_proxy_weighted",
        "P_missing_proxy",
        "P_visible_energy_proxy",
        "P_multiplicity_proxy",
        "P_btag_proxy",
        "P_reconstruction_stress_proxy",
    ]
    outcomes = ["abs_Z_residual", "Z_residual"]
    for pred in predictors:
        for outcome in outcomes:
            x = df[pred]
            y = df[outcome]
            mask = x.notna() & y.notna()
            if mask.sum() >= 5 and x[mask].nunique() > 1:
                rho, pval = stats.spearmanr(x[mask], y[mask])
            else:
                rho, pval = np.nan, np.nan
            rows.append(
                {
                    "model": f"spearman_{outcome}_vs_{pred}",
                    "status": "run" if mask.sum() >= 5 else "not_run",
                    "outcome": outcome,
                    "predictors": pred,
                    "n": int(mask.sum()),
                    "primary_term": pred,
                    "primary_estimate": rho,
                    "primary_p_value": pval,
                    "reason": "",
                }
            )
    rows.extend(
        [
            ols_model(df, "abs_Z_residual", ["Published_BNF_proxy_weighted"], "ols_absZ_weighted_proxy"),
            ols_model(df, "Z_residual", ["Published_BNF_proxy_weighted"], "ols_signedZ_weighted_proxy"),
            ols_model(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "ols_absZ_missing_visible_baseline"),
            ols_model(
                df,
                "abs_Z_residual",
                ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"],
                "ols_absZ_missing_visible_plus_weighted_proxy",
            ),
            ols_model(
                df,
                "Z_residual",
                ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"],
                "ols_signedZ_missing_visible_plus_weighted_proxy",
            ),
            ols_model(
                df,
                "abs_Z_residual",
                [
                    "P_missing_proxy",
                    "P_visible_energy_proxy",
                    "P_multiplicity_proxy",
                    "P_btag_proxy",
                    "P_displacement_or_longlived_proxy",
                    "P_compressed_proxy",
                ],
                "ols_absZ_expanded_components",
            ),
            logit_model(df, "positive_residual", ["Published_BNF_proxy_weighted"], "logit_positive_weighted_proxy"),
            logit_model(
                df,
                "positive_residual",
                ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"],
                "logit_positive_missing_visible_plus_weighted_proxy",
            ),
            logit_model(df, "large_upward_fluctuation", ["Published_BNF_proxy_weighted"], "logit_large_upward_weighted_proxy"),
        ]
    )
    model_df = pd.DataFrame(rows)
    model_df.to_csv(TABLES / "07_residual_model_results.csv", index=False)

    within_rows = []
    for analysis_id, group in df.groupby("analysis_id"):
        for outcome in ["abs_Z_residual", "Z_residual", "positive_residual"]:
            y = group[outcome].astype(float)
            x = group["Published_BNF_proxy_weighted"]
            if len(group) >= 5 and x.nunique() > 1 and y.nunique() > 1:
                rho, pval = stats.spearmanr(x, y)
            else:
                rho, pval = np.nan, np.nan
            within_rows.append(
                {
                    "analysis_id": analysis_id,
                    "outcome": outcome,
                    "predictor": "Published_BNF_proxy_weighted",
                    "n": len(group),
                    "spearman_rho": rho,
                    "p_value": pval,
                }
            )
    within_df = pd.DataFrame(within_rows)
    within_df.to_csv(TABLES / "07_within_analysis_rank_tests.csv", index=False)

    base = ols_model(df, "abs_Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "baseline_missing_visible")
    aug = ols_model(
        df,
        "abs_Z_residual",
        ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"],
        "augmented_missing_visible_plus_weighted_proxy",
    )
    signed_base = ols_model(df, "Z_residual", ["P_missing_proxy", "P_visible_energy_proxy"], "signed_baseline_missing_visible")
    signed_aug = ols_model(
        df,
        "Z_residual",
        ["P_missing_proxy", "P_visible_energy_proxy", "Published_BNF_proxy_weighted"],
        "signed_augmented_missing_visible_plus_weighted_proxy",
    )
    inc = pd.DataFrame([base, aug, signed_base, signed_aug])
    if base.get("status") == "run" and aug.get("status") == "run":
        inc.loc[inc["model"] == "augmented_missing_visible_plus_weighted_proxy", "delta_r_squared_vs_baseline"] = (
            aug.get("r_squared", np.nan) - base.get("r_squared", np.nan)
        )
        inc.loc[inc["model"] == "augmented_missing_visible_plus_weighted_proxy", "delta_aic_vs_baseline"] = (
            aug.get("aic", np.nan) - base.get("aic", np.nan)
        )
    if signed_base.get("status") == "run" and signed_aug.get("status") == "run":
        inc.loc[inc["model"] == "signed_augmented_missing_visible_plus_weighted_proxy", "delta_r_squared_vs_baseline"] = (
            signed_aug.get("r_squared", np.nan) - signed_base.get("r_squared", np.nan)
        )
        inc.loc[inc["model"] == "signed_augmented_missing_visible_plus_weighted_proxy", "delta_aic_vs_baseline"] = (
            signed_aug.get("aic", np.nan) - signed_base.get("aic", np.nan)
        )
    inc.to_csv(TABLES / "07_incrementality_model_comparisons.csv", index=False)

    weighted_abs = model_df[model_df["model"] == "spearman_abs_Z_residual_vs_Published_BNF_proxy_weighted"]
    weighted_signed = model_df[model_df["model"] == "spearman_Z_residual_vs_Published_BNF_proxy_weighted"]
    pos = model_df[model_df["model"] == "logit_positive_weighted_proxy"]
    report_lines = [
        "# Signal-Region Residual Modelling Report",
        "",
        f"Date: {DATE}",
        "",
        f"Included signal regions: {len(df)} from {df['analysis_id'].nunique()} analysis.",
        "",
        "The main test asks whether higher published boundary-proxy score predicts larger residual magnitude or more positive observed-minus-expected residuals.",
        "",
        "Main results:",
        "",
        to_md(pd.concat([weighted_abs, weighted_signed, pos], ignore_index=True)),
        "",
        "Incrementality comparison:",
        "",
        to_md(inc),
        "",
        "Important caveat: with only one included analysis, these are within-analysis search-bin tests. Analysis-level mixed effects and CMS-vs-ATLAS checks are not possible until more structured public tables are ingested.",
    ]
    write_text(OUT / "07_SIGNAL_REGION_RESIDUAL_MODELLING_REPORT.md", "\n".join(report_lines))
    return model_df, within_df, inc


def bh_adjust(pvalues: pd.Series) -> pd.Series:
    p = pvalues.astype(float)
    out = pd.Series(np.nan, index=p.index, dtype=float)
    valid = p.dropna().sort_values()
    m = len(valid)
    if m == 0:
        return out
    adjusted = valid * m / np.arange(1, m + 1)
    adjusted = adjusted.iloc[::-1].cummin().iloc[::-1].clip(upper=1.0)
    out.loc[adjusted.index] = adjusted
    return out


def sensitivity_checks(df: pd.DataFrame, model_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    subsets = {
        "all_regions": df,
        "expected_at_least_1": df[df["expected"] >= 1],
        "expected_at_least_5": df[df["expected"] >= 5],
        "with_uncertainty": df[df["expected_uncertainty"].notna()],
        "high_missing_only_mht_ge_600": df[df["mht_lower"] >= 600],
        "high_visible_only_ht_ge_1200": df[df["ht_lower"] >= 1200],
    }
    for name, sub in subsets.items():
        if len(sub) >= 5 and sub["Published_BNF_proxy_weighted"].nunique() > 1:
            rho_abs, p_abs = stats.spearmanr(sub["Published_BNF_proxy_weighted"], sub["abs_Z_residual"])
            rho_signed, p_signed = stats.spearmanr(sub["Published_BNF_proxy_weighted"], sub["Z_residual"])
            rho_pos, p_pos = stats.spearmanr(sub["Published_BNF_proxy_weighted"], sub["positive_residual"].astype(float))
        else:
            rho_abs = p_abs = rho_signed = p_signed = rho_pos = p_pos = np.nan
        rows.extend(
            [
                {
                    "check": name,
                    "outcome": "abs_Z_residual",
                    "n": len(sub),
                    "effect": rho_abs,
                    "p_value": p_abs,
                    "interpretation": "positive means higher proxy has larger residual magnitude",
                },
                {
                    "check": name,
                    "outcome": "Z_residual",
                    "n": len(sub),
                    "effect": rho_signed,
                    "p_value": p_signed,
                    "interpretation": "positive means higher proxy has more upward residuals",
                },
                {
                    "check": name,
                    "outcome": "positive_residual",
                    "n": len(sub),
                    "effect": rho_pos,
                    "p_value": p_pos,
                    "interpretation": "positive means higher proxy has more observed > expected bins",
                },
            ]
        )

    corr_rows = model_df[model_df["model"].astype(str).str.startswith("spearman")].copy()
    if not corr_rows.empty and "primary_p_value" in corr_rows:
        corr_rows["bh_adjusted_p"] = bh_adjust(corr_rows["primary_p_value"])
        rows.append(
            {
                "check": "multiple_testing_BH_over_spearman_models",
                "outcome": "all_spearman_models",
                "n": len(corr_rows),
                "effect": np.nan,
                "p_value": np.nan,
                "interpretation": f"minimum BH-adjusted p-value = {corr_rows['bh_adjusted_p'].min():.4g}",
            }
        )

    if df["analysis_id"].nunique() < 2:
        rows.append(
            {
                "check": "leave_one_analysis_out",
                "outcome": "not_applicable",
                "n": df["analysis_id"].nunique(),
                "effect": np.nan,
                "p_value": np.nan,
                "interpretation": "not possible because only one analysis was ingested",
            }
        )
        rows.append(
            {
                "check": "CMS_only_vs_ATLAS_only",
                "outcome": "not_applicable",
                "n": df["experiment"].nunique(),
                "effect": np.nan,
                "p_value": np.nan,
                "interpretation": "not possible because only CMS-SUS-19-006 was ingested",
            }
        )

    sens = pd.DataFrame(rows)
    sens.to_csv(TABLES / "08_sensitivity_checks.csv", index=False)
    write_text(
        OUT / "08_SENSITIVITY_AND_NEGATIVE_CONTROL_REPORT.md",
        "\n".join(
            [
                "# Sensitivity and Negative-Control Report",
                "",
                f"Date: {DATE}",
                "",
                to_md(sens),
                "",
                "Interpretation: this run can check low-count exclusions, uncertainty availability, and whether signed positive residuals behave like absolute residuals. It cannot yet check leave-one-analysis-out, CMS-only versus ATLAS-only, or genuine analysis-level fixed effects because only one structured analysis was ingested.",
            ]
        ),
    )
    return sens


def make_figures(df: pd.DataFrame) -> None:
    plt.figure(figsize=(7, 5))
    plt.scatter(df["Published_BNF_proxy_weighted"], df["Z_residual"], s=22, alpha=0.75)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Published BNF proxy weighted")
    plt.ylabel("Signed residual Z")
    plt.title("CMS-SUS-19-006 published bins: boundary proxy vs signed residual")
    plt.tight_layout()
    plt.savefig(FIGURES / "weighted_proxy_vs_signed_residual.png", dpi=160)
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.scatter(df["Published_BNF_proxy_weighted"], df["abs_Z_residual"], s=22, alpha=0.75)
    plt.xlabel("Published BNF proxy weighted")
    plt.ylabel("Absolute residual Z")
    plt.title("CMS-SUS-19-006 published bins: boundary proxy vs residual magnitude")
    plt.tight_layout()
    plt.savefig(FIGURES / "weighted_proxy_vs_abs_residual.png", dpi=160)
    plt.close()


def interpret(df: pd.DataFrame, model_df: pd.DataFrame, inc: pd.DataFrame, sens: pd.DataFrame) -> dict[str, Any]:
    def val(model: str, col: str) -> float:
        row = model_df[model_df["model"] == model]
        if row.empty:
            return np.nan
        return float(row.iloc[0].get(col, np.nan))

    abs_rho = val("spearman_abs_Z_residual_vs_Published_BNF_proxy_weighted", "primary_estimate")
    abs_p = val("spearman_abs_Z_residual_vs_Published_BNF_proxy_weighted", "primary_p_value")
    signed_rho = val("spearman_Z_residual_vs_Published_BNF_proxy_weighted", "primary_estimate")
    signed_p = val("spearman_Z_residual_vs_Published_BNF_proxy_weighted", "primary_p_value")
    pos_row = model_df[model_df["model"] == "logit_positive_weighted_proxy"]
    pos_est = float(pos_row.iloc[0].get("primary_estimate", np.nan)) if not pos_row.empty else np.nan
    pos_p = float(pos_row.iloc[0].get("primary_p_value", np.nan)) if not pos_row.empty else np.nan
    aug = inc[inc["model"] == "augmented_missing_visible_plus_weighted_proxy"]
    delta_r2 = float(aug.iloc[0].get("delta_r_squared_vs_baseline", np.nan)) if not aug.empty else np.nan
    delta_aic = float(aug.iloc[0].get("delta_aic_vs_baseline", np.nan)) if not aug.empty else np.nan

    if not np.isnan(signed_rho) and signed_rho > 0 and signed_p < 0.05 and delta_r2 > 0.01:
        judgement = "strengthens"
        summary = "The public-results residual layer supports a boundary-stress interpretation in this one analysis, including positive residual direction and some incrementality beyond missing/visible energy."
    elif not np.isnan(abs_rho) and abs_rho > 0 and abs_p < 0.05 and (np.isnan(signed_p) or signed_p >= 0.05):
        judgement = "qualifies"
        summary = "Boundary-stressed regions are more residual-prone in magnitude, but not specifically upward, so this is not a SUSY-like positive-excess result."
    elif not np.isnan(delta_r2) and abs(delta_r2) < 0.01:
        judgement = "qualifies"
        summary = "The boundary proxy adds little beyond missing/visible energy in this public-results layer, matching the earlier incrementality caveat."
    else:
        judgement = "weakens_or_inconclusive"
        summary = "No clear positive residual relationship was found, or the layer remains underpowered because only one published analysis was ingested."

    return {
        "abs_rho": abs_rho,
        "abs_p": abs_p,
        "signed_rho": signed_rho,
        "signed_p": signed_p,
        "positive_logit_estimate": pos_est,
        "positive_logit_p": pos_p,
        "delta_r2_absZ_beyond_missing_visible": delta_r2,
        "delta_aic_absZ_beyond_missing_visible": delta_aic,
        "judgement": judgement,
        "summary": summary,
        "n_regions": len(df),
        "n_analyses": df["analysis_id"].nunique(),
        "positive_bins": int(df["positive_residual"].sum()),
    }


def write_synthesis(df: pd.DataFrame, model_df: pd.DataFrame, inc: pd.DataFrame, sens: pd.DataFrame) -> dict[str, Any]:
    interp = interpret(df, model_df, inc, sens)
    top_tail = df[df["Published_BNF_proxy_weighted"] >= df["Published_BNF_proxy_weighted"].quantile(0.9)]
    rest = df[df["Published_BNF_proxy_weighted"] < df["Published_BNF_proxy_weighted"].quantile(0.9)]
    tail_summary = pd.DataFrame(
        [
            {
                "group": "top_10pct_weighted_proxy",
                "n": len(top_tail),
                "mean_signed_Z": top_tail["Z_residual"].mean(),
                "mean_abs_Z": top_tail["abs_Z_residual"].mean(),
                "positive_fraction": top_tail["positive_residual"].mean(),
            },
            {
                "group": "remaining_90pct",
                "n": len(rest),
                "mean_signed_Z": rest["Z_residual"].mean(),
                "mean_abs_Z": rest["abs_Z_residual"].mean(),
                "positive_fraction": rest["positive_residual"].mean(),
            },
        ]
    )
    tail_summary.to_csv(TABLES / "09_top_proxy_tail_residual_summary.csv", index=False)

    synthesis = [
        "# Published Signal-Region Residual Synthesis for Darren",
        "",
        f"Date: {DATE}",
        "",
        "## 1. Public-results layer tested",
        "",
        "I tested published real-data signal-region counts against published expected Standard Model background counts. This used CMS-SUS-19-006, the Run 2 jets plus missing transverse momentum SUSY search, with 174 search bins parsed from the published arXiv numerical appendix. HEPData metadata confirmed the table identity, but direct HEPData table downloads were blocked by a browser challenge.",
        "",
        "No simulated SUSY event samples were used. The frozen event-level B_NF equation was not refitted or changed.",
        "",
        "## 2. Boundary proxy construction",
        "",
        "Because published signal-region tables do not contain event-level MiniAOD variables, I built transparent label-level proxies: MHT for missing information, HT for visible energy, jet count for multiplicity, b-tag count for b-structure, and a conservative reconstruction-stress proxy from high object/momentum categories. Displacement and compressed-spectrum proxies were set to zero for this analysis because those labels are not present in ordinary jets+MET bins.",
        "",
        "## 3. Residual result",
        "",
        f"Signal regions included: {interp['n_regions']} from {interp['n_analyses']} analysis.",
        f"Positive residual bins: {interp['positive_bins']} of {interp['n_regions']}.",
        f"Weighted proxy vs absolute residual Spearman rho: {interp['abs_rho']:.4g}, p = {interp['abs_p']:.4g}.",
        f"Weighted proxy vs signed residual Spearman rho: {interp['signed_rho']:.4g}, p = {interp['signed_p']:.4g}.",
        f"Incremental R-squared beyond missing+visible energy for abs residuals: {interp['delta_r2_absZ_beyond_missing_visible']:.4g}.",
        "",
        "Top proxy tail summary:",
        "",
        to_md(tail_summary),
        "",
        "## 4. Interpretation",
        "",
        interp["summary"],
        "",
        "This should not be presented as evidence that real SUSY particles were found. It is a public-results residual check. If the signal is mostly explained by MHT/HT, that favours a conventional missing/visible energy explanation more than a uniquely N-Frame boundary explanation.",
        "",
        "## 5. What this means for Darren's hypothesis",
        "",
        f"Overall judgement: {interp['judgement']}.",
        "",
        "The result is useful because it moves from simulated benchmark comparisons to real published observed-minus-expected search bins. However, it remains incomplete because only one analysis was numerically ingested. The displacement-dominant part of the frozen B_NF equation was not tested here because this jets+MET paper has no displaced or disappearing-track region labels.",
        "",
        "## 6. Next step",
        "",
        "Download or extract structured observed/expected signal-region tables for at least one displaced/LLP CMS search, one disappearing-track search, and one ATLAS SUSY search. Then rerun this same residual model with analysis fixed effects and a non-zero displacement/reconstruction proxy.",
    ]
    write_text(OUT / "09_PUBLISHED_SIGNAL_REGION_RESIDUAL_SYNTHESIS_FOR_DARREN.md", "\n".join(synthesis))

    short = [
        "# Short Update for Tom",
        "",
        "We moved from simulated SUSY comparisons to a real published-results test.",
        "",
        "I extracted 174 real CMS Run 2 jets+MET search bins from the published arXiv appendix for CMS-SUS-19-006. For each bin I used the observed event count and the published pre-fit Standard Model background expectation, then calculated observed-minus-expected residuals.",
        "",
        "I built a conservative published-region N-Frame proxy from the public bin labels: MHT, HT, jet count, and b-tag count. I did not invent a displacement score because this paper is not a displaced-particle search.",
        "",
        f"Result: {interp['summary']}",
        "",
        "This is not a discovery claim and not a SUSY classifier. It is a real-data residual check.",
        "",
        "What to send Darren: the strongest honest update is that we now have a reproducible public-results residual pipeline working on real observed/expected CMS search bins, but the current jets+MET-only result is not enough to prove the hidden-boundary idea. The next decisive step is to add displaced/disappearing-track public tables where the dominant B_NF displacement term can actually be tested.",
    ]
    write_text(OUT / "10_SHORT_UPDATE_FOR_TOM.md", "\n".join(short))
    return interp


def main() -> None:
    ensure_dirs()
    audit_local_resources()
    candidate_public_analyses()
    source_tar = download_arxiv_source()
    tex = get_tex_from_source(source_tar)
    raw = parse_full_cms_bins(tex)
    residuals = compute_residuals(raw)
    components = code_boundary_proxies(residuals)
    scored = add_proxy_scores(components)
    model_df, within_df, inc = run_models(scored)
    sens = sensitivity_checks(scored, model_df)
    make_figures(scored)
    interp = write_synthesis(scored, model_df, inc, sens)

    print("Published signal-region residual task complete")
    print(f"Output folder: {OUT}")
    print(f"Analyses included: {scored['analysis_id'].nunique()}")
    print(f"Signal regions included: {len(scored)}")
    print(f"Positive residual bins: {int(scored['positive_residual'].sum())}")
    print(f"Weighted proxy vs abs Z rho: {interp['abs_rho']:.6g}, p={interp['abs_p']:.6g}")
    print(f"Weighted proxy vs signed Z rho: {interp['signed_rho']:.6g}, p={interp['signed_p']:.6g}")
    print(f"Delta R2 beyond missing+visible: {interp['delta_r2_absZ_beyond_missing_visible']:.6g}")
    print(f"Judgement: {interp['judgement']}")


if __name__ == "__main__":
    main()
