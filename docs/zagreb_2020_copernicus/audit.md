# Zagreb EMSN074 — FileGDB measurement and suitability decision

**Decision: auxiliary remote-sensing damage product, not a large-N labelled
building vulnerability dataset. Do not describe 1H as “Zagreb acquired and
suitable”, and do not merge on that basis.** The reference map has nearly 30,000
building polygons; the damage layer has only 556 polygons, does not provide
undamaged controls, and does not form a complete one-to-one building join.

## Reproduce

```bash
python -m pip install -r requirements-audit.txt
python -m src.data.acquire_zagreb_copernicus
python -m src.data.audit_zagreb_copernicus
python -m pytest -q
```

The audit verifies the observed archive SHA256
`96fdaa2e40fc0e9a74f6a1b075df563b700d40e890ea84bc864877a0b6c36c93`,
checks ZIP CRCs and safe paths, then extracts a fresh temporary GDB under ignored
`data/raw/zagreb_2020_copernicus/`. The hash pins our acquired archive; it is not
claimed to be a publisher-supplied checksum. No modified geometries, inferred
labels, or training records are created. Every listed layer is fully read.

`layer_audit.json` contains every layer's feature count, columns, dtypes,
missingness, low-cardinality native values, CRS/bounds, geometry checks,
embedded field aliases/domains, and join diagnostics. `layer_counts.csv` and
`damage_counts.csv` provide compact review tables. Native category strings are
preserved. Row-level geodata remain outside Git.

## What the GDB contains

There are **30 layers/tables exposed by pyogrio: 14 spatial layers and 16 empty
non-spatial internal raster-support tables**. The latter are not building or
damage observations. All spatial layers use **EPSG:32633, WGS84 / UTM zone 33N**,
with metre coordinates. The JSON also gives each layer's longitude/latitude bounds.

| Layer | Features | Role |
|---|---:|---|
| P02_building_poly | **29,398** | Reference building footprints |
| P02_building_point | **687** | Reference building points; do not add to polygon count as unique buildings |
| P08_damage_assessment_poly | **556** | Damage-assessment polygons |
| P09_reconstruction_monitoring_poly | **560** | Later reconstruction status, not extra damage labels |
| P02_road_line | 7,007 | Roads |
| P02_railway_line | 729 | Railways |
| P02_cart_track_line | 43 | Tracks |
| P02_power_station_poly | 2 | Power stations |
| P02_facility_poly | 137 | Facilities |
| P02_helipad_poly | 2 | Helipads |
| P02_tunnel_point / P02_tunnel_line | 21 / 5 | Tunnels |
| P02_bridge_line / P02_bridge_point | 47 / 44 | Bridges |

Thus there are **two reference-building layers, one damage-assessment layer,
and one separate reconstruction layer**. Damage bounds in WGS84 are approximately
**15.925331–16.083939°E, 45.782613–45.848795°N**.

All 556 damage polygons have valid, nonempty MultiPolygon geometry and a
recognized, non-null native category. No normalized duplicate geometries occur
in the two reference-building layers, damage layer or reconstruction layer.
The reference building polygons include **23 invalid geometries**; none are
repaired silently. OGR FIDs are unique within each layer, not global building IDs.

## Actual category semantics

Definitions are recovered directly from the **GDB_Items XML domain bindings**,
not inferred from numeric code order. `damage_gra` is bound to
`damage_grade_list`:

| Native string code | Embedded domain label | Damage polygons |
|---|---|---:|
| `1` | Possible damage | **244** |
| `2` | Moderate damage | **136** |
| `3` | Severe damage | **155** |
| `4` | Destroyed | **21** |

Every damage record has `notation=2`, whose bound domain says **Impact on
buildings**, and `det_method=1`, **Photo-interpretation**. This establishes the
object of interest, not one polygon per separately identified building or a
whole-building engineering damage grade.

