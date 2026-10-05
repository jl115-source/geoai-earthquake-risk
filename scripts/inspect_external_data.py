#!/usr/bin/env python3
"""Summarize locally acquired project datasets."""

from pathlib import Path
import zipfile
import pandas as pd

ROOT = Path("data/raw")


def inspect_csv(path: Path, nrows: int = 5) -> None:
    if not path.exists():
        print(f"[missing] {path}")
        return
    df = pd.read_csv(path, nrows=nrows)
    print(f"\n{path}")
    print(f"size={path.stat().st_size:,} bytes")
    print("columns:")
    for c in df.columns:
        print(f"  - {c}")
    print("\npreview:")
    print(df.head().to_string(index=False))


def inspect_zip(path: Path) -> None:
    if not path.exists():
        print(f"[missing] {path}")
        return
    print(f"\n{path}")
    print(f"size={path.stat().st_size:,} bytes")
    if not zipfile.is_zipfile(path):
        print("not a zip archive")
        return
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        print(f"archive members={len(names):,}")
        for name in names[:30]:
            print(f"  - {name}")
        if len(names) > 30:
            print(f"  ... {len(names)-30:,} more")


def main() -> None:
    inspect_csv(ROOT / "nepal_2015" / "Impact_Buildings_Detailed.csv")
    inspect_zip(ROOT / "rc616" / "rc616.zip")
    inspect_zip(
        ROOT / "turkiye_2023_context" / "2023Turkey_earthquake_data.zip"
    )


if __name__ == "__main__":
    main()
