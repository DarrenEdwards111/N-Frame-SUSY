from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
PYDEPS = ROOT / ".atlas_pydeps"
OUT = ROOT / "outputs_atlas_local_subset_q99_streaming"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
LOG = OUT / "atlas_streaming_progress.log"
DATA_ROOT = Path(r"D:\cern_open_data\atlas_nframe_q99_analogue")

DATA_FILES = ["data_A.1lep.root"]
SM_FILES = [
    "mc_410025.single_top_schan.1lep.root",
    "mc_364165.Wmunu_PTV280_500_CVetoBVeto.1lep.root",
    "mc_364166.Wmunu_PTV280_500_CFilterBVeto.1lep.root",
    "mc_364167.Wmunu_PTV280_500_BFilter.1lep.root",
    "mc_364168.Wmunu_PTV500_1000.1lep.root",
]

FEATURES = ["MET_pt", "HT", "N_jets_30", "N_btags_medium", "N_leptons", "leading_lepton_pt"]
VISIBLE = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_leptons", "leading_lepton_pt"]
MET_BINS = 10
SCORE_QS = [0.0, 0.50, 0.80, 0.90, 0.95, 0.975, 0.99, 1.0]
SCORE_BANDS = ["q000_050", "q050_080", "q080_090", "q090_095", "q095_0975", "q0975_099", "q099_100"]
MIDPOINTS = {
    "q000_050": 0.25,
    "q050_080": 0.65,
    "q080_090": 0.85,
    "q090_095": 0.925,
    "q095_0975": 0.9625,
    "q0975_099": 0.9825,
    "q099_100": 0.995,
}
SIDEBAND_FIT_BANDS = ["q050_080", "q080_090", "q090_095"]
SIDE_REPORT_BANDS = ["q080_090", "q090_095"]
REL_UNC = 0.30
LUMI_PB = 10_000.0


def add_pydeps() -> None:
    import sys

    if str(PYDEPS) not in sys.path:
        sys.path.insert(0, str(PYDEPS))


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    print(msg, flush=True)


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES]:
        path.mkdir(parents=True, exist_ok=True)
    if LOG.exists():
        LOG.unlink()


def family_from_file(name: str) -> str:
    if "Wmunu" in name:
        return "Wmunu"
    if "single_top" in name:
        return "single_top"
    return "other"


def iter_features(path: Path, role: str, family: str, step_size: str = "150 MB"):
    add_pydeps()
    import awkward as ak
    import uproot

    branches = [
        "runNumber",
        "eventNumber",
        "mcWeight",
        "scaleFactor_PILEUP",
        "scaleFactor_ELE",
        "scaleFactor_MUON",
        "scaleFactor_BTAG",
        "scaleFactor_LepTRIGGER",
        "trigE",
        "trigM",
        "lep_n",
        "lep_pt",
        "met_et",
        "jet_pt",
        "jet_MV2c10",
        "XSection",
        "SumWeights",
    ]
    for arrays in uproot.iterate(f"{path}:mini", branches, step_size=step_size, library="ak"):
        n = len(arrays["eventNumber"])
        jet_pt = arrays["jet_pt"]
        jet_n_30 = ak.sum(jet_pt > 30_000, axis=1)
        ht = ak.sum(jet_pt[jet_pt > 30_000], axis=1) / 1000.0
        btags = ak.sum(arrays["jet_MV2c10"] > 0.8244273, axis=1)
        lep_first = ak.fill_none(ak.firsts(arrays["lep_pt"] / 1000.0), 0.0)
        df = pd.DataFrame(
            {
                "source_file": path.name,
                "role": role,
                "family": family,
                "run": np.asarray(arrays["runNumber"], dtype=np.int64),
                "event": np.asarray(arrays["eventNumber"], dtype=np.int64),
                "MET_pt": np.asarray(arrays["met_et"], dtype=float) / 1000.0,
                "HT": np.asarray(ht, dtype=float),
                "N_jets_30": np.asarray(jet_n_30, dtype=float),
                "N_btags_medium": np.asarray(btags, dtype=float),
                "N_leptons": np.asarray(arrays["lep_n"], dtype=float),
                "leading_lepton_pt": np.asarray(lep_first, dtype=float),
                "trigE": np.asarray(arrays["trigE"], dtype=float),
                "trigM": np.asarray(arrays["trigM"], dtype=float),
            }
        )
        if role == "sm_mc":
            weight = np.asarray(arrays["mcWeight"], dtype=float)
            for sf in ["scaleFactor_PILEUP", "scaleFactor_ELE", "scaleFactor_MUON", "scaleFactor_BTAG", "scaleFactor_LepTRIGGER"]:
                weight = weight * np.asarray(arrays[sf], dtype=float)
            xsec = np.asarray(arrays["XSection"], dtype=float)
            sumw = np.asarray(arrays["SumWeights"], dtype=float)
            df["event_weight"] = weight * xsec * LUMI_PB / np.clip(sumw, 1e-12, np.inf)
        else:
            df["event_weight"] = 1.0
        yield df


