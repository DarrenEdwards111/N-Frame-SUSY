from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "expanded_run2016h_miniaod_full" / "expanded_run2016h_miniaod_with_fitted_nframe_score.csv"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
PARAMS = [
    "expanded_P_displacement_proxy", "expanded_P_reconstruction", "expanded_P_multiplicity",
    "expanded_P_btag_structure", "expanded_P_visible_energy", "expanded_P_missing", "expanded_P_compression",
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
    score = "B_NF_fitted_expanded_run2016h_z"
    summary = df.groupby("primary_dataset", as_index=False).agg(events=("event", "count"), files=("source_file", "nunique"), runs=("run", "nunique"), mean_score=(score, "mean"), median_score=(score, "median"))
    base = df.primary_dataset.value_counts(normalize=True)
    tail_rows, driver_rows, conc_rows, trig_rows = [], [], [], []
    for q, label in [(0.95, "top05"), (0.99, "top01"), (0.999, "top001")]:
        tail = df[df[score] >= df[score].quantile(q)].copy()
        rest = df.drop(index=tail.index)
        tail["lumi_bin"] = (tail["lumi"] // 25) * 25
        for ds, frac in tail.primary_dataset.value_counts(normalize=True).items():
            tail_rows.append({"tail_label": label, "primary_dataset": ds, "tail_fraction": frac, "baseline_fraction": base[ds], "enrichment_ratio": frac / base[ds], "events": int((tail.primary_dataset == ds).sum())})
        for p in PARAMS:
            driver_rows.append({"tail_label": label, "parameter_family": p.replace("expanded_", ""), "top_mean": tail[p].mean(), "rest_mean": rest[p].mean(), "top_minus_rest": tail[p].mean() - rest[p].mean()})
        conc_rows.append({"tail_label": label, "top_file_fraction": tail.source_file.value_counts(normalize=True).iloc[0], "top_run_fraction": tail.run.value_counts(normalize=True).iloc[0], "top_lumi_bin_fraction": tail.lumi_bin.value_counts(normalize=True).iloc[0], "events": len(tail)})
        for col in [c for c in FILTERS if c in df]:
            trig_rows.append({"tail_label": label, "variable": col, "top_mean": tail[col].mean(), "rest_mean": rest[col].mean(), "top_minus_rest": tail[col].mean() - rest[col].mean()})
    tails = pd.DataFrame(tail_rows)
    drivers = pd.DataFrame(driver_rows).sort_values(["tail_label", "top_minus_rest"], ascending=[True, False])
    conc = pd.DataFrame(conc_rows)
    trig = pd.DataFrame(trig_rows)
    summary.to_csv(TABLES / "expanded_run2016h_fitted_boundary_summary_by_dataset.csv", index=False)
    tails.to_csv(TABLES / "expanded_run2016h_top_tail_composition.csv", index=False)
    drivers.to_csv(TABLES / "expanded_run2016h_parameter_drivers.csv", index=False)
    conc.to_csv(TABLES / "expanded_run2016h_file_run_lumi_concentration.csv", index=False)
    trig.to_csv(TABLES / "expanded_run2016h_trigger_filter_tail_summary.csv", index=False)
    def core(dataset, enriched=True):
        sub = tails[tails.primary_dataset.eq(dataset) & tails.tail_label.isin(["top05", "top01"])]
        return len(sub) == 2 and bool((sub.enrichment_ratio > 1).all() if enriched else (sub.enrichment_ratio < 1).all())
    jetht_core = core("JetHT", True)
    met_core = core("MET", True)
    sm_core = core("SingleMuon", False)
    dominant = drivers[drivers.tail_label.eq("top01")].head(3).parameter_family.tolist()
    compression_weak = drivers[drivers.parameter_family.eq("P_compression")].top_minus_rest.abs().median() < drivers.top_minus_rest.abs().median()
    if jetht_core and met_core and sm_core and "P_displacement_proxy" in dominant:
        classification = "Strong validation"
    elif jetht_core and sm_core and "P_displacement_proxy" in dominant:
        classification = "Partial validation"
    else:
        classification = "Weak validation"
    report = ["# Expanded Run2016H MiniAOD Boundary Validation Report", "", "Date: 2026-06-09", "", "This validates the existing fitted N-Frame equation on expanded independent real Run2016H MiniAOD data. The equation was not refitted.", "", "## Summary", "", summary.to_markdown(index=False), "", "## Top Tail Composition", "", tails.to_markdown(index=False), "", "## Parameter Drivers", "", drivers.to_markdown(index=False), "", "## File/Run/Lumi Concentration", "", conc.to_markdown(index=False), "", "## Trigger/Filter Summary", "", trig.to_markdown(index=False), "", f"Classification: **{classification}**."]
    (REPORTS / "EXPANDED_RUN2016H_MINIAOD_BOUNDARY_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    interp = ["# Expanded Run2016H N-Frame Interpretation", "", "Date: 2026-06-09", "", f"Classification: **{classification}**.", "", "The expanded validation uses real CMS Run2016H MiniAOD data only. It does not use simulation and does not refit the equation.", "", "## What Replicated", "", f"JetHT core enrichment replicated: {jetht_core}.", f"SingleMuon core depletion replicated: {sm_core}.", f"MET core enrichment replicated: {met_core}.", f"Top-1% dominant drivers: {', '.join(dominant)}.", f"Compression remains weak/secondary: {compression_weak}.", "", "## Interpretation", "", "The result remains a boundary-stress validation, not a SUSY classifier and not a discovery claim. Secondary-vertex structure is a proxy and should not be treated as direct evidence of displaced particles."]
    (REPORTS / "EXPANDED_RUN2016H_NFRAME_INTERPRETATION.md").write_text("\n".join(interp), encoding="utf-8")
    update = ["# Update To Darren: Expanded Run2016H Validation", "", "Date: 2026-06-09", "", "We expanded the independent MiniAOD validation using real CMS Run2016H data only. No simulated samples were used.", "", f"Classification: **{classification}**.", "", f"Top-1% dominant boundary parameters: {', '.join(dominant)}.", "", f"JetHT enrichment replicated: {jetht_core}. MET enrichment replicated across top 5% and 1%: {met_core}. SingleMuon depletion replicated: {sm_core}.", "", "This remains a real-data boundary-stress result, not evidence that SUSY was found.", "", "Next step: manually inspect the top fitted-boundary events and then repeat on another run era."]
    (REPORTS / "UPDATE_TO_DARREN_EXPANDED_RUN2016H_VALIDATION.md").write_text("\n".join(update), encoding="utf-8")
    print(summary.to_string(index=False))
    print(tails.to_string(index=False))
    print(drivers[drivers.tail_label.eq("top01")].to_string(index=False))
    print(classification)


if __name__ == "__main__":
    main()
