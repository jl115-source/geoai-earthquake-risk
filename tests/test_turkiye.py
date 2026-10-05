"""Unit and offline data-regression tests for the registered workbook."""

import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from src.data.turkiye import (
    DEFAULT_INPUT, canonicalize, ingest, quality_report, read_workbook, validate_schema,
)
from src.data.turkiye_schema import COLUMNS, SCHEMA
from src.data.turkiye_eda import damage_rates, geographic_coverage, run_eda


def fixture_rows(labels):
    records = []
    for label in labels:
        record = {c.source: None for c in COLUMNS}
        record.update({"damage_condition": label, "latitude": 37., "longitude": 36.,
                       "structure_type": " RC MRF (1-3 Storeys) ",
                       "PGA_mean": -1., "PGV_mean": 4., "SA(0.3)_mean": 0., "SA(1.0)_mean": -.5,
                       "storeys_above_ground_incl_ground_floor": 3.})
        records.append(record)
    return pd.DataFrame(records, dtype=object)


@pytest.mark.parametrize("label,expected", [
    ("None", 0), ("Minor (few cracks)", 1), ("Moderate (extensive cracks in walls)", 2),
    ("moderate damage but repaired", 2), ("Severe (structural damage to system)", 3),
    ("Partial collapse (portion collapsed)", 3), ("Complete collapse", 4),
])
def test_explicit_damage_mapping(label, expected):
    table, issues = canonicalize(fixture_rows([label]), [2])
    assert table.damage_grade.iloc[0] == expected
    assert not issues


def test_missing_unknown_and_literal_none_are_distinct():
    raw = fixture_rows(["None", None, "", "  ", " None ", "unrecognised", "NA"])
    table, issues = canonicalize(raw, range(2, 9))
    assert table.damage_grade.fillna(-1).tolist() == [0, -1, -1, -1, 0, -1, -1]
    assert len(issues) == 2
    assert {i["raw_value"] for i in issues} == {"unrecognised", "NA"}
    assert table.loc[4, "raw__damage_condition"] == " None "
    assert len(table) == 7


def test_physical_scale_and_raw_engineering_fields():
    raw = fixture_rows(["None"])
    raw.loc[0, "Unnamed: 54"] = "15-30%"
    raw.loc[0, "pounding"] = "yes"
    raw.loc[0, "SA(3.0)_mean"] = -2.
    table, _ = canonicalize(raw, [15])
    assert table.PGA.iloc[0] == pytest.approx(np.exp(-1))
    assert table.PGV.iloc[0] == pytest.approx(np.exp(4))
    assert table.SA_0p3.iloc[0] == 1.
    assert table.SA_3p0.iloc[0] == pytest.approx(np.exp(-2))
    assert table.loc[0, "raw__PGA_mean"] == "-1.0"
    assert table.pounding.iloc[0] == "yes"
    assert table.unlabelled_damage_band.iloc[0] == "15-30%"
    assert table.building_id.iloc[0] == "turkiye_2023_r0015"
    assert len([c for c in table if c.startswith("raw__")]) == 55


def test_invalid_values_flagged_and_retained():
    raw = fixture_rows(["None"] * 5)
    raw.loc[0, "latitude"] = 91
    raw.loc[1, "longitude"] = -181
    raw.loc[2, ["latitude", "longitude"]] = [0, 0]
    raw.loc[0, "storeys_above_ground_incl_ground_floor"] = 0
    raw.loc[1, "storeys_above_ground_incl_ground_floor"] = 2.5
    raw.loc[2, "storeys_below_ground"] = -1
    raw.loc[0, "area"] = -30
    raw.loc[1, "vs30"] = -1
    raw.loc[2, "MMI_mean"] = 13
    raw.loc[3, "PGA_mean"] = 1000  # overflow retained as infinity and flagged
    raw.loc[4, "PGV_mean"] = "not numeric"
    raw.loc[4, "date"] = "not a date"
    table, issues = canonicalize(raw, range(2, 7))
    report = quality_report(table, issues)
    assert len(table) == 5
    assert len(report["invalid_coordinates"]) == 3
    assert len(report["impossible_values"]) == 7
    assert len(report["parse_and_mapping_issues"]) == 2
    assert table.area.iloc[0] == -30
    assert table.floors.iloc[1] == 2.5
    assert np.isinf(table.PGA.iloc[3])
    assert table.loc[4, "raw__PGV_mean"] == "not numeric"
    json.dumps(report, allow_nan=False)


def test_duplicate_coordinates_not_deduplicated_or_merged():
    table, issues = canonicalize(fixture_rows(["None", "Complete collapse", "None"]), [2, 3, 4])
    report = quality_report(table, issues)
    assert len(table) == 3
    assert report["duplicate_coordinate_row_count"] == 3
    assert report["exact_duplicate_excess_count"] == 1
    assert len(report["duplicate_coordinate_groups"]) == 1
    assert table.building_id.nunique() == 3


@pytest.mark.parametrize("mutation", ["drop", "dtype", "ids", "damage", "source", "flag", "raw"])
def test_schema_rejects_corruption(mutation):
    table, _ = canonicalize(fixture_rows(["None", "None"]), [2, 3])
    if mutation == "drop":
        table = table.drop(columns="latitude")
    elif mutation == "dtype":
        table["floors"] = table.floors.astype("string")
    elif mutation == "ids":
        table.loc[1, "building_id"] = table.loc[0, "building_id"]
    elif mutation == "damage":
        table.loc[0, "damage_grade"] = 4
    elif mutation == "source":
        table.loc[0, "source_row"] = 999
    elif mutation == "flag":
        table.loc[0, "has_damage_and_structure"] = False
    else:
        table = table.drop(columns="raw__pounding")
    with pytest.raises(ValueError):
        validate_schema(table)


