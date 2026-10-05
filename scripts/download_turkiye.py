#!/usr/bin/env python3
"""Download the open Türkiye 2023 engineering-survey inputs.

Data provenance:
- maxandersonloake/TUR2023_02_06
- Engineering survey data: CC BY 4.0
- Companion analysis code: MIT

Raw data are intentionally git-ignored.
"""

from pathlib import Path
from urllib.request import urlretrieve

BASE = "https://raw.githubusercontent.com/maxandersonloake/TUR2023_02_06/main/Data"
FILES = {
    "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx":
        f"{BASE}/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx",
    "ShakeMapUpd.xml.gz":
        f"{BASE}/ShakeMapUpd.xml.gz",
}

OUT = Path("data/raw/turkiye_2023")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        dst = OUT / name
        if dst.exists() and dst.stat().st_size > 0:
            print(f"[exists] {dst} ({dst.stat().st_size:,} bytes)")
            continue
        print(f"[download] {url}")
        urlretrieve(url, dst)
        print(f"[saved] {dst} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
