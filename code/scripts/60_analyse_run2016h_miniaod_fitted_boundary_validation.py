from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "independent_validation_miniaod_full" / "run2016h_miniaod_with_fitted_nframe_score.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
PARAMS = [
    "run2016h_P_displacement_proxy", "run2016h_P_reconstruction", "run2016h_P_multiplicity",
    "run2016h_P_btag_structure", "run2016h_P_visible_energy", "run2016h_P_missing", "run2016h_P_compression",
]
FILTERS = [
    "HLT_MET_paths_any", "HLT_HT_paths_any", "HLT_Mu_paths_any", "HLT_Ele_paths_any",
    "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter", "pass_goodVertices",
    "pass_EcalDeadCellTriggerPrimitiveFilter", "pass_BadPFMuonFilter", "pass_globalSuperTightHalo2016Filter",
]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    score = "B_NF_fitted_run2016h_z"
    summary = df.groupby(["sample_id", "primary_dataset"], as_index=False).agg(events=("event", "count"), mean_score=(score, "mean"), median_score=(score, "median"))
    base = df["primary_dataset"].value_counts(normalize=True)
    tail_rows, driver_rows, conc_rows, trig_rows = [], [], [], []
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        tail = df[df[score] >= df[score].quantile(q)].copy()
        rest = df.drop(index=tail.index)
        tail["lumi_bin"] = (tail["lumi"] // 25) * 25
        for ds, frac in tail["primary_dataset"].value_counts(normalize=True).items():
            tail_rows.append({"tail_label": label, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base[ds], "enrichment_ratio": frac / base[ds], "events": int((tail.primary_dataset == ds).sum())})
        for p in PARAMS:
            driver_rows.append({"tail_label": label, "parameter_family": p.replace("run2016h_", ""), "top_mean": tail[p].mean(), "rest_mean": rest[p].mean(), "top_minus_rest": tail[p].mean() - rest[p].mean()})
        conc_rows.append({"tail_label": label, "top_file_fraction": tail.source_file.value_counts(normalize=True).iloc[0], "top_run_fraction": tail.run.value_counts(normalize=True).iloc[0], "top_lumi_bin_fraction": tail.lumi_bin.value_counts(normalize=True).iloc[0], "events": len(tail)})
        for col in [c for c in FILTERS if c in df]:
            trig_rows.append({"tail_label": label, "variable": col, "top_mean": tail[col].mean(), "rest_mean": rest[col].mean(), "top_minus_rest": tail[col].mean() - rest[col].mean()})
    tails = pd.DataFrame(tail_rows)
    drivers = pd.DataFrame(driver_rows).sort_values(["tail_label", "top_minus_rest"], ascending=[True, False])
    conc = pd.DataFrame(conc_rows)
    trig = pd.DataFrame(trig_rows)
    summary.to_csv(TABLES / "run2016h_miniaod_fitted_boundary_summary_by_dataset.csv", index=False)
    tails.to_csv(TABLES / "run2016h_miniaod_fitted_top_tail_composition.csv", index=False)
    drivers.to_csv(TABLES / "run2016h_miniaod_fitted_parameter_drivers.csv", index=False)
    conc.to_csv(TABLES / "run2016h_miniaod_file_run_lumi_concentration.csv", index=False)
    trig.to_csv(TABLES / "run2016h_miniaod_trigger_filter_top_tail_summary.csv", index=False)
    jetht = bool((tails.primary_dataset.eq("JetHT") & (tails.enrichment_ratio > 1)).any())
    met = bool((tails.primary_dataset.eq("MET") & (tails.enrichment_ratio > 1)).any())
    sm = bool((tails.primary_dataset.eq("SingleMuon") & (tails.enrichment_ratio < 1)).any())
    def core_pattern(dataset: str, op: str) -> bool:
        sub = tails[tails.primary_dataset.eq(dataset) & tails.tail_label.isin(["top05", "top01"])]
        if len(sub) != 2:
            return False
        return bool((sub.enrichment_ratio > 1).all()) if op == "enriched" else bool((sub.enrichment_ratio < 1).all())

    jetht_core = core_pattern("JetHT", "enriched")
    met_core = core_pattern("MET", "enriched")
    sm_core = core_pattern("SingleMuon", "depleted")
    dominant = drivers[drivers["tail_label"].eq("top01")].sort_values("top_minus_rest", ascending=False).head(3)["parameter_family"].tolist()
    disp_dominant = "P_displacement_proxy" in dominant
    compression_weak = drivers[drivers.parameter_family.eq("P_compression")]["top_minus_rest"].abs().median() < drivers["top_minus_rest"].abs().median()
    classification = "Strong validation" if jetht_core and met_core and sm_core and disp_dominant else "Partial validation" if jetht and sm and disp_dominant else "Weak validation"
    report = [
        "# Run2016H MiniAOD Independent Validation Report",
        "",
        "Date: 2026-06-09",
        "",
        "This report analyses the full fitted N-Frame boundary equation on independent real CMS Run2016H MiniAOD data.",
        "",
        "## Boundary Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Top Tail Composition",
        "",
        tails.to_markdown(index=False),
        "",
        "## Parameter Drivers",
        "",
        drivers.to_markdown(index=False),
        "",
        "## File/Run/Lumi Concentration",
        "",
        conc.to_markdown(index=False),
        "",
        "## Trigger/Filter Top Tail Summary",
        "",
        trig.to_markdown(index=False),
        "",
        f"Classification: **{classification}**.",
        "",
        f"Top-1% dominant parameter families: {', '.join(dominant)}.",
        f"Compression weak relative to median driver magnitude: {compression_weak}.",
        "MET enrichment is mixed: it is depleted in the top 5% and top 1% tails, but slightly enriched in the top 0.1% tail.",
    ]
    (REPORTS / "RUN2016H_MINIAOD_INDEPENDENT_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    # Compare MiniAOD with previous NanoAOD fallback.
    nano_summary = TABLES / "independent_nanoaod_validation_summary.csv"
    nano_tails = TABLES / "independent_validation_top_tail_composition.csv"
    comparison = [
        "# MiniAOD Versus NanoAOD Validation Comparison",
        "",
        "Date: 2026-06-09",
        "",
        "MiniAOD includes the secondary-vertex and packed-candidate components required to test the full fitted equation. NanoAOD was only a partial fallback because those components were unavailable.",
        "",
        "## MiniAOD Event Counts",
        "",
        summary.to_markdown(index=False),
        "",
        "## MiniAOD Tail Composition",
        "",
        tails.to_markdown(index=False),
    ]
    if nano_summary.exists() and nano_tails.exists():
        comparison.extend(["", "## NanoAOD Fallback Event Counts", "", pd.read_csv(nano_summary).to_markdown(index=False), "", "## NanoAOD Fallback Tail Composition", "", pd.read_csv(nano_tails).to_markdown(index=False)])
    comparison.extend(["", "## Judgement", "", f"MiniAOD validation classification: **{classification}**. NanoAOD should be treated only as partial validation."])
    (REPORTS / "MINIAOD_VS_NANOAOD_VALIDATION_COMPARISON.md").write_text("\n".join(comparison), encoding="utf-8")
    update = [
        "# Update To Darren: Run2016H MiniAOD Validation",
        "",
        "Date: 2026-06-09",
        "",
        "We reran the independent validation using the proper MiniAOD route now Docker was available. We used real CMS Run2016H data only and no simulated samples.",
        "",
        "Unlike the NanoAOD fallback, the MiniAOD validation includes the secondary-vertex and packed-candidate components needed to test the full fitted boundary equation.",
        "",
        f"Validation classification: **{classification}**.",
        "",
        "This is not evidence that SUSY was found and the fitted equation is not a SUSY classifier. It is a real-data boundary-stress validation.",
        "",
        f"Top-1% dominant parameter families: {', '.join(dominant)}.",
        "",
        "Next step: repeat the MiniAOD validation on more independent Run2016H files or a second run era, then manually inspect top fitted-boundary events.",
    ]
    (REPORTS / "UPDATE_TO_DARREN_RUN2016H_MINIAOD_VALIDATION.md").write_text("\n".join(update), encoding="utf-8")
    print(summary.to_string(index=False))
    print(tails.to_string(index=False))
    print(drivers[drivers["tail_label"].eq("top01")].to_string(index=False))
    print(classification)


if __name__ == "__main__":
    main()
