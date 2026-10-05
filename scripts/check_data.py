#!/usr/bin/env python3
"""Lightweight inventory check for local external datasets."""

from pathlib import Path

EXPECTED = {
    "turkiye_survey": Path(
        "data/raw/turkiye_2023/"
        "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx"
    ),
    "turkiye_shakemap": Path("data/raw/turkiye_2023/ShakeMapUpd.xml.gz"),
    "nepal_dir": Path("data/raw/nepal"),
    "italy_dado_dir": Path("data/raw/italy_dado"),
}


def main() -> None:
    for name, path in EXPECTED.items():
        if path.is_file():
            print(f"[OK] {name}: {path} ({path.stat().st_size:,} bytes)")
        elif path.is_dir():
            n = sum(1 for p in path.rglob("*") if p.is_file())
            print(f"[OK] {name}: {path} ({n} files)")
        else:
            print(f"[MISSING] {name}: {path}")


if __name__ == "__main__":
    main()
