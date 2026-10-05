#!/usr/bin/env python3
"""Validate the local earthquake-data inventory before analysis/model fitting."""

from __future__ import annotations

from pathlib import Path
import zipfile

CHECKS = {
    "turkiye_survey_reference": {
        "path": Path(
            "data/reference/turkiye_2023/"
            "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx"
        ),
        "expected_size": 218_642,
    },
    "turkiye_shakemap_raw": {
        "path": Path("data/raw/turkiye_2023/ShakeMapUpd.xml.gz"),
        "expected_size": 14_980_986,
    },
    "nepal_geid_detailed": {
        "path": Path("data/raw/nepal_2015/Impact_Buildings_Detailed.csv"),
        "expected_size": 78_448_526,
    },
    "nepal_shakemap": {
        "path": Path("data/raw/nepal_2015/usgs_shakemap_grid.xml"),
        "min_size": 100_000,
    },
    "nepal_nso_metadata": {
        "path": Path("data/raw/nepal_2015/NSO_HRHRS_metadata.json"),
        "min_size": 10_000,
    },
    "nepal_questionnaire_en": {
        "path": Path("data/raw/nepal_2015/docs/HRHRS_questionnaire_en.pdf"),
        "min_size": 100_000,
    },
    "nepal_key_findings_14": {
        "path": Path(
            "data/raw/nepal_2015/docs/HRHRS_key_findings_14_districts.pdf"
        ),
        "min_size": 300_000,
    },
    "rc616_archive": {
        "path": Path("data/raw/rc616/rc616.zip"),
        "min_size": 100_000,
        "zip": True,
    },
}

OPTIONAL = {
    "turkiye_geoai_context": {
        "path": Path(
            "data/raw/turkiye_2023_context/2023Turkey_earthquake_data.zip"
        ),
        "min_size": 500_000_000,
        "zip": True,
    },
}

RC616_EVENTS = (
    "erzincan_1992",
    "duzce_1999",
    "bingol_2003",
    "pisco_2007",
    "wenchuan_2008",
    "haiti_2010",
)


def check_file(name: str, spec: dict, optional: bool = False) -> bool:
    path: Path = spec["path"]
    if not path.is_file():
        print(f"[{'OPTIONAL' if optional else 'MISSING'}] {name}: {path}")
        return optional

    size = path.stat().st_size
    ok = True
    reason = ""

    if "expected_size" in spec and size != spec["expected_size"]:
        ok = False
        reason = f"expected {spec['expected_size']:,} bytes"
    elif "min_size" in spec and size < spec["min_size"]:
        ok = False
        reason = f"minimum {spec['min_size']:,} bytes"
    elif spec.get("zip") and not zipfile.is_zipfile(path):
        ok = False
        reason = "not a valid ZIP archive"

    if ok:
        print(f"[OK] {name}: {path} ({size:,} bytes)")
    else:
        print(f"[BAD] {name}: {path} ({size:,} bytes; {reason})")
    return ok or optional


def check_rc616_shakemaps() -> bool:
    root = Path("data/raw/rc616_shakemaps")
    missing = []
    for event in RC616_EVENTS:
        grid = root / event / "grid.xml"
        if not grid.is_file() or grid.stat().st_size < 1_000:
            missing.append(event)

    if missing:
        print("[MISSING] rc616_shakemaps: " + ", ".join(missing))
        return False

    print(f"[OK] rc616_shakemaps: {len(RC616_EVENTS)} non-empty grids")
    return True


def main() -> None:
    ok = True
    for name, spec in CHECKS.items():
        ok = check_file(name, spec) and ok

    extracted = Path("data/raw/rc616/extracted/.extracted")
    if extracted.is_file():
        print("[OK] rc616_extracted")
    else:
        print("[MISSING] rc616_extracted")
        ok = False

    ok = check_rc616_shakemaps() and ok

    for name, spec in OPTIONAL.items():
        check_file(name, spec, optional=True)

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
