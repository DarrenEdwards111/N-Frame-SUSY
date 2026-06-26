from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "reports"
DATE = "2026-06-09"
MAX_BYTES = 25 * 1024**3
BG = TABLES / "miniaodsim_background_candidates.csv"
SUSY = TABLES / "miniaodsim_susy_candidate_samples.csv"


def first_url(row) -> tuple[str, int]:
    urls = str(row.get("first_file_urls", "")).split(";")
    sizes = [int(float(x)) for x in str(row.get("first_file_sizes", "")).split(";") if x not in ["", "nan"]]
    return (urls[0] if urls else "", sizes[0] if sizes else int(row.get("min_file_size_bytes", 0)))


def pick(df: pd.DataFrame, contains: str, stage: str, max_size_gb: float = 12) -> list[dict]:
    if df.empty:
        return []
    mask = df["process_label"].astype(str).str.contains(contains, case=False, na=False) if "process_label" in df else df["model_label"].astype(str).str.contains(contains, case=False, na=False)
    cand = df[mask & (df["min_file_size_bytes"] <= max_size_gb * 1024**3)].sort_values(["priority", "min_file_size_bytes"])
    if cand.empty:
        return []
    row = cand.iloc[0].to_dict()
    url, size = first_url(row)
    return [{**row, "stage": stage, "selected_file_url": url, "expected_size_bytes": size}]


def main() -> None:
    bg = pd.read_csv(BG) if BG.exists() else pd.DataFrame()
    susy = pd.read_csv(SUSY) if SUSY.exists() else pd.DataFrame()
    rows = []
    rows += pick(bg, "TTJets|TTTo", "A")
    rows += pick(bg, "QCD HT1000", "A")
    rows += pick(bg, "QCD HT700", "A")
    rows += pick(bg, "DYJets|ZJets|WJets", "B", max_size_gb=6)
    rows += pick(bg, "SingleTop|Diboson", "B", max_size_gb=6)
    rows += pick(susy, "T5Wg|T2tt|T1", "C", max_size_gb=8)
    plan = pd.DataFrame(rows)
    if plan.empty:
        plan = pd.DataFrame(columns=["stage", "record_id", "process_label", "model_label", "data_tier", "selected_file_url", "expected_size_bytes", "reason"])
    plan["classification"] = ["signal" if "model_label" in plan.columns and pd.notna(r.get("model_label")) else "SM_background" for _, r in plan.iterrows()]
    plan["expected_component_improvement"] = "MiniAODSIM should expose packed candidates and secondary vertices through CMSSW, enabling fuller P_reconstruction/P_displacement benchmarking."
    plan["proceed_automatically"] = plan["expected_size_bytes"].sum() <= MAX_BYTES
    plan.to_csv(TABLES / "fuller_component_download_plan.csv", index=False)
    total = int(plan["expected_size_bytes"].sum()) if not plan.empty else 0
    report = ["# Fuller Component Download Plan", "", f"Date: {DATE}", "", f"Planned size: {total / 1024**3:.3f} GiB. Cap: 25 GiB. Proceed automatically: {total <= MAX_BYTES}.", "", plan.to_markdown(index=False) if not plan.empty else "No suitable MiniAODSIM files found under the staged constraints."]
    if total > MAX_BYTES:
        report += ["", "Planned download exceeds cap, so no download should proceed without approval."]
    (REPORTS / "FULLER_COMPONENT_DOWNLOAD_PLAN.md").write_text("\n".join(report), encoding="utf-8")
    print(plan.to_string(index=False))


if __name__ == "__main__":
    main()