The [official activation description](https://mapping.emergency.copernicus.eu/activations/EMSN074/DAMAGEASSESSMENT/)
specifies roof/chimney assessment using post-event drone/VHR imagery. It dates
the reference imagery to 2019 and distinguishes May reconstruction monitoring
from the April damage imagery. Therefore damage polygons are relevant to
buildings, but should remain a remote-sensing component-damage product rather
than being renamed engineering inspection labels.

There is **no undamaged category**. Unmatched reference buildings are unlabelled,
not confirmed undamaged. `Possible damage` is not a negative control either.
P09 statuses are New (1), Unchanged (147), Reconstruction on-going (115), Removed
(5), Reconstructed (292); these are counts for the embedded category names, not
additional first-event damage observations.

## Can the reference and damage layers link one-to-one?

**No, not across the dataset.** There is no documented shared unique building key
or embedded relationship class. Common columns (`aoi_id`, `det_method`,
`notation`, `or_src_id`) are nonunique descriptors. Source identifiers refer to
imagery sources, not building identities. Layer-local OBJECTID/FID must not be
joined as if it were a global ID.

Full-geometry intersection diagnostics give **617 pairs**, covering all **556
damage polygons** but only **325 reference polygons**. **58 damage polygons**
intersect multiple references; **110 reference polygons** intersect multiple
damage polygons. Raw intersections include **62 pairs involving invalid
reference geometry**, so those are diagnostic only.

For defensible area comparisons the audit excludes invalid geometries without
repair. This gives **555 positive-area pairs**, covering **497 damage polygons
and 315 reference polygons**. The other 59 damage polygons lack a valid positive-
area reference match. Exact topological equality gives **zero pairs**.

Fixed intersection-over-union (IoU) diagnostics, using valid geometries only:

| Minimum IoU | Mutually unique reference–damage pairs |
|---|---:|
| 0.50 | 127 |
| 0.90 | 100 |
| 0.95 | 99 |
| 0.99 | **99** |
| 0.999 | 99 |

At IoU ≥0.99, the native category counts are **50 possible, 14 moderate, 19
severe, 16 destroyed**. These are 99 high-overlap *candidate* correspondences,
not a newly approved training cohort. The thresholds are reported together;
none was optimized to inflate the dataset. No nearest-neighbour assignment,
geometry rounding/repair, worst-damage aggregation or label filling is used.

**491 damage polygons are at least 95% covered by a valid reference polygon**,
yet only 99 have near-equal footprints. This is consistent with damage regions
occupying parts of larger reference footprints; containment alone cannot prove
an independent, unique building identity. Both the mapping purpose and measured
many-to-many relationships preclude counting all 29,398 references as labelled.

## Usable sample size and project decision

- **556** valid, categorized damage polygons: usable as native mapping-product
  observations, subject to the roof/chimney interpretation and selection bias.
- **99** near-identical, mutually unique footprint candidates at IoU ≥0.99:
  potentially useful for a small external comparison after semantic review.
- **No verified large-N complete labelled-building inventory**, and **zero
  explicit undamaged controls** in the damage product. Neither 29,398 nor
  29,398+687 is a defensible supervised sample count.

Keep Zagreb **auxiliary** for reference geometry, damage-location checks or a
small product-specific external validation. It is unsuitable as the main
large-N vulnerability training dataset or a representative damage-rate/loss
sample. No shaking field is present in these building/damage layers; hazard
sampling would be an additional step even for a future small experiment.
Noto remains the stronger large-N candidate. No models fitted, no cross-dataset
target harmonization, no post-event imagery used as predictors, and no PR merged.

Validation: **96 tests passed**, including six Zagreb tests and an actual-GDB
regression. Two fresh extractions/audit runs produced byte-identical JSON and
both aggregate CSVs. Tests cover many-to-one footprint parts, invalid geometry
exclusion without repair, CRS rejection, unsafe ZIP paths, and archive pinning.
