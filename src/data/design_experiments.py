"""Freeze deterministic partitions and eligibility; never train a model."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .acquire_expansion import ROOT, digest
from .audit_expansion import haversine_distances, write_json
from .harmonize import OUTPUT as INPUT, validate, valid_coordinates

OUTPUT = ROOT / "data/processed/experiment_design"
CONFIG = ROOT / "configs/experiments_1d.json"


def proximity_groups(frame, radius_m=100):
    """Conservative connected components for small engineering tables, not deduplication."""
    if len(frame) > 5000:
        raise ValueError("Pairwise proximity grouping is only for small engineering tables")
    parents = list(range(len(frame)))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    valid = np.flatnonzero(valid_coordinates(frame).to_numpy(dtype=bool))
    distances = haversine_distances(frame.iloc[valid][["latitude", "longitude"]], frame.iloc[valid][["latitude", "longitude"]])
    for i, j in np.argwhere(np.triu(distances <= radius_m, 1)):
        a, b = root(int(valid[i])), root(int(valid[j]))
        parents[max(a, b)] = min(a, b)
    identifiers = {}
    for i in range(len(frame)):
        key = root(i)
        identifiers.setdefault(key, []).append(str(frame.iloc[i].record_id))
    names = {k: "site_" + hashlib.sha256("|".join(sorted(v)).encode()).hexdigest()[:20] for k, v in identifiers.items()}
    return pd.Series([names[root(i)] for i in range(len(frame))], index=frame.index, dtype="string")


def eligibility(frame, spatial=False):
    reasons = pd.Series("", index=frame.index, dtype="string")
    if spatial:
        reasons.loc[frame.damage_native.isna()] = "missing_native_label"
        reasons.loc[~valid_coordinates(frame)] = "missing_or_invalid_coordinate"
    else:
        reasons.loc[frame.damage_ordinal_native.isna()] = "missing_or_unmapped_native_damage"
    # Do not resolve a conflicting repeated survey location by majority voting.
    if frame.dataset_id.eq("turkiye_survey").all():
        known = frame.loc[valid_coordinates(frame)]
        conflicts = known.groupby(["latitude", "longitude"]).damage_native.transform("nunique") > 1
        reasons.loc[known.index[conflicts]] = "conflicting_labels_at_exact_coordinate"
    return reasons


def make_partition(frame, domain, test_domain, validation_domain, groups, coordinate_required=False, spatial=False):
    """All records receive a role or an explicit exclusion; no label balancing."""
    if test_domain == validation_domain:
        raise ValueError("Test and validation domains must differ")
    reasons = eligibility(frame, spatial=spatial)
    if coordinate_required:
        reasons.loc[~valid_coordinates(frame)] = "missing_or_invalid_coordinate"
    reasons.loc[frame[domain].isna()] = "missing_domain"
    roles = pd.Series("train", index=frame.index, dtype="string")
    roles.loc[frame[domain].eq(validation_domain)] = "validation"
    roles.loc[frame[domain].eq(test_domain)] = "test"
    # If a proximity component crosses city roles, quarantine every member.
    check = pd.DataFrame({"group": groups, "role": roles})
    cross = check.groupby("group").role.transform("nunique") > 1
    reasons.loc[cross] = "group_crosses_domain_partition"
    roles.loc[reasons.ne("")] = "excluded"
    # Equal total weight per exact-coordinate record group, without deleting data.
    duplicate_keys = frame.record_id.astype("string").copy()
    has_coords = valid_coordinates(frame)
    duplicate_keys.loc[has_coords] = (frame.loc[has_coords, "event_id"] + ":" +
                                     frame.loc[has_coords, "latitude"].astype("string") + ":" +
                                     frame.loc[has_coords, "longitude"].astype("string"))
    retained = roles.ne("excluded")
    sizes = duplicate_keys.loc[retained].map(duplicate_keys.loc[retained].value_counts())
    weights = pd.Series(0.0, index=frame.index)
    weights.loc[retained] = 1 / sizes
    result = pd.DataFrame({"record_id": frame.record_id, "partition": roles,
                           "exclusion_reason": reasons, "leakage_group": groups,
                           "evaluation_weight": weights})
    result["uncertainty_group"] = groups
    if frame.dataset_id.eq("nepal_geid").all():
        result["uncertainty_group"] = frame.admin1 + ":" + frame.admin2
    if spatial:
        from pyproj import Transformer
        x, y = Transformer.from_crs(4326, 32637, always_xy=True).transform(frame.longitude.to_numpy(float), frame.latitude.to_numpy(float))
        result["uncertainty_group"] = [f"utm37_5km_{int(a // 5000)}_{int(b // 5000)}" if np.isfinite(a) and np.isfinite(b) else "invalid_coordinate" for a, b in zip(x, y)]
    assert_disjoint(result)
    return result


def assert_disjoint(partition):
    if partition.record_id.duplicated().any():
        raise ValueError("Record appears more than once")
    kept = partition.loc[partition.partition.ne("excluded")]
    if (kept.groupby("leakage_group").partition.nunique() > 1).any():
        raise ValueError("Leakage group crosses partitions")
    if not partition.loc[partition.partition.eq("excluded"), "evaluation_weight"].eq(0).all():
        raise ValueError("Excluded records have nonzero weight")


def fold_summary(frame, partition):
    result = {}
    for role in ["train", "validation", "test", "excluded"]:
        mask = partition.partition.eq(role)
        labels = frame.loc[mask, "damage_native"].fillna("<missing>")
        result[role] = {"records": int(mask.sum()), "groups": int(partition.loc[mask, "leakage_group"].nunique()),
                        "native_class_counts": labels.value_counts().sort_index().to_dict(),
                        "evaluation_weight_sum": float(partition.loc[mask, "evaluation_weight"].sum())}
    result["exclusions"] = partition.loc[partition.partition.eq("excluded"), "exclusion_reason"].value_counts().sort_index().to_dict()
    result["empty_partition"] = any(result[r]["records"] == 0 for r in ["train", "validation", "test"])
    result["small_validation_warning"] = result["validation"]["records"] < 30
    result["small_test_warning"] = result["test"]["records"] < 30
    return result


def make_design(input_dir=INPUT, output_dir=OUTPUT, datasets=None):
    config = json.loads(CONFIG.read_text())
    output_dir.mkdir(parents=True, exist_ok=True)
    available = {}
    for dataset in (datasets or config["datasets"]):
        path = input_dir / f"{dataset}.parquet"
        frame = pd.read_parquet(path)
        validate(frame)
        available[dataset] = frame
    summary = {"version": config["version"], "config_sha256": digest(CONFIG), "model_fitting_performed": False,
               "inputs": {d: digest(input_dir / f"{d}.parquet") for d in available}, "experiments": {}}
    if "spatial_this_study" in available:
        # Bounding-box distance is a conservative lower bound on point separation.
        from pyproj import Transformer
        spatial = available["spatial_this_study"]
        x, y = Transformer.from_crs(4326, 32637, always_xy=True).transform(spatial.longitude.to_numpy(float), spatial.latitude.to_numpy(float))
        projected = pd.DataFrame({"x": x, "y": y, "city": spatial.city})
        bounds = {city: (g.x.min(), g.y.min(), g.x.max(), g.y.max()) for city, g in projected.groupby("city")}
        separations = {}
        cities = sorted(bounds)
        for i, city in enumerate(cities):
            a = bounds[city]
            for other in cities[i + 1:]:
                b = bounds[other]
                distance = float(np.hypot(max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0)))
                if distance < config["spatial_cross_partition_buffer_metres"]:
                    raise ValueError("Spatial city partitions cannot certify the required 1 km buffer")
                separations[f"{city}/{other}"] = distance
        summary["spatial_city_separation_lower_bound_metres"] = separations
    group_map = {}
    # ACI is held external. Shared proximity groups support later train/test purging.
    engineering = [available[d] for d in ["turkiye_survey", "aci133"] if d in available]
    if engineering:
        combined = pd.concat(engineering, ignore_index=True)
        combined["leakage_group"] = proximity_groups(combined, config["engineering_proximity_metres"])
        group_map = combined.set_index("record_id").leakage_group.to_dict()
        combined[["record_id", "dataset_id", "leakage_group"]].to_parquet(output_dir / "engineering_groups.parquet", index=False)
    for experiment in config["experiments"]:
        dataset = experiment["dataset"]
        if dataset not in available:
            continue
        frame = available[dataset]
        domain = experiment["domain"]
        actual = sorted(frame[domain].dropna().unique().tolist())
        domains = experiment["domains"]
        if set(actual) != set(domains):
            raise ValueError(f"Domain vocabulary changed for {dataset}: {actual}")
        groups = frame.record_id.map(group_map).astype("string") if dataset == "turkiye_survey" else frame[domain].astype("string")
        experiment_output = output_dir / experiment["id"]
        experiment_output.mkdir(exist_ok=True)
        folds = []
        for i, test in enumerate(domains):
            val = experiment.get("validation_overrides", {}).get(test, domains[(i + 1) % len(domains)])
            partition = make_partition(frame, domain, test, val, groups,
                                       coordinate_required=experiment.get("coordinates_required", False),
                                       spatial=dataset == "spatial_this_study")
            name = f"fold_{i:02d}.parquet"
            partition.to_parquet(experiment_output / name, index=False)
            folds.append({"fold": i, "test_domain": test, "validation_domain": val,
                          "training_domains": [d for d in domains if d not in [test, val]],
                          "file": f"{experiment['id']}/{name}", "sha256": digest(experiment_output / name),
                          **fold_summary(frame, partition)})
        summary["experiments"][experiment["id"]] = {"readiness": experiment["readiness"], "folds": folds}
    if "aci133" in available:
        aci = available["aci133"]
        # No train/validation allocation for this external-only source.
        pd.DataFrame({"record_id": aci.record_id, "partition": "reserved_external",
                      "leakage_group": aci.record_id.map(group_map),
                      "evaluation_enabled": False}).to_parquet(output_dir / "aci133_reserved.parquet", index=False)
        shared = set(available["turkiye_survey"].record_id.map(group_map)) if "turkiye_survey" in available else set()
        summary["aci133_reserved"] = {"records": len(aci), "proximity_connected_to_survey": int(aci.record_id.map(group_map).isin(shared).sum()),
                                     "evaluation_enabled": False,
                                     "reason": "Identity, damage crosswalk, header and supplementation adjudication pending"}
    write_json(output_dir / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--datasets", nargs="+")
    args = parser.parse_args()
    summary = make_design(args.input_dir, args.output_dir, args.datasets)
    print(f"Created {sum(len(e['folds']) for e in summary['experiments'].values())} design folds; no models fitted.")


if __name__ == "__main__":
    main()
