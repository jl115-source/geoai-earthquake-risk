"""Acquire Milestone 1C public inputs locally; never commit downloaded data."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import tarfile

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"
SOURCES = {
    "nepal-geid": ("https://raw.githubusercontent.com/gem/geid/d6eb5ed42475ef67ba28cd9e0567f2d0d17a6393/South_Asia/Nepal/20150425_M7.8_Gorkha/1_Impact/Impact_Buildings_Detailed.csv", "nepal_2015/Impact_Buildings_Detailed.csv", None),
    "aci133": ("https://zenodo.org/records/13386343/files/ACI133v3.xlsx?download=1", "turkiye_aci133/ACI133v3.xlsx", "c912ccae688adf77339571c621f31e2d"),
    "turkiye-spatial": ("https://zenodo.org/records/18437501/files/2023Turkey_earthquake_data.zip?download=1", "turkiye_2023_context/2023Turkey_earthquake_data.zip", "f3a3a9982cf63bd954616a898c7416b9"),
    "nso-metadata": ("https://microdata.nsonepal.gov.np/index.php/metadata/export/69/json", "audit_metadata/nso_69.json", None),
    "nso-access": ("https://microdata.nsonepal.gov.np/index.php/catalog/69/get-microdata", "audit_metadata/nso_access.html", None),
    "nso-study": ("https://microdata.nsonepal.gov.np/index.php/catalog/69/study-description", "audit_metadata/nso_study.html", None),
    "aci-metadata": ("https://zenodo.org/api/records/13386343", "audit_metadata/zenodo_13386343.json", None),
    "spatial-metadata": ("https://zenodo.org/api/records/18437501", "audit_metadata/zenodo_18437501.json", None),
    "rc616-page": ("https://www.dropbox.com/scl/fo/qi3d9rbwjdqn8vev74bjs/APrtlwCls_w8csviSUJfbqY?rlkey=y1p57c5axbj9fkxs4x2itfwp2&dl=0", "audit_metadata/rc616_dropbox.html", None),
    "nso-building-dictionary": ("https://microdata.nsonepal.gov.np/index.php/catalog/69/data-dictionary/F2?file_name=Building", "audit_metadata/nso_building.html", None),
    "nso-ddi": ("https://microdata.nsonepal.gov.np/index.php/metadata/export/69/ddi", "audit_metadata/nso_69.xml", None),
}
RC_URL = "https://www.dropbox.com/scl/fo/qi3d9rbwjdqn8vev74bjs/AJACOPsS6f6ZlIQKQyiEBTA/454_bag_2024-01-25.tgz?rlkey=y1p57c5axbj9fkxs4x2itfwp2&dl=1"
RC_MEMBERS = [f"454_bag_2024-01-25/data/datatables/{name}" for name in
              ("454_866_Priority_I_data.csv", "454_866_Priority_I_metadata.csv", "454_datatables_metadata.csv")]
EXPECTED_SHA256 = {"nepal-geid": "695762d973e9bdbf93178542333b3a0bef4328c9be036577cfd7fdcf65546d66"}
RC_HASHES = dict(zip(RC_MEMBERS, [
    "8b17a9c5dd145280d24025ec8ff123af6d47ab60e6ac0597e4cae42c26ec2d55",
    "d3ae908b1be2a7ac266ed0538e3bf46a744f1a0ef6bb0831b00d9b5d0ffec707",
    "9dfe12785b0dc2936439b3f3e56f65dbb690a3d9ac2e7bf3a94f6521de420957",
]))


def extract_rc_tables(archive, output):
    """Read only the explicitly named tables; never extract arbitrary tar paths."""
    found = {}
    scanned = 0
    for member in archive:
        scanned += member.size
        if scanned > 5_000_000:
            raise ValueError("RC616 tables not found in the first 5 MB; archive layout changed")
        if member.name not in RC_MEMBERS:
            continue
        if not member.isfile():
            raise ValueError("RC616 table is not a regular file")
        path = output / Path(member.name).name
        path.write_bytes(archive.extractfile(member).read())
        found[member.name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
        if len(found) == len(RC_MEMBERS):
            return found
    raise ValueError("Incomplete RC616 table set")


def acquire_rc616():
    output = RAW / "rc616"
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "acquisition.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if set(manifest["members"]) != set(RC_MEMBERS):
            raise ValueError("Incomplete cached RC616 member set")
        for member, metadata in manifest["members"].items():
            if digest(output / Path(member).name) != metadata["sha256"] or metadata["sha256"] != RC_HASHES[member]:
                raise ValueError("Cached RC616 checksum mismatch")
        return manifest
    with requests.get(RC_URL, stream=True, timeout=(30, 180)) as response:
        response.raise_for_status()
        with tarfile.open(fileobj=response.raw, mode="r|gz") as archive:
            members = extract_rc_tables(archive, output)
        if any(metadata["sha256"] != RC_HASHES[member] for member, metadata in members.items()):
            raise ValueError("RC616 source table hashes changed; inspect before accepting")
        manifest = {"source_url": RC_URL, "archive_content_length": response.headers.get("Content-Length"),
                    "acquisition_scope": "Only three data/metadata CSV members streamed; 15.4 GB media archive not downloaded in full.",
                    "members": members}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest), flush=True)
    return manifest


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def acquire(name):
    if name == "rc616":
        return acquire_rc616()
    url, relative, md5 = SOURCES[name]
    path = RAW / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        temporary = path.with_suffix(path.suffix + ".part")
        with requests.get(url, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    stream.write(chunk)
        if temporary.stat().st_size == 0:
            raise ValueError(f"Empty response for {name}; not a successful acquisition")
        if md5 and digest(temporary, "md5") != md5:
            raise ValueError(f"Checksum mismatch for {name}; partial file retained for inspection")
        temporary.replace(path)
    if md5 and digest(path, "md5") != md5:
        raise ValueError(f"Checksum mismatch for existing {name}")
    if name in EXPECTED_SHA256 and digest(path) != EXPECTED_SHA256[name]:
        raise ValueError(f"SHA-256 mismatch for {name}")
    manifest = {"dataset": name, "source_url": url, "relative_path": relative,
                "bytes": path.stat().st_size, "sha256": digest(path), "expected_md5": md5}
    path.with_suffix(path.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest), flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="+", choices=[*SOURCES, "rc616"])
    args = parser.parse_args()
    failures = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {name: pool.submit(acquire, name) for name in args.datasets}
        for name, future in futures.items():
            try:
                future.result()
            except Exception as exc:
                failures.append(name)
                failure_path = RAW / "audit_metadata" / f"{name}_failure.json"
                failure_path.parent.mkdir(parents=True, exist_ok=True)
                failure_path.write_text(json.dumps({"dataset": name, "acquired": False, "reason": str(exc)}, indent=2) + "\n")
                print(f"FAILED {name}: {exc}", flush=True)
    if failures:
        raise SystemExit(f"Acquisition incomplete: {failures}")


if __name__ == "__main__":
    main()
