#!/usr/bin/env python3
"""Lightweight inventory check for local external datasets."""

from pathlib import Path

EXPECTED_FILES = {
    "turkiye_survey_reference": Path(
        "data/reference/turkiye_2023/"
        "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx"
    ),
    "turkiye_shakemap_reference": Path(
        "data/reference/turkiye_2023/ShakeMapUpd.xml.gz"
    ),
    "nepal_geid_detailed": Path(
        "data/raw/nepal_2015/Impact_Buildings_Detailed.csv"
    ),
    "nepal_shakemap": Path(
        "data/raw/nepal_2015/usgs_shakemap_grid.xml"
    ),
    "nepal_nso_metadata": Path(
        "data/raw/nepal_2015/NSO_HRHRS_metadata.json"
    ),
    "rc616_priority_i": Path("data/raw/rc616/454_866_Priority_I_data.csv"),
}

EXPECTED_DIRS = {
    "rc616_shakemaps": Path("data/raw/rc616_shakemaps"),
}

OPTIONAL_FILES = {
    "turkiye_geoai_context": Path(
        "data/raw/turkiye_2023_context/2023Turkey_earthquake_data.zip"
    ),
}


def file_status(name: str, path: Path, optional: bool = False) -> None:
    if path.is_file():
        print(f"[OK] {name}: {path} ({path.stat().st_size:,} bytes)")
    else:
        tag = "OPTIONAL" if optional else "MISSING"
        print(f"[{tag}] {name}: {path}")


def dir_status(name: str, path: Path) -> None:
    if path.is_dir():
        n = sum(1 for p in path.rglob("*") if p.is_file())
        print(f"[OK] {name}: {path} ({n} files)")
    else:
        print(f"[MISSING] {name}: {path}")


def main() -> None:
    for name, path in EXPECTED_FILES.items():
        file_status(name, path)
    for name, path in EXPECTED_DIRS.items():
        dir_status(name, path)
    for name, path in OPTIONAL_FILES.items():
        file_status(name, path, optional=True)


if __name__ == "__main__":
    main()
