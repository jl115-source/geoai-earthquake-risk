"""Acquire the public 26-event Oxford/Patten earthquake building-point corpus from Dryad.

The 2026 Oxford follow-up to Patten et al. (2024) cites Dryad DOI
10.5061/dryad.05qfttfcv for the underlying earthquake impact data. This
acquirer resolves the Dryad v2 API, inventories all published files, and
downloads the files without assuming filenames.

Raw data remain under ignored data/raw/patten_dryad/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urljoin

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "patten_dryad"
EVIDENCE = ROOT / "docs" / "patten_dryad"

DOI = "10.5061/dryad.05qfttfcv"
API = "https://datadryad.org/api/v2/"
META_URL = API + "datasets/" + quote("doi:" + DOI, safe="")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_json(session: requests.Session, url: str) -> dict:
    r = session.get(url, timeout=(30, 120))
    r.raise_for_status()
    return r.json()


def _absolutize(href: str) -> str:
    return urljoin("https://datadryad.org", href)


def _walk_links(obj):
    """Yield every href-like URL in nested Dryad JSON."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "href" and isinstance(v, str):
                yield _absolutize(v)
            elif k.lower() in {"downloadlink", "download_url", "url"} and isinstance(v, str):
                if "datadryad.org" in v or v.startswith("/"):
                    yield _absolutize(v)
            else:
                yield from _walk_links(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_links(v)


def _file_objects(obj):
    """Yield dicts that look like Dryad file metadata objects."""
    if isinstance(obj, dict):
        keys = {str(k).lower() for k in obj}
        nameish = any(k in keys for k in {"path", "filename", "name"})
        sizeish = any(k in keys for k in {"size", "filesize"})
        if nameish and (sizeish or any("download" in str(k).lower() for k in obj)):
            yield obj
        for v in obj.values():
            yield from _file_objects(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _file_objects(v)


def _pick_name(obj: dict) -> str | None:
    for k in ("path", "filename", "name"):
        value = obj.get(k)
        if isinstance(value, str) and value.strip():
            return Path(value).name
    return None


def _pick_size(obj: dict) -> int | None:
    for k in ("size", "fileSize", "filesize"):
        value = obj.get(k)
        if isinstance(value, (int, float)):
            return int(value)
    return None


def _pick_download(obj: dict) -> str | None:
    # Prefer explicitly named download fields/relations.
    for k, v in obj.items():
        lk = str(k).lower()
        if isinstance(v, str) and "download" in lk:
            return _absolutize(v)
        if isinstance(v, dict) and "download" in lk:
            href = v.get("href")
            if isinstance(href, str):
                return _absolutize(href)
    for url in _walk_links(obj):
        if "download" in url or "file_stream" in url:
            return url
    return None


def resolve(session: requests.Session) -> tuple[dict, list[dict]]:
    """Resolve dataset metadata and a deduplicated list of downloadable files."""
    meta = _get_json(session, META_URL)

    queue = [META_URL]
    visited = set()
    payloads = [meta]

    # Follow only Dryad API links that plausibly expose versions/files.
    for url in list(_walk_links(meta)):
        if "/api/v2/" in url and any(x in url.lower() for x in ("version", "file")):
            queue.append(url)

    while queue:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            payload = meta if url == META_URL else _get_json(session, url)
        except Exception:
            continue
        if payload is not meta:
            payloads.append(payload)
        for link in _walk_links(payload):
            low = link.lower()
            if "/api/v2/" in low and any(x in low for x in ("version", "file")) and link not in visited:
                queue.append(link)

    files = {}
    for payload in payloads:
        for obj in _file_objects(payload):
            name = _pick_name(obj)
            download = _pick_download(obj)
            if not name or not download:
                continue
            files[(name, download)] = {
                "name": name,
                "bytes_reported": _pick_size(obj),
                "download_url": download,
            }

    # Some Dryad responses put file objects in an embedded list with generic links.
    if not files:
        raise RuntimeError(
            "Dryad metadata resolved but no downloadable file objects were found. "
            "Inspect docs/patten_dryad/dryad_metadata.json and update the resolver for API drift."
        )
    return meta, sorted(files.values(), key=lambda x: x["name"])


def download(session: requests.Session, item: dict, force: bool = False) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    destination = RAW / item["name"]
    if destination.exists() and not force:
        return {
            **item,
            "path": str(destination.relative_to(ROOT)),
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "status": "cached",
        }

    tmp = destination.with_suffix(destination.suffix + ".part")
    with session.get(item["download_url"], stream=True, timeout=(30, 600), allow_redirects=True) as r:
        r.raise_for_status()
        with tmp.open("wb") as stream:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    stream.write(chunk)
    if not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"Empty Dryad download for {item['name']}")
    tmp.replace(destination)
    return {
        **item,
        "path": str(destination.relative_to(ROOT)),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "status": "downloaded",
    }


def run(metadata_only: bool = False, force: bool = False) -> dict:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        session.headers.update({"User-Agent": "geoai-earthquake-risk/1.0"})
        meta, files = resolve(session)
        (EVIDENCE / "dryad_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        (EVIDENCE / "dryad_file_manifest.json").write_text(json.dumps(files, indent=2) + "\n")

        result = {
            "doi": DOI,
            "metadata_url": META_URL,
            "n_files": len(files),
            "reported_total_bytes": sum(x["bytes_reported"] or 0 for x in files),
            "files": files,
            "downloaded": [],
        }
        if not metadata_only:
            result["downloaded"] = [download(session, x, force=force) for x in files]

    (EVIDENCE / "acquisition.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = run(args.metadata_only, args.force)
    print(json.dumps({
        "doi": result["doi"],
        "n_files": result["n_files"],
        "reported_total_bytes": result["reported_total_bytes"],
        "downloaded_files": len(result["downloaded"]),
    }, indent=2))


if __name__ == "__main__":
    main()
