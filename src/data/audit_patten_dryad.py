"""Audit public Dryad files for the Patten/Anderson-Loake 26-event point corpus.

This intentionally does not fit a model. It inventories downloaded files and
searches tabular files for building-level geolocation, event and damage fields.
"""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "patten_dryad"
OUT = ROOT / "docs" / "patten_dryad"

GEO_NAMES = {"longitude", "latitude", "lon", "lat", "x", "y"}
DAMAGE_HINTS = ("damage", "grading", "grade", "class")
EVENT_HINTS = ("event", "earthquake", "eqid", "date")


def _profile_frame(df: pd.DataFrame, source: str) -> dict:
    cols = [str(c) for c in df.columns]
    lower = {c.lower(): c for c in cols}
    geo = [c for c in cols if c.lower() in GEO_NAMES]
    damage = [c for c in cols if any(h in c.lower() for h in DAMAGE_HINTS)]
    event = [c for c in cols if any(h in c.lower() for h in EVENT_HINTS)]
    profile = {
        "source": source,
        "rows": int(len(df)),
        "columns": cols,
        "geo_columns": geo,
        "damage_columns": damage,
        "event_columns": event,
    }
    for c in geo + damage + event:
        s = df[c]
        profile.setdefault("field_summary", {})[c] = {
            "non_null": int(s.notna().sum()),
            "unique": int(s.nunique(dropna=True)),
            "examples": [str(x) for x in s.dropna().astype(str).unique()[:12]],
        }
    return profile


def _read_tabular(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        yield path.name, pd.read_csv(path, low_memory=False)
    elif suffix in {".parquet", ".pq"}:
        yield path.name, pd.read_parquet(path)
    elif suffix in {".tsv", ".txt"}:
        try:
            yield path.name, pd.read_csv(path, sep="\t", low_memory=False)
        except Exception:
            return
    elif suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                low = member.lower()
                if low.endswith(".csv"):
                    with zf.open(member) as f:
                        yield f"{path.name}::{member}", pd.read_csv(f, low_memory=False)
                elif low.endswith((".tsv", ".txt")):
                    try:
                        with zf.open(member) as f:
                            yield f"{path.name}::{member}", pd.read_csv(f, sep="\t", low_memory=False)
                    except Exception:
                        pass


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    if not RAW.exists():
        raise FileNotFoundError("Run python -m src.data.acquire_patten_dryad first")

    inventory = []
    profiles = []
    for path in sorted(RAW.iterdir()):
        if not path.is_file():
            continue
        item = {"name": path.name, "bytes": path.stat().st_size}
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                item["zip_members"] = len(zf.infolist())
                item["zip_member_names"] = zf.namelist()
        inventory.append(item)
        try:
            for source, frame in _read_tabular(path):
                profiles.append(_profile_frame(frame, source))
        except Exception as exc:
            item["tabular_read_error"] = f"{type(exc).__name__}: {exc}"

    candidates = [
        p for p in profiles
        if len(p["geo_columns"]) >= 2 and p["damage_columns"] and p["event_columns"]
    ]

    result = {
        "files": inventory,
        "tabular_profiles": profiles,
        "building_point_candidates": candidates,
        "candidate_count": len(candidates),
        "interpretation": (
            "A candidate requires at least two obvious geolocation columns plus "
            "a damage-like field and an event-like field. This is a schema screen, "
            "not proof of semantic equivalence or unbiased sampling."
        ),
    }
    (OUT / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def main():
    r = run()
    print(json.dumps({
        "files": len(r["files"]),
        "tabular_profiles": len(r["tabular_profiles"]),
        "building_point_candidates": [
            {"source": x["source"], "rows": x["rows"],
             "geo": x["geo_columns"], "damage": x["damage_columns"],
             "event": x["event_columns"]}
            for x in r["building_point_candidates"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
