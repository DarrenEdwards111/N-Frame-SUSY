from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parents[0]
OUT = ROOT / "outputs_mht_proxy_fresh_run2016h_validation"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
SOURCES = OUT / "sources"
LOGS = OUT / "logs"

DOWNLOAD_ROOT = Path(r"D:\cern_open_data\nframe_fresh_run2016h_tri_dynamic_validation")
CMSSW_WORK = MAIN / "nframe_cms_raw_multi_sample" / "cmssw_full_extraction"
IMAGE = "cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest"

RECORDS = {
    "HTMHT": 30540,
    "JetHT": 30541,
    "MET": 30542,
    "SingleMuon": 30546,
}

QUALITY_FILTERS = ["pass_goodVertices", "pass_HBHENoiseFilter", "pass_HBHENoiseIsoFilter"]
TARGET_JET_BIN = "1to2jets"
JET_BINS = ["0jet", "1to2jets", "3to4jets", "5plusjets"]

WEIGHTS = {
    "MET": {
        "observer_projection": 0.80,
        "physical_projection": 0.00,
        "algebraic_projection": 0.00,
        "ordinary_qcd_axis": -0.20,
        "leptonic_control_axis": 0.00,
    },
    "HTMHT": {
        "observer_projection": 0.45,
        "physical_projection": 0.35,
        "algebraic_projection": 0.10,
        "ordinary_qcd_axis": -0.10,
        "leptonic_control_axis": 0.00,
    },
    "JetHT": {
        "observer_projection": 0.55,
        "physical_projection": 0.00,
        "algebraic_projection": 0.10,
        "ordinary_qcd_axis": -0.35,
        "leptonic_control_axis": 0.00,
    },
    "SingleMuon": {
        "observer_projection": 0.55,
        "physical_projection": 0.00,
        "algebraic_projection": 0.10,
        "ordinary_qcd_axis": -0.20,
        "leptonic_control_axis": -0.15,
    },
}


def ensure_dirs() -> None:
    for path in [OUT, TABLES, REPORTS, SOURCES, LOGS]:
        path.mkdir(parents=True, exist_ok=True)


