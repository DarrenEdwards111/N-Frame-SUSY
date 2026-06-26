from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TABLES = ROOT / "results" / "tables"
DATE = "2026-06-09"

ANALYSES = [
    {
        "analysis_id": "CMS jets+MET 2016",
        "experiment": "CMS",
        "year": "2016",
        "url": "https://inspirehep.net/literature/1519090",
        "final_state": "multijet plus missing transverse momentum",
        "boundary_relevance": "MET; HT; jet multiplicity; b-tag multiplicity",
        "status": "identified; yield table extraction still required",
    },
    {
        "analysis_id": "CMS photon+jets+MET 2016",
        "experiment": "CMS",
        "year": "2016",
        "url": "https://arxiv.org/abs/1901.06726",
        "final_state": "photon, jets, b-jets and missing transverse momentum",
        "boundary_relevance": "MET; visible recoil; jets; b-tags; T5Wg-like topology",
        "status": "identified; yield table extraction still required",
    },
    {
        "analysis_id": "CMS jets+MET full Run 2",
        "experiment": "CMS",
        "year": "2016-2018",
        "url": "https://arxiv.org/abs/1908.04722",
        "final_state": "jets and missing transverse momentum",
        "boundary_relevance": "MET; HT; jet multiplicity; b-tag multiplicity",
        "status": "identified; yield table extraction still required",
    },
    {
        "analysis_id": "CMS displaced vertices + MET",
        "experiment": "CMS",
        "year": "2016-2018",
        "url": "https://cms-results.web.cern.ch/cms-results/public-results/publications/EXO-22-020/",
        "final_state": "displaced vertices and missing transverse momentum",
        "boundary_relevance": "MET; displacement; reconstruction boundary; split-SUSY/GMSB benchmarks",
        "status": "identified; HEPData link exists but structured yields not locally extracted",
    },
    {
        "analysis_id": "CMS disappearing tracks",
        "experiment": "CMS",
        "year": "2016-2018",
        "url": "https://arxiv.org/abs/2309.16823",
        "final_state": "disappearing tracks",
        "boundary_relevance": "disappearance-compatible topology; reconstruction boundary",
        "status": "identified; yield table extraction still required",
    },
]


def proxy(row: pd.Series) -> float:
    text = f"{row['final_state']} {row['boundary_relevance']}".lower()
    score = 0
    score += 1.0 if "met" in text or "missing" in text else 0
    score += 1.0 if "ht" in text or "recoil" in text or "jets" in text else 0
    score += 1.0 if "multiplicity" in text or "multijet" in text else 0
    score += 0.7 if "b-tag" in text or "b-jets" in text else 0
    score += 1.0 if "displaced" in text or "disappearing" in text or "reconstruction" in text else 0
    score += 0.5 if "compressed" in text else 0
    return score


def main() -> None:
    inventory = pd.DataFrame(ANALYSES)
    inventory["observed_events"] = np.nan
    inventory["expected_background"] = np.nan
    inventory["background_uncertainty"] = np.nan
    inventory["residual"] = np.nan
    inventory["standardised_residual_z"] = np.nan
    inventory.to_csv(TABLES / "published_signal_region_inventory_after_signal_parity.csv", index=False)
    proxy_table = inventory.copy()
    proxy_table["Published_BNF_proxy"] = proxy_table.apply(proxy, axis=1)
    proxy_table["missing_information_flag"] = proxy_table["boundary_relevance"].str.contains("MET|missing", case=False, regex=True)
    proxy_table["visible_recoil_flag"] = proxy_table["boundary_relevance"].str.contains("HT|recoil|jets", case=False, regex=True)
    proxy_table["displacement_or_reconstruction_flag"] = proxy_table["boundary_relevance"].str.contains("displaced|disappearing|reconstruction", case=False, regex=True)
    proxy_table.to_csv(TABLES / "published_signal_region_boundary_proxy_after_signal_parity.csv", index=False)
    residual_models = pd.DataFrame([{
        "model": "residual_vs_published_BNF_proxy",
        "status": "not_run",
        "reason": "Local structured observed/expected signal-region yield tables were not available. Public analyses were identified, but numerical HEPData/yield extraction remains a separate data-ingestion step.",
        "required_next_data": "For each signal region: observed events, expected background, uncertainty, MET/HT/jet/b-tag/displacement labels.",
    }])
    residual_models.to_csv(TABLES / "published_signal_region_residual_models_after_signal_parity.csv", index=False)
    report = [
        "# Published SUSY Signal-Region Overlap After Signal Parity Report",
        "",
        f"Date: {DATE}",
        "",
        "Local files did not contain structured observed/expected HEPData-style signal-region yields. I therefore created an inventory and transparent extraction template instead of overclaiming residual correlations.",
        "",
        "## Analysis Inventory",
        "",
        inventory.to_markdown(index=False),
        "",
        "## Boundary Proxy Template",
        "",
        proxy_table.to_markdown(index=False),
        "",
        "## Residual Model Status",
        "",
        residual_models.to_markdown(index=False),
    ]
    (REPORTS / "PUBLISHED_SIGNAL_REGION_OVERLAP_AFTER_SIGNAL_PARITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(residual_models.to_string(index=False))


if __name__ == "__main__":
    main()
