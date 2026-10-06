"""Acquire the public Copernicus EMS Zagreb 2020 earthquake geospatial package.

This module resolves the authoritative public distribution from the EU/JRC/CEMS
catalogue at runtime, downloads it, verifies that it is a ZIP archive, inventories
all members, and extracts GeoJSON/vector metadata needed for audit. Raw content
stays under ignored data/raw/.
"""
from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "zagreb_2020_copernicus"
RESULTS = ROOT / "docs" / "zagreb_2020_copernicus"

DATASET_ID = "0f79c223-1225-4f9b-91dc-1ce948e1ff2b"
JRC_PAGE = f"https://data.jrc.ec.europa.eu/dataset/{DATASET_ID}"
CURRENT_ACTIVATION = "https://mapping.emergency.copernicus.eu/activations/EMSN074/DAMAGEASSESSMENT/"
EU_REPO = f"https://data.europa.eu/api/hub/repo/datasets/{DATASET_ID}"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.urls.append(value)

def digest(path: Path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def get_text(url: str, **kwargs) -> str:
    with requests.get(url, timeout=(30, 120), **kwargs) as response:
        response.raise_for_status()
        return response.text

def candidate_urls():
    urls = []
    # Current activation page: most reliable public landing page.
    for page in (CURRENT_ACTIVATION, JRC_PAGE):
        try:
            text = get_text(page)
        except Exception:
            continue
        parser = Links(); parser.feed(text)
        urls.extend(parser.urls)
        urls.extend(re.findall(r'https?://[^"\'<>\s]+', text))

    # data.europa DCAT graph sometimes exposes dcat:downloadURL/accessURL directly.
    try:
        text = get_text(EU_REPO, headers={"Accept": "text/turtle"})
        urls.extend(re.findall(r'<(https?://[^>]+)>', text))
    except Exception:
        pass

    normalized = []
    for url in urls:
        url = url.replace("&amp;", "&")
        if url.startswith("/"):
            url = "https://mapping.emergency.copernicus.eu" + url
        if "emergency.copernicus.eu/EMSN074" in url:
            continue
        normalized.append(url)
    # Prefer explicit ZIP/download resources mentioning activation/geodata.
    def score(url):
        lower = url.lower()
        return (
            5 * (".zip" in lower)
            + 4 * ("emsn074" in lower)
            + 3 * ("geospatial" in lower or "geodata" in lower or "gdb" in lower)
            + 2 * ("download" in lower)
            - 4 * (".pdf" in lower or ".jpg" in lower or ".png" in lower)
        )
    return sorted(set(normalized), key=lambda x: (-score(x), x))

def try_download(url: str, destination: Path) -> dict | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(".part")
    try:
        with requests.get(url, stream=True, timeout=(30, 300), allow_redirects=True) as response:
            response.raise_for_status()
            ctype = response.headers.get("content-type", "")
            with tmp.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        stream.write(chunk)
            if tmp.stat().st_size < 1024:
                tmp.unlink(missing_ok=True)
                return None
            if not zipfile.is_zipfile(tmp):
                tmp.unlink(missing_ok=True)
                return None
            tmp.replace(destination)
            return {
                "source_url": url,
                "content_type": ctype,
                "bytes": destination.stat().st_size,
                "sha256": digest(destination),
            }
    except Exception:
        tmp.unlink(missing_ok=True)
        return None

def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    archive = RAW / "EMSN074_geospatial.zip"

    if archive.exists():
        if not zipfile.is_zipfile(archive):
            raise ValueError("Cached Zagreb file is not a ZIP archive")
        source = {"source_url": "cached", "bytes": archive.stat().st_size, "sha256": digest(archive)}
    else:
        source = None
        attempted = []
        for url in candidate_urls():
            attempted.append(url)
            source = try_download(url, archive)
            if source:
                break
        if not source:
            (RESULTS / "resolution_failure.json").write_text(json.dumps({
                "dataset_id": DATASET_ID,
                "landing_pages": [JRC_PAGE, CURRENT_ACTIVATION],
                "attempted_urls": attempted,
                "reason": "No public URL resolved to a valid ZIP archive"
            }, indent=2) + "\n")
            raise RuntimeError("Could not resolve a public EMSN074 geospatial ZIP; inspect resolution_failure.json")

    with zipfile.ZipFile(archive) as zf:
        members = []
        for info in zf.infolist():
            members.append({
                "name": info.filename,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "crc32": info.CRC,
            })
        geojson = [m["name"] for m in members if m["name"].lower().endswith((".geojson", ".json"))]
        gdb = sorted({m["name"].split(".gdb/")[0] + ".gdb/" for m in members if ".gdb/" in m["name"].lower()})
        tiffs = [m["name"] for m in members if m["name"].lower().endswith((".tif", ".tiff"))]
        report = {
            "dataset": "copernicus_emsn074_zagreb_2020",
            "access": "public_no_authentication",
            "dataset_id": DATASET_ID,
            "activation": "EMSN074",
            "event": "2020-03-22 Zagreb earthquake",
            "source": source,
            "member_count": len(members),
            "members": members,
            "geojson_members": geojson,
            "geodatabase_roots": gdb,
            "tiff_members": tiffs,
            "notes": [
                "Copernicus product is remote-sensing/reference geodata, not the City engineering inspection database.",
                "P02.1 reference buildings are based on pre-event 2019 VHR imagery.",
                "P08.1 damage assessment uses post-event drone/VHR imagery and is suitable as a label/validation product, not a pre-event predictor."
            ],
        }
        (RESULTS / "inventory.json").write_text(json.dumps(report, indent=2) + "\n")
        (RESULTS / "members.csv").write_text(
            "name,bytes,compressed_bytes,crc32\n" +
            "".join(f'"{m["name"].replace(chr(34), chr(34)*2)}",{m["bytes"]},{m["compressed_bytes"]},{m["crc32"]}\n' for m in members)
        )
    return report

def main():
    report = acquire()
    print(json.dumps({
        "bytes": report["source"]["bytes"],
        "member_count": report["member_count"],
        "geojson_members": len(report["geojson_members"]),
        "geodatabase_roots": len(report["geodatabase_roots"]),
        "tiff_members": len(report["tiff_members"]),
        "source_url": report["source"]["source_url"],
    }, indent=2))

if __name__ == "__main__":
    main()
