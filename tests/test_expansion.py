"""Offline tests for audit semantics and safe, selective extraction."""

import io
import json
from pathlib import Path
import tarfile
import zipfile

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("requests", reason="Install requirements-audit.txt for expansion acquisition tests")

from src.data.acquire_expansion import RC_MEMBERS, extract_rc_tables
from src.data.audit_expansion import (
    OUTPUT, RAW, RC_DAMAGE, audit_nepal, coordinate_profile, haversine_distances,
    ingest_rc616, parse_nso_ddi, safe_extract_zip, serializable,
)


def test_distances_are_metres_and_symmetric():
    points = [[0, 0], [0, 1]]
    distances = haversine_distances(points, points)
    np.testing.assert_allclose(distances, distances.T)
    assert np.diag(distances).tolist() == [0, 0]
    assert distances[0, 1] == pytest.approx(111195.08, abs=.1)
    with pytest.raises(ValueError):
        haversine_distances([[np.nan, 0]], points)


def test_coordinate_audit_does_not_count_missing_as_duplicates():
    data = pd.DataFrame({"latitude": [37, 37, None, None, 95, 0], "longitude": [36, 36, None, None, 36, 0]})
    report = coordinate_profile(data)
    assert report["unique_valid_pairs"] == 1
    assert report["rows_in_duplicate_coordinate_groups"] == 2
    assert report["missing_or_unparseable_pairs"] == 2
    assert report["invalid_present_pairs"] == 2
    assert len(data) == 6


def test_damage_mapping_leaves_undocumented_r_unmapped():
    labels = pd.Series(["None", "N", "Light", "L", "Moderate", "M", "Severe", "S", "C", "R"])
    mapped = labels.map(RC_DAMAGE)
    assert mapped.iloc[:9].tolist() == [0, 0, 1, 1, 2, 2, 3, 3, 4]
    assert pd.isna(mapped.iloc[9])


def test_tar_reads_only_requested_tables(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in ["../../untrusted.txt", *RC_MEMBERS, "huge_photos.bin"]:
            data = b"header\nvalue\n"
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    buffer.seek(0)
    with tarfile.open(fileobj=buffer, mode="r|gz") as archive:
        result = extract_rc_tables(archive, tmp_path)
    assert set(result) == set(RC_MEMBERS)
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(Path(p).name for p in RC_MEMBERS)


def test_tar_missing_tables_fails(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w"):
        pass
    buffer.seek(0)
    with tarfile.open(fileobj=buffer, mode="r|") as archive:
        with pytest.raises(ValueError, match="Incomplete"):
            extract_rc_tables(archive, tmp_path)


@pytest.mark.parametrize("name", ["../escape.txt", "/tmp/escape.txt", "dir\\escape.txt"])
def test_zip_traversal_rejected(tmp_path, name):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, "bad")
    buffer.seek(0)
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(ValueError, match="Unsafe"):
            safe_extract_zip(archive, tmp_path)
    assert not list(tmp_path.iterdir())


def test_json_never_emits_nonfinite_literals():
    data = serializable({"a": np.int64(2), "b": [np.inf, np.nan, pd.NA], "c": np.array([1, 2])})
    assert json.loads(json.dumps(data, allow_nan=False)) == {"a": 2, "b": [None, None, None], "c": [1, 2]}


@pytest.mark.skipif(not (RAW / "audit_metadata/nso_69.xml").exists(), reason="Local public metadata not acquired")
def test_official_metadata_is_not_reported_as_acquired_microdata():
    metadata = parse_nso_ddi(RAW / "audit_metadata/nso_69.xml")
    assert metadata["advertised_rows"] == 1052948
    assert len(metadata["variables"]) == metadata["advertised_variables"] == 105
    grade = next(v for v in metadata["variables"] if v["name"] == "dm_grade")
    assert sum(c["frequency"] for c in grade["categories"]) == 1052948


@pytest.mark.skipif(not (RAW / "rc616/454_866_Priority_I_data.csv").exists(), reason="Local RC616 data not acquired")
def test_rc_archive_regression_and_retention(tmp_path):
    report = ingest_rc616(tmp_path)
    assert report["rows"] == 619
    assert report["variables"] == 21
    assert sum(report["event_counts"].values()) == 619
    assert len(report["event_counts"]) == 6
    assert report["unmapped_damage_labels"] == {"R": 1}
    assert report["coordinates"]["missing_or_unparseable_pairs"] == 266
    frame = pd.read_parquet(tmp_path / "rc616.parquet")
    assert len(frame) == frame.building_id.nunique() == 619
    assert len([c for c in frame if c.startswith("raw__")]) == 21


@pytest.mark.skipif(not all((RAW / p).exists() for p in ["nepal_2015/Impact_Buildings_Detailed.csv", "audit_metadata/nso_69.xml"]), reason="Local GEID or official metadata not acquired")
def test_geid_district_reconciliation(tmp_path):
    report = audit_nepal(tmp_path)
    assert report["geid"]["rows"] == 762106
    assert report["geid"]["distinct_building_id_strings"] == 74
    assert all(c["exact_aggregate_match"] for c in report["district_reconciliation"])
    assert len(report["district_reconciliation"]) == 11
    assert report["official_hrhrs"]["locally_acquired_building_microdata"] is False


@pytest.mark.skipif(not (OUTPUT / "summary.json").exists(), reason="Local full spatial audit not run")
def test_completed_audit_reconciles_counts():
    report = json.loads((OUTPUT / "summary.json").read_text())
    assert report["aci133"]["rows"] == 242
    assert report["aci133"]["variables"] == 106
    assert report["aci133"]["overlap_threshold_metres"]["25"]["aci133_records"] == 12
    footprints = next(v for v in report["spatial"]["vectors"] if v["path"].endswith("Turkey_GBA_building_data.shp"))
    assert footprints["features"] == 4410028
    unosat = next(v for v in report["spatial"]["vectors"] if v["path"].endswith(".gmt"))
    assert unosat["features"] == 500
    assert len(report["spatial"]["rasters"]) == 5
    for raster in report["spatial"]["rasters"]:
        assert raster["valid_pixels"] + raster["masked_or_nonfinite_pixels"] == raster["rows"] * raster["columns"]
