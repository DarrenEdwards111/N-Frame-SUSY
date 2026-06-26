#!/usr/bin/env python3
"""
Jupyter-friendly remote CMS Open Data access helper.

This is the collider-data analogue of a Johns Hopkins Turbulence Database
notebook workflow: pick a manifest row, stream a small slice remotely, inspect
branches, and optionally write a compact CSV/Parquet sample. It does NOT pull
huge ROOT files to disk.

Usage from a terminal:

  python code/scripts/jupyter_collision_data_access.py --list
  python code/scripts/jupyter_collision_data_access.py --index 0 --branches 40 --events 200 --out /tmp/cms_sample.csv

Usage from Jupyter:

  %run code/scripts/jupyter_collision_data_access.py --index 0 --events 100

Dependencies:

  pip install uproot awkward pandas numpy

For root:// XRootD URLs, uproot also needs an XRootD backend available in the
Python environment. If root:// fails, run the same script inside a CERN/CMSSW
container or install the XRootD Python bindings for your platform.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_MANIFESTS = [
    REPO / "code/cloud_remote_nframe_package/manifests/01_real_cms_miniaod_remote_cloud_manifest.csv",
    REPO / "code/cloud_remote_nframe_package/manifests/04_xrootd_file_accessibility_scan.csv",
]

# MiniAOD jet leaves previously verified in this project for lightweight uproot access.
JET_PREFIX = "patJets_slimmedJets__PAT./patJets_slimmedJets__PAT.obj/patJets_slimmedJets__PAT.obj"
MINIAOD_JET_BRANCHES = {
    "jet_pt": f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fPt",
    "jet_eta": f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fEta",
    "jet_phi": f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fPhi",
    "jet_mass": f"{JET_PREFIX}.m_state.p4Polar_.fCoordinates.fM",
}

# Common NanoAOD-like branch names, if the selected file is a flat NanoAOD tree.
NANOAOD_BRANCHES = {
    "run": "run",
    "luminosityBlock": "luminosityBlock",
    "event": "event",
    "MET_pt": "MET_pt",
    "MET_phi": "MET_phi",
    "nJet": "nJet",
    "Jet_pt": "Jet_pt",
    "Jet_eta": "Jet_eta",
    "Jet_phi": "Jet_phi",
    "nMuon": "nMuon",
    "nElectron": "nElectron",
}


def first_existing_manifest() -> Path:
    for path in DEFAULT_MANIFESTS:
        if path.exists():
            return path
    raise FileNotFoundError("No default CMS remote manifest found in repo")


def load_manifest(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "xrootd_url" not in df.columns:
        if "uri" in df.columns:
            df = df.rename(columns={"uri": "xrootd_url"})
        elif "smallest_file_url" in df.columns:
            df = df.rename(columns={"smallest_file_url": "xrootd_url"})
    if "xrootd_url" not in df.columns:
        raise ValueError(f"Manifest lacks xrootd_url/uri/smallest_file_url column: {path}")
    df = df[df["xrootd_url"].astype(str).str.startswith("root://")].copy()
    df = df.reset_index(drop=True)
    return df


def list_manifest(df: pd.DataFrame, limit: int) -> None:
    cols = [c for c in ["record_id", "dataset_label", "process_family", "primary_dataset", "run_era", "data_tier", "size_gb", "xrootd_status", "xrootd_url"] if c in df.columns]
    view = df.loc[: limit - 1, cols].copy()
    if "xrootd_url" in view.columns:
        view["xrootd_url"] = view["xrootd_url"].str.slice(0, 110)
    print(view.to_string(index=True))


def require_uproot():
    try:
        import awkward as ak  # noqa: F401
        import uproot
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "Missing Python ROOT-reader deps. Install with: pip install uproot awkward pandas numpy\n"
            f"Original error: {exc!r}"
        )
    return uproot


def open_events_tree(url: str):
    uproot = require_uproot()
    root_file = uproot.open(url)
    if "Events" not in root_file:
        keys = list(root_file.keys())[:30]
        raise KeyError(f"No Events tree found. Top-level keys include: {keys}")
    return root_file, root_file["Events"]


def print_branches(tree, limit: int, contains: str | None = None) -> None:
    names = list(tree.keys())
    if contains:
        names = [n for n in names if contains.lower() in n.lower()]
    print(f"Events entries: {tree.num_entries:,}")
    print(f"Branches shown: {min(limit, len(names)):,} / {len(names):,}")
    for name in names[:limit]:
        print(name)


def nth_or_nan(ak, array, index: int) -> np.ndarray:
    padded = ak.pad_none(array, index + 1, clip=True)
    return ak.to_numpy(ak.fill_none(padded[:, index], np.nan))


def available(mapping: dict[str, str], branch_names: Iterable[str]) -> dict[str, str]:
    branch_set = set(branch_names)
    return {label: branch for label, branch in mapping.items() if branch in branch_set}


def extract_small_frame(tree, url: str, max_events: int) -> pd.DataFrame:
    import awkward as ak

    stop = min(max_events, tree.num_entries)
    branch_names = list(tree.keys())

    nano = available(NANOAOD_BRANCHES, branch_names)
    if {"Jet_pt", "Jet_eta", "Jet_phi"}.issubset(nano):
        arrays = tree.arrays(list(nano.values()), entry_stop=stop, library="ak")
        out = pd.DataFrame({
            "source_url": url,
            "event_index": np.arange(stop, dtype=np.int64),
            "extraction_mode": "uproot_remote_nanoaod",
        })
        for label, branch in nano.items():
            arr = arrays[branch]
            if label.startswith("Jet_"):
                out[f"leading_{label}"] = nth_or_nan(ak, arr, 0)
            else:
                try:
                    out[label] = ak.to_numpy(arr)
                except Exception:
                    pass
        return out

    mini = available(MINIAOD_JET_BRANCHES, branch_names)
    if {"jet_pt", "jet_eta", "jet_phi", "jet_mass"}.issubset(mini):
        arrays = tree.arrays(list(mini.values()), entry_stop=stop, library="ak")
        pt = arrays[mini["jet_pt"]]
        eta = arrays[mini["jet_eta"]]
        phi = arrays[mini["jet_phi"]]
        mass = arrays[mini["jet_mass"]]
        selected30 = (pt > 30) & (abs(eta) < 2.4)
        return pd.DataFrame({
            "source_url": url,
            "event_index": np.arange(stop, dtype=np.int64),
            "extraction_mode": "uproot_remote_miniaod_visible_jets_only",
            "N_jets": ak.to_numpy(ak.num(pt, axis=1)),
            "N_jets_30": ak.to_numpy(ak.sum(selected30, axis=1)),
            "HT_jets30": ak.to_numpy(ak.sum(pt * selected30, axis=1)),
            "sum_jet_pt": ak.to_numpy(ak.sum(pt, axis=1)),
            "leading_jet_pt": nth_or_nan(ak, pt, 0),
            "subleading_jet_pt": nth_or_nan(ak, pt, 1),
            "leading_jet_eta": nth_or_nan(ak, eta, 0),
            "leading_jet_phi": nth_or_nan(ak, phi, 0),
            "jet_mass_sum_30": ak.to_numpy(ak.sum(mass * selected30, axis=1)),
        })

    raise KeyError(
        "Could not find the known NanoAOD or MiniAOD jet branch sets. "
        "Run with --branches 200 or --contains Jet to inspect available names."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stream a small sample from CMS Open Data via remote XRootD")
    parser.add_argument("--manifest", type=Path, default=None, help="CSV manifest with xrootd_url/uri column")
    parser.add_argument("--index", type=int, default=0, help="Manifest row index to open")
    parser.add_argument("--url", default=None, help="Direct root:// URL; overrides --manifest/--index")
    parser.add_argument("--list", action="store_true", help="List candidate manifest rows and exit")
    parser.add_argument("--limit", type=int, default=20, help="Rows to show with --list")
    parser.add_argument("--branches", type=int, default=60, help="Number of branches to print")
    parser.add_argument("--contains", default=None, help="Only show branches containing this substring")
    parser.add_argument("--events", type=int, default=100, help="Max events to extract")
    parser.add_argument("--out", type=Path, default=None, help="Optional output CSV or Parquet path")
    args = parser.parse_args(argv)

    manifest_path = args.manifest or first_existing_manifest()
    df = load_manifest(manifest_path)

    if args.list:
        print(f"Manifest: {manifest_path}")
        list_manifest(df, args.limit)
        return 0

    url = args.url or str(df.loc[args.index, "xrootd_url"])
    print(f"Opening: {url}")
    root_file, tree = open_events_tree(url)
    try:
        print_branches(tree, args.branches, args.contains)
        frame = extract_small_frame(tree, url, args.events)
    finally:
        root_file.close()

    print("\nSample frame:")
    print(frame.head().to_string(index=False))
    print(f"\nRows extracted: {len(frame):,}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if args.out.suffix.lower() == ".parquet":
            frame.to_parquet(args.out, index=False)
        else:
            frame.to_csv(args.out, index=False)
        print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
