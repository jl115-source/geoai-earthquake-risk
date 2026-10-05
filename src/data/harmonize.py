"""Offline Milestone 1D adapters. Source-native labels remain authoritative."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .acquire_expansion import ROOT, RAW, digest
from .audit_expansion import ACI_DAMAGE, RC_DAMAGE, counts, write_json

OUTPUT = ROOT / "data/processed/harmonized"
VERSION = "1d-v1"
STRING_FIELDS = """schema_version dataset_id record_id event_id event_scope country
source_path source_sha256 source_row_unit source_id_native identity_status
damage_native damage_scale damage_mapping_status label_provenance
coordinate_status coordinate_method city admin1 admin2 admin3 floors_native
floors_time_status structure_native structure_family im_status im_source im_transform im_event_id license""".split()
FLOAT_FIELDS = "latitude longitude floors PGA PGV SA_0p3 SA_1p0".split()
SCHEMA = {**dict.fromkeys(STRING_FIELDS, "string"), **dict.fromkeys(FLOAT_FIELDS, "Float64"),
          "source_row": "Int64", "damage_ordinal_native": "Int8",
          "high_damage_candidate": "Int8", "author_supplemented": "boolean"}
TURKEY_EVENT = "turkiye_syria_2023_sequence"
INPUTS = {
    "turkiye_survey": "data/processed/turkiye_2023/buildings.parquet",
    "rc619": "data/processed/expansion_audit/rc616.parquet",
    "aci133": "data/processed/expansion_audit/aci133.parquet",
    "nepal_geid": "data/raw/nepal_2015/Impact_Buildings_Detailed.csv",
}
LICENSES = {"turkiye_survey": "CC-BY-4.0", "rc619": "CC-BY-SA-3.0",
            "aci133": "CC-BY-4.0", "nepal_geid": "CC-BY-NC-SA-4.0; upstream NSO restrictions",
            "spatial_this_study": "CC-BY-4.0 deposit; preserve upstream attribution"}


def valid_coordinates(frame):
    lat, lon = frame.latitude, frame.longitude
    return (lat.between(-90, 90) & lon.between(-180, 180) &
            ~((lat == 0) & (lon == 0))).fillna(False)


def empty_frame(n, dataset, source, source_hash, start=1, row_unit="data row, 1-based"):
    frame = pd.DataFrame({c: pd.Series(pd.NA, index=range(n), dtype=t) for c, t in SCHEMA.items()})
    frame["schema_version"] = VERSION
    frame["dataset_id"] = dataset
    frame["record_id"] = [f"{dataset}_r{i:07d}" for i in range(start, start + n)]
    frame["source_row"] = pd.Series(range(start, start + n), dtype="Int64")
    frame["source_path"] = source
    frame["source_sha256"] = source_hash
    frame["source_row_unit"] = row_unit
    frame["identity_status"] = "source_record_not_verified_physical_building"
    frame["damage_scale"] = dataset + "_native"
    frame["damage_mapping_status"] = "native_only"
    frame["floors_time_status"] = "reported_time_basis_unverified"
    frame["im_status"] = "not_present"
    frame["coordinate_method"] = "source_point"
    frame["license"] = LICENSES[dataset]
    return frame


def finish(frame):
    frame = frame.astype(SCHEMA)
    present = frame.latitude.notna() & frame.longitude.notna()
    frame["coordinate_status"] = pd.Series(np.where(valid_coordinates(frame), "valid_range_only",
                                                        np.where(present, "invalid", "missing")), dtype="string")
    validate(frame)
    return frame


def validate(frame):
    if set(frame.columns) != set(SCHEMA):
        raise ValueError("Canonical schema columns differ")
    for column, dtype in SCHEMA.items():
        if str(frame[column].dtype) != dtype:
            raise ValueError(f"Wrong dtype: {column}")
    required = ["record_id", "dataset_id", "source_path", "source_sha256", "source_row", "event_id", "damage_scale"]
    if frame[required].isna().any().any() or frame.record_id.duplicated().any():
        raise ValueError("Missing provenance/event or repeated record identity")
    if not frame.source_sha256.str.fullmatch("[a-f0-9]{64}").all():
        raise ValueError("Invalid source hash")
    if frame.high_damage_candidate.notna().any() and not frame.loc[frame.high_damage_candidate.notna(), "damage_mapping_status"].eq("provisional_not_for_pooling").all():
        raise ValueError("Candidate damage representation must remain provisional")
    spatial = frame.dataset_id.eq("spatial_this_study")
    if frame.loc[spatial, ["damage_ordinal_native", "high_damage_candidate"]].notna().any().any():
        raise ValueError("Spatial codes have no verified ordinal semantics")
    nepal = frame.dataset_id.eq("nepal_geid")
    if frame.loc[nepal, "high_damage_candidate"].notna().any():
        raise ValueError("Nepal has no approved cross-scale mapping")
    for dataset, group in frame.groupby("dataset_id"):
        values = group.damage_ordinal_native.dropna()
        allowed = range(1, 6) if dataset == "nepal_geid" else range(5)
        if not values.isin(allowed).all():
            raise ValueError("Native damage ordinal outside dataset scale")


def native_damage(frame, labels, mapping, candidate=False):
    frame["damage_native"] = labels.astype("string").replace("", pd.NA)
    frame["damage_ordinal_native"] = frame.damage_native.map(mapping).astype("Int8")
    if candidate:
        frame["high_damage_candidate"] = (frame.damage_ordinal_native >= 3).astype("Int8")
        frame["damage_mapping_status"] = "provisional_not_for_pooling"


def adapt_engineering(dataset):
    path = ROOT / INPUTS[dataset]
    raw = pd.read_parquet(path)
    f = empty_frame(len(raw), dataset, INPUTS[dataset], digest(path))
    f["source_id_native"] = raw.building_id
    f["latitude"], f["longitude"] = raw.latitude, raw.longitude
    f["label_provenance"] = "field_engineering_survey"
    if dataset == "rc619":
        f["event_id"] = raw.event_id
        f["event_scope"] = "single_event"
        f["country"] = raw.event_id.map({"bingol_2003": "TUR", "duzce_1999": "TUR", "erzincan_1992": "TUR",
                                           "pisco_2007": "PER", "haiti_2010": "HTI", "wenchuan_2008": "CHN"})
        f["floors"] = raw.floors
        f["floors_native"] = raw["raw__No. \nFloors"]
        f["structure_family"] = "RC_or_concrete_masonry_cohort_not_record_taxonomy"
        native_damage(f, raw.structural_damage_label, RC_DAMAGE, candidate=True)
    else:
        f["event_id"], f["event_scope"], f["country"] = TURKEY_EVENT, "sequence_damage_not_single_shock", "TUR"
        if dataset == "turkiye_survey":
            f["city"] = raw.city
            f["floors"], f["floors_native"] = raw.floors, raw.floors.astype("string")
            f["structure_native"] = raw.structure_type
            f["structure_family"] = raw.structure_type.map(lambda x: "RC" if pd.notna(x) and x.startswith("RC ") else pd.NA)
            f["damage_native"], f["damage_ordinal_native"] = raw.damage_label, raw.damage_grade
            f["high_damage_candidate"] = (raw.damage_grade >= 3).astype("Int8")
            f["damage_mapping_status"] = "provisional_not_for_pooling"
            for column in ["PGA", "PGV", "SA_0p3", "SA_1p0"]:
                f[column] = raw[column]
            f["im_status"] = "published_exp_log_medians_sequence_attribution_caveat"
            f["im_source"] = "registered_survey_workbook_log_mean_columns"
            f["im_transform"] = "exp(natural_log_mean); PGA_SA_g; PGV_cm_s"
        else:
            f["floors_native"] = raw.c003
            f["floors"] = pd.to_numeric(raw.c003, errors="raise")
            f["structure_family"] = "RC_cohort_not_record_taxonomy"
            f["author_supplemented"] = raw.has_author_supplemented_cells
            f["label_provenance"] = "engineering_survey_with_author_supplementation"
            native_damage(f, raw.damage_label_5class, ACI_DAMAGE, candidate=True)
            f["im_status"] = "source_columns_preserved_event_headers_unresolved"
            f["im_source"] = "ACI133_physical_columns_c050_to_c106; consult_native_IM_catalog"
    return finish(f)


def adapt_nepal():
    path = ROOT / INPUTS["nepal_geid"]
    raw = pd.read_csv(path, dtype="string", keep_default_na=False)
    f = empty_frame(len(raw), "nepal_geid", INPUTS["nepal_geid"], digest(path))
    f["source_id_native"] = raw.BUILDING_ID
    f["identity_status"] = "rounded_native_ID_use_source_row_only"
    f["event_id"], f["event_scope"], f["country"] = "gorkha_2015_sequence", "survey_after_mainshock_and_aftershocks", "NPL"
    f["admin1"], f["admin2"], f["admin3"] = raw.DISTRICT_ID, raw.VDCMUN_ID, raw.WARD_ID
    f["label_provenance"] = "GEID_transformed_HRHRS_derived_survey"
    native_damage(f, raw.DAMAGE_GRADE, {f"Grade {i}": i for i in range(1, 6)})
    f["floors_native"] = raw.BUILDING_FLOORS
    # GEID uses H:1 ... H:9. Reject drift rather than stripping arbitrary text.
    if not raw.BUILDING_FLOORS.str.fullmatch(r"H:[1-9][0-9]*").all():
        raise ValueError("Unknown GEID floor encoding")
    f["floors"] = pd.to_numeric(raw.BUILDING_FLOORS.str.removeprefix("H:"), errors="raise")
    f["structure_native"] = "see_source_11_multilabel_superstructure_flags"
    f["coordinate_method"] = "administrative_codes_only_no_centroid_imputation"
    return finish(f)


def adapt_spatial():
    import pyogrio
    base = RAW / "turkiye_2023_context/extracted/2023Turkey_earthquake_data/Building_damage_data/This_study"
    frames = []
    for path in sorted(base.glob("*.shp")):
        raw = pyogrio.read_dataframe(path)
        if raw.crs is None or raw.geometry.isna().any() or raw.geometry.is_empty.any() or not raw.geometry.is_valid.all():
            raise ValueError("Spatial geometry/CRS needs adjudication before deriving interior points")
        city = path.stem.removeprefix("Global_GBA_")
        # Bind geometry AND attribute/CRS sidecars, not only the .shp bytes.
        parts = {p.name: digest(p) for p in sorted(path.parent.glob(path.stem + ".*"))}
        source_hash = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()
        f = empty_frame(len(raw), "spatial_this_study", str(path.relative_to(ROOT)), source_hash,
                        row_unit="feature position, 1-based; SHA256 of sorted sidecar-hash JSON")
        f["record_id"] = f"spatial_this_study_{city}_r" + f.source_row.astype("string").str.zfill(7)
        f["source_id_native"] = f.source_row.astype("string")
        f["city"], f["country"] = city, "SYR" if city == "Jindires" else "TUR"
        f["event_id"], f["event_scope"] = TURKEY_EVENT, "sequence_damage_not_single_shock"
        f["damage_native"] = raw.damage_lev.astype("string")
        f["damage_mapping_status"] = "codebook_and_label_generation_unresolved"
        f["label_provenance"] = "This_study_product_not_verified_independent_field_truth"
        points = raw.to_crs(32637).geometry.representative_point().to_crs(4326)
        f["latitude"], f["longitude"] = points.y, points.x
        f["coordinate_method"] = "polygon_interior_point_UTM37N_to_WGS84"
        f["im_status"] = "encoded_PGV_raster_not_physical_intensity"
        frames.append(finish(f))
    if not frames:
        raise FileNotFoundError(f"No This_study shapefiles: {base}")
    result = pd.concat(frames, ignore_index=True)
    validate(result)
    return result


def summarize(frame):
    native_present = frame.damage_native.notna()
    mapped = frame.damage_ordinal_native.notna()
    return {"records": len(frame), "events": counts(frame.event_id), "cities": counts(frame.city),
            "native_labels": counts(frame.damage_native), "native_ordinal": counts(frame.damage_ordinal_native),
            "unmapped_present_labels": counts(frame.loc[native_present & ~mapped, "damage_native"]),
            "coordinate_status": counts(frame.coordinate_status),
            "floors_present": int(frame.floors.notna().sum()),
            "floors_nonpositive": int((frame.floors.notna() & (frame.floors <= 0)).sum()),
            "floors_fractional_reported": int((frame.floors.notna() & (frame.floors % 1 != 0)).sum()),
            "physical_IM_counts": {c: int(frame[c].notna().sum()) for c in ["PGA", "PGV", "SA_0p3", "SA_1p0"]},
            "source_hashes": sorted(frame.source_sha256.unique().tolist()),
            "source_row_retention": "all adapter input rows retained; no imputation or pooling"}


def im_catalog():
    """Inventory native intensity columns without choosing an ambiguous event block."""
    path = ROOT / INPUTS["aci133"]
    if not path.exists():
        return {"aci133": "not locally available"}
    raw = pd.read_parquet(path)
    dictionary = pd.read_csv(ROOT / "docs/data_expansion/aci133_variables.csv", keep_default_na=False)
    fields = []
    for row in dictionary.itertuples(index=False):
        if int(row.column[1:]) < 50:
            continue
        values = raw[row.column].astype("string")
        numeric = pd.to_numeric(values, errors="coerce")
        fields.append({"column": row.column, "native_header": row.source_header,
                       "source_block": row.group, "declared_units": row.source_units,
                       "finite_numeric_records": int(np.isfinite(numeric.fillna(np.nan).to_numpy(float)).sum()),
                       "literal_NaN_records": int(values.eq("NaN").sum()),
                       "blank_records": int((values.isna() | values.eq("")).sum()),
                       "event_assignment": "unresolved_not_selected_for_canonical_IM"})
    return {"aci133": fields, "aci133_source_sha256": digest(path),
            "turkiye_survey": {"transform": "exp(source natural-log means)", "PGA_SA_units": "g", "PGV_units": "cm/s",
                                "statistic": "geometric mean/median, not arithmetic mean", "event_assignment": "sequence target; exact shock/product identity not verified in canonical contract"},
            "nepal_geid": "No IMs and no point coordinates; no administrative centroid assignment",
            "rc619": "No native IMs; 353 coordinate candidates; actual grid coverage/nodata/product checks still required",
            "spatial_this_study": "Encoded PGV raster lacks a verified conversion to physical units; native labels may depend on this product"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", choices=[*INPUTS, "spatial_this_study"], default=[*INPUTS, "spatial_this_study"])
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"schema_version": VERSION, "datasets": {}, "pooling_enabled": False}
    for dataset in args.datasets:
        frame = adapt_nepal() if dataset == "nepal_geid" else adapt_spatial() if dataset == "spatial_this_study" else adapt_engineering(dataset)
        path = args.output_dir / f"{dataset}.parquet"
        frame.to_parquet(path, index=False)
        summary["datasets"][dataset] = {**summarize(frame), "parquet_sha256": digest(path)}
        summary["datasets"][dataset]["point_sampling_coordinate_candidates"] = int(valid_coordinates(frame).sum())
        print(f"{dataset}: {len(frame):,} source records retained", flush=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "schema.json", {"version": VERSION, "fields": SCHEMA})
    write_json(args.output_dir / "native_IM_catalog.json", im_catalog())


if __name__ == "__main__":
    main()
