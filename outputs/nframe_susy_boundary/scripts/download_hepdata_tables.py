import argparse
import json
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

from common import RAW_DIR, ensure_dirs


def record_url(record_id: int, fmt: str = "json", table: str | None = None) -> str:
    url = f"https://www.hepdata.net/record/{record_id}?format={fmt}"
    if table:
        url += f"&table={quote(table)}"
    return url


def download(url: str, destination: Path) -> None:
    headers = {
        "User-Agent": "nframe-boundary-reanalysis/0.1 (+public HEPData meta-analysis)"
    }
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    if "Just a moment" in response.text[:1000] and "Cloudflare" in response.text[:5000]:
        raise RuntimeError(
            "HEPData returned a browser challenge for this endpoint. "
            "Open the URL in a browser or download the table manually into data/raw/."
        )
    destination.write_bytes(response.content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download selected HEPData metadata and candidate tables.")
    parser.add_argument("--config", default=RAW_DIR / "selected_hepdata_sources.yml")
    parser.add_argument("--formats", nargs="+", default=["json", "csv"])
    args = parser.parse_args()

    ensure_dirs()
    with open(args.config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    manifest = []
    for source in config["sources"]:
        record_id = int(source["hepdata_record"])
        source_dir = RAW_DIR / source["analysis"]
        source_dir.mkdir(parents=True, exist_ok=True)

        meta_path = source_dir / f"hepdata_record_{record_id}.json"
        print(f"Downloading metadata: {source['analysis']} -> {meta_path}")
        download(record_url(record_id, "json"), meta_path)

        for table in source["candidate_tables"]:
            safe_table = "".join(ch if ch.isalnum() else "_" for ch in table["name"]).strip("_")
            for fmt in args.formats:
                out = source_dir / f"{safe_table}.{fmt}"
                url = record_url(record_id, fmt, table["name"])
                print(f"Downloading table: {source['analysis']} / {table['name']} ({fmt})")
                try:
                    download(url, out)
                    status = "downloaded"
                except Exception as exc:
                    status = f"failed: {exc}"
                    print(f"  {status}")
                manifest.append(
                    {
                        "analysis": source["analysis"],
                        "table": table["name"],
                        "role": table["role"],
                        "format": fmt,
                        "url": url,
                        "path": str(out),
                        "status": status,
                    }
                )

    manifest_path = RAW_DIR / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