def safe(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def build_manifest() -> pd.DataFrame:
    rows = []
    for dataset, record_id in RECORDS.items():
        folder = DOWNLOAD_ROOT / dataset / str(record_id)
        files = sorted(folder.glob("*.root"))
        if not files:
            raise FileNotFoundError(f"No ROOT files found for {dataset}: {folder}")
        for i, path in enumerate(files, start=1):
            rows.append(
                {
                    "primary_dataset": dataset,
                    "record_id": record_id,
                    "rank": i,
                    "filename": path.name,
                    "local_path": str(path),
                    "size_bytes": path.stat().st_size,
                    "size_gb": path.stat().st_size / 1e9,
                }
            )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(TABLES / "00_existing_root_manifest.csv", index=False)
    return manifest


def run_with_heartbeat(cmd: list[str], log_path: Path, label: str) -> int:
    started = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(" ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True, env=os.environ.copy())
        last_size = -1
        while True:
            code = proc.poll()
            size = log_path.stat().st_size if log_path.exists() else 0
            elapsed = (time.time() - started) / 60.0
            if code is not None:
                print(f"[extract] {label}: finished returncode={code} elapsed={elapsed:.1f} min log={size / 1e6:.2f} MB", flush=True)
                return int(code)
            if size != last_size:
                print(f"[extract] {label}: running elapsed={elapsed:.1f} min log={size / 1e6:.2f} MB", flush=True)
                last_size = size
            else:
                print(f"[extract] {label}: still running elapsed={elapsed:.1f} min log unchanged={size / 1e6:.2f} MB", flush=True)
            time.sleep(30)


def run_cmssw_batch(dataset: str, group: pd.DataFrame) -> dict[str, object]:
    run_id = f"mht_fresh_run2016h_{safe(dataset)}_batch{len(group)}"
    out_csv = SOURCES / f"{run_id}_event_features.csv"
    if out_csv.exists():
        existing = pd.read_csv(out_csv, nrows=5)
        if {"MHT_pt", "MHT_phi", "MHT_over_HT", "MET_minus_MHT"}.issubset(existing.columns):
            events = sum(1 for _ in out_csv.open("r", encoding="utf-8", errors="replace")) - 1
            print(f"[extract] already present {dataset}: {events} MHT-aware events", flush=True)
            return {
                "primary_dataset": dataset,
                "run_id": run_id,
                "status": "existing",
                "events_written": events,
                "output_csv": str(out_csv),
                "log_path": "",
                "returncode": 0,
            }

    container_paths = [f"/data/{dataset}/{int(r.record_id)}/{r.filename}" for r in group.itertuples(index=False)]
    output_dir = f"/work/outputs/{run_id}"
    cmd_inside = (
        f"export SAMPLE_ID={run_id}; "
        f"export NFRAME_INPUT_FILES={','.join(container_paths)}; "
        "export NFRAME_INPUT_DIR=/data; "
        f"export NFRAME_OUTPUT_DIR={output_dir}; "
        "export NFRAME_TEST_MAXEVENTS=50; "
        "export NFRAME_MAXEVENTS_FULL=-1; "
        "bash /work/run_one_sample.sh"
    )
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{CMSSW_WORK}:/work",
        "-v",
        f"{DOWNLOAD_ROOT}:/data",
        IMAGE,
        "bash",
        "-lc",
        cmd_inside,
    ]
    log_path = LOGS / f"{run_id}.log"
    print(f"[extract] starting {dataset}: {len(group)} files", flush=True)
    returncode = run_with_heartbeat(cmd, log_path, dataset)
    raw = CMSSW_WORK / "outputs" / run_id / "event_features.csv"
    if returncode != 0 or not raw.exists():
        return {
            "primary_dataset": dataset,
            "run_id": run_id,
            "status": "failed",
            "events_written": 0,
            "output_csv": "",
            "log_path": str(log_path),
            "returncode": returncode,
        }

    df = pd.read_csv(raw, low_memory=False)
    required = {"MHT_pt", "MHT_phi", "MHT_over_HT", "MET_minus_MHT"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise RuntimeError(f"{dataset} extraction finished but MHT columns are missing: {missing}")
    df.insert(0, "sample_id", run_id)
    df.insert(1, "primary_dataset", dataset)
    df.insert(2, "record_id", ";".join(group["record_id"].astype(str)))
    df.insert(3, "run_era", "Run2016H_fresh")
    df.insert(4, "source_file", ";".join(group["filename"].astype(str)))
    df.insert(5, "source_file_count", len(group))
    df.insert(6, "local_input_path_or_container_path", " | ".join(group["local_path"].astype(str)) + " | " + ",".join(container_paths))
    df.insert(7, "event_index_within_batch", range(len(df)))
    df["is_real_collision"] = True
    df["is_simulated"] = False
    df.to_csv(out_csv, index=False)
    print(f"[extract] completed {dataset}: {len(df)} events", flush=True)
    return {
        "primary_dataset": dataset,
        "run_id": run_id,
        "status": "extracted",
        "events_written": len(df),
        "output_csv": str(out_csv),
        "log_path": str(log_path),
        "returncode": returncode,
    }


def extract_batches(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset, group in manifest.groupby("primary_dataset", sort=False):
        result = run_cmssw_batch(dataset, group)
        rows.append(result)
        pd.DataFrame(rows).to_csv(TABLES / "01_mht_extraction_audit.csv", index=False)
        if result["status"] == "failed":
            raise RuntimeError(f"CMSSW extraction failed for {dataset}; see {result['log_path']}")
    audit = pd.DataFrame(rows)
    audit.to_csv(TABLES / "01_mht_extraction_audit.csv", index=False)
    frames = [pd.read_csv(path, low_memory=False) for path in audit["output_csv"]]
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(SOURCES / "mht_fresh_run2016h_combined_event_features.csv", index=False)
    return audit


def numeric(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in df:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def strict_quality(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    for col in QUALITY_FILTERS:
        out[col] = numeric(out, col, -999)
    out["strict_quality_clean"] = (out[QUALITY_FILTERS] == 1).all(axis=1)
    audit = (
        out.groupby("primary_dataset", as_index=False)
        .agg(events_before=("event", "count"), events_after_strict_quality=("strict_quality_clean", "sum"))
    )
    audit["retention_fraction"] = audit["events_after_strict_quality"] / audit["events_before"].replace(0, np.nan)
    return out[out["strict_quality_clean"]].copy(), audit


def zscore(values: pd.Series, ref_mask: pd.Series | np.ndarray | None = None) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    ref = x if ref_mask is None else x.loc[ref_mask]
    mean = float(ref.mean()) if len(ref) else 0.0
    sd = float(ref.std(ddof=0)) if len(ref) else 1.0
    if not np.isfinite(sd) or sd <= 1e-9:
        sd = 1.0
    return (x - mean) / sd


def jet_bin(n_jets: pd.Series) -> pd.Series:
    n = pd.to_numeric(n_jets, errors="coerce").fillna(0).astype(float)
    bins = np.select(
        [n <= 0, (n >= 1) & (n <= 2), (n >= 3) & (n <= 4), n >= 5],
        ["0jet", "1to2jets", "3to4jets", "5plusjets"],
        default="unknown",
    )
    return pd.Series(pd.Categorical(bins, categories=JET_BINS), index=n.index)


def add_dataset_components(group: pd.DataFrame) -> pd.DataFrame:
    dataset = str(group["primary_dataset"].iloc[0])
    g = group.copy()
    g["missing_proxy_kind"] = "MHT_pt" if dataset == "HTMHT" else "MET_pt"
    g["missing_proxy_pt"] = numeric(g, "MHT_pt" if dataset == "HTMHT" else "MET_pt")
    g["log1p_missing_proxy"] = np.log1p(np.clip(g["missing_proxy_pt"], 0, None))
    g["log1p_MET_pt"] = np.log1p(np.clip(numeric(g, "MET_pt"), 0, None))
    g["log1p_MHT_pt"] = np.log1p(np.clip(numeric(g, "MHT_pt"), 0, None))
    g["log1p_HT"] = np.log1p(np.clip(numeric(g, "HT"), 0, None))
    g["N_jets_30"] = numeric(g, "N_jets_30")
    g["N_btags_medium"] = numeric(g, "N_btags_medium")
    g["N_muons"] = numeric(g, "N_muons")
    g["N_electrons"] = numeric(g, "N_electrons")
    g["secondary_vertex_count"] = numeric(g, "secondary_vertex_count")
    g["packed_candidate_count"] = numeric(g, "packed_candidate_count")
    g["mht_over_ht_clean"] = numeric(g, "MHT_over_HT").replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-10, 10)
    g["met_minus_mht"] = numeric(g, "MET_minus_MHT")
    g["jet_bin"] = jet_bin(g["N_jets_30"])

    lower_mask = g["log1p_missing_proxy"] <= g["log1p_missing_proxy"].quantile(0.95)
    x_cols = ["log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons"]
    x = g.loc[lower_mask, x_cols].to_numpy(float)
    y = g.loc[lower_mask, "log1p_missing_proxy"].to_numpy(float)
    if len(g.loc[lower_mask]) >= len(x_cols) + 5:
        design = np.column_stack([np.ones(len(x)), x])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        pred = np.column_stack([np.ones(len(g)), g[x_cols].to_numpy(float)]) @ beta
    else:
        pred = np.full(len(g), float(g.loc[lower_mask, "log1p_missing_proxy"].mean()))
    g["missing_visible_residual_raw"] = g["log1p_missing_proxy"].to_numpy(float) - pred
    g["observer_projection"] = zscore(g["missing_visible_residual_raw"], lower_mask)

    disp_raw = np.log1p(np.clip(g["secondary_vertex_count"], 0, None)) + 0.05 * zscore(np.log1p(np.clip(g["packed_candidate_count"], 0, None)))
    g["disp_reco_proxy"] = disp_raw
    g["physical_projection"] = (
        0.65 * zscore(g["log1p_missing_proxy"], lower_mask)
        + 0.20 * zscore(g["log1p_HT"], lower_mask)
        + 0.15 * zscore(g["disp_reco_proxy"], lower_mask)
    )

    pca_cols = ["log1p_missing_proxy", "log1p_HT", "N_jets_30", "N_btags_medium", "N_muons", "N_electrons", "mht_over_ht_clean", "met_minus_mht"]
    x_all = g[pca_cols].to_numpy(float)
    ref = g.loc[lower_mask, pca_cols].to_numpy(float)
    mean = ref.mean(axis=0)
    sd = ref.std(axis=0)
    sd = np.where(sd <= 1e-9, 1.0, sd)
    z_ref = (ref - mean) / sd
    z_all = (x_all - mean) / sd
    if len(ref) >= len(pca_cols) + 5:
        _, _, vt = np.linalg.svd(z_ref, full_matrices=False)
        basis = vt[: min(3, vt.shape[0])].T
        recon = (z_all @ basis) @ basis.T
        resid = np.sqrt(np.mean((z_all - recon) ** 2, axis=1))
    else:
        resid = np.zeros(len(g), dtype=float)
    g["algebraic_projection"] = zscore(pd.Series(resid, index=g.index), lower_mask)
    g["ordinary_qcd_axis"] = 0.70 * zscore(g["N_jets_30"], lower_mask) + 0.30 * zscore(g["N_btags_medium"], lower_mask)
    g["leptonic_control_axis"] = -zscore(g["N_muons"] + g["N_electrons"], lower_mask)

    w = WEIGHTS[dataset]
    score = np.zeros(len(g), dtype=float)
    for col, weight in w.items():
        score += weight * g[col].to_numpy(float)
    g["mht_dynamic_boundary_score"] = score
    return g


def add_components(clean: pd.DataFrame) -> pd.DataFrame:
    frames = [add_dataset_components(group) for _, group in clean.groupby("primary_dataset", sort=False)]
    scored = pd.concat(frames, ignore_index=True)
    scored.to_csv(SOURCES / "mht_fresh_run2016h_scored_events.csv", index=False)
    return scored


def component_readout(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cols = [
        "missing_proxy_pt",
        "observer_projection",
        "physical_projection",
        "algebraic_projection",
        "ordinary_qcd_axis",
        "leptonic_control_axis",
        "mht_dynamic_boundary_score",
        "MHT_pt",
        "MET_pt",
        "MHT_over_HT",
        "MET_minus_MHT",
    ]
    for dataset, group in scored.groupby("primary_dataset", sort=False):
        row = {
            "primary_dataset": dataset,
            "events": len(group),
            "missing_proxy_kind": group["missing_proxy_kind"].iloc[0],
        }
        for col in cols:
            if col in group:
                vals = pd.to_numeric(group[col], errors="coerce")
                row[f"{col}_mean"] = float(vals.mean())
                row[f"{col}_p95"] = float(vals.quantile(0.95))
                row[f"{col}_p99"] = float(vals.quantile(0.99))
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "03_mht_component_readout.csv", index=False)
    return out


def tail_enrichment(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset, group in scored.groupby("primary_dataset", sort=False):
        g = group.copy()
        if len(g) < 100:
            continue
        q = np.linspace(0, 1, 11)
        edges = np.unique(g["missing_proxy_pt"].quantile(q).to_numpy(float))
        if len(edges) < 3:
            edges = np.array([-np.inf, np.inf], dtype=float)
        else:
            edges[0], edges[-1] = -np.inf, np.inf
        g["missing_bin"] = pd.cut(g["missing_proxy_pt"], bins=edges, labels=False, include_lowest=True)
        thresholds = g.groupby("missing_bin", observed=False)["mht_dynamic_boundary_score"].quantile(0.99)
        g["q99_tail"] = g["mht_dynamic_boundary_score"] >= g["missing_bin"].map(thresholds).astype(float)
        global_frac = g.groupby("missing_bin", observed=False)["q99_tail"].mean().rename("bin_tail_fraction")
        for jet, sub in g.groupby("jet_bin", observed=False):
            if pd.isna(jet) or len(sub) == 0:
                continue
            exp = float(sub["missing_bin"].map(global_frac).astype(float).sum())
            obs = int(sub["q99_tail"].sum())
            rel_unc = 0.30
            z = (obs - exp) / np.sqrt(exp + (rel_unc * exp) ** 2) if exp > 0 else np.nan
            rows.append(
                {
                    "primary_dataset": dataset,
                    "jet_bin": str(jet),
                    "missing_proxy_kind": g["missing_proxy_kind"].iloc[0],
                    "events": len(sub),
                    "q99_observed": obs,
                    "q99_expected_internal": exp,
                    "q99_obs_exp_internal": obs / exp if exp > 0 else np.nan,
                    "q99_internal_Z_relunc30": z,
                    "tail_definition": "top 1% of MHT-aware dynamic score within same-stream missing-proxy deciles",
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "04_mht_internal_tail_enrichment.csv", index=False)
    return out


def validation_readout(tail: pd.DataFrame) -> pd.DataFrame:
    def get(dataset: str, jet: str = TARGET_JET_BIN, col: str = "q99_internal_Z_relunc30") -> float:
        row = tail[(tail["primary_dataset"].eq(dataset)) & (tail["jet_bin"].eq(jet))]
        return float(row[col].iloc[0]) if not row.empty else np.nan

    met_z = get("MET")
    htmht_z = get("HTMHT")
    jetht_z = get("JetHT")
    smuon_z = get("SingleMuon")
    signal = np.array([met_z, htmht_z], dtype=float)
    signal = signal[np.isfinite(signal)]
    combined = float(signal.sum() / np.sqrt(len(signal))) if len(signal) else np.nan
    out = pd.DataFrame(
        [
            {
                "test": "mht_proxy_dynamic_boundary_internal_tail",
                "events_total_clean": int(tail.groupby("primary_dataset")["events"].sum().sum()),
                "MET_1to2jets_Z": met_z,
                "MET_1to2jets_obs_exp": get("MET", col="q99_obs_exp_internal"),
                "HTMHT_1to2jets_Z": htmht_z,
                "HTMHT_1to2jets_obs_exp": get("HTMHT", col="q99_obs_exp_internal"),
                "combined_MET_HTMHT_stouffer_Z": combined,
                "JetHT_1to2jets_control_Z": jetht_z,
                "SingleMuon_1to2jets_control_Z": smuon_z,
                "controls_close_absZ_lt3": bool(np.isfinite(jetht_z) and np.isfinite(smuon_z) and abs(jetht_z) < 3 and abs(smuon_z) < 3),
                "mht_proxy_supports_dynamic_trace": bool(
                    len(signal) == 2
                    and met_z > 3
                    and htmht_z > 3
                    and combined > 5
                    and np.isfinite(jetht_z)
                    and np.isfinite(smuon_z)
                    and abs(jetht_z) < 3
                    and abs(smuon_z) < 3
                ),
            }
        ]
    )
    out.to_csv(TABLES / "05_mht_validation_readout.csv", index=False)
    return out


def compare_previous(readout: pd.DataFrame) -> pd.DataFrame:
    prev_path = ROOT / "outputs_fresh_run2016h_tri_dynamic_validation" / "tables" / "07_fresh_validation_readout.csv"
    rows = []
    if prev_path.exists():
        prev = pd.read_csv(prev_path).iloc[0]
        now = readout.iloc[0]
        for dataset in ["MET", "HTMHT"]:
            rows.append(
                {
                    "primary_dataset": dataset,
                    "previous_no_mht_Z": float(prev[f"{dataset}_1to2jets_Z"]),
                    "mht_proxy_Z": float(now[f"{dataset}_1to2jets_Z"]),
                    "delta_Z": float(now[f"{dataset}_1to2jets_Z"]) - float(prev[f"{dataset}_1to2jets_Z"]),
                    "previous_no_mht_obs_exp": float(prev[f"{dataset}_1to2jets_obs_exp"]),
                    "mht_proxy_obs_exp": float(now[f"{dataset}_1to2jets_obs_exp"]),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "06_previous_vs_mht_proxy_comparison.csv", index=False)
    return out


def write_reports(
    manifest: pd.DataFrame,
    extraction: pd.DataFrame,
    quality: pd.DataFrame,
    components: pd.DataFrame,
    tail: pd.DataFrame,
    readout: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    weights = pd.DataFrame([{"dataset_context": ds, **w} for ds, w in WEIGHTS.items()]).fillna(0.0)
    weights.to_csv(TABLES / "02_mht_dynamic_context_weights.csv", index=False)
    r = readout.iloc[0]
    interpretation = (
        "supports the dynamic-boundary trace diagnostic"
        if bool(r["mht_proxy_supports_dynamic_trace"])
        else "does not yet support the dynamic-boundary trace diagnostic at the strict all-stream level"
    )
    comparison_md = comparison.to_markdown(index=False) if not comparison.empty else "Previous comparison table was not available."
    manifest_md = manifest.to_markdown(index=False)
    extraction_md = extraction.to_markdown(index=False)
    quality_md = quality.to_markdown(index=False)
    weights_md = weights.to_markdown(index=False)
    components_md = components.to_markdown(index=False)
    tail_md = tail.to_markdown(index=False)
    readout_md = readout.to_markdown(index=False)
    report = f"""# MHT-Proxy Fresh Run2016H Dynamic Boundary Validation

## Purpose

This run tests the next N-Frame step Darren asked for: whether the missing-boundary trace becomes more coherent when HTMHT is represented by a jet-recoil missing observable rather than ordinary PF `MET_pt`.

The previous fresh Run2016H validation used `MET_pt` for every stream. That was defensible for MET, but incomplete for HTMHT because the HTMHT trigger family is built around missing transverse HT. The CMSSW MiniAOD extractor was therefore patched to write:

- `MHT_pt`
- `MHT_phi`
- `MHT_over_HT`
- `MET_minus_MHT`

## Input Data

No new CERN download was performed. The run reused the already-downloaded fresh CMS Run2016H MiniAOD files.

{manifest_md}

## Extraction Audit

{extraction_md}

## Strict Quality-Clean Audit

{quality_md}

## Dynamic Boundary Definition

For HTMHT only, the missing proxy is `MHT_pt`. For MET, JetHT, and SingleMuon, the missing proxy remains `MET_pt`.

The score is:

```latex
B_{{dyn}} = w_o O + w_p P + w_a A + w_q Q + w_l L
```

where:

```latex
O = z\\left[\\log(1 + p_T^{{miss}}) - \\widehat{{\\log(1 + p_T^{{miss}})}}(H_T,N_{{jets}},N_b,N_\\mu,N_e)\\right]
```

```latex
P = 0.65z\\left[\\log(1+p_T^{{miss}})\\right] + 0.20z\\left[\\log(1+H_T)\\right] + 0.15z(D_{{SV/PF}})
```

```latex
A = z\\left[\\left\\|x - \\Pi_{{PC1..PC3}}(x)\\right\\|_2\\right]
```

```latex
Q = 0.70z(N_{{jets}}) + 0.30z(N_b), \\quad L = -z(N_\\mu + N_e)
```

The weights were not tuned in this run; they reuse the previous dynamic-boundary form:

{weights_md}

## Component Readout

{components_md}

## Internal Tail-Enrichment Readout

This diagnostic asks whether the top 1 percent of the MHT-aware dynamic score is concentrated in the 1-2 jet boundary after matching each stream to its own missing-proxy deciles. It is a trigger-observable diagnostic, not an official CMS discovery likelihood.

{tail_md}

## Main Validation Readout

{readout_md}

## Comparison With Previous Fresh Run2016H Readout

{comparison_md}

## Interpretation

This result {interpretation}.

The important physics-method point is that HTMHT has now been tested with a closer proxy for its trigger-level missing-recoil structure. If HTMHT strengthens while JetHT and SingleMuon remain quiet, that would support Darren's dynamic-boundary interpretation. If HTMHT remains weak, then the blocker is not just the missing-HT proxy; the model needs a deeper trigger-aware or stage-aware boundary construction.

This is still not a direct SUSY-particle discovery claim. It is a test for an indirect hidden-sector/SUSY-like boundary trace in real CMS collision data.
"""
    (REPORTS / "01_MHT_PROXY_FRESH_RUN2016H_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    short = f"""# Short Update: MHT-Proxy Fresh Run2016H Validation

{readout_md}

Key comparison:

{comparison_md}
"""
    (REPORTS / "02_SHORT_UPDATE_MHT_PROXY_VALIDATION.md").write_text(short, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    print("[start] MHT-proxy fresh Run2016H validation", flush=True)
    manifest = build_manifest()
    print(f"[manifest] found {len(manifest)} existing ROOT files, total {manifest['size_gb'].sum():.3f} GB", flush=True)
    extraction = extract_batches(manifest)
    print("[extract] all MHT-aware batches complete", flush=True)
    raw = pd.read_csv(SOURCES / "mht_fresh_run2016h_combined_event_features.csv", low_memory=False)
    clean, quality = strict_quality(raw)
    quality.to_csv(TABLES / "02_mht_quality_audit.csv", index=False)
    print(f"[quality] retained {len(clean)} / {len(raw)} events", flush=True)
    scored = add_components(clean)
    components = component_readout(scored)
    tail = tail_enrichment(scored)
    readout = validation_readout(tail)
    comparison = compare_previous(readout)
    write_reports(manifest, extraction, quality, components, tail, readout, comparison)
    print("MHT-PROXY FRESH RUN2016H VALIDATION COMPLETE")
    print(readout.to_string(index=False))
    print("Outputs:", OUT)


if __name__ == "__main__":
    main()
