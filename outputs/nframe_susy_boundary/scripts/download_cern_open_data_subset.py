import argparse
import csv
import json
from pathlib import Path

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def root_uri_to_https(uri: str) -> str:
    prefix = "root://eospublic.cern.ch//"
    if not uri.startswith(prefix):
        raise ValueError(f"Unsupported URI: {uri}")
    return "https://eospublic.cern.ch/" + uri[len(prefix):]


def selected_files(record_json: Path, index_key_contains: str):
    record = json.loads(record_json.read_text(encoding="utf-8"))
    indices = record["metadata"]["_file_indices"]
    files = []
    for index in indices:
        if index_key_contains in index["key"]:
            files.extend(index["files"])
    if not files:
        raise SystemExit(f"No files matched index key containing {index_key_contains!r}")
    return files


def download_file(url: str, destination: Path, expected_size: int) -> str:
    if destination.exists() and destination.stat().st_size == expected_size:
        return "already_present"

    tmp = destination.with_suffix(destination.suffix + ".part")
    headers = {}
    mode = "wb"
    existing = tmp.stat().st_size if tmp.exists() else 0
    if existing:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"

    with requests.get(url, stream=True, verify=False, headers=headers, timeout=60) as response:
        response.raise_for_status()
        with open(tmp, mode + "") as handle:
            for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                if chunk:
                    handle.write(chunk)

    final_size = tmp.stat().st_size
    if final_size != expected_size:
        raise RuntimeError(f"Size mismatch for {destination.name}: got {final_size}, expected {expected_size}")
    tmp.replace(destination)
    return "downloaded"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a selected CERN Open Data file-index subset.")
    parser.add_argument("--record-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--index-key-contains", default="130000_file_index")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = selected_files(Path(args.record_json), args.index_key_contains)
    total = sum(int(f["size"]) for f in files)

    manifest_path = output_dir / "download_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=["filename", "size", "checksum", "root_uri", "https_url", "status"],
        )
        writer.writeheader()
        print(f"Selected {len(files)} files totaling {total / 1e9:.2f} GB")
        for i, file_info in enumerate(files, start=1):
            url = root_uri_to_https(file_info["uri"])
            destination = output_dir / file_info["filename"]
            print(f"[{i}/{len(files)}] {file_info['filename']} ({int(file_info['size']) / 1e9:.2f} GB)")
            status = download_file(url, destination, int(file_info["size"]))
            writer.writerow(
                {
                    "filename": file_info["filename"],
                    "size": file_info["size"],
                    "checksum": file_info.get("checksum", ""),
                    "root_uri": file_info["uri"],
                    "https_url": url,
                    "status": status,
                }
            )
            manifest_file.flush()
            print(f"  {status}")

    print(f"Wrote manifest: {manifest_path}")


if __name__ == "__main__":
    main()
