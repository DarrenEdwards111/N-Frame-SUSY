from __future__ import annotations

import pandas as pd

from fuller_component_common import DATE, OUT, REPORTS, TABLES


def tag_family(label: str) -> str:
    text = str(label).lower()
    if "t2tt" in text:
        return "SMS-T2tt compressed"
    if "t5wg" in text:
        return "SMS-T5Wg"
    if "qcd ht1000" in text or "ht1000to1500" in text:
        return "QCD HT1000to1500"
    if "qcd ht700" in text or "ht700to1000" in text:
        return "QCD HT700to1000"
    if "wjets" in text or "w4jets" in text:
        return "WJetsToLNu"
    if "single" in text and "top" in text:
        return "SingleTop"
    if "ttjets" in text:
        return "TTJets"
    return str(label)


def tail_table(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    th = pd.read_csv(TABLES / "bnf_thresholds_real_and_sm.csv")
    rows = []
    for (fam, sample, proc, cls), g in df.groupby(["benchmark_family", "sample_id", "process_label", "classification"]):
        row = {
            "component_source": prefix,
            "benchmark_family": fam,
            "sample_id": sample,
            "process_label": proc,
            "classification": cls,
            "events": len(g),
            "mean_BNF": g["B_NF_fitted_frozen_raw"].mean(),
            "component_mode": ";".join(sorted(g.get("component_mode", pd.Series(["unknown"])).dropna().astype(str).unique())),
        }
        for t in th.itertuples(index=False):
            row[f"{t.threshold}_tail_fraction"] = float((g["B_NF_fitted_frozen_raw"] > t.value).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    fuller = pd.read_csv(OUT / "fuller_component_benchmark_events_with_BNF.csv", low_memory=False)
    reduced = pd.read_csv(
        OUT.parents[0] / "expanded_benchmark_features" / "expanded_benchmark_events_with_BNF.csv",
        low_memory=False,
    )
    fuller["benchmark_family"] = fuller["process_label"].map(tag_family)
    reduced["benchmark_family"] = reduced["process_label"].map(tag_family)
    table = pd.concat([tail_table(fuller, "MiniAODSIM fuller-component"), tail_table(reduced, "NanoAODSIM/reduced prior")], ignore_index=True)
    table.to_csv(TABLES / "fuller_vs_reduced_component_tail_comparison.csv", index=False)
    pivot = table.pivot_table(index=["benchmark_family", "classification"], columns="component_source", values=["mean_BNF", "q95_tail_fraction"], aggfunc="mean").reset_index()
    pivot.to_csv(TABLES / "fuller_vs_reduced_component_pivot.csv", index=False)
    report = [
        "# Fuller Component Versus Reduced Component Comparison",
        "",
        f"Date: {DATE}",
        "",
        "This compares MiniAODSIM fuller-component samples against the earlier NanoAODSIM/reduced-component benchmark layer. B_NF is frozen in both cases.",
        "",
        table.to_markdown(index=False),
    ]
    (REPORTS / "FULLER_COMPONENT_VS_REDUCED_COMPONENT_COMPARISON.md").write_text("\n".join(report), encoding="utf-8")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
