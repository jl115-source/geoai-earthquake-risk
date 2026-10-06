# Milestone 1G — Noto 2024 actual-data audit

**Verdict: a viable large-N GeoAI candidate with a native survived/destroyed
target and complete MMI, conditional on a pre-event input audit and a geographic
evaluation protocol. It is not yet a modelling-ready or loss-calibrated dataset.**
No models were fitted, no target was harmonized to Türkiye, and no post-event
imagery was used as a predictor. All counts below use every source record.

## Reproduce

From the repository root, with Python 3.11 and `requirements-audit.txt` installed:

```bash
python -m src.data.acquire_large_geoai noto
python -m src.data.audit_noto
python -m pytest -q
```

The pinned GeoPackage stays in ignored `data/raw/noto_2024/`. The audit writes
only aggregate CSVs to `docs/noto_2024/`, execution evidence to
`docs/noto_2024_execution.json`, and seven PNGs to ignored `results/noto_2024/`.
No row-level derived file is committed or required. The JSON records software
versions, input checksums, aggregate hashes, and figure hashes. Different
rendering environments can change PNG bytes; repeated runs in the recorded
environment are checked separately from portable numeric accounting tests.

## Provenance and native meanings

Input: [Zenodo version 2.5](https://zenodo.org/records/15192949),
`Noto_Peninsula_Damage_2_5.gpkg`, **47,853,568 bytes**.
MD5 **`280e9c53cb45086786c20ed0b2c21ffb`** matches the published pin;
SHA256 `1adf3ff883951db42728448e6f338f93c9d0343d11de11fd8274dabfc27aaf9d`.
The deposit API declares **CC BY 4.0**. Preserve Vescovo et al. attribution and
upstream GSI/imagery attribution; the deposit license is not a blanket license
for all third-party imagery.

The authors describe human visual assessment, subsequently checked using
submitted evidence and limited surveys. These are independent annotations,
not model-generated pseudo-labels. Their [methods and Table 2](https://essd.copernicus.org/articles/17/5259/2025/)
define survived as including undamaged and some damaged structures; destroyed
includes structural failure from multiple mechanisms. Obscured and inconsistent
footprints are non-target states. `damage_val` is the post-validation class;
validation does not imply every record received a ground inspection.

The **GeoPackage's own embedded QGIS style** independently confirms the native
`damage_val` names: `0=Survived`, `1=Destroyed`, `9=Obscured (cloud/shade)`,
`99=Missing/inconsistent`. These category definitions are recorded in the
execution JSON, not inferred from their numeric ordering.

**Schema discrepancy:** no `damage` column exists in this pinned file. There is
`damage_2`. It is retained under that exact name and counted as raw codes.
It plausibly corresponds to the published initial-assessment field, but that
equivalence is not established. It must not be silently renamed or treated as
an ordinal scale. The acquisition manifest now reports the actual field.

## Full-record integrity

- **140,208 records**, all `MultiPolygon`, CRS **EPSG:4326**.
- Bounds `(west, south, east, north)`:
  **(136.670683417, 37.000347909, 137.360662401, 37.529975389)**.
- **0 null, 0 empty, 0 invalid geometries**; no invalid/out-of-range coordinate vertices.
- **0 duplicate polygons**, both orientation/order-normalized exact WKB and
  topological equality among valid polygons. No rounding or repair is applied.
- **9,441 partially overlapping polygon pairs** (`shapely.overlaps`), not exact
  duplicates. This count excludes containment and boundary-only contact. Such
  footprints require spatial grouping/overlap review before splitting.
- **140,208 unique `fid` values**, no missing or duplicated primary IDs.
- `s_fid` is **not a unique building key**: 25,689 rows have literal `manual`.
  Excluding that sentinel, 482 repeated-ID groups contain 975 records
  (493 extra occurrences). Including it, there are 483 repeated-ID groups and
  26,181 extra occurrences. Do not merge rows on this field.
- SQLite integrity check: **ok**. The file also contains a non-spatial
  `layer_styles` table; only `v2.5` is the building layer.

## Every source column

SQLite storage types and actual loaded dtypes are recorded rather than relying
on the deposit's nominal Int8/Bool schema. `fid` is explicitly recovered from the
OGR feature index; SQLite `geom` is exposed by the reader as `geometry`.

| Source column | SQLite / loaded dtype | Nulls | Meaning and caution |
|---|---|---:|---|
| `fid` | INTEGER / int64 | 0 | Unique GeoPackage building key |
| `s_fid` | TEXT / object | 0 | Original serialization identifier or `manual`; nonunique |
| `source` | TEXT / object | 135,320 | Oblique assessment source reference; also 2 blank strings; not an exposure variable |
| `damage_val` | MEDIUMINT / int32 | 0 | Validated native target/status code |
| `municipality` | TEXT / object | 22 | Native Japanese prefecture/city/locality string |
| `conf` | TEXT / object | 313 | Assessment source coverage category; not numeric probability |
| `damage_2` | MEDIUMINT / int32 | 0 | Undocumented field-name discrepancy; raw codes preserved |
| `GSI_fire` | INTEGER / int64 | 0 | Mapped fire-polygon intersection flag |
| `GSI_tsunami` | INTEGER / int64 | 0 | Mapped inundation-polygon intersection flag |
| `GSI_slope_failure` | INTEGER / int64 | 0 | Mapped slope-failure-polygon intersection flag |
| `USGS_MMI` | REAL / float64 | 0 | Inherited USGS shaking intensity |
| `geom` → `geometry` | MULTIPOLYGON / geometry | 0 | Building footprint |

Blank strings are counted separately, not converted to nulls. All null fractions
are in the execution JSON. Confidence counts: **119,085 `single`, 20,810 `multi`,
313 null**. These reflect source/oblique coverage, not calibrated reliability
scores; keep them as audit strata, not predictive exposure features.

## Native damage counts

| Native value | `damage_2` (semantics unconfirmed) | `damage_val` | Verified `damage_val` meaning |
|---|---:|---:|---|
| 0 | 112,320 | **112,275** | Survived; may still be damaged |
| 1 | 3,361 | **3,461** | Destroyed |
| 9 | 9,460 | **9,437** | Obscured |
| 99 | 15,067 | **15,035** | Missing/inconsistent footprint |

Both columns are complete with no unexpected codes. They disagree in **156
records**; `damage_cross_tab.csv` records every transition. There are **115,736
binary-target records**, not 140,208 usable binary labels. The remaining **24,472**
records retain native status codes and are not recoded as survived or removed
from the audit. Both destroyed and survived buildings are represented; a distinct
undamaged count is unavailable because it is combined within survived.

## Geographic coverage

There are **863 distinct non-null native locality strings**, with every count in
`municipality_native_counts.csv`. For city/town summaries only, the audit takes
the second token separated by the literal `、` delimiter, leaving the original
field intact. This gives seven named municipalities plus 22 missing records:

| Derived city/town | Records | Validated destroyed |
|---|---:|---:|
| 七尾市 (Nanao) | 43,898 | 116 |
| 中能登町 (Nakanoto) | 1,643 | 0 |
| 志賀町 (Shika) | 20,778 | 76 |
| 珠洲市 (Suzu) | 23,001 | 1,767 |
| 穴水町 (Anamizu) | 6,989 | 77 |
| 能登町 (Noto) | 17,177 | 113 |
| 輪島市 (Wajima) | 26,700 | 1,310 |
| Missing | 22 | 2 |

These are coverage counts, not municipal census totals. `municipality_damage.csv`,
`municipality_damage_no_secondary_flags.csv`, and `municipality_mmi.csv` expose
class support and shaking ranges for future split design. Nakanoto has no
destroyed examples, so some discrimination metrics will be undefined there;
city-level averages must disclose the imbalance and this partial coverage.

## Shaking and secondary perils

**MMI coverage: 140,208 / 140,208 (100%)**, no null/nonfinite/out-of-range values.
Range **7.2–9.0**, mean **8.259644**, median **8.4**, SD **0.382742**.
There are ten native values, spaced 0.2 apart; these are retained, not rounded
or reinterpolated. All frequencies and the native damage-by-MMI cross-tab are
versioned. No PGA, PGV, or spectral acceleration fields are supplied. The file
does not identify an exact USGS ShakeMap product revision or sampling procedure;
pinning the GeoPackage pins these values, not their full upstream derivation.

| Secondary-peril flag | Positive | Explicit zero | Null |
|---|---:|---:|---:|
| `GSI_fire` | **311** | 139,897 | 0 |
| `GSI_slope_failure` | **169** | 140,039 | 0 |
| `GSI_tsunami` | **3,418** | 136,790 | 0 |

All flags are 0/1. Their union contains **3,898** records; **0** records have
multiple positive flags. **136,310** have all three flags explicitly zero.
Within this apparently shaking-only subset, **112,228** have binary labels:
**109,771 survived + 2,457 destroyed**. This is an explicit audit subset, not a
committed training cohort. Zero flags only mean no mapped intersection; they
do not exclude liquefaction, unmapped slope effects, land deformation, or other
damage mechanisms. These post-event flags may define cohort restrictions or
sensitivity analyses, but must not become pre-event predictors.

## Project suitability and remaining gates

**Common minimum: yes for the binary-labelled subset.** It has georeferenced
footprints, human-assessed D independent of our proposed predictor pipeline,
and a complete native shaking H (MMI). It does not yet establish cross-event
hazard comparability, statistical independence of neighbouring observations,
or that label error is unrelated to location/visibility. Audit regional error
and source coverage rather than treating every label as ground-survey truth.

**Exposure X is sparse.** Location, footprint shape/area potential, and locality
are available. Structure type, materials, age, floors, height, occupancy,
replacement cost, contents value, and engineering condition are absent.
Morphology could be computed in a projected CRS but is not computed as a model
feature here. The curated footprints need a chronology check before predictive
use: retrospective additions/corrections can encode selection even when intended
to represent pre-event buildings. IDs, annotation source, confidence, label/status
codes, and secondary-peril outcomes are not substitutes for X.

| Intended use | Assessment |
|---|---|
| Large-N GeoAI training | **Suitable candidate**: 115,736 classified records, or 112,228 after mapped-secondary-peril exclusion. Must first audit pre-2024 imagery coverage/chronology, freeze target/cohort, and handle imbalance and annotation uncertainty. |
| Held-out municipality/geographic evaluation | **Suitable**, with seven uneven municipalities; group overlapping/nearby buildings and spatial contexts, buffer split boundaries, resolve 22 missing municipality values explicitly, and assess label/MMI support. One earthquake alone cannot validate event transfer. |
| Incomplete-exposure experiments | **Suitable for naturally sparse-X deployment and H vs H+Z comparisons**. Cannot supply its own rich-X reference or controlled rich-exposure masking experiment without another inventory. |
| Later catastrophe-loss modelling | **Conditional input, not a complete risk model**. Binary survival does not imply zero loss; need external damage-to-MDR/consequence assumptions, values/taxonomies, exposure completeness, event rates/catalogue, and uncertainty/dependence treatment. No direct AAL/OEP/AEP from this one damage inventory. |

No universal Türkiye/Noto damage mapping is introduced. No feature matrix or
learning split is frozen here. Post-event imagery supports the source annotations
only; this audit acquires none as a predictor. Future EO must be strictly
pre-event, with all transforms fitted on training geography only when modelling
is separately authorized.

## Figures

All valid centroids (140,208) are plotted in EPSG:6675; no data subsampling is
used. Overplotting is disclosed, and all numerical summaries use full records.
No external basemap or post-event image layer is used.

1. `results/noto_2024/damage_map.png` — native validated damage/status.
2. `results/noto_2024/damage_2_map.png` — alternate native field, codes only.
3. `results/noto_2024/mmi_map.png` — native shaking intensity.
4. `results/noto_2024/damage_counts.png` — both fields, all four codes.
5. `results/noto_2024/damage_vs_mmi.png` — counts and destroyed fraction among 0/1 labels.
6. `results/noto_2024/secondary_peril_map.png` — three exposure-intersection panels.
7. `results/noto_2024/secondary_peril_counts.png` — full-record counts and union.

## Implementation checks

Acquisition now verifies a newly downloaded temporary file **before** promotion
to the final filename; corrupt content cannot poison the cache as a completed
download. Existing files are checksum-checked without network access. The
manifest reports `damage_2` instead of the nonexistent advertised `damage`.
Tests exercise checksum rejection/retry, cached downloads, schema/CRS failures,
unknown flags/codes, missing/nonfinite MMI, overlapping peril flags, null/empty/
invalid/duplicate geometries, native municipality preservation, and deterministic
aggregate exports. A full-file test checks the pinned checksum and measured
report whenever raw data are locally present; it skips explicitly otherwise.

Validation result: **90 passed, 0 failed, 0 skipped**, including eight new Noto
tests and the full-file check. Two independent audit processes produced
byte-identical execution JSON, eight CSVs, and seven PNGs (16 artifacts). All
seven figures were visually inspected. See `noto_2024_validation.json`.
