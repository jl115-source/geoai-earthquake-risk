"""Bounded pre-event pixel/context audit for the independent Türkiye survey.

Network access is explicit. Cached chips/metadata are kept outside Git. No models.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from pyproj import Transformer
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
import requests
from shapely.geometry import Point, shape

from .acquire_expansion import ROOT, digest
from .audit_expansion import haversine_distances, write_json

RAW = ROOT / "data/raw/geoai_1f"
OUT = ROOT / "data/processed/geoai_1f"
API = "https://earth-search.aws.element84.com/v1/search"
BANDS = ["blue", "green", "red", "rededge1", "rededge2", "rededge3", "nir", "nir08", "swir16", "swir22"]
CUTOFF = "2023-02-06T01:17:35Z"
START, END = "2022-06-01T00:00:00Z", "2022-09-30T23:59:59Z"
MAX_SCENES = 12
PIXELS, RESOLUTION = 96, 10
SHAKEMAP_SHA = "a53fa6a50f5babf037e5afdd7c02e3e605d685607696332e1a8fe1814e61078e"
SHAKEMAP_URL = "https://raw.githubusercontent.com/maxandersonloake/TUR2023_02_06/be088671596f04ad5a058f7819ec3bb762156f17/Data/ShakeMapUpd.xml.gz"
WORLD_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36E036_Map.tif"
DEM_TEMPLATE = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM/Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM.tif"


def audit_spec():
    return {"version": "1f-pixel-v1", "catalog_sha256": digest(RAW / "sentinel_catalog.json"),
            "window": [START, END], "cutoff": CUTOFF, "bands": BANDS, "max_scenes": MAX_SCENES,
            "scene_cloud_limit": 20, "scl_clear": [2, 4, 5, 6], "bad_dilation_pixels": 1,
            "grid": "EPSG32637; centre snapped10m;96x96at10m", "reflectance": "STAC asset scale/offset once; bilinear",
            "categorical": "nearest; explicit destination nodata0", "continuous_nodata": "explicit destination NaN for warp",
            "composite": "median of first ranked prefix with full clear finite 10-band support",
            "ranking": "cloud ascending,time descending,id ascending", "worldcover": WORLD_URL, "dsm": DEM_TEMPLATE}


def spec_hash():
    return hashlib.sha256(json.dumps(audit_spec(), sort_keys=True).encode()).hexdigest()


def validate_cache(report, folder):
    if report.get("audit_spec_hash") != spec_hash():
        raise ValueError(f"Stale or unversioned pixel cache: {folder}. Re-audit explicitly; never relabel old chips.")
    artifacts = []
    if report["status"] == "complete_clear_composite":
        artifacts.append(("reflectance.npz", report["chip_sha256"]))
    for name in ["worldcover_2021", "copernicus_dem_2021"]:
        if "chip_sha256" in report[name]:
            artifacts.append((f"{name}.npz", report[name]["chip_sha256"]))
    for name, expected in artifacts:
        if digest(folder / name) != expected:
            raise ValueError(f"Cached chip checksum mismatch: {folder / name}")


def grid_for(lon, lat):
    x, y = Transformer.from_crs(4326, 32637, always_xy=True).transform(lon, lat)
    x, y = round(x / 10) * 10, round(y / 10) * 10
    return (x - 480, y - 480, x + 480, y + 480)


def location_key(lat, lon):
    # Preserve distinct source floats; display rounding is not an identity rule.
    return hashlib.sha256(f"{float(lat).hex()},{float(lon).hex()}".encode()).hexdigest()[:20]


def clear_mask(scl):
    # Dark topographic/terrain pixels (2) are valid observations; cloud shadows (3)
    # and unclassified pixels (7) are not. Expand rejected pixels by one 10 m cell.
    clear = np.isin(scl, [2, 4, 5, 6])
    bad = ~clear
    padded = np.pad(bad, 1, constant_values=False)
    expanded = np.zeros_like(bad)
    for i in range(3):
        for j in range(3):
            expanded |= padded[i:i + bad.shape[0], j:j + bad.shape[1]]
    return ~expanded


def composite(stack, masks):
    data = np.stack(stack)
    valid = np.stack(masks)
    support = valid.sum(axis=0)
    if not np.all(support > 0):
        return None, support
    # A valid measurement from a different PRE-event date is not nodata imputation.
    result = np.nanmedian(np.where(valid[:, None, :, :], data, np.nan), axis=0)
    return result.astype("float32"), support


def reflectance_from_asset(pixels, metadata):
    """STAC asset scale/offset are authoritative; apply exactly once."""
    return pixels.astype("float32") * metadata["scale"] + metadata.get("offset", 0)


def physical_im(values, field, unit):
    expected = "cm/s" if field == "PGV" else "%g"
    if unit != expected:
        raise ValueError(f"Unexpected {field} unit: {unit}")
    return np.asarray(values) / (1 if field == "PGV" else 100)


def fetch_catalog(survey):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "sentinel_catalog.json"
    bbox = [float(survey.longitude.min()) - .02, float(survey.latitude.min()) - .02,
            float(survey.longitude.max()) + .02, float(survey.latitude.max()) + .02]
    query = {"bbox": bbox, "datetime": f"{START}/{END}", "collection": "sentinel-2-l2a"}
    if path.exists():
        cached = json.loads(path.read_text())
        if cached["query"] != query:
            raise ValueError("Cached catalog query differs from frozen input query")
        return cached
    params = {"collections": "sentinel-2-l2a", "bbox": ",".join(map(str, bbox)), "datetime": f"{START}/{END}", "limit": 100}
    url, items = API, []
    while url:
        response = requests.get(url, params=params, timeout=90)
        response.raise_for_status()
        page = response.json()
        items.extend(page["features"])
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
        params = None
    result = {"query": query,
              "features": sorted(items, key=lambda f: f["id"])}
    write_json(path, result)
    return result


def ranked_candidates(items, lon, lat):
    candidates = [f for f in items if START <= f["properties"]["datetime"] <= END and f["properties"]["datetime"] < CUTOFF and
                  f["properties"].get("eo:cloud_cover", 100) <= 20 and
                  shape(f["geometry"]).covers(Point(lon, lat)) and all(b in f["assets"] for b in [*BANDS, "scl"])]
    # Latest sensing time breaks ties, then ID; selection never reads damage.
    candidates.sort(key=lambda f: f["id"])
    candidates.sort(key=lambda f: f["properties"]["datetime"], reverse=True)
    candidates.sort(key=lambda f: f["properties"]["eo:cloud_cover"])
    return candidates[:MAX_SCENES]


def read_window(dataset, bounds, target_crs=32637, size=PIXELS, categorical=False):
    if dataset.crs != rasterio.crs.CRS.from_epsg(target_crs):
        # Context products use geographic cells. Reproject directly to fixed UTM grid.
        from rasterio.vrt import WarpedVRT
        transform = rasterio.transform.from_bounds(*bounds, size, size)
        with WarpedVRT(dataset, crs=f"EPSG:{target_crs}", transform=transform, width=size, height=size,
                       nodata=0 if categorical else np.nan, dtype="uint8" if categorical else "float32",
                       resampling=Resampling.nearest if categorical else Resampling.bilinear) as vrt:
            return vrt.read(1, masked=True)
    window = from_bounds(*bounds, dataset.transform)
    return dataset.read(1, window=window, out_shape=(size, size), boundless=True, masked=True,
                        resampling=Resampling.nearest if categorical else Resampling.bilinear)


def audit_location(row, items):
    key = location_key(row.latitude, row.longitude)
    folder = RAW / "locations" / key
    folder.mkdir(parents=True, exist_ok=True)
    report_file = folder / "audit.json"
    if report_file.exists():
        report = json.loads(report_file.read_text())
        validate_cache(report, folder)
        return report
    bounds = grid_for(float(row.longitude), float(row.latitude))
    report = {"location_key": key, "latitude": float(row.latitude), "longitude": float(row.longitude),
              "utm37_bounds": bounds, "attempts": [], "selected_items": [], "status": "no_complete_clear_composite",
              "audit_spec_hash": spec_hash()}
    stack, masks = [], []
    for item in ranked_candidates(items, float(row.longitude), float(row.latitude)):
        try:
            with rasterio.open(item["assets"]["scl"]["href"]) as ds:
                scl = read_window(ds, bounds, categorical=True).filled(0)
            mask = clear_mask(scl)
            attempt = {"item": item["id"], "sensing_datetime": item["properties"]["datetime"],
                       "clear_fraction": float(mask.mean())}
            report["attempts"].append(attempt)
            if not mask.any():
                continue
            channels = []
            for band in BANDS:
                asset = item["assets"][band]
                with rasterio.open(asset["href"]) as ds:
                    pixels = read_window(ds, bounds)
                mask &= ~np.ma.getmaskarray(pixels)
                info = asset["raster:bands"][0]
                values = reflectance_from_asset(pixels.filled(0), info)
                mask &= np.isfinite(values)
                channels.append(values)
            if not mask.any():
                continue
            stack.append(np.stack(channels))
            masks.append(mask)
            report["selected_items"].append(item["id"])
            result, support = composite(stack, masks)
            report["complete_pixel_fraction"] = float((support > 0).mean())
            if result is not None:
                np.savez_compressed(folder / "reflectance.npz", reflectance=result, clear_observation_count=support)
                report.update(status="complete_clear_composite", min_clear_observations=int(support.min()),
                              max_clear_observations=int(support.max()), chip_sha256=digest(folder / "reflectance.npz"))
                break
        except (rasterio.errors.RasterioIOError, requests.RequestException) as exc:
            report["attempts"].append({"item": item["id"], "access_error": str(exc)})
    for name, url, categorical in [("worldcover_2021", WORLD_URL, True),
                                    ("copernicus_dem_2021", DEM_TEMPLATE.format(lat=int(row.latitude), lon=int(row.longitude)), False)]:
        try:
            with rasterio.open(url) as ds:
                a = read_window(ds, bounds, categorical=categorical)
                report[name] = {"url": url, "coverage_fraction": float((~np.ma.getmaskarray(a)).mean()),
                                "min": float(a.min()), "max": float(a.max()), "source_crs": str(ds.crs)}
                np.savez_compressed(folder / f"{name}.npz", values=a.filled(np.nan if not categorical else 0))
                report[name]["chip_sha256"] = digest(folder / f"{name}.npz")
        except rasterio.errors.RasterioIOError as exc:
            report[name] = {"url": url, "access_error": str(exc), "coverage_fraction": 0}
    write_json(report_file, report)
    return report


def sample_hazard(survey, network):
    path = RAW / "ShakeMapUpd.xml.gz"
    if not path.exists():
        if not network:
            raise FileNotFoundError("Pinned ShakeMap absent; use --network for the audit acquisition")
        response = requests.get(SHAKEMAP_URL, timeout=180)
        response.raise_for_status()
        path.write_bytes(response.content)
    if digest(path) != SHAKEMAP_SHA:
        raise ValueError("Pinned ShakeMap checksum mismatch")
    with gzip.open(path) as stream:
        root = ET.parse(stream).getroot()
    children = {c.tag.rsplit("}", 1)[-1]: c for c in root}
    fields = [c.attrib for c in root if c.tag.endswith("grid_field")]
    data = np.fromstring(children["grid_data"].text, sep=" ").reshape(-1, len(fields))
    spec = children["grid_specification"].attrib
    nx, ny = int(spec["nlon"]), int(spec["nlat"])
    xs, ys = np.unique(data[:, 0]), np.unique(data[:, 1])
    if len(xs) != nx or len(ys) != ny or len(data) != nx * ny:
        raise ValueError("Unexpected hazard grid")
    grid = data.reshape(ny, nx, len(fields))
    if not np.array_equal(grid[0, :, 0], xs) or not np.array_equal(grid[:, 0, 1], ys[::-1]):
        raise ValueError("Unexpected grid ordering")
    # Use actual printed nodes, not rounded nominal spacing. Ties choose lower coordinate.
    ix = np.abs(survey.longitude.to_numpy(float)[:, None] - xs).argmin(axis=1)
    iy = np.abs(survey.latitude.to_numpy(float)[:, None] - ys).argmin(axis=1)
    within = survey.longitude.between(xs.min(), xs.max()) & survey.latitude.between(ys.min(), ys.max())
    sampled = grid[ny - 1 - iy, ix]
    result = pd.DataFrame({"building_id": survey.building_id, "grid_longitude": sampled[:, 0], "grid_latitude": sampled[:, 1], "in_grid": within})
    names = {f["name"]: (int(f["index"]) - 1, f["units"]) for f in fields}
    for field, target in [("PGA", "PGA_g"), ("PGV", "PGV_cm_s"), ("PSA03", "SA_0p3_g"), ("PSA10", "SA_1p0_g")]:
        col, unit = names[field]
        result[target] = np.where(within, physical_im(sampled[:, col], field, unit), np.nan)
    result["sample_distance_m"] = np.diag(haversine_distances(survey[["latitude", "longitude"]], result[["grid_latitude", "grid_longitude"]]))
    result.to_parquet(OUT / "hazard.parquet", index=False)
    write_json(OUT / "hazard_provenance.json", {"source_url": SHAKEMAP_URL, "sha256": SHAKEMAP_SHA,
               "header": root.attrib, "event": children["event"].attrib, "grid": spec, "fields": fields,
               "sampling": "nearest actual grid node; ties choose lower lon/lat; outside bounds null, no extrapolation",
               "in_grid_records": int(within.sum()), "max_sample_distance_m": float(result.sample_distance_m.max()),
               "primary_H": "natural log of PGA_g, fixed before fitting; mainshock proxy for cumulative sequence damage"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true", help="Permit bounded metadata/COG/ShakeMap reads")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    survey = pd.read_parquet(ROOT / "data/processed/turkiye_2023/buildings.parquet")
    catalog_path = RAW / "sentinel_catalog.json"
    if not args.network and not catalog_path.exists():
        raise FileNotFoundError("Run --network once to audit actual public inputs")
    catalog = fetch_catalog(survey)
    unique = survey.drop_duplicates(["latitude", "longitude"])
    if not args.network:
        for row in unique.itertuples():
            key = location_key(row.latitude, row.longitude)
            if not (RAW / "locations" / key / "audit.json").exists():
                raise FileNotFoundError(f"No cached per-location audit: {key}")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                      GDAL_HTTP_TIMEOUT="60", GDAL_HTTP_MAX_RETRY="2", GDAL_CACHEMAX=512 * 1024 * 1024):
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            reports = []
            for i, result in enumerate(pool.map(lambda row: audit_location(row, catalog["features"]), unique.itertuples()), 1):
                reports.append(result)
                if i % 25 == 0:
                    print(f"Pixel/context audit: {i}/{len(unique)} distinct locations", flush=True)
    by_key = {r["location_key"]: r for r in reports}
    rows = []
    for row in survey.itertuples():
        r = by_key[location_key(row.latitude, row.longitude)]
        rows.append({"building_id": row.building_id, "city": row.city, "location_key": r["location_key"],
                     "eo_status": r["status"], "n_scenes": len(r["selected_items"]), "scene_ids": "|".join(r["selected_items"]),
                     "clear_pixel_fraction": r.get("complete_pixel_fraction", 0),
                     "worldcover_coverage": r["worldcover_2021"]["coverage_fraction"],
                     "dem_coverage": r["copernicus_dem_2021"]["coverage_fraction"]})
    pd.DataFrame(rows).to_csv(OUT / "location_audit.csv", index=False)
    write_json(OUT / "pixel_audit.json", {"catalog_sha256": digest(catalog_path), "locations": reports,
               "window": [START, END], "event_cutoff": CUTOFF, "bands": BANDS,
               "audit_spec": audit_spec(), "audit_spec_hash": spec_hash(),
               "support": "UTM37N 96x96 at10m; centre snapped10m; complete observed clear support, no nodata filling",
               "observations": len(survey), "distinct_coordinates": len(unique)})
    sample_hazard(survey, args.network)
    print("Completed pre-event feasibility and new pinned mainshock sampling; no models fitted.")


if __name__ == "__main__":
    main()
