"""Freeze paired city folds, chronology-qualified features and explicit exclusions.

No fitted transforms, embeddings or vulnerability models are estimated here.
"""
import json
import numpy as np
import pandas as pd

from .acquire_expansion import ROOT, digest
from .audit_expansion import haversine_distances, write_json
from .geoai_feasibility import RAW, OUT

CONFIG = ROOT / "configs/geoai_experiment_1f.json"


def structure_family(value):
    if pd.isna(value):
        return None
    for prefix, family in [("RC MRF (", "RC_MRF"), ("RC Wall (", "RC_WALL"),
                           ("RC Dual system (", "RC_DUAL")]:
        if value.startswith(prefix):
            return family
    return {"Unreinforced masonry": "UNREINFORCED_MASONRY",
            "Reinforced masonry": "REINFORCED_MASONRY",
            "Column with slab corrugated Asgolan": "OTHER",
            "1st storey stone, 2nd storey aerated concrete": "OTHER"}.get(value)


def eligible_manifest(survey, audit, hazard, config):
    frame = survey.merge(audit, on=["building_id", "city"], validate="one_to_one")
    frame = frame.merge(hazard, on="building_id", validate="one_to_one")
    if len(frame) != len(survey):
        raise ValueError("Audit/hazard joins must retain every survey record")
    frame["structure_family"] = frame.structure_type.map(structure_family)
    centers = frame.groupby("city")[["latitude", "longitude"]].transform("median")
    frame["city_median_distance_m"] = np.diag(haversine_distances(frame[["latitude", "longitude"]], centers))
    conflict = frame.groupby(["latitude", "longitude"]).damage_grade.transform("nunique") > 1
    flags = {
        "missing_native_damage": frame.damage_grade.isna(),
        "missing_or_unmapped_structure_family": frame.structure_family.isna(),
        "conflicting_labels_at_exact_coordinate": conflict,
        "coordinate_city_outlier_pending_adjudication": frame.city_median_distance_m > config["coordinate_city_median_limit_m"],
        "incomplete_pre_event_EO": frame.eo_status.ne("complete_clear_composite"),
        "incomplete_WorldCover": frame.worldcover_coverage.ne(1),
        "incomplete_DSM": frame.dem_coverage.ne(1),
        "invalid_primary_H": ~frame.in_grid | ~np.isfinite(frame.PGA_g) | frame.PGA_g.le(0),
    }
    for key, flag in flags.items():
        frame[key] = flag
    frame["exclusion_reasons"] = ["|".join(k for k in flags if bool(frame.loc[i, k])) for i in frame.index]
    frame["eligible"] = frame.exclusion_reasons.eq("")
    frame["log_PGA_g"] = np.log(frame.PGA_g.where(frame.PGA_g.gt(0)))
    weights = frame.loc[frame.eligible].location_key.value_counts()
    frame["site_weight"] = frame.location_key.map(1 / weights).fillna(0).where(frame.eligible, 0)
    return frame


def partitions(frame, config):
    distances = haversine_distances(frame[["latitude", "longitude"]], frame[["latitude", "longitude"]])
    domains = config["city_domains"]
    all_folds = []
    for index, test in enumerate(domains):
        val = config["validation_overrides"].get(test, domains[(index + 1) % len(domains)])
        role = pd.Series(np.where(frame.city.eq(test), "test", np.where(frame.city.eq(val), "validation", "train")), index=frame.index)
        active = frame.eligible.to_numpy()
        cross = (role.to_numpy()[:, None] != role.to_numpy()[None, :]) & active[:, None] & active[None, :]
        # Quarantine both sides; never move a held-out label into training.
        purge = ((distances < config["cross_partition_buffer_m"]) & cross).any(axis=1)
        reasons = frame.exclusion_reasons.copy()
        reasons.loc[purge] = "cross_partition_2km_context_buffer"
        role.loc[~active | purge] = "excluded"
        result = frame[["building_id", "city", "location_key", "damage_grade", "site_weight"]].copy()
        result["test_city"], result["validation_city"] = test, val
        result["partition"], result["exclusion_reasons"] = role, reasons
        result.loc[role.eq("excluded"), "site_weight"] = 0
        all_folds.append(result)
    return pd.concat(all_folds, ignore_index=True)


