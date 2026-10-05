"""Research-contract and leakage tests; no estimator dependencies or fitting."""

import json

import pandas as pd
import pytest

pytest.importorskip("requests", reason="Install requirements-audit.txt for harmonization tests")

from src.data.harmonize import (
    INPUTS, OUTPUT, ROOT, SCHEMA, adapt_engineering, empty_frame, finish,
    native_damage, validate,
)
from src.data.design_experiments import assert_disjoint, make_partition, proximity_groups


def fixture_frame(dataset="turkiye_survey", n=4):
    f = empty_frame(n, dataset, "data/raw/fixture", "a" * 64)
    f["event_id"] = "event"
    f["damage_native"] = ["Minor"] * n
    f["damage_ordinal_native"] = 1
    f["city"] = ["A", "A", "B", "C"][:n]
    f["latitude"] = [37.0, 37.0, 38.0, 39.0][:n]
    f["longitude"] = [36.0, 36.0, 36.0, 36.0][:n]
    return finish(f)


def test_schema_artifact_matches_runtime():
    spec = json.loads((ROOT / "configs/building_record_1d.schema.json").read_text())
    assert set(spec["required"]) == set(spec["properties"]) == set(SCHEMA)
    assert {k: v["pandas_dtype"] for k, v in spec["properties"].items()} == SCHEMA


def test_nepal_scale_is_not_shifted_or_mapped_to_engineering():
    f = empty_frame(3, "nepal_geid", "source", "a" * 64)
    f["event_id"] = "gorkha"
    native_damage(f, pd.Series(["Grade 1", "Grade 5", ""]), {f"Grade {i}": i for i in range(1, 6)})
    f = finish(f)
    assert f.damage_ordinal_native.iloc[:2].tolist() == [1, 5]
    assert pd.isna(f.damage_ordinal_native.iloc[2])
    assert f.high_damage_candidate.isna().all()
    f.loc[0, "high_damage_candidate"] = 0
    f.loc[0, "damage_mapping_status"] = "provisional_not_for_pooling"
    with pytest.raises(ValueError, match="Nepal"):
        validate(f)


def test_unknown_rc_damage_preserved_and_not_mapped():
    f = empty_frame(3, "rc619", "source", "a" * 64)
    f["event_id"] = "event"
    native_damage(f, pd.Series(["N", "C", "R"]), {"N": 0, "C": 4}, candidate=True)
    f = finish(f)
    assert f.high_damage_candidate.iloc[:2].tolist() == [0, 1]
    assert f.damage_native.iloc[2] == "R"
    assert pd.isna(f.damage_ordinal_native.iloc[2])
    assert pd.isna(f.high_damage_candidate.iloc[2])


def test_spatial_codes_cannot_be_treated_as_ordinal():
    f = empty_frame(1, "spatial_this_study", "source", "a" * 64)
    f["event_id"] = "sequence"
    f["damage_native"] = "4"
    f = finish(f)
    assert pd.isna(f.damage_ordinal_native.iloc[0])
    f.loc[0, "damage_ordinal_native"] = 4
    with pytest.raises(ValueError, match="Spatial"):
        validate(f)


def test_proximity_components_are_transitive_and_order_independent():
    f = fixture_frame(n=3)
    f["longitude"] = pd.Series([36.0, 36.0009, 36.0018], dtype="Float64")
    f["latitude"] = 37.0
    groups = proximity_groups(f, 100)
    assert groups.nunique() == 1
    assert groups.iloc[0] == proximity_groups(f.iloc[::-1].reset_index(drop=True), 100).iloc[0]


def test_partitions_preserve_rows_and_weight_repeated_sites():
    f = fixture_frame()
    p = make_partition(f, "city", "C", "B", proximity_groups(f))
    assert len(p) == len(f)
    assert p.partition.tolist() == ["train", "train", "validation", "test"]
    assert p.evaluation_weight.tolist() == [.5, .5, 1., 1.]
    assert_disjoint(p)


def test_cross_city_proximity_is_quarantined():
    f = fixture_frame()
    f.loc[1, "city"] = "C"
    p = make_partition(f, "city", "C", "B", proximity_groups(f))
    assert p.partition.iloc[:2].eq("excluded").all()
    assert p.exclusion_reason.iloc[:2].eq("group_crosses_domain_partition").all()
    assert p.evaluation_weight.iloc[:2].eq(0).all()


def test_conflicting_exact_coordinate_damage_is_not_majority_voted():
    f = fixture_frame()
    f.loc[1, "damage_native"] = "Severe"
    p = make_partition(f, "city", "C", "B", proximity_groups(f))
    assert p.partition.iloc[:2].eq("excluded").all()
    assert p.exclusion_reason.iloc[:2].eq("conflicting_labels_at_exact_coordinate").all()


def test_missing_coordinates_only_excluded_from_coordinate_arm():
    f = fixture_frame("rc619")
    f.loc[0, ["latitude", "longitude"]] = pd.NA
    x = make_partition(f, "city", "C", "B", f.record_id)
    hx = make_partition(f, "city", "C", "B", f.record_id, coordinate_required=True)
    assert x.partition.iloc[0] == "train"
    assert hx.partition.iloc[0] == "excluded"
    assert hx.exclusion_reason.iloc[0] == "missing_or_invalid_coordinate"


def test_schema_rejects_duplicate_record_identity():
    f = fixture_frame()
    f.loc[1, "record_id"] = f.record_id.iloc[0]
    with pytest.raises(ValueError, match="identity"):
        validate(f)


@pytest.mark.skipif(not (ROOT / INPUTS["turkiye_survey"]).exists(), reason="Run Türkiye ingestion first")
def test_registered_survey_harmonization_retains_every_row():
    f = adapt_engineering("turkiye_survey")
    assert len(f) == 559
    assert f.damage_ordinal_native.notna().sum() == 541
    assert f.PGA.notna().sum() == 559
    assert f.im_event_id.isna().all()  # Do not invent a uniquely identified shock.


@pytest.mark.skipif(not (OUTPUT / "summary.json").exists(), reason="Local harmonization not run")
def test_local_harmonization_counts_and_no_pooled_target():
    report = json.loads((OUTPUT / "summary.json").read_text())
    if len(report["datasets"]) != 5:
        pytest.skip("Only a partial dataset selection was harmonized")
    assert sum(d["records"] for d in report["datasets"].values()) == 793648
    assert report["pooling_enabled"] is False
    assert report["datasets"]["spatial_this_study"]["native_ordinal"] == {"<missing>": 30122}
