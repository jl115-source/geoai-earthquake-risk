#!/usr/bin/env python3
"""Download large/open external datasets used by the project.

Large third-party datasets are intentionally kept out of Git history.
This script places them under data/raw/.

Usage examples
--------------
python scripts/download_external_data.py nepal-geid
python scripts/download_external_data.py rc616
python scripts/download_external_data.py turkiye-context
python scripts/download_external_data.py nepal-metadata
python scripts/download_external_data.py all

Notes
-----
- Nepal GEID is licensed by GEM under CC BY-NC-SA 4.0.
- The RC616 database is CC BY-SA 3.0.
- The Türkiye 2026 Zenodo record is open-access, but the record page does not
  currently display an explicit license. It is therefore downloaded locally
  only and MUST NOT be redistributed from this repository.
- Nepal NSO microdata are not downloaded here because their access terms
  prohibit redistribution without written agreement. We only download the
  public study metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import requests


RAW = Path("data/raw")

SOURCES = {
    "nepal-geid": {
        "url": (
            "https://raw.githubusercontent.com/gem/geid/main/"
            "South_Asia/Nepal/20150425_M7.8_Gorkha/1_Impact/"
            "Impact_Buildings_Detailed.csv"
        ),
        "path": RAW / "nepal_2015" / "Impact_Buildings_Detailed.csv",
        "expected_size": 78_448_526,
    },
    "rc616": {
        "url": (
            "https://www.dropbox.com/scl/fo/"
            "qi3d9rbwjdqn8vev74bjs/APrtlwCls_w8csviSUJfbqY"
            "?rlkey=y1p57c5axbj9fkxs4x2itfwp2&dl=1"
        ),
        "path": RAW / "rc616" / "rc616.zip",
        "extract_to": RAW / "rc616" / "extracted",
    },
    "turkiye-context": {
        "url": (
            "https://zenodo.org/records/18437501/files/"
            "2023Turkey_earthquake_data.zip?download=1"
        ),
        "path": RAW / "turkiye_2023_context" / "2023Turkey_earthquake_data.zip",
        "extract_to": RAW / "turkiye_2023_context" / "extracted",
        "md5": "f3a3a9982cf63bd954616a898c7416b9",
    },
    "nepal-shakemap": {
        "url": (
            "https://earthquake.usgs.gov/product/shakemap/"
            "us20002926/atlas/1594162031303/download/grid.xml"
        ),
        "path": RAW / "nepal_2015" / "usgs_shakemap_grid.xml",
    },
    "nepal-metadata": {
        "url": (
            "https://microdata.nsonepal.gov.np/index.php/"
            "metadata/export/69/json"
        ),
        "path": RAW / "nepal_2015" / "NSO_HRHRS_metadata.json",
    },
}


def md5sum(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    headers = {"User-Agent": "geoai-earthquake-risk/0.1"}

    with requests.get(url, stream=True, timeout=(30, 300), headers=headers) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                fh.write(chunk)
                done += len(chunk)
                if total:
                    pct = 100 * done / total
                    print(f"\r{path.name}: {done/1e6:.1f}/{total/1e6:.1f} MB ({pct:.1f}%)", end="")
                else:
                    print(f"\r{path.name}: {done/1e6:.1f} MB", end="")
    print()
    tmp.replace(path)


def validate(name: str, spec: dict) -> None:
    path: Path = spec["path"]
    if "expected_size" in spec and path.stat().st_size != spec["expected_size"]:
        raise RuntimeError(
            f"{name}: size mismatch: got {path.stat().st_size:,}, "
            f"expected {spec['expected_size']:,}"
        )
    if "md5" in spec:
        digest = md5sum(path)
        if digest.lower() != spec["md5"].lower():
            raise RuntimeError(
                f"{name}: MD5 mismatch: got {digest}, expected {spec['md5']}"
            )


def extract_if_needed(name: str, spec: dict) -> None:
    if "extract_to" not in spec:
        return

    archive: Path = spec["path"]
    out: Path = spec["extract_to"]
    out.mkdir(parents=True, exist_ok=True)

    if not zipfile.is_zipfile(archive):
        raise RuntimeError(
            f"{name}: downloaded object is not a ZIP archive. "
            "The provider may have changed its public-download endpoint."
        )

    marker = out / ".extracted"
    if marker.exists():
        print(f"[exists] {out}")
        return

    print(f"[extract] {archive} -> {out}")
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(out)
    marker.write_text("ok\n")


def acquire(name: str) -> None:
    spec = SOURCES[name]
    path: Path = spec["path"]

    if path.exists() and path.stat().st_size > 0:
        print(f"[exists] {path} ({path.stat().st_size:,} bytes)")
    else:
        print(f"[download] {name}")
        download(spec["url"], path)

    validate(name, spec)
    extract_if_needed(name, spec)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dataset",
        choices=[*SOURCES.keys(), "all"],
        help="Dataset to download",
    )
    args = parser.parse_args()

    names = list(SOURCES) if args.dataset == "all" else [args.dataset]
    for name in names:
        print(f"\n=== {name} ===")
        try:
            acquire(name)
        except Exception as exc:
            print(f"[ERROR] {name}: {exc}", file=sys.stderr)
            if args.dataset != "all":
                raise


if __name__ == "__main__":
    main()
