"""Acquire/audit large geolocated earthquake-damage candidates for Milestone 1G.

Noto 2024 is fully public and can be downloaded automatically.
xBD Mexico requires the user to obtain the original xBD archive from xView2
(registration/login required); this module validates and inventories the Mexico
subset without bypassing those terms. xBD-S12 is recorded as an optional public
Sentinel companion, not a substitute for the original xBD labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

NOTO_URL = "https://zenodo.org/records/15192949/files/Noto_Peninsula_Damage_2_5.gpkg?download=1"
NOTO_MD5 = "280e9c53cb45086786c20ed0b2c21ffb"
NOTO_REL = Path("noto_2024/Noto_Peninsula_Damage_2_5.gpkg")

XBD_S12_URL = "https://zenodo.org/records/18960454/files/xbd_s12.tar.gz?download=1"
XBD_S12_MD5 = "891b86000caa6019c20a95fc2f3f4e68"
XBD_OFFICIAL = "https://xview2.org/dataset"
MEXICO_TOKEN = "mexico-earthquake"


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path, expected_md5: str | None = None) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        with requests.get(url, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        stream.write(chunk)
        if temporary.stat().st_size == 0:
            raise ValueError("Empty download")
        temporary.replace(path)
    md5 = digest(path, "md5")
    if expected_md5 and md5 != expected_md5:
        raise ValueError(f"MD5 mismatch for {path.name}: {md5}")
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "md5": md5,
        "sha256": digest(path),
        "source_url": url,
    }


def acquire_noto() -> dict:
    result = download(NOTO_URL, RAW / NOTO_REL, NOTO_MD5)
    manifest = {
        "dataset": "noto_2024_building_damage_v2_5",
        "access": "open_public_zenodo",
        "records_expected": 140208,
        "crs_expected": "EPSG:4326",
        "source_record": "https://zenodo.org/records/15192949",
        "doi_family": "10.5281/zenodo.11055711",
        "file": result,
        "expected_fields": [
            "fid", "s_fid", "damage", "source", "damage_val", "municipality",
            "conf", "GSI_fire", "GSI_slope_failure", "GSI_tsunami", "USGS_MMI",
            "geometry",
        ],
    }
    out = RAW / "noto_2024" / "acquisition.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _json_files(root: Path):
    for path in root.rglob("*.json"):
        if path.is_file():
            yield path


def audit_xbd_mexico(xbd_root: Path) -> dict:
    """Inventory original xBD Mexico labels already obtained from xView2.

    Does not download xBD or accept third-party mirrors as authoritative.
    """
    xbd_root = xbd_root.expanduser().resolve()
    if not xbd_root.exists():
        raise FileNotFoundError(
            f"xBD root not found: {xbd_root}. Obtain the official dataset from {XBD_OFFICIAL} first."
        )
    labels = []
    for path in _json_files(xbd_root):
        name = path.name.lower()
        if MEXICO_TOKEN not in name:
            # Some layouts nest by disaster and use generic filenames.
            if MEXICO_TOKEN not in str(path.parent).lower():
                continue
        labels.append(path)
    if not labels:
        raise ValueError(
            "No mexico-earthquake JSON labels found. Expected original xBD labels from the official xView2 download."
        )

    counts = {"json_files": len(labels), "buildings": 0, "classes": {}}
    bounds = [180.0, 90.0, -180.0, -90.0]
    coordinate_count = 0
    parse_errors = []
    for path in labels:
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            parse_errors.append({"file": str(path), "error": str(exc)})
            continue
        features = data.get("features", {})
        xy = features.get("xy", []) if isinstance(features, dict) else []
        counts["buildings"] += len(xy)
        for feat in xy:
            props = feat.get("properties", {}) or {}
            subtype = str(props.get("subtype", "<missing>"))
            counts["classes"][subtype] = counts["classes"].get(subtype, 0) + 1
            # WKT polygons are image-space, while label metadata may contain lon/lat.
        metadata = data.get("metadata", {}) or {}
        for key in ("bounds", "bbox"):
            value = metadata.get(key)
            if isinstance(value, list) and len(value) == 4:
                try:
                    x0, y0, x1, y1 = map(float, value)
                    if -180 <= x0 <= 180 and -180 <= x1 <= 180 and -90 <= y0 <= 90 and -90 <= y1 <= 90:
                        bounds[0] = min(bounds[0], x0); bounds[1] = min(bounds[1], y0)
                        bounds[2] = max(bounds[2], x1); bounds[3] = max(bounds[3], y1)
                        coordinate_count += 1
                except Exception:
                    pass

    manifest = {
        "dataset": "xbd_mexico_earthquake",
        "access": "user_obtained_official_xview2",
        "official_source": XBD_OFFICIAL,
        "license": "CC-BY-NC-SA-4.0 per xView/xBD terms",
        "root": str(xbd_root),
        "mexico_label_files": len(labels),
        "building_annotation_count": counts["buildings"],
        "damage_class_counts": dict(sorted(counts["classes"].items())),
        "label_files_with_metadata_bounds": coordinate_count,
        "metadata_bounds": None if coordinate_count == 0 else bounds,
        "parse_errors": parse_errors,
        "note": (
            "xBD-S12 is an optional public Sentinel-1/2 companion. It does not replace "
            "the original xBD labels and is not auto-downloaded here because the full "
            "archive is ~9.5 GB."
        ),
        "xbd_s12": {
            "record": "https://zenodo.org/records/18960454",
            "archive_url": XBD_S12_URL,
            "archive_md5": XBD_S12_MD5,
        },
    }
    out = RAW / "xbd_mexico"
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("noto")
    x = sub.add_parser("xbd-mexico")
    x.add_argument("--xbd-root", type=Path, required=True)
    args = p.parse_args()

    if args.command == "noto":
        result = acquire_noto()
    else:
        result = audit_xbd_mexico(args.xbd_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
