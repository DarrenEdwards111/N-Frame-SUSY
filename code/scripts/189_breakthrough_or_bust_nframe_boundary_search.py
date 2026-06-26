from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_breakthrough_or_bust_nframe_boundary_search"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"

SPEC = importlib.util.spec_from_file_location("v4", ROOT / "scripts/188_quality_aware_nframe_v4_cross_era_search.py")
v4 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v4)


COMPONENTS = [
    "missing_resid",
    "disp_reco",
    "visible_energy",
    "multiplicity",
    "btag_structure",
    "lepton_suppression",
    "original_proxy",
]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def normalise_weights(weights: dict[str, float]) -> dict[str, float]:
    scale = sum(abs(v) for v in weights.values() if np.isfinite(v))
    if scale <= 0:
        return weights
    return {k: float(v / scale) for k, v in weights.items() if abs(v) > 1e-12}


def candidate_formulas() -> list[tuple[str, dict[str, float], str]]:
    rows: list[tuple[str, dict[str, float], str]] = []
    for name, weights in v4.candidate_formulas():
        rows.append((f"seed_{name}", normalise_weights(weights), "previous_v4_seed"))

    # Structured grid: this is intentionally broad, but still interpretable.
    missing_vals = [0.35, 0.65, 1.0]
    disp_vals = [0.0, 0.30, 0.60]
    visible_vals = [-0.20, 0.0, 0.20]
    mult_vals = [-0.20, 0.0]
    btag_vals = [0.0, 0.15]
    lepton_vals = [0.0, 0.15]
    for i, vals in enumerate(product(missing_vals, disp_vals, visible_vals, mult_vals, btag_vals, lepton_vals)):
        m, d, vis, mult, btag, lep = vals
        if m == d == vis == mult == btag == lep == 0:
            continue
        weights = normalise_weights(
            {
                "missing_resid": m,
                "disp_reco": d,
                "visible_energy": vis,
                "multiplicity": mult,
                "btag_structure": btag,
                "lepton_suppression": lep,
            }
        )
        rows.append((f"grid_{i:04d}", weights, "structured_component_grid"))

    # A small deterministic random layer can find combinations the coarse grid misses.
    rng = np.random.default_rng(20260616)
    for i in range(48):
        raw = rng.normal(0.0, 0.45, size=len(COMPONENTS))
        raw[0] += rng.choice([0.0, 0.5, 0.9])  # missing-residual emphasis is the current physical trace hypothesis.
        raw[1] += rng.choice([0.0, 0.3, 0.6])  # displacement/reconstruction stress is Darren's original axis.
        weights = normalise_weights(dict(zip(COMPONENTS, raw)))
        rows.append((f"random_{i:03d}", weights, "deterministic_random_component_search"))
    return rows


def direct_tail_summary(counts: pd.DataFrame) -> pd.DataFrame:
    tail = counts[counts["score_band"].eq("q099_100")].copy()
    if tail.empty:
        return pd.DataFrame()
    group_cols = ["candidate", "split", "era", "primary_dataset", "jet_bin"]
    out = (
        tail.groupby(group_cols, observed=False)
        .agg(q99_observed=("observed", "sum"), q99_expected_profile=("expected_official", "sum"))
        .reset_index()
    )
    rel_unc = 0.30
    out["q99_obs_exp_profile"] = out["q99_observed"] / out["q99_expected_profile"].replace(0, np.nan)
    out["q99_profile_Z"] = (out["q99_observed"] - out["q99_expected_profile"]) / np.sqrt(
        out["q99_expected_profile"] + (rel_unc * out["q99_expected_profile"]) ** 2
    ).replace(0, np.nan)
    return out