def engineered_features(report):
    folder = RAW / "locations" / report["location_key"]
    r = np.load(folder / "reflectance.npz")["reflectance"]
    wc = np.load(folder / "worldcover_2021.npz")["values"]
    dsm = np.load(folder / "copernicus_dem_2021.npz")["values"]
    if not np.isfinite(r).all() or not np.isfinite(dsm).all() or (wc == 0).any():
        raise ValueError("Incomplete context cannot enter engineered features")
    red = r[2]
    # Direct moments avoid undefined normalized differences in dark pixels.
    # This choice is frozen from input QA, before any predictive fitting.
    features = {f"{name}_{stat}": getattr(r[index], stat)() for name, index in [("green", 1), ("red", 2), ("nir", 6), ("swir1", 8)] for stat in ["mean", "std"]}
    features.update({"red_texture": (np.abs(np.diff(red, axis=0)).mean() + np.abs(np.diff(red, axis=1)).mean()) / 2,
                "dsm_mean": dsm.mean(), "dsm_relief": np.percentile(dsm, 95) - np.percentile(dsm, 5)})
    gy, gx = np.gradient(dsm, 10)
    features["dsm_slope_mean"] = np.degrees(np.arctan(np.hypot(gx, gy))).mean()
    yy, xx = np.indices(wc.shape)
    radius = np.hypot((xx + .5 - 48) * 10, (yy + .5 - 48) * 10)
    for metres in [250, 480]:
        mask = radius <= metres
        features[f"built_fraction_{metres}m"] = (wc[mask] == 50).mean()
        features[f"vegetation_fraction_{metres}m"] = np.isin(wc[mask], [10, 20, 30, 40, 90, 95, 100]).mean()
    return {k: float(v) for k, v in features.items()}


def main():
    config = json.loads(CONFIG.read_text())
    survey_path = ROOT / "data/processed/turkiye_2023/buildings.parquet"
    survey = pd.read_parquet(survey_path)
    audit = pd.read_csv(OUT / "location_audit.csv")
    hazard = pd.read_parquet(OUT / "hazard.parquet")
    frame = eligible_manifest(survey, audit, hazard, config)
    pixel = json.loads((OUT / "pixel_audit.json").read_text())
    features = {}
    for report in pixel["locations"]:
        if report["status"] == "complete_clear_composite" and all(report[k]["coverage_fraction"] == 1 for k in ["worldcover_2021", "copernicus_dem_2021"]):
            features[report["location_key"]] = engineered_features(report)
    engineered = pd.DataFrame.from_dict(features, orient="index").rename_axis("location_key").reset_index()
    paired = frame.merge(engineered, on="location_key", how="left", validate="many_to_one")
    if not np.isfinite(paired.loc[paired.eligible, config["allowlists"]["Z_engineered"]].to_numpy(float)).all():
        raise ValueError("Eligible records must have every finite engineered feature")
    allowed = ["building_id", "city", "location_key", "latitude", "longitude", "damage_grade", "structure_family", "log_PGA_g", "eligible", "exclusion_reasons", "site_weight", "city_median_distance_m"]
    paired[allowed + config["allowlists"]["Z_engineered"]].to_parquet(OUT / "feature_manifest.parquet", index=False)
    frame[[c for c in allowed if c in frame]].to_csv(OUT / "eligibility.csv", index=False)
    folds = partitions(frame, config)
    folds.to_csv(OUT / "city_folds.csv", index=False)
    support = folds.groupby(["test_city", "validation_city", "partition"], dropna=False).agg(records=("building_id", "size"), sites=("location_key", "nunique"), weight=("site_weight", "sum")).reset_index()
    support.to_csv(OUT / "fold_support.csv", index=False)
    class_support = folds.groupby(["test_city", "partition", "damage_grade"], dropna=False).size().rename("records").reset_index()
    class_support.to_csv(OUT / "fold_class_support.csv", index=False)
    counts = frame.loc[~frame.eligible].exclusion_reasons.str.split("|").explode().value_counts().to_dict()
    write_json(OUT / "freeze_summary.json", {"config_sha256": digest(CONFIG), "survey_sha256": digest(survey_path),
               "observations": len(frame), "eligible_records": int(frame.eligible.sum()), "eligible_sites": frame.loc[frame.eligible, "location_key"].nunique(),
               "overlapping_exclusion_counts": counts, "all_arms_same_manifest": True, "model_fitting": False,
               "test_city_counts": folds.loc[folds.partition.eq("test")].groupby("test_city").size().reindex(config["city_domains"], fill_value=0).to_dict(),
               "pixel_audit_sha256": digest(OUT / "pixel_audit.json"), "hazard_provenance_sha256": digest(OUT / "hazard_provenance.json")})
    print((OUT / "freeze_summary.json").read_text())


if __name__ == "__main__":
    main()
