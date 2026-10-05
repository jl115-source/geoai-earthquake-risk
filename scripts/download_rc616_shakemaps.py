#!/usr/bin/env python3
"""Download ShakeMap grids for the six-event RC616 benchmark.

For ordinary USGS event IDs this script discovers the current preferred
ShakeMap product from the USGS event detail feed. Bingöl uses a stable
ShakeMap Atlas fallback because its historical product is exposed under an
Atlas product identifier.
"""

from __future__ import annotations

import json
from pathlib import Path
import requests
import yaml

CONFIG = Path("data/reference/rc616_events.yml")
OUT = Path("data/raw/rc616_shakemaps")

DETAIL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=(30, 180)) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)


def find_grid_url(event_id: str) -> str:
    r = requests.get(DETAIL.format(event_id=event_id), timeout=60)
    r.raise_for_status()
    detail = r.json()
    products = detail["properties"]["products"].get("shakemap", [])
    if not products:
        raise RuntimeError(f"No ShakeMap product found for {event_id}")

    products = sorted(
        products,
        key=lambda p: (
            p.get("preferredWeight", 0),
            p.get("updateTime", 0),
        ),
        reverse=True,
    )

    for product in products:
        contents = product.get("contents", {})
        for key in (
            "download/grid.xml",
            "download/grid.xml.zip",
            "grid.xml",
            "grid.xml.zip",
        ):
            if key in contents and contents[key].get("url"):
                return contents[key]["url"]

    raise RuntimeError(f"ShakeMap exists but no grid.xml product found for {event_id}")


def atlas_grid_url(product_id: str, version: str) -> str:
    return (
        "https://earthquake.usgs.gov/product/shakemap/"
        f"{product_id}/atlas/{version}/download/grid.xml"
    )


def main() -> None:
    cfg = yaml.safe_load(CONFIG.read_text())
    OUT.mkdir(parents=True, exist_ok=True)

    for label, meta in cfg["events"].items():
        dst = OUT / label / "grid.xml"
        if dst.exists() and dst.stat().st_size:
            print(f"[exists] {dst}")
            continue

        try:
            if label == "bingol_2003":
                url = atlas_grid_url(
                    meta["usgs_atlas_product_id"],
                    meta["usgs_atlas_product_version"],
                )
            else:
                url = find_grid_url(meta["usgs_event_id"])
        except Exception:
            # Explicit Wenchuan Atlas fallback.
            if label == "wenchuan_2008":
                url = (
                    "https://earthquake.usgs.gov/product/shakemap/"
                    "usp000g650/atlas/1594174375811/download/grid.xml"
                )
            else:
                raise

        print(f"[download] {label}: {url}")
        download(url, dst)
        print(f"[saved] {dst} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
