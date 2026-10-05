# Milestone 1C: data expansion audit

Audit of locally acquired inputs on 2026-10-05. No models fitted, records removed,
or datasets pooled. Reproduction commands are in the [README](../README.md#milestone-1c-data-expansion-audit).
[Machine-readable aggregate results](data_expansion/summary.json) accompany this report.
Downloaded microdata, workbook cells, proximity candidates and derived row-level
Parquet files remain in ignored directories, outside Git.

## What is actually available

| Dataset | Records | Source variables | Coordinates | Acquisition |
|---|---:|---:|---|---|
| Existing Türkiye survey | 559 | See Milestone 1A dictionary | 559 present, 499 distinct pairs | Previously acquired |
| Nepal GEID | 762,106 | 19 | Administrative IDs only | Local, 78,448,526 bytes |
| Official HRHRS Building | **1,052,948 advertised** | **105 advertised** | No lat/lon/GPS variable in published Building dictionary | **Metadata only; microdata not acquired** |
| RC616 Priority I | **619** | 21 | 353 present, 335 distinct pairs | Three CSV tables acquired |
| ACI133 Türkiye | **242** | 106 physical columns | 242 present, 234 distinct pairs | Workbook acquired |
| Türkiye/Syria spatial package | **4,410,028 footprints** | Layer-specific | Georeferenced vectors/rasters | Entire ZIP acquired and inventoried |

These counts cannot be added as independent building observations. The footprint
inventory is not a count of surveyed or damage-labelled buildings.

## Nepal: strong evidence of a transformed HRHRS subset

The pinned [GEID file and provenance](https://github.com/gem/geid/tree/d6eb5ed42475ef67ba28cd9e0567f2d0d17a6393/South_Asia/Nepal/20150425_M7.8_Gorkha/1_Impact)
contain building/district/municipality/ward IDs, damage grade, occupancy, floors,
11 superstructure indicators and a reference field. All references identify the
2015 Nepal earthquake open-data source. There are no coordinates, building ages,
or detailed damage-assessment fields in this 19-column projection.

Every one of its **11 district counts exactly matches** the corresponding district
in the official HRHRS published DDI. See the
[district reconciliation](data_expansion/nepal_district_reconciliation.csv).
The [KLL portal account](https://kathmandulivinglabs.org/our-work/earthquake-data-portal)
also describes the government survey and portal handed to the National Planning
Commission. Together these support an HRHRS-derived 11-district projection.
Row-level equivalence remains unverified: we do not have the official file, and
GEID's `BUILDING_ID` has already been rounded to scientific-notation strings.
There are only **74 distinct ID strings** and **762,032 repeats after the first**.
Reading strings cannot recover lost precision; these IDs are unusable as unique
building keys or exact join keys.

| Damage grade | GEID measured rows | Official DDI published frequency |
|---|---:|---:|
| Grade 1 | 78,815 | 101,818 |
| Grade 2 | 87,257 | 141,996 |
| Grade 3 | 136,412 | 204,179 |
| Grade 4 | 183,844 | 253,135 |
| Grade 5 | 275,766 | 351,808 |
| Missing | 12 | 12 |

The official [Building dictionary](https://microdata.nsonepal.gov.np/index.php/catalog/69/data-dictionary/F2?file_name=Building)
and [full DDI](https://microdata.nsonepal.gov.np/index.php/metadata/export/69/ddi)
report 1,052,948 cases across 31 districts and 105 variables. The difference from
GEID is 290,842 cases, not a separate independent training sample. Published
variables include age, pre/post-earthquake floors and height, plinth area,
foundation and roof construction, superstructure flags, detailed structural and
geotechnical damage, overall grade, repair/reconstruction and secondary use.
The [105-variable inventory](data_expansion/nso_building_variables.csv) and
[category/statistics dictionary](data_expansion/nso_building_dictionary.json)
are public metadata, not downloaded Building microdata. No latitude, longitude or
GPS variable appears in that Building dictionary. Survey coverage differs:
census collection in 11 districts and verification of damaged-house lists
elsewhere; do not treat all districts as a uniform population sample.

**Access outcome:** the official `get-microdata` endpoint repeatedly returned a
successful HTTP status with an empty body. That is recorded as acquisition
failure, not a downloaded dataset. The [official study terms](https://microdata.nsonepal.gov.np/index.php/catalog/69/study-description)
specify public-use access from CBS premises, scientific/statistical research,
aggregate reporting, no redistribution without written agreement, and no
reidentification or identifying linkage. They also require citation and copies
of resulting publications. No application, account or agreement was submitted.
An authorized official Building file is the remaining acquisition dependency;
store it under `data/raw/nepal_2015/hrhrs_official/`. Do not use an unofficial
mirror to bypass that process. GEID carries CC BY-NC-SA 4.0; preserve upstream
restrictions and keep all Nepal row data outside this repository.

## RC616: 619 retained rows from six earthquakes

The [Sim et al. archive](https://datacenterhub.org/deedsdv/publications/view/454)
(DOI 10.7277/ACX0-DG18, CC BY-SA 3.0) advertises 616 buildings. Its archived
Priority I CSV actually has **619 unique Experiment IDs and event-case pairs**.
The reason for the three-row discrepancy is not established; all rows are retained.
The source media archive is 15,420,287,590 bytes. Acquisition streams only the
three explicitly named data/metadata CSV members, verifies pinned SHA-256 hashes,
and stops before downloading the full media archive.

| Event | Rows | Valid coordinate pairs |
|---|---:|---:|
| Erzincan 1992 | 49 | 0 |
| Düzce 1999 | 210 | 117 |
| Bingöl 2003 | 57 | 57 |
| Pisco, Peru 2007 | 27 | 20 |
| Wenchuan 2008 | 116 | 0 |
| Haiti 2010 | 160 | 159 |
| Total | 619 | 353 |

There are 266 missing coordinate pairs, no invalid present pairs, and 33 rows
belong to repeated-coordinate groups. Repeated coordinates do not establish
building identity. The [21-column source dictionary](data_expansion/rc616_variables.csv)
covers IDs/event, coordinates, floors, areas, structural and masonry damage,
captive columns and column/wall indices. This selected table has **no PGA/PGV/SA
fields**. Floor area is missing in 219 rows, masonry damage in 222 and captive
columns in 343; all source fields and blank values remain available as `raw__*`.

The project mapping is explicitly dataset-specific:

| Original structural labels | Ordinal | Rows |
|---|---:|---:|
| N / None | 0 | 67 |
| L / Light | 1 | 242 |
| M / Moderate | 2 | 122 |
| S / Severe | 3 | 180 |
| C | 4 | 7 |
| R (undocumented) | null | 1 |

The publication's four damage classes do not fully describe the table's observed
vocabulary. `R` remains unmapped, with its original label retained and reported.
Masonry damage remains a separate variable. This ordinal is not asserted to be
equivalent to Nepal grades or the original Türkiye survey scale.

## ACI133 Türkiye: 242 records, potential overlap unresolved

[Zenodo 13386343](https://zenodo.org/records/13386343), Hariri-Ardebili (2024),
is CC BY 4.0 according to the record API. `ACI133v3.xlsx` contains 242 records
on Sheet1, Excel rows 4–245; the first three rows contain group notes, headers
and units. Its 106 physical columns cover building properties (36), site (13),
Kriging intensity measures (37) and USGS measures (20).
The [column inventory](data_expansion/aci133_variables.csv) retains physical
column IDs, exact headers, source units and source blocks.

The five-class structural labels are **N=19, L=42, M=24, S=151, C=6**. The source's
three-class labels are **L=61, M=24, S=157**. All 242 IDs are unique and coordinates
are complete and valid; 13 records are in repeated-coordinate groups.

This is an augmented engineering dataset, not 242 fresh independent field
observations. **84 red-font cells across 42 rows** indicate author-supplemented
values. The workbook contains **5,091 formulas**, all with available cached
values. Local sidecars preserve formulas, cached results and supplementation
flags. Repeated M7.8 headers and inconsistent M7.5/M7.7, M6.7/M6.8 and M6.3/M6.4
labels prevent confident automatic event assignment. Physical column IDs avoid
silently conflating these measures. Seven columns (`c048`, `c049`, `c102`–`c106`)
each contain 106 literal `NaN` strings. Those tokens are separately reported
and retained; the source columns are stored as strings in the audit Parquet,
with separate numeric coordinates and mapped damage fields.

All-pairs haversine distance (sphere radius 6,371,008.8 m) against the existing
559 survey records gives:

| Threshold | Candidate pairs | ACI records involved | Existing survey records involved |
|---|---:|---:|---:|
| Exact coordinates | 0 | 0 | 0 |
| ≤10 m | 3 | 3 | 3 |
| ≤25 m | 21 | 12 | 20 |
| ≤50 m | 60 | 19 | 45 |
| ≤100 m | 214 | 34 | 99 |

The closest pair is 5.323 m apart. Proximity is a screening result, not proof of
identity; absent exact matches do not prove independence. Source-specific IDs
provide no verified cross-source identity key. Candidate IDs/distances are saved
locally for later adjudication. **Do not claim 801 independent buildings** or
randomly split these surveys without resolving shared buildings/sites.

## Spatial package: separate products with different label meanings

[Zenodo 18437501](https://zenodo.org/records/18437501), Liu (2026), declares
CC BY 4.0 in its API metadata. The full ZIP is **584,760,454 bytes**, contains
75 members including directories, and expands to **2,916,264,899 bytes**.
The [archive inventory](data_expansion/spatial_archive_inventory.json) lists every
member. Preserve original-source attribution; the deposit license does not by
itself resolve every upstream product's rights.

| Layer/product | Feature count | Observed attributes and interpretation |
|---|---:|---|
| GBA building footprints | 4,410,028 | source, id, height, var, region; no damage field |
| This_study Antakya | 23,167 | damage_lev 1: 3,742; 2: 2,894; 3: 12,338; 4: 4,193 |
| This_study Jindires | 6,081 | damage_lev 1: 2,884; 2: 740; 3: 2,022; 4: 435 |
| This_study Nurdagi | 874 | damage_lev 1: 20; 2: 48; 3: 524; 4: 282 |
| Visual interpretation Antakya | 17,148 | Join_Count 0–7; **not an explicit damage grade** |
| Visual interpretation Jindires | 2,764 | Footprint attributes, no explicit grade |
| Visual interpretation Nurdagi | 778 | Footprint attributes, no explicit grade |
| UNOSAT Jindires | 500 points | Damage 202; Possible Damage 298; all “Not yet field validated” |
| Microsoft Nurdagi | 834 polygons | damaged=0: 773; damaged=1: 61; also dmg and area |
| ARIA Antakya/Jindires/Nurdagi | 3 ground overlays | RGBA PNGs, zero building placemarks; not calibrated numeric DPM rasters |

`This_study` totals **30,122** records; visual interpretation totals **20,690**.
Do not sum products as independent labels. Numeric `damage_lev` meanings require
a codebook before mapping to engineering grades. Do not interpret Join_Count as
damage severity, infer negative controls from missing visual selections, or
assume the Microsoft `dmg` numeric field has the engineering scale.
Jindires is in **Syria**, despite the archive's Türkiye name.

The footprint bounds are longitude 34.419118–38.965014 and latitude
35.635616–39.121592, EPSG:4326. Counts/schema/bounds of that 4.4M-feature layer
were read from metadata; its geometry validity and attributes were not fully
scanned. All smaller vector layers were fully scanned. Antakya visual
interpretation contains **9 invalid geometries** and **8 duplicate geometries
after the first**. No automatic repair or removal was performed.

Point intersections with `This_study` polygons involve 6 existing-survey / 5 ACI
records in Antakya and 0 / 18 in Nurdagi; neither engineering dataset intersects
Jindires. These indicate spatial coverage, not verified building matches or
agreement of labels. Detailed bounds, categories, missingness and intersection
counts are in the aggregate JSON.

All five raster bands were scanned in windows, including nodata accounting:

| Raster | Columns × rows | Encoding | Observed valid range | Declared nodata |
|---|---|---|---|---|
| DEM | 16,409 × 12,768 | float32 | −6 to 3,887 | −3.402823466e38 |
| Epicenter distance | 42,911 × 38,736 | uint8 | 15 to 255 | 0 |
| Fault distance | 48,334 × 38,778 | uint8 | 15 to 195 | 255 |
| Lithology | 32,818 × 26,225 | uint8 | 1 to 13 | 15 |
| PGV | 32,818 × 25,533 | uint8 | 4 to 168 | 255 |

They use geographic WGS84, with scale=1, offset=0 and no declared physical band
units. Full uint8 value histograms and pixel accounting are retained. **Do not
interpret encoded PGV or distance values as physical cm/s or metres** without
an encoding/codebook. ARIA overlays have image sizes 15,000×12,868 (Antakya),
9,659×10,000 (Jindires) and 12,000×7,384 (Nurdagi); image headers and geographic
extents were inventoried without decoding the large rendered images.

## Reproducibility and next boundary

Acquisition records URLs, sizes and SHA-256 hashes; GEID is pinned to a commit,
ACI/spatial downloads verify published MD5 checksums, and RC table hashes are
pinned. Empty or failed acquisitions exit nonzero and are recorded explicitly.
Offline auditing preserves original records and values, produces local Parquet
for RC616/ACI133, and emits aggregate JSON and complete variable inventories.
Tests cover damage mapping, coordinate accounting, distance units, nonfinite
JSON values, selective/archive-safe extraction and local dataset regressions.
CI uses no Nepal microdata and skips unavailable local-data regressions.

Pause collection here. Before modelling, obtain authorized HRHRS access and
restore trustworthy building identifiers, resolve engineering-survey overlap,
clarify ACI event headers/supplementation, and obtain spatial label/raster
codebooks. Preserve event identity and dataset-specific label provenance.
Italy Da.D.O. remains deferred.