def extract_to_features() -> tuple[pd.DataFrame, list[Path]]:
    sm_frames = []
    real_csvs = []
    audit = []
    for name in SM_FILES:
        path = DATA_ROOT / name
        if not path.exists():
            log(f"SM missing: {name}")
            continue
        out = SOURCES / f"{path.stem}_features.csv"
        chunks = []
        n_total = 0
        log(f"Extracting SM {name}")
        for i, chunk in enumerate(iter_features(path, "sm_mc", family_from_file(name))):
            chunks.append(chunk)
            n_total += len(chunk)
            if (i + 1) % 5 == 0:
                log(f"  {name}: {n_total:,} events")
        df = pd.concat(chunks, ignore_index=True)
        df.to_csv(out, index=False)
        sm_frames.append(df)
        audit.append({"file": name, "role": "sm_mc", "events": len(df), "feature_csv": str(out)})
        log(f"Finished SM {name}: {len(df):,} events")
    for name in DATA_FILES:
        path = DATA_ROOT / name
        out = SOURCES / f"{path.stem}_features.csv"
        if not path.exists():
            log(f"DATA missing: {name}")
            continue
        first = True
        n_total = 0
        log(f"Extracting DATA {name}")
        for i, chunk in enumerate(iter_features(path, "real_data", "real_data")):
            chunk.to_csv(out, mode="w" if first else "a", index=False, header=first)
            first = False
            n_total += len(chunk)
            if (i + 1) % 5 == 0:
                log(f"  {name}: {n_total:,} events")
        real_csvs.append(out)
        audit.append({"file": name, "role": "real_data", "events": n_total, "feature_csv": str(out)})
        log(f"Finished DATA {name}: {n_total:,} events")
    pd.DataFrame(audit).to_csv(TABLES / "00_atlas_local_feature_audit.csv", index=False)
    if not sm_frames or not real_csvs:
        raise SystemExit("Missing SM or real ATLAS feature inputs.")
    return pd.concat(sm_frames, ignore_index=True), real_csvs


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / weights.sum()
    return float(np.interp(q, cdf, values))


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    mean = float(np.average(values[mask], weights=weights[mask]))
    var = float(np.average((values[mask] - mean) ** 2, weights=weights[mask]))
    return mean, np.sqrt(max(var, 1e-12))


