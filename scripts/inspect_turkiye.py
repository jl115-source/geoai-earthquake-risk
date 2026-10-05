#!/usr/bin/env python3
"""Inspect the Türkiye engineering-survey workbook and export a clean preview.

This intentionally does not fit a model. It establishes the empirical schema,
damage classes, spatial coverage, and missingness before any feature engineering.
"""

from pathlib import Path
import pandas as pd

RAW_SRC = Path(
    "data/raw/turkiye_2023/"
    "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx"
)
REFERENCE_SRC = Path(
    "data/reference/turkiye_2023/"
    "Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx"
)


def main() -> None:
    src = RAW_SRC if RAW_SRC.exists() else REFERENCE_SRC
    if not src.exists():
        raise SystemExit("Run: python scripts/download_turkiye.py")

    print(f"source={src}")
    df = pd.read_excel(src)

    print(f"rows={len(df):,} columns={len(df.columns)}")
    print("\nColumns:")
    for c in df.columns:
        print(f"  - {c}")

    key_candidates = [
        "longitude", "latitude", "City/Town", "structure_type",
        "damage_condition", "PGV_mean", "PGA_mean",
        "SA(0.3)_mean", "SA(1.0)_mean",
    ]
    keys = [c for c in key_candidates if c in df.columns]

    print("\nMissingness in core fields:")
    if keys:
        print(df[keys].isna().mean().sort_values(ascending=False).to_string())

    if "damage_condition" in df.columns:
        print("\nDamage labels:")
        print(df["damage_condition"].value_counts(dropna=False).to_string())

    if "structure_type" in df.columns:
        print("\nStructure types:")
        print(df["structure_type"].value_counts(dropna=False).to_string())

    out = Path("data/processed/turkiye_2023")
    out.mkdir(parents=True, exist_ok=True)
    df.head(50).to_csv(out / "survey_preview.csv", index=False)
    print(f"\nWrote local preview: {out / 'survey_preview.csv'}")


if __name__ == "__main__":
    main()
