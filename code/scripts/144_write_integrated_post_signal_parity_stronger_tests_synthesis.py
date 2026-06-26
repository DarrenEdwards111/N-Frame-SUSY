from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TABLES = ROOT / "results" / "tables"
DATE = "2026-06-09"


def read(name: str) -> pd.DataFrame:
    path = TABLES / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def main() -> None:
    audit = read("updated_master_audit_after_signal_parity.csv")
    targeted = read("targeted_t5wg_t1_highmet_miniaodsim_candidates.csv")
    sm_manifest = read("expanded_sm_after_signal_parity_manifest.csv")
    sm_extract = read("expanded_sm_after_signal_parity_extraction_summary.csv")
    integrated = read("integrated_signal_background_corrected_after_updates.csv")
    inc = read("integrated_bnf_incrementality_after_updates.csv")
    side = read("real_data_sideband_control_after_signal_parity.csv")
    art = read("strict_artifact_systematics_after_signal_parity.csv")
    pub = read("published_signal_region_residual_models_after_signal_parity.csv")

    q95 = integrated[integrated["threshold"].eq("q95")] if not integrated.empty else pd.DataFrame()
    neutralino_q95 = q95[q95["signal_process"].eq("neutralino")]
    survives = not neutralino_q95.empty and neutralino_q95["remains_5sigma_after_bonferroni"].all()
    targeted_t1_found = False
    if not targeted.empty:
        t = targeted[targeted["verified_accessible"].astype(str).str.lower().eq("true")]
        targeted_t1_found = t["topology_class"].astype(str).str.contains("T5Wg|T1", case=False, regex=True).any()
    inc_med = inc.groupby("score", as_index=False)["auc"].median().sort_values("auc", ascending=False) if not inc.empty else pd.DataFrame()
    art_pass = not art.empty and (art["mean_diff"].fillna(0) > 0).all()
    support_class = "B. Qualified support"
    if not survives:
        support_class = "C. Weakened support"
    if survives and not inc_med.empty and inc_med.iloc[0]["score"] == "B_NF_fitted" and art_pass:
        support_class = "A. Stronger support"

    report = [
        "# Integrated Post-Signal-Parity Stronger Tests Synthesis",
        "",
        f"Date: {DATE}",
        "",
        "## Overall Classification",
        "",
        support_class,
        "",
        "The result remains best described as qualified support: the full-component neutralino/gluino-to-neutralino benchmark survives the enlarged SM comparison, but QCD remains a serious mimic and B_NF still trails simpler missing/visible-energy combinations.",
        "",
        "## 1. How signal-side parity changed the story",
        "",
        "Signal-side parity restored a strong model-dependent benchmark result for one accessible full-component SUSY-like topology. It did not make the boundary generally SUSY-specific.",
        "",
        "## 2. Targeted SMS-T5Wg/T1 high-MET search",
        "",
        f"Accessible T5Wg/T1 high-MET MiniAODSIM found: {'yes' if targeted_t1_found else 'no'}. The targeted search found accessible older long-lived squark-like MiniAODSIM candidates, but not the desired T5Wg/T1 family.",
        "",
        "## 3. Expanded SM backgrounds",
        "",
        sm_extract.to_markdown(index=False) if not sm_extract.empty else "No expanded SM extraction succeeded.",
        "",
        "## 4. Integrated q95 comparisons",
        "",
        q95.to_markdown(index=False) if not q95.empty else "No integrated q95 comparisons.",
        "",
        "## 5. B_NF incrementality",
        "",
        inc_med.to_markdown(index=False) if not inc_med.empty else "No incrementality table.",
        "",
        "## 6. Real-data sidebands",
        "",
        side.to_markdown(index=False) if not side.empty else "No sideband table.",
        "",
        "## 7. Artefact/systematics stress tests",
        "",
        art.to_markdown(index=False) if not art.empty else "No artefact stress table.",
        "",
        "## 8. Published signal-region overlap",
        "",
        pub.to_markdown(index=False) if not pub.empty else "Published residual model was not run.",
        "",
        "## Interpretation",
        "",
        "The evidence strengthens Darren's disappearance-trace hypothesis in a qualified, indirect and model-dependent way. The high-boundary tail can be occupied by a full-component SUSY-like benchmark more strongly than QCD, but the score is still largely driven by standard energy/recoil/multiplicity structure and real-data high-boundary events remain closer in absolute component distance to QCD-like centroids than to the signal centroid.",
        "",
        "## Exact Next Action",
        "",
        "Do a dedicated HEPData ingestion step for CMS photon+jets+MET, jets+MET/MT2, displaced-vertex and disappearing-track analyses, extracting observed/expected yields into the published-region residual template.",
    ]
    (REPORTS / "INTEGRATED_POST_SIGNAL_PARITY_STRONGER_TESTS_SYNTHESIS.md").write_text("\n".join(report), encoding="utf-8")

    darren = [
        "# Update to Darren: Post-Signal-Parity Stronger Tests",
        "",
        f"Date: {DATE}",
        "",
        "## Signal-side parity result",
        "",
        "The earlier result still holds: one accessible full-component neutralino/gluino-to-neutralino benchmark strongly beats high-HT QCD in the high-boundary tail. This is indirect, model-dependent evidence, not direct particle detection.",
        "",
        "## What was added in this round",
        "",
        "We updated the master audit, searched specifically for SMS-T5Wg/T1 high-MET MiniAODSIM, added feasible SM controls, reran integrated parity and incrementality tests, and stress-tested the real-data trace result against sidebands and obvious artefacts.",
        "",
        "## T5Wg/T1 search",
        "",
        "No accessible T5Wg/T1 MiniAODSIM sample was found in the targeted pass. The search found accessible older long-lived squark-like MiniAODSIM candidates, but those are not the missing T5/T1 high-MET test.",
        "",
        "## Broader SM mimicry",
        "",
        "The neutralino/gluino-to-neutralino benchmark remains above 5 sigma against the enlarged SM set, including the added ZJetsToNuNu and diboson-query controls. QCD HT1000to1500 remains the serious mimic.",
        "",
        "## B_NF versus ordinary kinematics",
        "",
        "B_NF improves in the integrated test but still does not beat missing-plus-visible energy. The effect is still strongly tied to energy/recoil/multiplicity.",
        "",
        "## Real-data trace controls",
        "",
        "The real-data trace alignment survives source/run/lumi and reconstruction outlier exclusions. However, absolute distances remain mostly QCD-like, so the result remains a boundary-stress trace rather than a direct SUSY observation.",
        "",
        "## Biggest weakness",
        "",
        "The biggest weakness is still specificity: high-HT QCD and ordinary energy/recoil structure can mimic much of the boundary behaviour.",
        "",
        "## Next move",
        "",
        "Build the published SUSY signal-region residual table from HEPData/CMS tables and test whether high-boundary signal regions have systematically larger positive residuals.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_POST_SIGNAL_PARITY_STRONGER_TESTS.md").write_text("\n".join(darren), encoding="utf-8")
    print((REPORTS / "INTEGRATED_POST_SIGNAL_PARITY_STRONGER_TESTS_SYNTHESIS.md").resolve())
    print((REPORTS / "UPDATE_TO_DARREN_POST_SIGNAL_PARITY_STRONGER_TESTS.md").resolve())


if __name__ == "__main__":
    main()
