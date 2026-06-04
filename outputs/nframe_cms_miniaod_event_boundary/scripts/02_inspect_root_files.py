import argparse
from pathlib import Path

from common import FILELIST_DIR, LOGS_DIR, ensure_dirs


PATTERNS = [
    "MET",
    "slimmedMETs",
    "Jet",
    "slimmedJets",
    "Electron",
    "slimmedElectrons",
    "Muon",
    "slimmedMuons",
    "Tau",
    "slimmedTaus",
    "packedPFCandidates",
    "Trigger",
    "HLT",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect first MiniAOD ROOT file with uproot.")
    parser.add_argument("--filelist", default=str(FILELIST_DIR / "miniaod_files.txt"))
    parser.add_argument("--output", default=str(LOGS_DIR / "root_file_structure.txt"))
    args = parser.parse_args()

    ensure_dirs()
    files = [line.strip() for line in Path(args.filelist).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not files:
        raise SystemExit("No ROOT files found in filelist.")
    first = files[0]
    lines = [f"First file: {first}", ""]

    try:
        import uproot

        with uproot.open(first) as root_file:
            keys = root_file.keys()
            lines.append("Top-level keys:")
            lines.extend(f"  {key}" for key in keys)
            lines.append("")
            if "Events" not in root_file:
                lines.append("MiniAOD requires CMSSW/FWLite analyzer")
            else:
                events = root_file["Events"]
                branches = events.keys()
                lines.append(f"Events tree is accessible with {len(branches)} branches.")
                lines.append("")
                for pattern in PATTERNS:
                    matches = [branch for branch in branches if pattern.lower() in branch.lower()]
                    lines.append(f"Branches containing {pattern}:")
                    if matches:
                        lines.extend(f"  {branch}" for branch in matches[:100])
                        if len(matches) > 100:
                            lines.append(f"  ... {len(matches) - 100} more")
                    else:
                        lines.append("  none")
                    lines.append("")
    except Exception as exc:
        lines.append("MiniAOD requires CMSSW/FWLite analyzer")
        lines.append(f"uproot failure: {type(exc).__name__}: {exc}")

    output = Path(args.output)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output}")
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    main()