def score_counts_fast(real: pd.DataFrame, sm: pd.DataFrame, split: str, candidate: str) -> pd.DataFrame:
    rows = []
    sm_den = (
        sm.groupby(["jet_bin", "met_bin_v4"], observed=False)["event_weight"]
        .sum()
        .rename("sm_metbin_weight")
        .reset_index()
    )
    sm_num = (
        sm.groupby(["jet_bin", "met_bin_v4", "score_band_v4"], observed=False)["event_weight"]
        .sum()
        .rename("sm_band_weight")
        .reset_index()
    )
    sm_frac = sm_num.merge(sm_den, on=["jet_bin", "met_bin_v4"], how="left")
    sm_frac["frac"] = sm_frac["sm_band_weight"] / sm_frac["sm_metbin_weight"].replace(0, np.nan)

    r = real[real["split"].eq(split)].copy()
    real_den = (
        r.groupby(["era", "primary_dataset", "jet_bin", "met_bin_v4"], observed=False)
        .size()
        .rename("real_metbin_count")
        .reset_index()
    )
    real_num = (
        r.groupby(["era", "primary_dataset", "jet_bin", "met_bin_v4", "score_band_v4"], observed=False)
        .size()
        .rename("observed")
        .reset_index()
    )
    merged = real_num.merge(real_den, on=["era", "primary_dataset", "jet_bin", "met_bin_v4"], how="left")
    merged = merged.merge(
        sm_frac[["jet_bin", "met_bin_v4", "score_band_v4", "frac"]],
        on=["jet_bin", "met_bin_v4", "score_band_v4"],
        how="left",
    )
    merged["expected_official"] = merged["real_metbin_count"] * merged["frac"].fillna(0.0)
    merged["candidate"] = candidate
    merged["split"] = split
    merged["met_bin"] = merged["met_bin_v4"].astype(int)
    merged["score_band"] = merged["score_band_v4"].astype(str)
    merged["midpoint"] = merged["score_band"].map(v4.MIDPOINTS)
    cols = [
        "candidate",
        "split",
        "era",
        "primary_dataset",
        "jet_bin",
        "met_bin",
        "score_band",
        "observed",
        "expected_official",
        "midpoint",
    ]
    return merged[cols].copy()


def evaluate_region(summary: pd.DataFrame, candidate: str, split: str, signal_jet_bin: str) -> dict:
    sub = summary[(summary["candidate"].eq(candidate)) & (summary["split"].eq(split))]

    def z(era: str, dataset: str, jet_bin: str) -> float:
        row = sub[(sub["era"].eq(era)) & (sub["primary_dataset"].eq(dataset)) & (sub["jet_bin"].eq(jet_bin))]
        if row.empty:
            return np.nan
        return float(row["q99_profile_Z"].iloc[0])

    r16 = z("Run2016", "MET", signal_jet_bin)
    r15_met = z("Run2015D", "MET", signal_jet_bin)
    r15_htmht = z("Run2015D", "HTMHT", signal_jet_bin)
    r15_jetht = z("Run2015D", "JetHT", signal_jet_bin)
    r15_mu = z("Run2015D", "SingleMuon", signal_jet_bin)
    run2016_other = [z("Run2016", "MET", jb) for jb in ["0jet", "1to2jets", "3to4jets", "5plusjets"] if jb != signal_jet_bin]
    max_r16_other = np.nanmax(np.abs(run2016_other)) if any(np.isfinite(run2016_other)) else np.nan
    max_dataset_control = np.nanmax(np.abs([r15_jetht, r15_mu]))
    signal_values = np.array([r16, r15_met, r15_htmht], dtype=float)
    finite = np.isfinite(signal_values)
    stouffer = float(np.nansum(signal_values) / np.sqrt(finite.sum())) if finite.any() else np.nan
    min_signal = float(np.nanmin(signal_values)) if finite.any() else np.nan
    score = min_signal
    for ctrl in [max_r16_other, max_dataset_control]:
        if np.isfinite(ctrl):
            score -= max(0.0, ctrl - 3.0)
    return {
        "candidate": candidate,
        "split": split,
        "signal_jet_bin": signal_jet_bin,
        "Run2016_MET_Z": r16,
        "Run2015D_MET_Z": r15_met,
        "Run2015D_HTMHT_Z": r15_htmht,
        "Run2015D_JetHT_control_Z": r15_jetht,
        "Run2015D_SingleMuon_control_Z": r15_mu,
        "Run2016_other_jetbin_max_absZ": max_r16_other,
        "Run2015D_dataset_control_max_absZ": max_dataset_control,
        "signal_stouffer_Z": stouffer,
        "min_signal_Z": min_signal,
        "selection_score": score,
        "passes_trace_breakthrough_screen": bool(
            min_signal >= 3.0
            and stouffer >= 5.0
            and (not np.isfinite(max_r16_other) or max_r16_other < 3.0)
            and (not np.isfinite(max_dataset_control) or max_dataset_control < 3.0)
        ),
    }


