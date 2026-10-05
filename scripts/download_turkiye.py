#!/usr/bin/env python3
"""Download and validate the open Türkiye 2023 engineering-survey inputs.

Data provenance
---------------
- maxandersonloake/TUR2023_02_06
- Engineering survey workbook: CC BY 4.0
- Companion analysis code: MIT

The workbook is small and also retained under data/reference/ for provenance.
The ~15 MB ShakeMap is downloaded locally under data/raw/ and is not committed.
"""

from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/maxandersonloake/TUR2023_02_06/main/Data"
OUT = Path("data/raw/turkiye_2023")

FILES = {
    "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx": {
        "url": f"{BASE}/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx",
        "expected_size": 218_642,
    },
    "ShakeMapUpd.xml.gz": {
        "url": f"{BASE}/ShakeMapUpd.xml.gz",
        "expected_size": 14_980_986,
    },
}


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    req = Request(url, headers={"User-Agent": "geoai-earthquake-risk/0.1"})
    with urlopen(req, timeout=300) as r, tmp.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dst)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    for name, spec in FILES.items():
        dst = OUT / name
        expected = spec["expected_size"]

        if dst.exists() and dst.stat().st_size == expected:
            print(f"[exists] {dst} ({expected:,} bytes)")
            continue

        if dst.exists():
            print(
                f"[replace] {dst}: size={dst.stat().st_size:,}, "
                f"expected={expected:,}"
            )

        print(f"[download] {spec['url']}")
        download(spec["url"], dst)

        got = dst.stat().st_size
        if got != expected:
            raise RuntimeError(
                f"{name}: size mismatch after download: got {got:,}, "
                f"expected {expected:,}"
            )
        print(f"[saved] {dst} ({got:,} bytes)")


if __name__ == "__main__":
    main()