def fit_score(sm: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    sm = sm.copy()
    sm["log1p_MET_pt"] = np.log1p(sm["MET_pt"].clip(lower=0))
    sm["log1p_HT"] = np.log1p(sm["HT"].clip(lower=0))
    w = sm["event_weight"].abs().clip(lower=1e-12).to_numpy(float)
    mean_met, sd_met = weighted_stats(sm["log1p_MET_pt"].to_numpy(float), w)
    x_df = sm[VISIBLE].apply(pd.to_numeric, errors="coerce")
    med = x_df.median().to_numpy(float)
    x = x_df.fillna(pd.Series(med, index=VISIBLE)).to_numpy(float)
    y = ((sm["log1p_MET_pt"] - mean_met) / sd_met).to_numpy(float)
    sw = np.sqrt(w)
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
    sm["atlas_missing_z"] = y
    sm["atlas_missing_resid_visible_only"] = y - design @ coef
    return sm, {"mean_met": mean_met, "sd_met": sd_met, "median": med, "coef": coef}


def apply_score(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    out["log1p_MET_pt"] = np.log1p(out["MET_pt"].clip(lower=0))
    out["log1p_HT"] = np.log1p(out["HT"].clip(lower=0))
    out["atlas_missing_z"] = (out["log1p_MET_pt"] - params["mean_met"]) / params["sd_met"]
    x = out[VISIBLE].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(params["median"], index=VISIBLE)).to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    out["atlas_missing_resid_visible_only"] = out["atlas_missing_z"].to_numpy(float) - design @ params["coef"]
    return out


def define_bins(sm: pd.DataFrame) -> tuple[list[float], dict[int, list[float]]]:
    w = sm["event_weight"].abs().clip(lower=1e-12).to_numpy(float)
    met = sm["MET_pt"].to_numpy(float)
    met_edges = [weighted_quantile(met, w, q) for q in np.linspace(0, 1, MET_BINS + 1)]
    met_edges[0], met_edges[-1] = -np.inf, np.inf
    score = sm["atlas_missing_resid_visible_only"].to_numpy(float)
    score_edges = {}
    for i, (lo, hi) in enumerate(zip(met_edges[:-1], met_edges[1:])):
        mask = (met >= lo) & (met < hi)
        edges = [weighted_quantile(score[mask], w[mask], q) for q in SCORE_QS]
        edges[0], edges[-1] = -np.inf, np.inf
        score_edges[i] = edges
    return met_edges, score_edges


def assign_bands(df: pd.DataFrame, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["met_bin"] = pd.cut(out["MET_pt"], bins=met_edges, labels=False, include_lowest=True).astype("Int64")
    band = np.full(len(out), None, dtype=object)
    score = out["atlas_missing_resid_visible_only"].to_numpy(float)
    met_bin = out["met_bin"].to_numpy()
    for i in range(MET_BINS):
        mask = met_bin == i
        edges = score_edges[i]
        for name, lo, hi in zip(SCORE_BANDS, edges[:-1], edges[1:]):
            band[mask & (score >= lo) & (score < hi)] = name
    out["score_band"] = band
    return out[out["score_band"].notna()].copy()


def score_sm(sm: pd.DataFrame, params: dict, met_edges: list[float], score_edges: dict[int, list[float]]) -> pd.DataFrame:
    sm = assign_bands(sm, met_edges, score_edges)
    sm["jet_bin"] = pd.cut(
        sm["N_jets_30"],
        bins=[-np.inf, 0, 2, 4, np.inf],
        labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
    ).astype(str)
    return sm


def init_counts() -> dict:
    return {
        (jet, met, band): {"observed": 0, "met_bin_n": 0}
        for jet, met, band in product(["0jet", "1to2jets", "3to4jets", "5plusjets"], range(MET_BINS), SCORE_BANDS)
    }


def accumulate_real_counts(real_csvs: list[Path], params: dict, met_edges: list[float], score_edges: dict[int, list[float]]) -> tuple[dict, int]:
    counts = init_counts()
    total = 0
    for csv in real_csvs:
        log(f"Scoring DATA CSV {csv.name}")
        for chunk in pd.read_csv(csv, chunksize=500_000):
            chunk = assign_bands(apply_score(chunk, params), met_edges, score_edges)
            chunk["jet_bin"] = pd.cut(
                chunk["N_jets_30"],
                bins=[-np.inf, 0, 2, 4, np.inf],
                labels=["0jet", "1to2jets", "3to4jets", "5plusjets"],
            ).astype(str)
            total += len(chunk)
            met_totals = chunk.groupby(["jet_bin", "met_bin"], observed=False).size()
            band_totals = chunk.groupby(["jet_bin", "met_bin", "score_band"], observed=False).size()
            for (jet, met), n in met_totals.items():
                for band in SCORE_BANDS:
                    counts[(str(jet), int(met), band)]["met_bin_n"] += int(n)
            for (jet, met, band), n in band_totals.items():
                counts[(str(jet), int(met), str(band))]["observed"] += int(n)
        log(f"  scored {total:,} real events so far")
    return counts, total


def expected_fractions(sm: pd.DataFrame) -> dict:
    out = {}
    for jet, met, band in product(["0jet", "1to2jets", "3to4jets", "5plusjets"], range(MET_BINS), SCORE_BANDS):
        sub = sm[(sm["jet_bin"].eq(jet)) & (sm["met_bin"].eq(met))]
        den = sub["event_weight"].abs().sum()
        num = sub.loc[sub["score_band"].eq(band), "event_weight"].abs().sum()
        out[(jet, met, band)] = float(num / den) if den > 0 else 0.0
    return out


def z_unc(obs: float, exp: float, rel: float) -> float:
    return float((obs - exp) / np.sqrt(max(exp + (rel * exp) ** 2, 1e-12)))


def summarize(counts: dict, fractions: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for key, val in counts.items():
        jet, met, band = key
        exp = val["met_bin_n"] * fractions[key]
        rows.append(
            {
                "jet_bin": jet,
                "met_bin": met,
                "score_band": band,
                "observed": val["observed"],
                "met_bin_n": val["met_bin_n"],
                "sm_fraction": fractions[key],
                "expected_official_shape": exp,
                "midpoint": MIDPOINTS[band],
            }
        )
    table = pd.DataFrame(rows)
    summaries = []
    for jet, sub in table.groupby("jet_bin"):
        fit = sub[sub["score_band"].isin(SIDEBAND_FIT_BANDS)].copy()
        oe = (fit["observed"].to_numpy(float) + 0.5) / (fit["expected_official_shape"].to_numpy(float) + 0.5)
        x = fit["midpoint"].to_numpy(float) - 0.90
        y = np.log(np.clip(oe, 1e-6, np.inf))
        ww = np.sqrt(np.clip(fit["observed"].to_numpy(float), 1.0, np.inf))
        design = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(design * ww[:, None], y * ww, rcond=None)
        sideband_rms = float(np.sqrt(np.average((y - design @ coef) ** 2, weights=ww)))
        idx = table["jet_bin"].eq(jet)
        table.loc[idx, "shape_correction"] = np.exp(coef[0] + (table.loc[idx, "midpoint"] - 0.90) * coef[1])
        table.loc[idx, "expected_shape"] = table.loc[idx, "expected_official_shape"] * table.loc[idx, "shape_correction"]
        rel = float(np.sqrt(REL_UNC**2 + sideband_rms**2))
        shaped = table[idx]
        sig = shaped[shaped["score_band"].eq("q099_100")]
        side = shaped[shaped["score_band"].isin(SIDE_REPORT_BANDS)]
        obs = float(sig["observed"].sum())
        exp = float(sig["expected_shape"].sum())
        side_obs = float(side["observed"].sum())
        side_exp = float(side["expected_official_shape"].sum())
        summaries.append(
            {
                "jet_bin": jet,
                "real_events": int(shaped.groupby("met_bin")["met_bin_n"].first().sum()),
                "sideband_80_95_observed": side_obs,
                "sideband_80_95_expected_official": side_exp,
                "sideband_80_95_obs_exp": side_obs / side_exp if side_exp > 0 else np.inf,
                "q99_observed": obs,
                "q99_expected_shape": exp,
                "q99_obs_exp": obs / exp if exp > 0 else np.inf,
                "sideband_log_rms": sideband_rms,
                "relative_uncertainty_used": rel,
                "q99_Z": z_unc(obs, exp, rel),
            }
        )
    return table, pd.DataFrame(summaries)


def main() -> None:
    ensure_dirs()
    log("ATLAS local subset streaming Q99 analysis started")
    sm, real_csvs = extract_to_features()
    log(f"Fitting ATLAS analogue score on {len(sm):,} SM events")
    sm, params = fit_score(sm)
    met_edges, score_edges = define_bins(sm)
    sm = score_sm(sm, params, met_edges, score_edges)
    sm.to_csv(SOURCES / "atlas_local_sm_scored.csv", index=False)
    fractions = expected_fractions(sm)
    counts, total_real = accumulate_real_counts(real_csvs, params, met_edges, score_edges)
    table, summary = summarize(counts, fractions)
    table.to_csv(TABLES / "01_atlas_local_subset_q99_counts.csv", index=False)
    summary.to_csv(TABLES / "02_atlas_local_subset_q99_summary.csv", index=False)
    report = f"""# ATLAS Local Subset Q99 Streaming Analogue

## Scope

This is a first ATLAS independent-detector analogue using verified local ATLAS Open Data files.

It is not an exact CMS replication: ATLAS 2020 Open Data is a preselected exactly-one-lepton ntuple release, while the CMS result used MET MiniAOD. The purpose is to test whether a similar missing-vs-visible Q99 boundary trace appears in ATLAS event data.

## Inputs

- Real data: {", ".join(DATA_FILES)}
- SM template: {", ".join(SM_FILES)}
- Total real events scored: {total_real:,}
- SM event rows: {len(sm):,}

## Result

{summary.to_markdown(index=False)}

## Interpretation

The key analogue row is `1to2jets`. A positive high-Z result there, without comparable control-bin behaviour, would support detector-independent behaviour. A null result or control-dominated result would not invalidate the CMS finding, but it would mean this ATLAS one-lepton release does not reproduce the trace directly.
"""
    (REPORTS / "01_ATLAS_LOCAL_SUBSET_Q99_STREAMING_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: ATLAS Local Subset Q99 Analogue

Result:

{summary.to_markdown(index=False)}

This uses ATLAS `data_A.1lep.root` and the currently verified local Wmunu/single-top SM subset.
"""
    (REPORTS / "02_SHORT_UPDATE_ATLAS_LOCAL_SUBSET_Q99.md").write_text(short, encoding="utf-8")
    log("ATLAS local subset streaming Q99 analysis complete")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