def main() -> None:
    ensure_dirs()
    sm_raw = v4.add_base_transforms(v4.read_sm())
    ref = v4.fit_reference(sm_raw)
    sm = v4.apply_reference(sm_raw, ref)
    real = v4.split_files(v4.apply_reference(v4.read_real(), ref))

    split_audit = (
        real.groupby(["era", "primary_dataset", "split"], observed=False)
        .agg(source_files=("source_file", "nunique"), events=("source_file", "size"))
        .reset_index()
    )
    split_audit.to_csv(TABLES / "01_split_audit.csv", index=False)

    formulas = candidate_formulas()
    formula_rows = []
    dev_rows = []
    all_validation_rows = []
    retained_summary_frames = []
    for idx, (candidate, weights, source) in enumerate(formulas):
        score_col = "candidate_score"
        sm[score_col] = v4.apply_score(sm, weights)
        real[score_col] = v4.apply_score(real, weights)
        met_edges, score_edges = v4.define_edges(sm, score_col)
        sm_b = v4.assign_bands(sm, score_col, met_edges, score_edges)
        real_b = v4.assign_bands(real, score_col, met_edges, score_edges)
        counts_dev = score_counts_fast(real_b, sm_b, "development", candidate)
        summary_dev = direct_tail_summary(counts_dev)
        formula_rows.append({"candidate": candidate, "source": source, **weights})
        for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
            dev_rows.append(evaluate_region(summary_dev, candidate, "development", jet_bin))

        # Keep validation cost bounded: validate any candidate-region that looks remotely promising in development.
        dev_candidate = pd.DataFrame([r for r in dev_rows if r["candidate"] == candidate])
        if dev_candidate["selection_score"].max() >= 0.0 or dev_candidate["signal_stouffer_Z"].max() >= 4.0 or candidate.startswith("seed_"):
            counts_val = score_counts_fast(real_b, sm_b, "validation", candidate)
            summary_val = direct_tail_summary(counts_val)
            retained_summary_frames.append(summary_dev)
            retained_summary_frames.append(summary_val)
            for jet_bin in ["0jet", "1to2jets", "3to4jets", "5plusjets"]:
                all_validation_rows.append(evaluate_region(summary_val, candidate, "validation", jet_bin))
        if (idx + 1) % 25 == 0:
            print(f"evaluated {idx + 1} / {len(formulas)} candidate scores", flush=True)

    formulas_df = pd.DataFrame(formula_rows).fillna(0.0)
    dev_df = pd.DataFrame(dev_rows).sort_values("selection_score", ascending=False)
    val_df = pd.DataFrame(all_validation_rows)
    if not val_df.empty:
        val_df = val_df.merge(
            dev_df[["candidate", "signal_jet_bin", "selection_score", "signal_stouffer_Z"]].rename(
                columns={"selection_score": "development_selection_score", "signal_stouffer_Z": "development_signal_stouffer_Z"}
            ),
            on=["candidate", "signal_jet_bin"],
            how="left",
        )
        val_df = val_df.sort_values(
            ["passes_trace_breakthrough_screen", "selection_score", "signal_stouffer_Z", "min_signal_Z"],
            ascending=False,
        )
    summary_df = pd.concat(retained_summary_frames, ignore_index=True) if retained_summary_frames else pd.DataFrame()

    # Run the slower sideband-profile likelihood only for the best held-out candidates.
    profiled_rows = []
    if not val_df.empty:
        shortlist = val_df.head(20)[["candidate", "signal_jet_bin"]].drop_duplicates()
        weights_by_name = {name: weights for name, weights, _source in formulas}
        for _, row in shortlist.iterrows():
            candidate = row["candidate"]
            weights = weights_by_name[candidate]
            sm["candidate_score"] = v4.apply_score(sm, weights)
            real["candidate_score"] = v4.apply_score(real, weights)
            met_edges, score_edges = v4.define_edges(sm, "candidate_score")
            sm_b = v4.assign_bands(sm, "candidate_score", met_edges, score_edges)
            real_b = v4.assign_bands(real, "candidate_score", met_edges, score_edges)
            counts_val = score_counts_fast(real_b, sm_b, "validation", candidate)
            summary_val_profile = v4.summarize_counts(counts_val)
            profiled_rows.append(evaluate_region(summary_val_profile, candidate, "validation", row["signal_jet_bin"]))
        profile_df = pd.DataFrame(profiled_rows).sort_values(
            ["passes_trace_breakthrough_screen", "selection_score", "signal_stouffer_Z", "min_signal_Z"],
            ascending=False,
        )
    else:
        profile_df = pd.DataFrame()

    formulas_df.to_csv(TABLES / "02_candidate_formula_weights.csv", index=False)
    dev_df.to_csv(TABLES / "03_development_region_screen.csv", index=False)
    val_df.to_csv(TABLES / "04_heldout_validation_region_screen.csv", index=False)
    summary_df.to_csv(TABLES / "05_retained_candidate_profile_summaries.csv", index=False)
    profile_df.to_csv(TABLES / "06_shortlisted_sideband_profile_validation.csv", index=False)

    best = val_df.head(20) if not val_df.empty else pd.DataFrame()
    passes = int(val_df["passes_trace_breakthrough_screen"].sum()) if not val_df.empty else 0
    best_row = best.iloc[0].to_dict() if not best.empty else {}
    report = f"""# Breakthrough-or-Bust N-Frame Boundary Search

## Purpose

This run asked the most direct exploratory question currently available without downloading a new raw-data era:

Can the N-Frame boundary parameters be adjusted so that a high-boundary tail appears in quality-clean Run2016 MET, transfers to quality-clean Run2015D MET and HTMHT, and does not also appear in JetHT or SingleMuon controls?

This is model-development evidence only. It is not a direct SUSY-particle search and it does not prove hidden bulk-space physics. It is designed to tell us whether a stronger trace-region exists in the currently extracted CMS open data.

## Data Split

{split_audit.to_markdown(index=False)}

## Search Space

- Candidate scores tested: {len(formulas_df)}
- Components allowed: {", ".join(COMPONENTS)}
- Boundary band: top 1% score tail within MET-matched bins
- Candidate signal jet bins tested independently: 0jet, 1to2jets, 3to4jets, 5plusjets
- Validation rule: development-selected candidates must work on held-out source files
- Final robustness check: best held-out candidates are rerun with the sideband-profile tail model

The screen is intentionally strict for a trace claim:

- Run2016 MET signal Z must be positive.
- Run2015D MET and HTMHT signal Z must be positive.
- Combined signal Stouffer Z should exceed 5.
- JetHT and SingleMuon controls should stay below |Z| = 3.
- Other Run2016 jet-bin controls should stay below |Z| = 3.

## Best Held-Out Validation Results

{best.to_markdown(index=False)}

## Sideband-Profile Check on Shortlisted Candidates

{profile_df.head(20).to_markdown(index=False) if not profile_df.empty else "No candidates reached the sideband-profile shortlist."}

## Readout

- Candidate-region combinations passing the strict trace-breakthrough screen: {passes}
- Best validation candidate: {best_row.get("candidate", "none")}
- Best validation signal jet bin: {best_row.get("signal_jet_bin", "none")}
- Best validation combined trace Z: {best_row.get("signal_stouffer_Z", np.nan)}
- Best validation minimum per-signal Z: {best_row.get("min_signal_Z", np.nan)}
- Best validation Run2015D dataset-control max |Z|: {best_row.get("Run2015D_dataset_control_max_absZ", np.nan)}

## Interpretation

If no held-out candidate passes this screen, then the present extracted data do not yet contain a clean cross-era N-Frame trace breakthrough. That does not rule out the N-Frame idea, but it means the next step must be either a better official-style SM likelihood for the surviving Run2016 trace or genuinely fresh data, rather than more tuning on the same 2015/2016 samples.
"""
    (REPORTS / "01_BREAKTHROUGH_OR_BUST_NFRAME_BOUNDARY_SEARCH_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: Breakthrough-or-Bust Boundary Search

Candidate scores tested: {len(formulas_df)}

Strict held-out pass count: {passes}

Best held-out rows:

{best.head(10).to_markdown(index=False)}
"""
    (REPORTS / "02_SHORT_UPDATE_BREAKTHROUGH_OR_BUST.md").write_text(short, encoding="utf-8")
    print("BREAKTHROUGH-OR-BUST N-FRAME BOUNDARY SEARCH COMPLETE")
    print(best.head(10).to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
