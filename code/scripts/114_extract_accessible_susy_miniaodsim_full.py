from __future__ import annotations

import pandas as pd

from susy_signal_common import DATE, REPORTS, SIGNAL_OUT, TABLES, run_cmssw_signal


def main() -> None:
    manifest = pd.read_csv(TABLES / "accessible_susy_signal_download_manifest.csv")
    smoke = pd.read_csv(TABLES / "accessible_susy_signal_smoke_extraction_summary.csv")
    ok = manifest.merge(smoke[smoke["status"].eq("success")][["sample_id"]], on="sample_id", how="inner")
    rows = []
    for _, row in ok.iterrows():
        rows.append(run_cmssw_signal(row, "full", 50000))
        pd.DataFrame(rows).to_csv(TABLES / "accessible_susy_signal_full_extraction_summary.csv", index=False)
    summary = pd.DataFrame(rows)
    frames = [pd.read_csv(path, low_memory=False) for path in summary[summary["status"].eq("success")]["output_csv"]] if not summary.empty else []
    combined = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    out = SIGNAL_OUT / "accessible_susy_miniaodsim_event_features.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out, index=False)
    report = [
        "# Accessible SUSY MiniAODSIM Full Extraction Report",
        "",
        f"Date: {DATE}",
        "",
        "Full extraction used a cap of maxEvents=50000 per file. For these files the actual event counts were lower than the cap.",
        "",
        summary.to_markdown(index=False) if not summary.empty else "No full extraction was attempted.",
        "",
        f"Combined output: `{out}`",
    ]
    (REPORTS / "ACCESSIBLE_SUSY_SIGNAL_FULL_EXTRACTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False) if not summary.empty else "No full extraction attempted.")


if __name__ == "__main__":
    main()
