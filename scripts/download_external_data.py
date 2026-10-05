#!/usr/bin/env python3
"""Download large/open external datasets and documentation used by the project.

Large third-party datasets are intentionally kept out of Git history.
This script places them under data/raw/.

Examples
--------
python scripts/download_external_data.py nepal-geid
python scripts/download_external_data.py nepal-docs
python scripts/download_external_data.py rc616
python scripts/download_external_data.py turkiye-context
python scripts/download_external_data.py all

Notes
-----
- Nepal GEID is licensed by GEM under CC BY-NC-SA 4.0.
- The RC616 database is CC BY-SA 3.0.
- The Türkiye 2026 Zenodo record is open-access, but currently shows no
  explicit license; it is therefore local-only.
- Nepal NSO HRHRS microdata are NOT downloaded here. Their access terms
  prohibit redistribution without written agreement. We download only public
  metadata and documentation so the schema and sampling design are reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
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
        "min_size": 100_000,
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
        "min_size": 100_000,
    },
    "nepal-metadata": {
        "url": "https://microdata.nsonepal.gov.np/index.php/metadata/export/69/json",
        "path": RAW / "nepal_2015" / "NSO_HRHRS_metadata.json",
        "min_size": 10_000,
    },
    "nepal-questionnaire-en": {
        "url": "https://microdata.nsonepal.gov.np/index.php/catalog/69/download/989",
        "path": RAW / "nepal_2015" / "docs" / "HRHRS_questionnaire_en.pdf",
        "min_size": 100_000,
    },
    "nepal-key-findings-14": {
        "url": "https://microdata.nsonepal.gov.np/index.php/catalog/69/download/991",
        "path": RAW / "nepal_2015" / "docs" / "HRHRS_key_findings_14_districts.pdf",
        "min_size": 300_000,
    },
    "nepal-affected-districts-map": {
        "url": "https://microdata.nsonepal.gov.np/index.php/catalog/69/download/994",
        "path": RAW / "nepal_2015" / "docs" / "HRHRS_affected_districts_map.pdf",
        "min_size": 100_000,
    },
}

GROUPS = {
    "nepal-docs": [
        "nepal-metadata",
        "nepal-questionnaire-en",
        "nepal-key-findings-14",
        "nepal-affected-districts-map",
    ],
    "all": list(SOURCES),
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
                    print(
                        f"\r{path.name}: {done/1e6:.1f}/{total/1e6:.1f} MB "
                        f"({pct:.1f}%)",
                        end="",
                    )
                else:
                    print(f"\r{path.name}: {done/1e6:.1f} MB", end="")
    print()
    tmp.replace(path)


def validate(name: str, spec: dict) -> None:
    path: Path = spec["path"]
    size = path.stat().st_size

    if "expected_size" in spec and size != spec["expected_size"]:
        raise RuntimeError(
            f"{name}: size mismatch: got {size:,}, "
            f"expected {spec['expected_size']:,}"
        )

    if "min_size" in spec and size < spec["min_size"]:
        raise RuntimeError(
            f"{name}: suspiciously small download: got {size:,}, "
            f"minimum {spec['min_size']:,}"
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

    if not zipfile.is_zipfile(archive):
        raise RuntimeError(
            f"{name}: downloaded object is not a ZIP archive. "
            "The provider may have changed its public-download endpoint."
        )

    marker = out / ".extracted"
    if marker.exists():
        print(f"[exists] {out}")
        return

    out.mkdir(parents=True, exist_ok=True)
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
        choices=[*SOURCES.keys(), *GROUPS.keys()],
        help="Dataset or dataset group to download",
    )
    args = parser.parse_args()

    names = GROUPS.get(args.dataset, [args.dataset])
    for name in names:
        print(f"\n=== {name} ===")
        try:
            acquire(name)
        except Exception as exc:
            print(f"[ERROR] {name}: {exc}", file=sys.stderr)
            if args.dataset not in GROUPS:
                raise


if __name__ == "__main__":
    main()