def test_rate_denominator_and_undefined_rate():
    raw = fixture_rows(["None", "Complete collapse", None, None])
    raw.loc[3, "structure_type"] = "Unreinforced masonry"
    table, _ = canonicalize(raw, [2, 3, 4, 5])
    rates = damage_rates(table).set_index("structure_type")
    assert rates.loc["RC MRF (1-3 Storeys)", "damage_rate"] == .5
    assert rates.loc["RC MRF (1-3 Storeys)", "missing_damage"] == 1
    assert pd.isna(rates.loc["Unreinforced masonry", "damage_rate"])
    assert geographic_coverage(table).records.sum() == 4


@pytest.fixture(scope="module")
def real_data():
    raw, rows, empty = read_workbook(DEFAULT_INPUT)
    table, issues = canonicalize(raw, rows)
    return raw, table, quality_report(table, issues), empty


def test_registered_workbook_regression(real_data):
    raw, table, report, empty = real_data
    assert raw.shape == (559, 55)
    assert len(table) == 559
    assert table.has_damage_and_structure.sum() == 527
    assert table.damage_grade.value_counts().to_dict() == {2: 169, 1: 147, 0: 111, 3: 111, 4: 3}
    assert table.damage_grade.isna().sum() == 18
    assert table.structure_type.isna().sum() == 22
    assert table.floors.isna().sum() == 8
    assert table.unlabelled_damage_band.notna().sum() == 6
    assert report["unique_coordinate_pairs"] == 499
    assert report["duplicate_coordinate_row_count"] == 105
    assert len(report["duplicate_coordinate_groups"]) == 45
    assert report["exact_duplicate_excess_count"] == 11
    assert report["error_count"] == 0
    assert empty == list(range(561, 612))
    assert set(SCHEMA).issubset(table.columns)
    # Workbook cells and canonical values independently reconcile for every row.
    assert raw["damage_condition"].eq("None").sum() == 111
    for source, target in [("PGA_mean", "PGA"), ("PGV_mean", "PGV"), ("SA(0.3)_mean", "SA_0p3"), ("SA(1.0)_mean", "SA_1p0")]:
        np.testing.assert_allclose(table[target].astype(float), np.exp(raw[source].astype(float)))


def test_deterministic_parquet_and_reports(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    expected, _ = ingest(DEFAULT_INPUT, first)
    ingest(DEFAULT_INPUT, second)
    pd.testing.assert_frame_equal(expected, pd.read_parquet(first / "buildings.parquet"))
    for name in ("buildings.parquet", "manifest.json", "quality_report.json", "source_dictionary.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_workbook_schema_drift_rejected(tmp_path):
    import openpyxl

    workbook = openpyxl.load_workbook(DEFAULT_INPUT)
    workbook.active["A1"] = "unknown_new_header"
    path = tmp_path / "changed.xlsx"
    workbook.save(path)
    workbook.close()
    with pytest.raises(ValueError, match="Source columns changed"):
        read_workbook(path)


def test_cli_retains_unknown_labels_but_fails_validation(tmp_path):
    import openpyxl

    workbook = openpyxl.load_workbook(DEFAULT_INPUT)
    workbook.active["AW2"] = "Unexpected new label"
    path = tmp_path / "unknown.xlsx"
    workbook.save(path)
    workbook.close()
    output = tmp_path / "processed"
    result = subprocess.run([sys.executable, "-m", "src.data.turkiye", "--input", str(path),
                             "--output-dir", str(output)], capture_output=True, text=True)
    assert result.returncode != 0
    table = pd.read_parquet(output / "buildings.parquet")
    assert len(table) == 559
    assert pd.isna(table.damage_grade.iloc[0])
    assert table.loc[0, "raw__damage_condition"] == "Unexpected new label"
    report = json.loads((output / "quality_report.json").read_text())
    assert report["parse_and_mapping_issues"][0]["kind"] == "unmapped_damage_label"


def test_nonfinite_duplicate_coordinates_have_serializable_report():
    raw = fixture_rows(["None", "None"])
    raw.loc[:, "latitude"] = float("inf")
    table, issues = canonicalize(raw, [2, 3])
    report = quality_report(table, issues)
    assert len(report["invalid_coordinates"]) == 2
    json.dumps(report, allow_nan=False)


def test_eda_outputs_and_accounting(tmp_path):
    ingest(DEFAULT_INPUT, tmp_path / "data")
    summary = run_eda(tmp_path / "data/buildings.parquet", tmp_path / "eda")
    assert summary["records"] == 559
    assert summary["excluded_coordinate_records"] == 0
    assert len(list((tmp_path / "eda").glob("*.png"))) == 8
    assert all(p.stat().st_size > 1000 for p in (tmp_path / "eda").glob("*.png"))
    rates = pd.read_csv(tmp_path / "eda/damage_rate_by_structure.csv")
    assert rates.known_damage.sum() == 541
    assert rates.total_records.sum() == 559
    for accounting in summary["shaking_plot_accounting"].values():
        assert accounting == {"used": 559, "missing": 0, "invalid": 0}
