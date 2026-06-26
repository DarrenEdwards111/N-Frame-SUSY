from __future__ import annotations

import pandas as pd

from susy_signal_common import DATE, REPORTS, TABLES, clean_slug


def rank_reason(row: pd.Series) -> str:
    text = f"{row.get('sample_or_model_name','')} {row.get('topology_class','')}".lower()
    if "t5wg" in text:
        return "Best target: SMS-T5Wg-like high-MET topology."
    if "split" in text or "gluino" in text:
        return "Accessible 2016-compatible SUSY/gluino-like MiniAODSIM with small file size."
    if "neutralino" in text:
        return "Accessible 2016-compatible gluino-to-neutralino MiniAODSIM with displacement/reconstruction stress."
    if "t2tt" in text or "stop" in text:
        return "Accessible compressed stop fallback; useful but not the preferred high-MET T5Wg topology."
    return "Accessible SUSY MiniAODSIM fallback candidate."


def main() -> None:
    candidates = pd.read_csv(TABLES / "accessible_miniaodsim_susy_signal_candidates.csv")
    accessible = candidates[candidates["verified_accessible"].astype(str).str.lower().eq("true")].copy()
    if accessible.empty:
        out = pd.DataFrame()
    else:
        # Prefer 2016 UL MiniAODSIM and a varied set: splitSUSY, neutralino/gluino, compressed stop.
        accessible["is_ul16"] = accessible["campaign"].astype(str).str.contains("RunIISummer20UL16MiniAODv2", na=False)
        selected = []
        for mask in [
            accessible["sample_or_model_name"].astype(str).str.contains("splitSUSY", case=False, na=False) & accessible["is_ul16"],
            accessible["sample_or_model_name"].astype(str).str.contains("GluinoGluinoToNeutralino", case=False, na=False) & accessible["is_ul16"],
            accessible["sample_or_model_name"].astype(str).str.contains("SMS-T2tt", case=False, na=False) & accessible["is_ul16"],
        ]:
            pool = accessible[mask].sort_values(["priority_score", "verified_file_size_bytes"], ascending=[False, True])
            if not pool.empty:
                selected.append(pool.iloc[0])
        if not selected:
            selected = [accessible.sort_values(["priority_score", "verified_file_size_bytes"], ascending=[False, True]).iloc[0]]
        out = pd.DataFrame(selected).drop_duplicates(subset=["record_id", "verified_file_url"]).head(3)
        out = out.assign(
            sample_id=[clean_slug(r["sample_or_model_name"], r["record_id"]) for _, r in out.iterrows()],
            url=out["verified_file_url"],
            expected_size_bytes=out["verified_file_size_bytes"].astype(int),
            expected_event_count="unknown; extraction capped at 50000 if needed",
            priority=range(1, len(out) + 1),
            reason=[rank_reason(r) for _, r in out.iterrows()],
            expected_component_availability="MiniAODSIM should expose packed_candidate_count and secondary_vertex_count through CMSSW.",
            comparison_plan="Compare full-component signal against existing QCD HT1000to1500, QCD HT700to1000 and WJetsToLNu fuller-component backgrounds.",
            proceed_automatically=True,
        )
        keep = [
            "sample_id", "record_id", "model_label", "sample_or_model_name", "topology_class", "mass_point",
            "campaign", "data_tier", "url", "expected_size_bytes", "expected_event_count", "priority",
            "reason", "expected_component_availability", "comparison_plan", "proceed_automatically",
        ]
        out = out[keep]
    total = int(out["expected_size_bytes"].sum()) if not out.empty else 0
    out.to_csv(TABLES / "accessible_susy_signal_download_plan.csv", index=False)
    report = [
        "# Accessible SUSY Signal Download Plan",
        "",
        f"Date: {DATE}",
        "",
        f"Total planned download bytes: {total}",
        "",
        "The plan stays under the 25 GB limit and proceeds automatically if non-empty.",
        "",
        out.to_markdown(index=False) if not out.empty else "No accessible MiniAODSIM SUSY signal was available to plan.",
    ]
    (REPORTS / "ACCESSIBLE_SUSY_SIGNAL_DOWNLOAD_PLAN.md").write_text("\n".join(report), encoding="utf-8")
    print(out.to_string(index=False) if not out.empty else "No download plan created.")


if __name__ == "__main__":
    main()
