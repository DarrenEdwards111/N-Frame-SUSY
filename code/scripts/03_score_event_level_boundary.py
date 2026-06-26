from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from stage2_common import PROCESSED, TABLES, ensure_dirs


def zscore(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    std = vals.std(skipna=True, ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(np.nan, index=series.index)
    return (vals - vals.mean(skipna=True)) / std


def find_input() -> tuple[Path, str]:
    cmssw_dir = PROCESSED / "cmssw_event_features"
    if cmssw_dir.exists():
        files = sorted(cmssw_dir.rglob("event_features*.csv"))
        if files:
            frames = []
            for file in files:
                df = pd.read_csv(file)
                if "sample_id" not in df:
                    df["sample_id"] = file.parent.name
                frames.append(df)
            combined = pd.concat(frames, ignore_index=True)
            out = PROCESSED / "stage2_cmssw_event_features_combined.csv"
            combined.to_csv(out, index=False)
            return out, "cmssw"
    partial = PROCESSED / "stage2_uproot_partial_event_features.csv"
    if partial.exists():
        return partial, "uproot_partial"
    raise SystemExit("No CMSSW or uproot partial event-feature input found.")


def main() -> None:
    ensure_dirs()
    input_path, source = find_input()
    df = pd.read_csv(input_path)
    out = df.copy()
    limitations = []

    for col in ["MET_pt", "N_jets_30", "N_jets_50", "HT", "leading_jet_pt", "subleading_jet_pt", "N_muons", "N_electrons", "N_btags_medium", "jet_mass_sum_30"]:
        if col not in out:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["N_leptons"] = out.get("N_leptons", out["N_muons"].fillna(0) + out["N_electrons"].fillna(0))
    out["N_objects_proxy"] = out["N_jets_30"].fillna(0) + out["N_leptons"].fillna(0) + out["N_btags_medium"].fillna(0)

    if out["MET_pt"].notna().any():
        out["R_missing"] = zscore(np.log1p(out["MET_pt"].clip(lower=0)))
    else:
        out["R_missing"] = np.nan
        limitations.append("R_missing unavailable because MET was not extracted")

    if out["N_jets_30"].notna().any():
        out["R_multiplicity"] = zscore(out["N_jets_30"].fillna(0) + 0.5 * out["N_jets_50"].fillna(0) + out["N_objects_proxy"].fillna(0))
    else:
        out["R_multiplicity"] = np.nan
        limitations.append("R_multiplicity unavailable because jet counts were not extracted")

    recon_raw = (
        np.log1p(out["HT"].clip(lower=0).fillna(0))
        + 0.4 * np.log1p(out["leading_jet_pt"].clip(lower=0).fillna(0))
        + 0.5 * out["N_btags_medium"].fillna(0)
        + 0.2 * out["N_leptons"].fillna(0)
    )
    out["R_reconstruction"] = zscore(recon_raw) if recon_raw.notna().any() else np.nan

    if out["MET_pt"].notna().any() and out["HT"].notna().any():
        out["R_compression_proxy"] = zscore(np.log1p(out["MET_pt"].clip(lower=0)) - np.log1p(out["HT"].clip(lower=0) + 1))
    else:
        out["R_compression_proxy"] = np.nan
        limitations.append("R_compression_proxy unavailable because MET and HT were not both available")

    out["R_lifetime_proxy"] = np.nan
    out["R_displacement_proxy"] = np.nan
    limitations.append("R_lifetime_proxy unavailable; no displaced/lifetime variables extracted")
    limitations.append("R_displacement_proxy unavailable; no displaced track/vertex variables extracted")

    components = [
        "R_missing",
        "R_multiplicity",
        "R_reconstruction",
        "R_compression_proxy",
        "R_lifetime_proxy",
        "R_displacement_proxy",
    ]
    z_components = []
    for component in components:
        z_col = f"{component}_z"
        out[z_col] = zscore(out[component])
        z_components.append(z_col)
    out["available_component_count"] = out[z_components].notna().sum(axis=1)
    out["B_boundary_equal_weight"] = out[z_components].mean(axis=1, skipna=True)
    out["B_boundary_equal_weight_z"] = zscore(out["B_boundary_equal_weight"])
    out["feature_source"] = source
    out["scoring_limitations"] = "; ".join(dict.fromkeys(limitations))

    out_path = PROCESSED / "stage2_event_features_scored.csv"
    out.to_csv(out_path, index=False)

    rows = []
    for sample_id, sub in out.groupby("sample_id", sort=False):
        rows.append(
            {
                "sample_id": sample_id,
                "n_events": len(sub),
                "feature_source": source,
                "mean_available_component_count": sub["available_component_count"].mean(),
                "mean_B_boundary_equal_weight_z": sub["B_boundary_equal_weight_z"].mean(),
                "median_B_boundary_equal_weight_z": sub["B_boundary_equal_weight_z"].median(),
                "mean_R_missing": sub["R_missing"].mean(),
                "mean_R_multiplicity": sub["R_multiplicity"].mean(),
                "mean_R_reconstruction": sub["R_reconstruction"].mean(),
                "mean_R_compression_proxy": sub["R_compression_proxy"].mean(),
                "limitations": "; ".join(dict.fromkeys(sub["scoring_limitations"].dropna().astype(str))),
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "stage2_boundary_component_summary_by_sample.csv", index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

